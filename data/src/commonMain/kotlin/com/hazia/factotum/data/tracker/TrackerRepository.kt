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
import com.hazia.factotum.data.label.labelKey
import com.hazia.factotum.data.label.nfc
import com.hazia.factotum.data.page.automatic
import com.hazia.factotum.data.page.byHand
import com.hazia.factotum.data.time.TIME_SPAN
import com.hazia.factotum.data.time.endRunning
import com.hazia.factotum.data.time.localNow
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

enum class TrackerType { NUMBER, BOOLEAN, RATING, CHOICE }

data class Tracker(val id: String, val name: String, val type: TrackerType)

/** One option of a CHOICE tracker, which a Log picks (SPEC:R203). */
data class TrackerChoice(val id: String, val label: String, val color: Long?)

/**
 * Trackers (Chronicle's, SPEC:R79) as far as habits need them: making one, Logging on it and
 * undoing a Log, its goals, and deleting it, which takes the habits that use it (owner,
 * 2026-10-02); and a CHOICE tracker's choices, kept as a database's Select options are,
 * except that a deleted one still reads on its Logs (SPEC:R203). The rest of the Trackers module comes with the sole-owner modules (SPEC:R195).
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
        var picked: String? = null
        writes.write({
            // A live choice of this tracker's, read through merges, inside the write (SPEC:R203).
            picked = choiceId?.let { c ->
                val choices = dao.choicesOf(trackerId)
                requireNotNull(chainEnd(choices)(c)?.takeIf { end -> choices.any { it.id == end && it.deletedAt == null } }) { "no choice $c on $trackerId" }
            }
            mapOf(TRACKER_READING to listOf(id))
        }) { store, _ ->
            writes.merger.created(store, Row(TRACKER_READING, id, mapOf(WHOLE to Group(clock.tick(), mapOf(
                "tracker_id" to trackerId, "at" to at.toString(), "number_value" to number, "bool_value" to yes,
                "rating_value" to rating?.toLong(), "choice_id" to picked, "label" to null, "note" to note,
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

    /** Its Logs; a choice merged into another reads as that one (SPEC:R203). */
    suspend fun logs(trackerId: String): List<Log> {
        val resolve = chainEnd(dao.choicesOf(trackerId))
        return dao.liveReadingsOf(listOf(trackerId)).map { it.toLog().copy(choiceId = resolve(it.choiceId) ?: it.choiceId) }
    }

    /** A CHOICE tracker's live choices, in order (SPEC:R203). */
    suspend fun choices(trackerId: String): List<TrackerChoice> =
        dao.choicesOf(choosing(trackerId).id).filter { it.deletedAt == null }.sortedWith(choiceOrder).map { it.toChoice() }

    /** A new choice, last; its name is not another live choice's of this tracker, ignoring case. */
    suspend fun addChoice(trackerId: String, label: String, color: Long? = null): String {
        val id = newId()
        var clean = ""
        var order = 0L
        writes.write({
            choosing(trackerId)
            clean = uniqueChoice(trackerId, label, except = null)
            order = dao.choicesOf(trackerId).maxOfOrNull { it.sortOrder }?.plus(CHOICE_STEP) ?: 0L
            mapOf(TRACKER_CHOICE to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, TrackerChoiceEntity(id, trackerId, clean, color, order, null, s.hlc, s.device).toRow())
        }
        return id
    }

    suspend fun renameChoice(id: String, label: String) {
        var clean = ""
        writes.edit(TRACKER_CHOICE, id, WHOLE, { clean = uniqueChoice(liveChoice(id).trackerId, label, except = id) }) { mapOf("label" to clean) }
    }

    suspend fun recolorChoice(id: String, color: Long?) = writes.edit(TRACKER_CHOICE, id, WHOLE, { liveChoice(id) }) { mapOf("color_argb" to color) }

    /**
     * Places [id] just after the live choice [after], or first when null. Only the moved choice is
     * written, as a whole row carries every field: rewriting the others would undo a rename made
     * meanwhile on another device. They are renumbered only when no room is left between two.
     */
    suspend fun moveChoice(id: String, after: String?) {
        var orders = emptyMap<String, Long>()
        writes.write({
            val choice = liveChoice(id)
            val others = dao.choicesOf(choice.trackerId).filter { it.deletedAt == null && it.id != id }.sortedWith(choiceOrder)
            val at = if (after == null) 0 else others.indexOfFirst { it.id == after }.also { require(it >= 0) { "no choice $after beside $id" } } + 1
            val before = others.getOrNull(at - 1)?.sortOrder
            val next = others.getOrNull(at)?.sortOrder
            val room = if (before == null) next?.minus(CHOICE_STEP) ?: 0L
            else if (next == null) before + CHOICE_STEP
            else if (next - before > 1) before + (next - before) / 2
            else null
            orders = if (room != null) mapOf(id to room)
            else (others.map { it.id }.toMutableList().apply { add(at, id) }).withIndex().associate { (i, c) -> c to i * CHOICE_STEP }
            mapOf(TRACKER_CHOICE to orders.keys.toList())
        }) { store, _ ->
            val s = clock.tick()
            for ((c, order) in orders) store.put(requireNotNull(store.row(c)).edit(WHOLE, s, mapOf("sort_order" to order)))
        }
    }

    /** Moves a choice to the Trash; the Logs that picked it keep it and still read it. */
    suspend fun deleteChoice(id: String) = writes.edit(TRACKER_CHOICE, id, WHOLE, { liveChoice(id) }) { s -> mapOf("deleted_at" to s.hlc, "merged_into" to null) }

    /** Restores a choice from the Trash. One whose name a live choice has taken since is refused. */
    suspend fun restoreChoice(id: String) = writes.edit(TRACKER_CHOICE, id, WHOLE, {
        val c = trashedChoice(id)
        choosing(c.trackerId)
        uniqueChoice(c.trackerId, c.label, except = id)
    }) { mapOf("deleted_at" to null, "merged_into" to null) }

    /** A tracker's choices in the Trash; one merged into another of its name is not there, as no person deleted it. */
    suspend fun trashedChoices(trackerId: String): List<TrackerChoice> =
        dao.choicesOf(choosing(trackerId).id).filter { it.deletedAt != null && it.mergedInto == null }.sortedBy { it.id }.map { it.toChoice() }

    /**
     * "Delete forever", from the Trash of a live tracker, as its Trash is listed only then: the purge
     * travels, and the Logs that picked it keep its id.
     */
    suspend fun purgeChoice(id: String) = writes.write({
        choosing(trashedChoice(id).trackerId)
        mapOf(TRACKER_CHOICE to listOf(id))
    }) { store, _ -> writes.merger.purge(store, id) }

    /**
     * After every import (SPEC:R203), as Select options settle: a choice in the Trash comes back when
     * a person Logged it, or a choice merged into it, after it was deleted, on a device that had not
     * seen the delete; then live choices of one tracker a sync left with one name merge into the
     * lowest id, the one made first. Both are
     * stamped [automatic]ally from what caused them, so every device writes the same rows.
     */
    suspend fun settleChoices() {
        var back = emptyMap<String, Stamp>()
        writes.write({
            val all = dao.allChoices()
            val trashed = all.filter { it.deletedAt != null && it.mergedInto == null }
            val found = HashMap<String, Stamp>()
            if (trashed.isNotEmpty()) {
                val resolve = chainEnd(all)
                val byId = trashed.associateBy { it.id }
                for (r in dao.readingsPicking(all.map { it.id })) {
                    val c = byId[resolve(r.choiceId)] ?: continue
                    val logged = Stamp(r.hlc, r.device)
                    val gone = Stamp(c.hlc, c.device)
                    if (logged.byHand && logged > gone) found[c.id] = gone
                }
            }
            back = found
            mapOf(TRACKER_CHOICE to found.keys.toList())
        }) { store, _ ->
            for ((id, gone) in back) store.put(requireNotNull(store.row(id)).edit(WHOLE, automatic(gone), mapOf("deleted_at" to null, "merged_into" to null)))
        }
        var into = emptyMap<String, Pair<String, Stamp>>()
        writes.write({
            into = dao.allChoices().filter { it.deletedAt == null }.groupBy { it.trackerId to labelKey(it.label) }.values.filter { it.size > 1 }
                .flatMap { same -> val first = same.minOf { it.id }; same.filter { it.id != first }.map { it.id to (first to Stamp(it.hlc, it.device)) } }.toMap()
            mapOf(TRACKER_CHOICE to into.keys.toList())
        }) { store, _ ->
            for ((id, merge) in into) {
                val (survivor, last) = merge
                store.put(requireNotNull(store.row(id)).edit(WHOLE, automatic(last), mapOf("deleted_at" to last.hlc, "merged_into" to survivor)))
            }
        }
    }

    /** A live CHOICE tracker: an edit to a trashed tracker's choices waits for its restore. */
    private suspend fun choosing(trackerId: String) =
        requireNotNull(dao.trackers(listOf(trackerId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no tracker $trackerId" }
            .also { require(it.type == TrackerType.CHOICE.name) { "${it.name} has no choices" } }

    private suspend fun liveChoice(id: String) =
        requireNotNull(dao.choices(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no choice $id" }.also { choosing(it.trackerId) }

    private suspend fun trashedChoice(id: String) =
        requireNotNull(dao.choices(listOf(id)).singleOrNull()?.takeIf { it.deletedAt != null && it.mergedInto == null }) { "choice $id is not in the Trash" }

    private suspend fun uniqueChoice(trackerId: String, label: String, except: String?): String {
        val clean = nfc(label.trim())
        require(clean.isNotEmpty()) { "a choice needs a name" }
        require(dao.choicesOf(trackerId).none { it.deletedAt == null && it.id != except && labelKey(it.label) == labelKey(clean) }) { "there is already a choice \"$clean\"" }
        return clean
    }

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

/** The gap left between two choices' places, so a move between them writes one row. */
private const val CHOICE_STEP = 1L shl 20

/** A choice's place, ties between choices placed apart broken by id. */
private val choiceOrder = compareBy<TrackerChoiceEntity>({ it.sortOrder }, { it.id })

private fun TrackerChoiceEntity.toChoice() = TrackerChoice(id, label, colorArgb)

/**
 * Follows [choices]' merges from a choice id to the last one held, live or in the Trash, so a Log
 * of a merged choice reads as the one it went into; an id no choice has reads as none.
 */
private fun chainEnd(choices: List<TrackerChoiceEntity>): (String?) -> String? {
    val byId = choices.associateBy { it.id }
    return { start -> generateSequence(start?.let(byId::get)) { it.mergedInto?.let(byId::get) }.take(choices.size + 1).lastOrNull()?.id }
}

internal fun TrackerReadingEntity.toLog() =
    Log(LocalDateTime.parse(at), yes = boolValue, rating = ratingValue?.toInt(), number = numberValue, choiceId = choiceId)
