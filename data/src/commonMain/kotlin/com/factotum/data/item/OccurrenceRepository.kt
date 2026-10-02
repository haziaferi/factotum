package com.factotum.data.item

import com.factotum.core.recurrence.EditChanges
import com.factotum.core.recurrence.EditPlace
import com.factotum.core.recurrence.EditScope
import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.clashes
import com.factotum.core.recurrence.occurrencesWithEdits
import com.factotum.core.recurrence.timed
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.PersonalSettings
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/**
 * Two edits of one occurrence made apart that a person must settle (ADR 11); the later applies
 * meanwhile. Keeping both is offered for one occurrence only: a pattern cannot be in two places.
 */
data class OccurrenceQuestion(val itemId: String, val earlier: String, val later: String, val canKeepBoth: Boolean)

/** The answer to an [OccurrenceQuestion]: keep one edit's schedule, or keep both as two occurrences. */
sealed interface OccurrenceAnswer {
    data class Keep(val editId: String) : OccurrenceAnswer

    data object KeepBoth : OccurrenceAnswer
}

/**
 * ADR 11: changes to single occurrences, a week, a day or "from now on", kept in one insert-once
 * log for every kind of item. Undo tombstones the edit. Writes go through [writes]; [newId] makes ids.
 */
internal class OccurrenceRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val personal: PersonalSettings,
) {
    private val dao = db.itemDao()
    private val readings = db.trackerDao()
    private val clock = writes.clock

    suspend fun skip(itemId: String, occurrence: LocalDateTime) =
        edit(itemId, EditScope.OCCURRENCE, EditChanges(skip = true), at = occurrence)

    /** Moves one occurrence to [day], at [time] if given, else its own time. */
    suspend fun move(itemId: String, occurrence: LocalDateTime, day: LocalDate, time: LocalTime? = null) =
        edit(itemId, EditScope.OCCURRENCE, EditChanges(movedTo = day, time = time), at = occurrence)

    suspend fun change(itemId: String, occurrence: LocalDateTime, changes: EditChanges) =
        edit(itemId, EditScope.OCCURRENCE, changes, at = occurrence)

    /** "This day only": every occurrence of [itemId] on [day]. */
    suspend fun thisDay(itemId: String, day: LocalDate, changes: EditChanges) = edit(itemId, EditScope.DAY, changes, date = day)

    /** "This week" (tasks and events gain it, ADR 11): the week of [monday], or only its [days]. */
    suspend fun thisWeek(itemId: String, monday: LocalDate, changes: EditChanges, days: Set<DayOfWeek> = emptySet()) =
        edit(itemId, EditScope.WEEK, changes, date = monday, days = days)

    /** A week's confirmed days, as the planner stores them (ADR 04's PLANNED kind). */
    suspend fun confirmWeek(itemId: String, monday: LocalDate, days: Set<DayOfWeek>) =
        edit(itemId, EditScope.WEEK, EditChanges(weekDays = days), date = monday)

    /** "From now on": every occurrence from [day], or only on [days]. */
    suspend fun fromNowOn(itemId: String, day: LocalDate, changes: EditChanges, days: Set<DayOfWeek> = emptySet()) =
        edit(itemId, EditScope.FROM, changes, date = day, days = days)

    /** An occurrence the series does not have. */
    suspend fun add(itemId: String, at: LocalDateTime) = edit(itemId, EditScope.EXTRA, EditChanges(), at = at)

    /** Undoes one edit: the series underneath shows again. */
    suspend fun undo(editId: String) = writes.edit(OCCURRENCE_EDIT, editId, WHOLE) { s -> mapOf("deleted_at" to s.hlc) }

    /**
     * [itemId]'s occurrences in `[from, to)`, its live edits applied. A habit rolls from its last
     * Log and shows none while paused (ADR 06). None once the item is deleted.
     */
    suspend fun occurrences(itemId: String, from: LocalDateTime, to: LocalDateTime): List<Occurrence> {
        val item = dao.items(listOf(itemId)).singleOrNull()?.takeIf { it.deletedAt == null } ?: return emptyList()
        val start = item.dtstart() ?: return emptyList()
        val habit = item.trackerId?.let { t ->
            if (readings.trackers(listOf(t)).singleOrNull()?.deletedAt != null) return emptyList()
            habitStates(readings, listOf(HabitRef(itemId, t, item.pauseFrom, item.pauseUntil)), personal.dayStart(), from, to).getValue(itemId)
        } ?: HabitState.NONE
        val recurrence = item.recurrence()
        val edits = dao.liveEditsOf(itemId).map { it.toEdit() }
        return recurrence.occurrencesWithEdits(itemId, start, item.title, item.durationMin, edits, from, to, habit.lastDone)
            .filter { !habit.paused(it, recurrence.timed(it, edits, item.startTime != null)) }
    }

    suspend fun questions(): List<OccurrenceQuestion> =
        dao.liveEdits().map { it.itemId to it.toEdit() }.groupBy({ it.first }, { it.second }).flatMap { (itemId, edits) ->
            clashes(edits).map { (a, b) -> OccurrenceQuestion(itemId, a.id, b.id, canKeepBoth = a.scope == EditScope.OCCURRENCE) }
        }

    /**
     * Settles a clash with a new edit on the same place that has seen both, so it settles them on
     * every device. Keeping one re-sets that edit's schedule fields; the other's title and other
     * non-schedule fields still merge (ADR 11). Keeping both also adds an occurrence where the
     * earlier edit had put it, under an id made from that edit, so two devices answering alike
     * make one. Two devices answering differently make two corrections that clash in turn.
     */
    suspend fun answer(question: OccurrenceQuestion, answer: OccurrenceAnswer) {
        val edits = dao.liveEditsOf(question.itemId).map { it.toEdit() }
        val earlier = edits.single { it.id == question.earlier }
        val later = edits.single { it.id == question.later }
        val kept = when (answer) {
            is OccurrenceAnswer.Keep -> {
                require(answer.editId == earlier.id || answer.editId == later.id) { "${answer.editId} is not in this question" }
                if (answer.editId == earlier.id) earlier else later
            }
            OccurrenceAnswer.KeepBoth -> {
                require(question.canKeepBoth) { "keeping both is for one occurrence" }
                val original = requireNotNull(earlier.at)
                val item = requireNotNull(dao.items(listOf(question.itemId)).singleOrNull()) { "no item ${question.itemId}" }
                val start = requireNotNull(item.dtstart())
                // Where the earlier edit had put the occurrence, with every other edit as it is: on its
                // own day, or a day an edit of this occurrence moved it to.
                val days = listOf(original.date) + edits.filter { it.place == earlier.place }.mapNotNull { it.changes.movedTo }
                val there = item.recurrence().occurrencesWithEdits(
                    question.itemId, start, item.title, null, edits - later,
                    LocalDateTime(days.min(), LocalTime(0, 0)), LocalDateTime(days.max().plus(1, DateTimeUnit.DAY), LocalTime(0, 0)),
                ).first { it.original == original }
                write(question.itemId, "both-${earlier.id}", EditScope.EXTRA, EditChanges(title = there.title.takeIf { it != item.title }), at = there.at)
                later
            }
        }
        val schedule = kept.changes
        write(question.itemId, newId(), kept.scope, EditChanges(movedTo = schedule.movedTo, time = schedule.time, durationMin = schedule.durationMin, rule = schedule.rule, weekDays = schedule.weekDays),
            at = kept.at, date = kept.date, days = kept.days)
    }

    /** Writes one edit; its base is the newest edit on the same place this device has seen, live or undone. */
    private suspend fun edit(
        itemId: String,
        scope: EditScope,
        changes: EditChanges,
        at: LocalDateTime? = null,
        date: LocalDate? = null,
        days: Set<DayOfWeek> = emptySet(),
    ): String = write(itemId, newId(), scope, changes, at, date, days)

    /** Writes one edit as [id]; it has seen every edit on the same place this device holds, live or undone. */
    private suspend fun write(
        itemId: String,
        id: String,
        scope: EditScope,
        changes: EditChanges,
        at: LocalDateTime? = null,
        date: LocalDate? = null,
        days: Set<DayOfWeek> = emptySet(),
    ): String {
        val place = EditPlace(scope, at, date, days)
        var seen = emptyList<String>()
        writes.write({
            seen = dao.editsOf(itemId).map { it.toEdit() }.filter { it.place == place && it.id != id }.map { it.id }.sorted()
            mapOf(OCCURRENCE_EDIT to listOf(id))
        }) { store, _ ->
            // Keep both twice, from two devices, is one occurrence: the second finds the first's row.
            if (store.row(id) != null) return@write
            val s = clock.tick()
            writes.merger.created(store, Row(OCCURRENCE_EDIT, id, mapOf(
                WHOLE to Group(s, mapOf(
                    "item_id" to itemId, "scope" to scope.name, "at" to at?.toString(), "date" to date?.toString(),
                    "days" to maskOf(days), "changes" to EditCodec.encode(changes), "created_hlc" to s.hlc,
                    "created_device" to s.device, "seen" to seen.joinToString(","), "deleted_at" to null,
                )),
            )))
        }
        return id
    }
}
