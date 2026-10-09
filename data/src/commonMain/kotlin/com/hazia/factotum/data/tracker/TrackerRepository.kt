package com.hazia.factotum.data.tracker

import com.hazia.factotum.core.habit.Log
import com.hazia.factotum.core.habit.dayOf
import com.hazia.factotum.core.sync.Group
import com.hazia.factotum.core.sync.Row
import com.hazia.factotum.core.sync.Stamp
import com.hazia.factotum.data.FactotumDatabase
import com.hazia.factotum.data.LocalWrites
import com.hazia.factotum.data.item.ITEM
import com.hazia.factotum.data.item.SCHEDULE
import com.hazia.factotum.data.item.WHOLE
import com.hazia.factotum.data.label.LABELLED
import com.hazia.factotum.data.time.TIME_SPAN
import com.hazia.factotum.data.time.endRunning
import com.hazia.factotum.data.time.localNow
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

enum class TrackerType { NUMBER, BOOLEAN, RATING, CHOICE }

data class Tracker(val id: String, val name: String, val type: TrackerType)

/**
 * Trackers (Chronicle's, SPEC §0.1.5) as far as habits need them: making one, Logging on it and
 * undoing a Log, its goals, and deleting it, which takes the habits that use it (owner,
 * 2026-10-02). The rest of the Trackers module comes with it in §7 step 3.
 */
internal class TrackerRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val now: () -> LocalDateTime = ::localNow,
) {
    private val dao = db.trackerDao()
    private val items = db.itemDao()
    private val times = db.timeDao()
    private val clock = writes.clock

    /** A new tracker row, for [create] or for a habit made in the same write. */
    internal fun trackerRow(id: String, name: String, type: TrackerType, unit: String?, unitLabel: String?, defaultNumber: Double?): Row {
        val s = clock.tick()
        return Row(TRACKER, id, mapOf(
            WHOLE to Group(s, mapOf(
                "name" to name, "type" to type.name, "unit" to unit, "unit_label" to unitLabel, "default_number" to defaultNumber,
                "default_bool" to null, "default_rating" to null, "polarity" to "NEUTRAL", "sort_order" to 0L,
                "deleted_at" to null,
            )),
            LABELLED to Group(s, mapOf("label_id" to null)),
        ))
    }

    /** A daily (or weekly, monthly) amount to reach, kept as Chronicle's recurring, automatic goal. */
    internal fun trackerGoalRow(id: String, trackerId: String, period: String, value: Double) = goalRow(id, clock.tick(), "TRACKER", trackerId, period, value, "RECURRING")

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

    suspend fun goalsOf(trackerId: String): List<GoalEntity> = dao.goalsOf("TRACKER", trackerId)

    /**
     * Deletes the tracker and, with it, every habit that uses it and its goals (owner, 2026-10-02);
     * the habits' running timers stop. A habit another device makes on it meanwhile is deleted
     * too: readers treat a habit whose tracker is deleted as deleted.
     */
    suspend fun delete(trackerId: String) = writes.write({
        val habits = items.liveHabitsOf(trackerId)
        mapOf(TRACKER to listOf(trackerId), ITEM to habits, GOAL to dao.goalsOf("TRACKER", trackerId).map { it.id }, TIME_SPAN to times.runningOf(habits))
    }) { store, targets ->
        val s = clock.tick()
        endRunning(store, targets.getValue(TIME_SPAN), now(), s)
        store.put(requireNotNull(store.row(trackerId)) { "no tracker $trackerId" }.edit(WHOLE, s, mapOf("deleted_at" to s.hlc)))
        for (habit in targets.getValue(ITEM)) store.put(requireNotNull(store.row(habit)).edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
        for (goal in targets.getValue(GOAL)) store.put(requireNotNull(store.row(goal)).edit(WHOLE, s, mapOf("deleted_at" to s.hlc)))
    }

    /**
     * Restores [trackerId] from the Trash (owner, 2026-10-09), with the habits and goals its deletion
     * took, in that one stamp; a habit or goal deleted by hand before stays deleted. A new stamp, so
     * the restore syncs as any edit does.
     */
    suspend fun restore(trackerId: String) = writes.write({
        val tracker = requireNotNull(dao.trackers(listOf(trackerId)).singleOrNull()?.takeIf { it.deletedAt != null }) { "tracker $trackerId is not in the Trash" }
        mapOf(
            TRACKER to listOf(trackerId),
            ITEM to items.habitsOf(trackerId).filter { it.deletedAt == tracker.deletedAt }.map { it.id },
            GOAL to dao.goals(dao.everyGoalOf("TRACKER", trackerId)).filter { it.deletedAt == tracker.deletedAt }.map { it.id },
        )
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(trackerId)).edit(WHOLE, s, mapOf("deleted_at" to null)))
        for (habit in targets.getValue(ITEM)) store.put(requireNotNull(store.row(habit)).edit(SCHEDULE, s, mapOf("deleted_at" to null)))
        for (goal in targets.getValue(GOAL)) store.put(requireNotNull(store.row(goal)).edit(WHOLE, s, mapOf("deleted_at" to null)))
    }

    /** The live trackers, by name. */
    suspend fun trackers(): List<Tracker> = dao.allTrackers().filter { it.deletedAt == null }.map { it.toTracker() }.sortedWith(compareBy({ it.name.lowercase() }, { it.id }))

    /** The trackers in the Trash. */
    suspend fun trashed(): List<Tracker> = dao.allTrackers().filter { it.deletedAt != null }.map { it.toTracker() }

    /**
     * "Delete forever", from the Trash only (owner, 2026-10-09): the purges travel. Its habits, readings and choices go by the foreign keys;
     * its goals, which name it without one (Chronicle), are purged with it.
     */
    suspend fun purge(trackerId: String) = writes.write({
        require(requireNotNull(dao.trackers(listOf(trackerId)).singleOrNull()) { "no tracker $trackerId" }.deletedAt != null) { "only a tracker in the Trash is deleted forever" }
        mapOf(TRACKER to listOf(trackerId), GOAL to dao.everyGoalOf("TRACKER", trackerId))
    }) { store, targets ->
        writes.merger.purge(store, trackerId)
        targets.getValue(GOAL).forEach { writes.merger.purge(store, it) }
    }
}

/** A goal on a tracker or an activity (ADR 07: an activity's goal names the activity item), automatic as Chronicle's are. */
internal fun goalRow(id: String, s: Stamp, targetType: String, targetId: String, period: String, value: Double, kind: String) =
    Row(GOAL, id, mapOf(WHOLE to Group(s, mapOf(
        "target_type" to targetType, "target_id" to targetId, "period" to period, "value" to value, "kind" to kind,
        "completion_mode" to "AUTO", "achieved_at" to null, "deleted_at" to null,
    ))))

private fun TrackerEntity.toTracker() = Tracker(id, name, TrackerType.valueOf(type))

internal fun TrackerReadingEntity.toLog() =
    Log(LocalDateTime.parse(at), yes = boolValue, rating = ratingValue?.toInt(), number = numberValue, choiceId = choiceId)
