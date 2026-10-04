package com.factotum.data.checklist

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val CHECKLIST = "checklist"
internal const val CHECKLIST_ITEM = "checklist_item"

/*
 * ADR 01 groups for Chronicle's checklists (decision 14), one per thing written apart: a name or a
 * text, a place, a tick, the last reset, the making, and a deletion that wins over an edit made
 * apart (owner, 2026-10-03), as a label's or a check-in's does.
 */
internal const val MADE = "made"
internal const val NAME = "name"
internal const val TEXT = "text"
internal const val CHECK = "check"
internal const val RUN = "run"
internal const val ORDER = "order"
internal const val GONE = "gone"

/**
 * A checklist (Chronicle's): a list run again and again, standalone. Its reset is a stamp, not a
 * write to every item: an item reads as ticked only when ticked after it (owner, 2026-10-03), so a
 * tick from before a reset is cleared even when it syncs after it.
 */
@Entity(tableName = CHECKLIST)
internal data class ChecklistEntity(
    @PrimaryKey val id: String,
    val name: String,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "order_hlc") val orderHlc: Long,
    @ColumnInfo(name = "order_device") val orderDevice: String,
    @ColumnInfo(name = "run_hlc") val runHlc: Long,
    @ColumnInfo(name = "run_device") val runDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Entity(
    tableName = CHECKLIST_ITEM,
    foreignKeys = [ForeignKey(ChecklistEntity::class, ["id"], ["checklist_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("checklist_id")],
)
internal data class ChecklistItemEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "checklist_id") val checklistId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val text: String,
    @ColumnInfo(name = "text_hlc") val textHlc: Long,
    @ColumnInfo(name = "text_device") val textDevice: String,
    val checked: Boolean,
    @ColumnInfo(name = "check_hlc") val checkHlc: Long,
    @ColumnInfo(name = "check_device") val checkDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "order_hlc") val orderHlc: Long,
    @ColumnInfo(name = "order_device") val orderDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Dao
internal interface ChecklistDao {
    @Query("SELECT * FROM checklist WHERE id IN (:ids)") suspend fun checklists(ids: List<String>): List<ChecklistEntity>
    @Query("SELECT * FROM checklist ORDER BY id") suspend fun allChecklists(): List<ChecklistEntity>
    @Upsert suspend fun putChecklists(rows: List<ChecklistEntity>)
    @Query("DELETE FROM checklist WHERE id IN (:ids)") suspend fun deleteChecklists(ids: List<String>)

    @Query("SELECT * FROM checklist_item WHERE id IN (:ids)") suspend fun items(ids: List<String>): List<ChecklistItemEntity>
    @Query("SELECT * FROM checklist_item ORDER BY checklist_id, id") suspend fun allItems(): List<ChecklistItemEntity>
    @Upsert suspend fun putItems(rows: List<ChecklistItemEntity>)
    @Query("DELETE FROM checklist_item WHERE id IN (:ids)") suspend fun deleteItems(ids: List<String>)

    @Query("SELECT * FROM checklist_item WHERE checklist_id = :checklistId") suspend fun itemsOf(checklistId: String): List<ChecklistItemEntity>
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun checklistTable(dao: ChecklistDao) =
    EntityTable(dao::checklists, dao::allChecklists, dao::putChecklists, dao::deleteChecklists, ChecklistEntity::toRow, Row::toChecklistEntity) { emptyList() }

internal fun checklistItemTable(dao: ChecklistDao) =
    EntityTable(dao::items, dao::allItems, dao::putItems, dao::deleteItems, ChecklistItemEntity::toRow, Row::toChecklistItemEntity) { listOf(CHECKLIST to it.checklistId) }

internal fun ChecklistEntity.toRow() = Row(CHECKLIST, id, mapOf(
    NAME to stamped(nameHlc, nameDevice, mapOf("name" to name)),
    ORDER to stamped(orderHlc, orderDevice, mapOf("sort_key" to sortKey)),
    RUN to stamped(runHlc, runDevice, emptyMap()),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toChecklistEntity(): ChecklistEntity {
    val name = groups.getValue(NAME)
    val order = groups.getValue(ORDER)
    val run = groups.getValue(RUN)
    val gone = groups.getValue(GONE)
    return ChecklistEntity(
        id, name.values["name"] as String, name.stamp.hlc, name.stamp.device, order.values["sort_key"] as String, order.stamp.hlc, order.stamp.device,
        run.stamp.hlc, run.stamp.device, gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun ChecklistItemEntity.toRow() = Row(CHECKLIST_ITEM, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("checklist_id" to checklistId)),
    TEXT to stamped(textHlc, textDevice, mapOf("text" to text)),
    CHECK to stamped(checkHlc, checkDevice, mapOf("checked" to checked)),
    ORDER to stamped(orderHlc, orderDevice, mapOf("sort_key" to sortKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toChecklistItemEntity(): ChecklistItemEntity {
    val made = groups.getValue(MADE)
    val text = groups.getValue(TEXT)
    val check = groups.getValue(CHECK)
    val order = groups.getValue(ORDER)
    val gone = groups.getValue(GONE)
    return ChecklistItemEntity(
        id, made.values["checklist_id"] as String, made.stamp.hlc, made.stamp.device, text.values["text"] as String, text.stamp.hlc, text.stamp.device,
        check.values["checked"] as Boolean, check.stamp.hlc, check.stamp.device, order.values["sort_key"] as String, order.stamp.hlc, order.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}
