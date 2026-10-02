package com.factotum.data.item

import com.factotum.core.habit.HabitPresence
import com.factotum.core.habit.Log
import com.factotum.core.habit.dayOf
import com.factotum.core.habit.presenceOf
import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.Recurrence
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.tracker.GOAL
import com.factotum.data.tracker.TRACKER
import com.factotum.data.tracker.TrackerRepository
import com.factotum.data.tracker.TrackerType
import com.factotum.data.sync.StagedStore
import com.factotum.data.tracker.TrackerDao
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/** Today's amount against a daily goal: "6 of 8 glasses". */
data class Progress(val amount: Double, val goal: Double?)

/**
 * Habits (ADR 06): items of kind HABIT, each Logged as readings on its tracker. A habit and its
 * tracker are made together (owner, 2026-10-02); deleting the habit leaves the tracker and its
 * Logs. A habit that uses an existing tracker shares its Logs: they belong to the tracker, which the
 * habit is a face of. [dayStart] is the personal day boundary (owner, 2026-10-02), midnight until
 * settings carry it (slice 09).
 */
internal class HabitRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val dayStart: LocalTime = LocalTime(0, 0),
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
            goal?.let { (id, value) -> writes.merger.created(store, trackers.goalRow(id, tracker, "DAY", value)) }
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
    suspend fun undo(habitId: String, day: LocalDate): Boolean = trackers.undoLast(habitAndTracker(habitId).second.id, day, dayStart)

    suspend fun presence(habitId: String, today: LocalDate): HabitPresence = presenceOf(logsOf(habitId), today, dayStart)

    /** Today's amount against the tracker's daily goal, if it has one. */
    suspend fun progress(habitId: String, today: LocalDate): Progress {
        val tracker = habitAndTracker(habitId).second
        val amount = logsOf(habitId).filter { it.isPresence && dayOf(it.at, dayStart) == today }.sumOf { it.number ?: 1.0 }
        return Progress(amount, trackers.goalsOf(tracker.id).firstOrNull { it.period == "DAY" }?.value)
    }

    /** Pauses [habitId] from [from], until [until] or until resumed. */
    suspend fun pause(habitId: String, from: LocalDate, until: LocalDate? = null) =
        writes.edit(ITEM, habitId, SCHEDULE) { mapOf("pause_from" to from.toString(), "pause_until" to until?.toString()) }

    suspend fun resume(habitId: String) = writes.edit(ITEM, habitId, SCHEDULE) { mapOf("pause_from" to null, "pause_until" to null) }

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
 * personal day ([dayStart]).
 */
internal class HabitState(
    val lastDone: LocalDate?,
    private val pauseFrom: LocalDate?,
    private val pauseUntil: LocalDate?,
    private val dayStart: LocalTime,
    private val named: Set<LocalDateTime>,
    private val unnamedPerDay: Map<LocalDate, Int>,
) {
    fun paused(at: LocalDateTime): Boolean {
        val day = dayOf(at, dayStart)
        return pauseFrom != null && day >= pauseFrom && (pauseUntil == null || day <= pauseUntil)
    }

    /**
     * [occurrences] (in time order) less those already Logged: one a presence Log names, and for each
     * Log that names none, the first other occurrence of its day. Three doses a day, one Logged, leave two.
     */
    fun unlogged(occurrences: List<Occurrence>): List<Occurrence> {
        val left = unnamedPerDay.toMutableMap()
        return occurrences.filter { o ->
            if (o.original in named || o.at in named) return@filter false
            val day = dayOf(o.at, dayStart)
            val n = left[day] ?: 0
            if (n > 0) left[day] = n - 1
            n == 0
        }
    }

    companion object {
        val NONE = HabitState(null, null, null, LocalTime(0, 0), emptySet(), emptyMap())
    }
}

/**
 * The [HabitState] of each habit tracker among [trackerIds] over `[from, to)`: the last presence
 * from one query, and only the Logs of that window (a day either side, for the personal day).
 */
internal suspend fun habitStates(
    dao: TrackerDao,
    trackerIds: Collection<String>,
    pause: (String) -> Pair<String?, String?>,
    dayStart: LocalTime,
    from: LocalDateTime,
    to: LocalDateTime,
): Map<String, HabitState> {
    val ids = trackerIds.distinct()
    if (ids.isEmpty()) return emptyMap()
    val last = ids.chunked(StagedStore.CHUNK).flatMap { dao.lastPresence(it) }.associate { it.trackerId to dayOf(LocalDateTime.parse(it.at), dayStart) }
    val lo = LocalDateTime(from.date.plus(-1, DateTimeUnit.DAY), from.time).toString()
    val hi = LocalDateTime(to.date.plus(1, DateTimeUnit.DAY), to.time).toString()
    val logs = ids.chunked(StagedStore.CHUNK).flatMap { dao.presenceBetween(it, lo, hi) }.groupBy { it.trackerId }
    return ids.associateWith { t ->
        val (pauseFrom, pauseUntil) = pause(t)
        val window = logs[t].orEmpty()
        HabitState(
            lastDone = last[t],
            pauseFrom = pauseFrom?.let(LocalDate::parse),
            pauseUntil = pauseUntil?.let(LocalDate::parse),
            dayStart = dayStart,
            named = window.mapNotNull { it.occurrence?.let(LocalDateTime::parse) }.toSet(),
            unnamedPerDay = window.filter { it.occurrence == null }.groupingBy { dayOf(LocalDateTime.parse(it.at), dayStart) }.eachCount(),
        )
    }
}
