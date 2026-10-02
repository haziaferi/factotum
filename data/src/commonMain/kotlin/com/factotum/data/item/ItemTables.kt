package com.factotum.data.item

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.sync.RowTable
import com.factotum.data.tracker.TRACKER

internal const val ITEM = "item"
internal const val COMPLETION = "completion"
internal const val DETAILS = "details"
internal const val SCHEDULE = "schedule"
internal const val STATUS = "status"
internal const val WHOLE = "row"

/** ADR 01: only an item's schedule asks a person when both sides changed it. */
internal val ASK_GROUPS = setOf(SCHEDULE)

/** A synced table seen as [Row]s: [toRow] and [fromRow] map its entity [E] to ADR 01's groups and back. */
internal class EntityTable<E>(
    private val byIds: suspend (List<String>) -> List<E>,
    private val every: suspend () -> List<E>,
    private val put: suspend (List<E>) -> Unit,
    private val remove: suspend (List<String>) -> Unit,
    private val toRow: (E) -> Row,
    private val fromRow: (Row) -> E,
    private val parentsOf: (E) -> List<Pair<String, String>>,
) : RowTable {
    override suspend fun load(ids: Collection<String>) = byIds(ids.toList()).map(toRow)
    override suspend fun all() = every().map(toRow)
    override suspend fun save(rows: Collection<Row>) = put(rows.map(fromRow))
    override suspend fun delete(ids: Collection<String>) = remove(ids.toList())
    override fun fits(row: Row) = runCatching { fromRow(row) }.isSuccess
    override fun parents(row: Row) = parentsOf(fromRow(row))
}

internal fun itemTable(dao: ItemDao) =
    EntityTable(dao::items, dao::allItems, dao::putItems, dao::deleteItems, ItemEntity::toRow, Row::toItemEntity) {
        listOfNotNull(it.parentId?.let { p -> ITEM to p }, it.trackerId?.let { t -> TRACKER to t })
    }

internal fun completionTable(dao: ItemDao) =
    EntityTable(dao::completions, dao::allCompletions, dao::putCompletions, dao::deleteCompletions, CompletionEntity::toRow, Row::toCompletionEntity) {
        listOf(ITEM to it.itemId)
    }

internal fun ItemEntity.toRow() = Row(ITEM, id, mapOf(
    DETAILS to Group(Stamp(detailsHlc, detailsDevice), mapOf("kind" to kind, "title" to title, "parent_id" to parentId, "tracker_id" to trackerId, "block_id" to blockId)),
    SCHEDULE to Group(
        Stamp(scheduleHlc, scheduleDevice),
        mapOf(
            "start_date" to startDate, "start_time" to startTime, "end_date" to endDate, "end_time" to endTime,
            "due_date" to dueDate, "deleted_at" to deletedAt, "pause_from" to pauseFrom, "pause_until" to pauseUntil,
            "duration_min" to durationMin,
        ) + repeat.values,
        settles = scheduleSettlesHlc?.let { Stamp(it, requireNotNull(scheduleSettlesDevice)) },
    ),
    STATUS to Group(Stamp(statusHlc, statusDevice), mapOf("status" to status, "importance" to importance, "capacity_rank" to capacityRank)),
))

/** Throws when [this] lacks an item's groups, holds a value of the wrong type, or a recurrence this version cannot read. */
internal fun Row.toItemEntity(): ItemEntity {
    val d = groups.getValue(DETAILS)
    val s = groups.getValue(SCHEDULE)
    val st = groups.getValue(STATUS)
    return ItemEntity(
        id = id,
        kind = d.values["kind"] as String,
        title = d.values["title"] as String,
        parentId = d.values["parent_id"] as String?,
        trackerId = d.values["tracker_id"] as String?,
        blockId = d.values["block_id"] as String?,
        detailsHlc = d.stamp.hlc,
        detailsDevice = d.stamp.device,
        startDate = s.values["start_date"] as String?,
        startTime = s.values["start_time"] as String?,
        endDate = s.values["end_date"] as String?,
        endTime = s.values["end_time"] as String?,
        dueDate = s.values["due_date"] as String?,
        deletedAt = s.values["deleted_at"] as Long?,
        repeat = RecurrenceColumns.read({ s.values[it] as String? }, { s.values[it] as Long? }),
        pauseFrom = s.values["pause_from"] as String?,
        pauseUntil = s.values["pause_until"] as String?,
        durationMin = s.values["duration_min"] as Long?,
        scheduleHlc = s.stamp.hlc,
        scheduleDevice = s.stamp.device,
        scheduleSettlesHlc = s.settles?.hlc,
        scheduleSettlesDevice = s.settles?.device,
        status = st.values["status"] as String?,
        importance = st.values["importance"] as Long,
        capacityRank = st.values["capacity_rank"] as Long?,
        statusHlc = st.stamp.hlc,
        statusDevice = st.stamp.device,
    ).also { it.recurrence() }
}

internal fun CompletionEntity.toRow() = Row(COMPLETION, id, mapOf(
    WHOLE to Group(Stamp(hlc, device), mapOf("item_id" to itemId, "occurrence" to occurrence, "status" to status, "deleted_at" to deletedAt)),
))

/** Throws when [this] lacks a completion's group or holds a value of the wrong type. */
internal fun Row.toCompletionEntity(): CompletionEntity {
    val g = groups.getValue(WHOLE)
    return CompletionEntity(
        id = id,
        itemId = g.values["item_id"] as String,
        occurrence = g.values["occurrence"] as String,
        status = g.values["status"] as String,
        deletedAt = g.values["deleted_at"] as Long?,
        hlc = g.stamp.hlc,
        device = g.stamp.device,
    )
}
