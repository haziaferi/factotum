package com.factotum.data.item

import com.factotum.core.habit.HabitPresence
import com.factotum.core.habit.Log
import com.factotum.core.habit.dayOf
import com.factotum.core.habit.presenceOf
import com.factotum.core.plan.BlockOverride
import com.factotum.core.plan.Overrides
import com.factotum.core.plan.PlanHabit
import com.factotum.core.plan.PlanWeek
import com.factotum.core.plan.TimeBlock
import com.factotum.core.plan.mondayOf
import com.factotum.core.plan.planWeek
import com.factotum.core.recurrence.EditScope
import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.inForceOn
import com.factotum.core.recurrence.occurrencesWithEdits
import com.factotum.core.recurrence.timed
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.PersonalSettings
import com.factotum.data.tracker.GOAL
import com.factotum.data.tracker.TRACKER
import com.factotum.data.tracker.TrackerRepository
import com.factotum.data.tracker.TrackerType
import com.factotum.data.sync.StagedStore
import com.factotum.data.tracker.TrackerDao
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/** The start of a day, as local times are kept. */
internal val MIDNIGHT = LocalTime(0, 0)

/** Today's amount against a daily goal: "6 of 8 glasses". */
data class Progress(val amount: Double, val goal: Double?)

/**
 * Habits (ADR 06): items of kind HABIT, each Logged as readings on its tracker. A habit and its
 * tracker are made together (owner, 2026-10-02); deleting the habit leaves the tracker and its
 * Logs. A habit that uses an existing tracker shares its Logs: they belong to the tracker, which the
 * habit is a face of. [personal] gives the personal day boundary (owner, 2026-10-02), a
 * PERSONAL setting (ADR 09).
 */
internal class HabitRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val personal: PersonalSettings,
) {
    private val items = db.itemDao()
    private val readings = db.trackerDao()
    private val trackers = TrackerRepository(db, writes, newId)
    private val clock = writes.clock

    /**
     * A habit and, unless it uses an existing [trackerId], its own tracker of [type], made in one
     * write. A number habit Logs [amountPerLog] by default; [dailyGoal] becomes the tracker's
     * recurring daily goal ("8 glasses a day").
     */
    suspend fun create(
        title: String,
        start: LocalDate,
        at: LocalTime? = null,
        recurrence: Recurrence? = null,
        type: TrackerType = TrackerType.BOOLEAN,
        unit: String? = null,
        unitLabel: String? = null,
        amountPerLog: Double? = null,
        dailyGoal: Double? = null,
        blockId: String? = null,
        durationMin: Long? = null,
        trackerId: String? = null,
    ): String {
        require(type != TrackerType.CHOICE) { "a habit Logs a yes, a rating or a number; a choice tracker has no presence" }
        if (trackerId != null && dailyGoal != null) {
            require(trackers.goalsOf(trackerId).none { it.period == "DAY" }) { "tracker $trackerId already has a daily goal" }
        }
        val habit = newId()
        val tracker = trackerId ?: newId()
        val goal = dailyGoal?.let { newId() to it }
        val made = if (trackerId == null) listOf(tracker) else emptyList()
        writes.write(mapOf(ITEM to listOf(habit), TRACKER to made, GOAL to listOfNotNull(goal?.first))) { store ->
            if (trackerId == null) writes.merger.created(store, trackers.trackerRow(tracker, title, type, unit, unitLabel, amountPerLog))
            goal?.let { (id, value) -> writes.merger.created(store, trackers.trackerGoalRow(id, tracker, "DAY", value)) }
            val schedule = schedule(start, at, null, null, null) + recurrenceValues(recurrence) + ("duration_min" to durationMin)
            writes.merger.created(store, itemRow(habit, clock.tick(), ItemKind.HABIT, title, null, schedule, null, 0, null, trackerId = tracker, blockId = blockId))
        }
        return habit
    }

    /**
     * Logs [habitId] at [at]. With no value, a yes/no habit Logs "yes" and a number habit its
     * amount per Log; [occurrence] names which of several a day this Log is for.
     */
    suspend fun log(habitId: String, at: LocalDateTime, number: Double? = null, rating: Int? = null, yes: Boolean? = null, occurrence: LocalDateTime? = null): String {
        val (habit, tracker) = habitAndTracker(habitId)
        val given = number != null || rating != null || yes != null
        val type = TrackerType.valueOf(tracker.type)
        require(given || type == TrackerType.BOOLEAN || type == TrackerType.NUMBER) { "a ${type.name.lowercase()} habit Logs a value" }
        val y = if (!given && type == TrackerType.BOOLEAN) true else yes
        val n = if (!given && type == TrackerType.NUMBER) requireNotNull(tracker.defaultNumber) { "say how much: ${habit.title} has no amount per Log" } else number
        return trackers.log(tracker.id, at, yes = y, rating = rating, number = n, occurrence = occurrence)
    }

    /** Undoes the latest Log of [habitId] counting for [day]: one glass less, or the day's "yes" gone. */
    suspend fun undo(habitId: String, day: LocalDate): Boolean = trackers.undoLast(habitAndTracker(habitId).second.id, day, personal.dayStart())

    suspend fun presence(habitId: String, today: LocalDate): HabitPresence = presenceOf(logsOf(habitId), today, personal.dayStart())

    /** Today's amount against the tracker's daily goal, if it has one. */
    suspend fun progress(habitId: String, today: LocalDate): Progress {
        val tracker = habitAndTracker(habitId).second
        val dayStart = personal.dayStart()
        val amount = logsOf(habitId).filter { it.isPresence && dayOf(it.at, dayStart) == today }.sumOf { it.number ?: 1.0 }
        return Progress(amount, trackers.goalsOf(tracker.id).firstOrNull { it.period == "DAY" }?.value)
    }

    /** Pauses [habitId] from [from], until [until] or until resumed. */
    suspend fun pause(habitId: String, from: LocalDate, until: LocalDate? = null) =
        writes.edit(ITEM, habitId, SCHEDULE) { mapOf("pause_from" to from.toString(), "pause_until" to until?.toString()) }

    suspend fun resume(habitId: String) = writes.edit(ITEM, habitId, SCHEDULE) { mapOf("pause_from" to null, "pause_until" to null) }

    /**
     * The plan of the week holding [day] (Tendril's planner, ADR 04's PLANNED): every live habit's
     * occurrences, edits applied and paused days gone, placed in the day's time blocks, with the
     * days suggested for each "n a week" habit whose week is not confirmed yet. A habit whose rule
     * this version cannot read is left out, not the whole plan.
     */
    suspend fun planWeek(day: LocalDate): PlanWeek {
        val monday = mondayOf(day)
        val week = (0 until 7).map { monday.plus(it, DateTimeUnit.DAY) }
        val from = LocalDateTime(monday, MIDNIGHT)
        val to = LocalDateTime(monday.plus(7, DateTimeUnit.DAY), MIDNIGHT)
        val habits = items.liveHabits()
        val edits = items.liveEdits().groupBy({ it.itemId }, { it.toEdit() })
        val dayStart = personal.dayStart()
        val states = habitStates(readings, habits.map { HabitRef(it.id, requireNotNull(it.trackerId), it.pauseFrom, it.pauseUntil) }, dayStart, from, to)
        val plan = habits.mapNotNull { h ->
            val recurrence = runCatching { h.recurrence() }.getOrElse { return@mapNotNull null }
            val start = requireNotNull(h.dtstart())
            val state = states.getValue(h.id)
            val mine = edits[h.id].orEmpty()
            val rules = week.associateWith { recurrence.inForceOn(it, mine) }
            PlanHabit(
                itemId = h.id,
                rules = rules,
                blockId = h.blockId,
                durationMin = (h.durationMin ?: 0).toInt(),
                setTime = h.startTime != null,
                occurrences = recurrence.occurrencesWithEdits(h.id, start, h.title, h.durationMin, mine, from, to, state.lastDone)
                    .filter { o -> !state.paused(o, recurrence.timed(o, mine, h.startTime != null)) },
                pool = week.filter { d ->
                    val r = rules.getValue(d) as? Recurrence.Planned
                    r?.per == Recurrence.Planned.Per.WEEK && d.dayOfWeek in r.days && d >= start.date && !state.pausedOn(d) &&
                        mine.none { it.changes.skip && it.reaches(LocalDateTime(d, start.time)) }
                },
                confirmed = mine.any { it.scope == EditScope.WEEK && it.date == monday && it.changes.weekDays != null },
                sortOrder = h.sortOrder ?: 0.0,
            )
        }
        return planWeek(monday, blocks(), plan)
    }

    /** The live time blocks, in their order. */
    suspend fun blocks(): List<TimeBlock> = items.liveBlocks().map { it.toBlock() }

    suspend fun addBlock(start: Int, end: Int, name: String, icon: String? = null, hue: Int? = null): String {
        val id = newId()
        val position = items.liveBlocks().maxOfOrNull { it.position + 1 } ?: 0
        writes.write(mapOf(HABIT_BLOCK to listOf(id))) { store ->
            writes.merger.created(store, Row(HABIT_BLOCK, id, mapOf(WHOLE to Group(clock.tick(), mapOf(
                "name" to name, "start_minute" to start.toLong(), "end_minute" to end.toLong(), "position" to position, "icon" to icon,
                "hue" to hue?.toLong(), "overrides" to null, "deleted_at" to null,
            )))))
        }
        return id
    }

    /**
     * Gives [blockId] new usual times, or new times on [on] those weekdays only. Weekday times stay
     * until retimed: a block retimed for weekends keeps those hours when its usual ones change.
     */
    suspend fun retimeBlock(blockId: String, start: Int, end: Int, on: Set<DayOfWeek> = emptySet()) = writes.write(mapOf(HABIT_BLOCK to listOf(blockId))) { store ->
        val row = requireNotNull(store.row(blockId)) { "no block $blockId" }
        val values = if (on.isEmpty()) {
            mapOf("start_minute" to start.toLong(), "end_minute" to end.toLong())
        } else {
            val kept = Overrides.parse(row.groups.getValue(WHOLE).values["overrides"] as String?)
                .mapNotNull { o -> (o.days - on).takeIf { it.isNotEmpty() }?.let { o.copy(days = it) } }
            mapOf("overrides" to Overrides.format(kept + BlockOverride(on, start, end)))
        }
        store.put(row.edit(WHOLE, clock.tick(), values))
    }

    suspend fun renameBlock(blockId: String, name: String) = writes.edit(HABIT_BLOCK, blockId, WHOLE) { mapOf("name" to name) }

    /** Deletes [blockId]; habits in it are then placed at any time of the day, as in Tendril. */
    suspend fun deleteBlock(blockId: String) = writes.edit(HABIT_BLOCK, blockId, WHOLE) { s -> mapOf("deleted_at" to s.hlc) }

    private suspend fun logsOf(habitId: String): List<Log> = trackers.logs(habitAndTracker(habitId).second.id)

    /** The live habit and its live tracker: a habit whose tracker was deleted (on any device) is deleted too. */
    private suspend fun habitAndTracker(habitId: String) = run {
        val habit = requireNotNull(items.items(listOf(habitId)).singleOrNull()?.takeIf { it.kind == ItemKind.HABIT.name && it.deletedAt == null }) { "no habit $habitId" }
        habit to requireNotNull(readings.trackers(listOf(requireNotNull(habit.trackerId))).singleOrNull()?.takeIf { it.deletedAt == null }) { "habit $habitId has no tracker" }
    }
}

/**
 * What decides a habit's occurrences beyond its rule (ADR 06): the day of its last presence Log,
 * which a rolling habit rolls from; its pause; and which occurrences are already Logged. All by the
 * personal day ([dayStart]): a timed occurrence's is the day its time counts for, a whole-day
 * one's is its own date (`timed`, from the series and its edits).
 */
internal class HabitState(
    val lastDone: LocalDate?,
    private val pauseFrom: LocalDate?,
    private val pauseUntil: LocalDate?,
    private val dayStart: LocalTime,
    private val named: Set<LocalDateTime>,
    private val unnamedPerDay: Map<LocalDate, Int>,
) {
    fun pausedOn(day: LocalDate): Boolean = pauseFrom != null && day >= pauseFrom && (pauseUntil == null || day <= pauseUntil)

    fun paused(o: Occurrence, timed: Boolean): Boolean = pausedOn(dayOf(o, timed))

    private fun dayOf(o: Occurrence, timed: Boolean): LocalDate = if (timed) dayOf(o.at, dayStart) else o.at.date

    /**
     * [occurrences] (in time order) less those already Logged: one a presence Log names, and for each
     * Log that names none, the first other occurrence of its day. Three doses a day, one Logged, leave two.
     */
    fun unlogged(occurrences: List<Occurrence>, timed: (Occurrence) -> Boolean): List<Occurrence> {
        val left = unnamedPerDay.toMutableMap()
        return occurrences.filter { o ->
            if (o.original in named || o.at in named) return@filter false
            val day = dayOf(o, timed(o))
            val n = left[day] ?: 0
            if (n > 0) left[day] = n - 1
            n == 0
        }
    }

    companion object {
        val NONE = HabitState(null, null, null, LocalTime(0, 0), emptySet(), emptyMap())
    }
}

/** A habit as [habitStates] reads it: its tracker, whose Logs it counts, and its own pause. */
internal class HabitRef(val id: String, val trackerId: String, val pauseFrom: String?, val pauseUntil: String?)

/**
 * The [HabitState] of each of [habits] over `[from, to)`, by habit id: the last presence from one
 * query, and only the Logs of that window (a day either side, for the personal day). Habits that
 * share a tracker share its Logs, each with its own pause.
 */
internal suspend fun habitStates(
    dao: TrackerDao,
    habits: Collection<HabitRef>,
    dayStart: LocalTime,
    from: LocalDateTime,
    to: LocalDateTime,
): Map<String, HabitState> {
    val ids = habits.map { it.trackerId }.distinct()
    if (ids.isEmpty()) return emptyMap()
    val last = ids.chunked(StagedStore.CHUNK).flatMap { dao.lastPresence(it) }.associate { it.trackerId to dayOf(LocalDateTime.parse(it.at), dayStart) }
    val lo = LocalDateTime(from.date.plus(-1, DateTimeUnit.DAY), from.time).toString()
    val hi = LocalDateTime(to.date.plus(1, DateTimeUnit.DAY), to.time).toString()
    val logs = ids.chunked(StagedStore.CHUNK).flatMap { dao.presenceBetween(it, lo, hi) }.groupBy { it.trackerId }
    return habits.associate { h ->
        val window = logs[h.trackerId].orEmpty()
        h.id to HabitState(
            lastDone = last[h.trackerId],
            pauseFrom = h.pauseFrom?.let(LocalDate::parse),
            pauseUntil = h.pauseUntil?.let(LocalDate::parse),
            dayStart = dayStart,
            named = window.mapNotNull { it.occurrence?.let(LocalDateTime::parse) }.toSet(),
            unnamedPerDay = window.filter { it.occurrence == null }.groupingBy { dayOf(LocalDateTime.parse(it.at), dayStart) }.eachCount(),
        )
    }
}
