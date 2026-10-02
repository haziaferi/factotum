package com.factotum.data.tracker

import com.factotum.core.habit.Log
import com.factotum.core.habit.dayOf
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.ITEM
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.WHOLE
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

enum class TrackerType { NUMBER, BOOLEAN, RATING, CHOICE }

/**
 * Trackers (Chronicle's, SPEC §0.1.5) as far as habits need them: making one, Logging on it and
 * undoing a Log, its goals, and deleting it, which takes the habits that use it (owner,
 * 2026-10-02). The rest of the Trackers module comes with it in §7 step 3.
 */
internal class TrackerRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val dao = db.trackerDao()
    private val items = db.itemDao()
    private val clock = writes.clock

    /** A new tracker row, for [create] or for a habit made in the same write. */
    internal fun trackerRow(id: String, name: String, type: TrackerType, unit: String?, unitLabel: String?, defaultNumber: Double?) =
        Row(TRACKER, id, mapOf(WHOLE to Group(clock.tick(), mapOf(
            "name" to name, "type" to type.name, "unit" to unit, "unit_label" to unitLabel, "default_number" to defaultNumber,
            "default_bool" to null, "default_rating" to null, "polarity" to "NEUTRAL", "archived" to false, "sort_order" to 0L,
            "deleted_at" to null,
        ))))

    /** A daily (or weekly, monthly) amount to reach, kept as Chronicle's recurring, automatic goal. */
    internal fun goalRow(id: String, trackerId: String, period: String, value: Double) =
        Row(GOAL, id, mapOf(WHOLE to Group(clock.tick(), mapOf(
            "target_type" to "TRACKER", "target_id" to trackerId, "period" to period, "value" to value, "kind" to "RECURRING",
            "completion_mode" to "AUTO", "achieved_at" to null, "deleted_at" to null,
        ))))

    suspend fun create(name: String, type: TrackerType, unit: String? = null, unitLabel: String? = null, defaultNumber: Double? = null): String {
        val id = newId()
        writes.write(mapOf(TRACKER to listOf(id))) { store -> writes.merger.created(store, trackerRow(id, name, type, unit, unitLabel, defaultNumber)) }
        return id
    }

    /** One Log, at the local time it was made; exactly one value, as the tracker's type takes. */
    suspend fun log(
        trackerId: String,
        at: LocalDateTime,
        yes: Boolean? = null,
        rating: Int? = null,
        number: Double? = null,
        choiceId: String? = null,
        occurrence: LocalDateTime? = null,
        note: String? = null,
    ): String {
        val type = requireNotNull(dao.trackers(listOf(trackerId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no tracker $trackerId" }.type
        val fits = when (TrackerType.valueOf(type)) {
            TrackerType.NUMBER -> number != null
            TrackerType.BOOLEAN -> yes != null
            TrackerType.RATING -> rating != null
            TrackerType.CHOICE -> choiceId != null
        }
        require(fits) { "a $type tracker Logs a ${type.lowercase()}" }
        val id = newId()
        writes.write(mapOf(TRACKER_READING to listOf(id))) { store ->
            writes.merger.created(store, Row(TRACKER_READING, id, mapOf(WHOLE to Group(clock.tick(), mapOf(
                "tracker_id" to trackerId, "at" to at.toString(), "number_value" to number, "bool_value" to yes,
                "rating_value" to rating?.toLong(), "choice_id" to choiceId, "label" to null, "note" to note,
                "occurrence" to occurrence?.toString(), "deleted_at" to null,
            )))))
        }
        return id
    }

    /** Undoes the Log made last among those that count for [day] (Tendril's undo); false when there is none. */
    suspend fun undoLast(trackerId: String, day: LocalDate, dayStart: LocalTime): Boolean {
        val last = dao.liveReadingsOf(listOf(trackerId)).filter { dayOf(LocalDateTime.parse(it.at), dayStart) == day }
            .maxByOrNull { Stamp(it.hlc, it.device) } ?: return false
        writes.edit(TRACKER_READING, last.id, WHOLE) { s -> mapOf("deleted_at" to s.hlc) }
        return true
    }

    suspend fun logs(trackerId: String): List<Log> = dao.liveReadingsOf(listOf(trackerId)).map { it.toLog() }

    suspend fun goalsOf(trackerId: String): List<GoalEntity> = dao.goalsOf(trackerId)

    /**
     * Deletes the tracker and, with it, every habit that uses it and its goals (owner, 2026-10-02).
     * A habit another device makes on it meanwhile is deleted too: readers treat a habit whose
     * tracker is deleted as deleted.
     */
    suspend fun delete(trackerId: String) = writes.write({
        mapOf(TRACKER to listOf(trackerId), ITEM to items.liveHabitsOf(trackerId), GOAL to dao.goalsOf(trackerId).map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(trackerId)) { "no tracker $trackerId" }.edit(WHOLE, s, mapOf("deleted_at" to s.hlc)))
        for (habit in targets.getValue(ITEM)) store.put(requireNotNull(store.row(habit)).edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
        for (goal in targets.getValue(GOAL)) store.put(requireNotNull(store.row(goal)).edit(WHOLE, s, mapOf("deleted_at" to s.hlc)))
    }

    /**
     * "Delete forever": the purges travel. Its habits, readings and choices go by the foreign keys;
     * its goals, which name it without one (Chronicle), are purged with it.
     */
    suspend fun purge(trackerId: String) = writes.write({
        mapOf(TRACKER to listOf(trackerId), GOAL to dao.everyGoalOf(trackerId))
    }) { store, targets ->
        writes.merger.purge(store, trackerId)
        targets.getValue(GOAL).forEach { writes.merger.purge(store, it) }
    }
}

internal fun TrackerReadingEntity.toLog() =
    Log(LocalDateTime.parse(at), yes = boolValue, rating = ratingValue?.toInt(), number = numberValue, choiceId = choiceId)
