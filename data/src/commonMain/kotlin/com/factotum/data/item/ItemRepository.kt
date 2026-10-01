package com.factotum.data.item

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.reminder.ALERT
import com.factotum.data.reminder.REMINDER
import com.factotum.data.sync.StagedStore
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime

/** The one way the app writes items (SPEC §5.3), each write through [writes]. [newId] makes row ids (ULIDs). */
internal class ItemRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val dao = db.itemDao()
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
    ): String = create(ItemKind.TASK, title, parentId, schedule(start, at, null, null, due), TaskStatus.PENDING, importance, capacityRank)

    suspend fun createEvent(title: String, start: LocalDate, at: LocalTime? = null, endDate: LocalDate? = null, endTime: LocalTime? = null): String =
        create(ItemKind.EVENT, title, null, schedule(start, at, endDate, endTime, null), null, 0, null)

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
        write(listOf(id)) { store ->
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

    suspend fun setStatus(id: String, status: TaskStatus) = edit(id, STATUS, mapOf("status" to status.name))

    suspend fun setImportance(id: String, importance: Long) = edit(id, STATUS, mapOf("importance" to importance))

    suspend fun setCapacityRank(id: String, rank: Long?) = edit(id, STATUS, mapOf("capacity_rank" to rank))

    /** Deletes [id] and its subtasks, which go with their parent (ADR 02); "delete forever" is [purge]. */
    suspend fun delete(id: String) = writes.write({ mapOf(ITEM to listOf(id) + dao.liveChildren(id)) }) { store, targets ->
        val s = clock.tick()
        for (target in targets.getValue(ITEM)) {
            store.put(requireNotNull(store.row(target)) { "no item $target" }.edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
        }
    }

    /** "Delete forever" (ADR 01): the purge travels; subtasks and completions go by the foreign keys. */
    suspend fun purge(id: String) = write(listOf(id)) { store -> merger.purge(store, id) }

    /** Records how one occurrence of a recurring task was resolved (ADR 02's completion log). */
    suspend fun resolve(itemId: String, occurrence: LocalDate, outcome: Outcome): String {
        val id = newId()
        write(listOf(id), table = COMPLETION) { store ->
            merger.created(store, Row(COMPLETION, id, mapOf(
                WHOLE to Group(clock.tick(), mapOf("item_id" to itemId, "occurrence" to occurrence.toString(), "status" to outcome.name, "deleted_at" to null)),
            )))
        }
        return id
    }

    /**
     * Each occurrence's outcome. Two devices resolving one occurrence leave two log rows; the
     * later stamp is the answer.
     */
    suspend fun outcomes(itemId: String): Map<LocalDate, Outcome> =
        dao.completionsOf(itemId).groupBy { it.occurrence }
            .mapValues { (_, rows) -> Outcome.valueOf(rows.maxBy { Stamp(it.hlc, it.device) }.status) }
            .mapKeys { LocalDate.parse(it.key) }

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

    private suspend fun write(ids: List<String>, table: String = ITEM, block: (StagedStore) -> Unit) =
        writes.write(mapOf(table to ids), block)

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
) = Row(ITEM, id, mapOf(
    DETAILS to Group(s, mapOf("kind" to kind.name, "title" to title, "parent_id" to parentId)),
    SCHEDULE to Group(s, schedule),
    STATUS to Group(s, mapOf("status" to status?.name, "importance" to importance, "capacity_rank" to capacityRank)),
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
)
