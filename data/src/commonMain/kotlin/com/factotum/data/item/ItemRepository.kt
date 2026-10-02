package com.factotum.data.item

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.label.LABELLED
import com.factotum.data.reminder.ALERT
import com.factotum.data.reminder.REMINDER
import com.factotum.data.time.TIME_SPAN
import com.factotum.data.time.endRunning
import com.factotum.data.time.localNow
import com.factotum.core.recurrence.Recurrence
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

/** The one way the app writes items (SPEC §5.3), each write through [writes]. [newId] makes row ids (ULIDs). */
internal class ItemRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val now: () -> LocalDateTime = ::localNow,
) {
    private val dao = db.itemDao()
    private val times = db.timeDao()
    private val reminders = db.reminderDao()
    private val sync = db.syncDao()
    private val clock = writes.clock
    private val merger = writes.merger

    suspend fun createTask(
        title: String,
        start: LocalDate? = null,
        at: LocalTime? = null,
        due: LocalDate? = null,
        importance: Long = 0,
        capacityRank: Long? = null,
        parentId: String? = null,
        recurrence: Recurrence? = null,
    ): String = create(ItemKind.TASK, title, parentId, schedule(start, at, null, null, due) + recurrenceValues(recurrence), TaskStatus.PENDING, importance, capacityRank)

    suspend fun createEvent(
        title: String,
        start: LocalDate,
        at: LocalTime? = null,
        endDate: LocalDate? = null,
        endTime: LocalTime? = null,
        recurrence: Recurrence? = null,
    ): String = create(ItemKind.EVENT, title, null, schedule(start, at, endDate, endTime, null) + recurrenceValues(recurrence), null, 0, null)

    private suspend fun create(
        kind: ItemKind,
        title: String,
        parentId: String?,
        schedule: Map<String, Any?>,
        status: TaskStatus?,
        importance: Long,
        capacityRank: Long?,
    ): String {
        val id = newId()
        writes.write(mapOf(ITEM to listOf(id))) { store ->
            merger.created(store, itemRow(id, clock.tick(), kind, title, parentId, schedule, status, importance, capacityRank))
        }
        return id
    }

    suspend fun rename(id: String, title: String) = edit(id, DETAILS, mapOf("title" to title))

    /**
     * Moves [id]. Taking the start date away from an item with live reminders is refused, as
     * adding a reminder to an undated item is (ADR 03): those reminders could never fire.
     */
    suspend fun reschedule(id: String, start: LocalDate?, at: LocalTime? = null, endDate: LocalDate? = null, endTime: LocalTime? = null, due: LocalDate? = null) =
        writes.write({
            require(start != null || reminders.remindersOf(id).isEmpty()) { "item $id has reminders, so it keeps a start date" }
            mapOf(ITEM to listOf(id))
        }) { store, _ ->
            store.put(requireNotNull(store.row(id)) { "no item $id" }.edit(SCHEDULE, clock.tick(), schedule(start, at, endDate, endTime, due) - "deleted_at"))
        }

    /** Sets how [id] repeats (ADR 04), from its start; an item that repeats needs a start date. */
    suspend fun setRecurrence(id: String, recurrence: Recurrence?) = writes.write({
        require(recurrence == null || dao.items(listOf(id)).singleOrNull()?.startDate != null) { "item $id has no start date to repeat from" }
        mapOf(ITEM to listOf(id))
    }) { store, _ ->
        store.put(requireNotNull(store.row(id)) { "no item $id" }.edit(SCHEDULE, clock.tick(), recurrenceValues(recurrence)))
    }

    /** Sets a task's status; done or skipped, its running timers stop (owner, 2026-10-02). */
    suspend fun setStatus(id: String, status: TaskStatus) = writes.write({
        mapOf(ITEM to listOf(id), TIME_SPAN to if (status == TaskStatus.PENDING) emptyList() else times.runningOf(listOf(id)))
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(id)) { "no item $id" }.edit(STATUS, s, mapOf("status" to status.name)))
        endRunning(store, targets.getValue(TIME_SPAN), now(), s)
    }

    /** The manual order of an activity, or of a habit inside its time block (ADR 07). */
    suspend fun setSortOrder(id: String, order: Double) = edit(id, DETAILS, mapOf("sort_order" to order))

    suspend fun setImportance(id: String, importance: Long) = edit(id, STATUS, mapOf("importance" to importance))

    suspend fun setCapacityRank(id: String, rank: Long?) = edit(id, STATUS, mapOf("capacity_rank" to rank))

    /**
     * Deletes [id] and its subtasks, which go with their parent (ADR 02), and stops their running
     * timers (owner, 2026-10-02); "delete forever" is [purge]. An activity is deleted with its
     * time by `ActivityRepository`.
     */
    suspend fun delete(id: String) = writes.write({
        val ids = listOf(id) + dao.liveChildren(id)
        mapOf(ITEM to ids, TIME_SPAN to times.runningOf(ids))
    }) { store, targets ->
        val s = clock.tick()
        for (target in targets.getValue(ITEM)) {
            store.put(requireNotNull(store.row(target)) { "no item $target" }.edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
        }
        endRunning(store, targets.getValue(TIME_SPAN), now(), s)
    }

    /**
     * "Delete forever" (ADR 01): the purge travels; subtasks, completions and tracked time go by the
     * foreign keys. An activity is never deleted forever (owner, 2026-10-02), so no time is lost to it.
     */
    suspend fun purge(id: String) {
        require(dao.items(listOf(id)).singleOrNull()?.kind != ItemKind.ACTIVITY.name) { "an activity is deleted, never deleted forever" }
        writes.write(mapOf(ITEM to listOf(id))) { store -> merger.purge(store, id) }
    }

    /**
     * Records how one occurrence of a recurring task was resolved (ADR 02's completion log). The
     * occurrence is named by the date-time the series gave it, or an added one's own, so two
     * occurrences on one day are told apart. The task's running timers stop (owner, 2026-10-02).
     */
    suspend fun resolve(itemId: String, occurrence: LocalDateTime, outcome: Outcome): String {
        val id = newId()
        writes.write({ mapOf(COMPLETION to listOf(id), TIME_SPAN to times.runningOf(listOf(itemId))) }) { store, targets ->
            val s = clock.tick()
            merger.created(store, Row(COMPLETION, id, mapOf(
                WHOLE to Group(s, mapOf("item_id" to itemId, "occurrence" to occurrence.toString(), "status" to outcome.name, "deleted_at" to null)),
            )))
            endRunning(store, targets.getValue(TIME_SPAN), now(), s, occurrence = occurrence.date)
        }
        return id
    }

    /**
     * Each occurrence's outcome. Two devices resolving one occurrence leave two log rows; the
     * later stamp is the answer.
     */
    suspend fun outcomes(itemId: String): Map<LocalDateTime, Outcome> =
        dao.completionsOf(itemId).groupBy { it.occurrence }
            .mapValues { (_, rows) -> Outcome.valueOf(rows.maxBy { Stamp(it.hlc, it.device) }.status) }
            .mapKeys { LocalDateTime.parse(it.key) }

    suspend fun item(id: String): Item? = dao.items(listOf(id)).singleOrNull()?.toItem()

    /**
     * One day's timeline (Tendril): timed items in time order, then whole-day ones. Standalone
     * reminders show only with [showReminders], a setting that is off by default (ADR 03).
     */
    suspend fun day(date: LocalDate, showReminders: Boolean = false): List<Item> = dao.day(date.toString(), showReminders).map { it.toItem() }

    /** Equipoise's capacity-sized day: at most [n] pending top-level tasks, by capacity rank. */
    suspend fun capacity(date: LocalDate, n: Int): List<Item> = dao.capacity(date.toString(), n).map { it.toItem() }

    suspend fun questions(): List<Question> = sync.allAsks().map { Question(it.id, it.grp) }

    /**
     * Settles a pending question. "Keep both" makes their version a new item; a standalone
     * reminder's copy gets copies of its reminders too, or it would never fire.
     */
    suspend fun answer(question: Question, answer: Answer) {
        val (id, group) = question
        val copy = if (answer == Answer.KEEP_BOTH) newId() else null
        val copied = mutableMapOf<String, String>()
        writes.write({
            if (copy != null && dao.items(listOf(id)).singleOrNull()?.kind == ItemKind.REMINDER.name) {
                reminders.remindersOf(id).forEach { copied[it.id] = newId() }
            }
            mapOf(ITEM to listOfNotNull(id, copy), REMINDER to (copied.keys + copied.values).toList())
        }) { store, _ ->
            when (answer) {
                Answer.KEEP_MINE -> merger.keepMine(store, id, group)
                Answer.TAKE_THEIRS -> merger.takeTheirs(store, id, group)
                Answer.KEEP_BOTH -> {
                    merger.keepBoth(store, id, group, requireNotNull(copy))
                    val s = clock.tick()
                    for ((original, reminderCopy) in copied) {
                        val groups = requireNotNull(store.row(original)).groups.mapValues { (name, g) ->
                            Group(s, if (name == ALERT) g.values + ("item_id" to copy) else g.values)
                        }
                        merger.created(store, Row(REMINDER, reminderCopy, groups))
                    }
                }
            }
        }
    }

    private suspend fun edit(id: String, group: String, changes: Map<String, Any?>) = writes.edit(ITEM, id, group) { changes }

}

/** An item's schedule group values; a new item is not deleted. */
internal fun schedule(start: LocalDate?, at: LocalTime?, endDate: LocalDate?, endTime: LocalTime?, due: LocalDate?) = mapOf(
    "start_date" to start?.toString(), "start_time" to at?.toString(), "end_date" to endDate?.toString(),
    "end_time" to endTime?.toString(), "due_date" to due?.toString(), "deleted_at" to null,
)

/** A new item row, every group stamped [s]. */
internal fun itemRow(
    id: String,
    s: Stamp,
    kind: ItemKind,
    title: String,
    parentId: String?,
    schedule: Map<String, Any?>,
    status: TaskStatus?,
    importance: Long,
    capacityRank: Long?,
    trackerId: String? = null,
    blockId: String? = null,
) = Row(ITEM, id, mapOf(
    DETAILS to Group(s, mapOf(
        "kind" to kind.name, "title" to title, "parent_id" to parentId, "tracker_id" to trackerId, "block_id" to blockId,
        "icon" to null, "color" to null, "sort_order" to null,
    )),
    SCHEDULE to Group(s, mapOf<String, Any?>("pause_from" to null, "pause_until" to null, "duration_min" to null) + schedule),
    STATUS to Group(s, mapOf("status" to status?.name, "importance" to importance, "capacity_rank" to capacityRank, "archived" to null)),
    LABELLED to Group(s, mapOf("label_id" to null)),
))

internal fun ItemEntity.toItem() = Item(
    id = id,
    kind = ItemKind.valueOf(kind),
    title = title,
    parentId = parentId,
    start = startDate?.let(LocalDate::parse),
    at = startTime?.let(LocalTime::parse),
    endDate = endDate?.let(LocalDate::parse),
    endTime = endTime?.let(LocalTime::parse),
    due = dueDate?.let(LocalDate::parse),
    deleted = deletedAt != null,
    status = status?.let(TaskStatus::valueOf),
    importance = importance,
    capacityRank = capacityRank,
    recurrence = recurrence(),
    trackerId = trackerId,
    pauseFrom = pauseFrom?.let(LocalDate::parse),
    pauseUntil = pauseUntil?.let(LocalDate::parse),
    blockId = blockId,
    durationMin = durationMin,
)

internal fun ItemEntity.dtstart(): LocalDateTime? = startDate?.let { dtstartOf(it, startTime) }

/** Where an item's recurrence starts (DTSTART): its start date at its start time, or midnight for a whole-day item. */
internal fun dtstartOf(startDate: String, startTime: String?) = LocalDateTime(LocalDate.parse(startDate), startTime?.let(LocalTime::parse) ?: LocalTime(0, 0))
