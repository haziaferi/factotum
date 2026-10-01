package com.factotum.data.item

import androidx.room.immediateTransaction
import androidx.room.useWriterConnection
import com.factotum.core.sync.Group
import com.factotum.core.sync.HybridClock
import com.factotum.core.sync.Merger
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.sync.StagedStore
import com.factotum.data.sync.saveClock
import com.factotum.data.syncedTables
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime

/**
 * The one way the app writes items (SPEC §5.3). Each write is one transaction: it stamps the
 * groups it changes with [clock], saves the clock with them (§3.1), and the outbox triggers queue
 * the row for export. [newId] makes row ids (ULIDs).
 */
internal class ItemRepository(
    private val db: FactotumDatabase,
    private val clock: HybridClock,
    private val newId: () -> String,
) {
    private val dao = db.itemDao()
    private val sync = db.syncDao()
    private val tables = db.syncedTables()
    private val merger = Merger(clock, ASK_GROUPS)

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
            val s = clock.tick()
            merger.created(store, Row(ITEM, id, mapOf(
                DETAILS to Group(s, mapOf("kind" to kind.name, "title" to title, "parent_id" to parentId)),
                SCHEDULE to Group(s, schedule),
                STATUS to Group(s, mapOf("status" to status?.name, "importance" to importance, "capacity_rank" to capacityRank)),
            )))
        }
        return id
    }

    suspend fun rename(id: String, title: String) = edit(id, DETAILS, mapOf("title" to title))

    suspend fun reschedule(id: String, start: LocalDate?, at: LocalTime? = null, endDate: LocalDate? = null, endTime: LocalTime? = null, due: LocalDate? = null) =
        edit(id, SCHEDULE, schedule(start, at, endDate, endTime, due) - "deleted_at")

    suspend fun setStatus(id: String, status: TaskStatus) = edit(id, STATUS, mapOf("status" to status.name))

    suspend fun setImportance(id: String, importance: Long) = edit(id, STATUS, mapOf("importance" to importance))

    suspend fun setCapacityRank(id: String, rank: Long?) = edit(id, STATUS, mapOf("capacity_rank" to rank))

    /** Deletes [id] and its subtasks, which go with their parent (ADR 02); "delete forever" is [purge]. */
    suspend fun delete(id: String) = write({ listOf(id) + dao.liveChildren(id) }) { store, targets ->
        val s = clock.tick()
        for (target in targets) {
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

    /** One day's timeline (Tendril): timed items in time order, then whole-day ones. */
    suspend fun day(date: LocalDate): List<Item> = dao.day(date.toString()).map { it.toItem() }

    /** Equipoise's capacity-sized day: at most [n] pending top-level tasks, by capacity rank. */
    suspend fun capacity(date: LocalDate, n: Int): List<Item> = dao.capacity(date.toString(), n).map { it.toItem() }

    suspend fun questions(): List<Question> = sync.allAsks().map { Question(it.id, it.grp) }

    suspend fun answer(question: Question, answer: Answer) {
        val (id, group) = question
        val copy = if (answer == Answer.KEEP_BOTH) newId() else null
        write(listOfNotNull(id, copy)) { store ->
            when (answer) {
                Answer.KEEP_MINE -> merger.keepMine(store, id, group)
                Answer.TAKE_THEIRS -> merger.takeTheirs(store, id, group)
                Answer.KEEP_BOTH -> merger.keepBoth(store, id, group, requireNotNull(copy))
            }
        }
    }

    private suspend fun edit(id: String, group: String, changes: Map<String, Any?>) = write(listOf(id)) { store ->
        store.put(requireNotNull(store.row(id)) { "no item $id" }.edit(group, clock.tick(), changes))
    }

    private suspend fun write(ids: List<String>, table: String = ITEM, block: (StagedStore) -> Unit) =
        write({ ids }, table) { store, _ -> block(store) }

    /** One transaction: finds the ids it touches with [ids], loads them, runs [block], writes back with the clock. */
    private suspend fun write(ids: suspend () -> List<String>, table: String = ITEM, block: (StagedStore, List<String>) -> Unit) {
        db.useWriterConnection { connection ->
            connection.immediateTransaction {
                val targets = ids()
                val store = StagedStore.load(sync, tables, mapOf(table to targets))
                block(store, targets)
                store.flush(sync, tables)
                sync.saveClock(clock)
            }
        }
    }

    private fun schedule(start: LocalDate?, at: LocalTime?, endDate: LocalDate?, endTime: LocalTime?, due: LocalDate?) = mapOf(
        "start_date" to start?.toString(), "start_time" to at?.toString(), "end_date" to endDate?.toString(),
        "end_time" to endTime?.toString(), "due_date" to due?.toString(), "deleted_at" to null,
    )
}

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
