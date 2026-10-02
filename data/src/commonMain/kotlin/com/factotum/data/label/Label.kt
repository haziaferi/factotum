package com.factotum.data.label

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val LABEL = "label"

/*
 * A label's ADR 01 groups, one per thing changed apart, so a rename on one device and a recolour,
 * a new scope, a new place in the order or a deletion on another all survive the merge.
 */
internal const val NAME = "name"
internal const val LOOK = "look"
internal const val SCOPE = "scope"
internal const val ORDER = "order"
internal const val GONE = "gone"

/** A link's own group on an item or tracker: setting or clearing a label never overwrites anything else there. */
internal const val LABELLED = "label"

/**
 * One label (ADR 08). [appliesTo] is ALL, ACTIVITY or TRACKER; [sortOrder] is fractional, as every
 * manual order here. [mergedInto] is set when a sync found it a second label of the same name and
 * merged it away (owner, 2026-10-02): what still names it reads as that label.
 */
@Entity(tableName = LABEL)
internal data class LabelEntity(
    @PrimaryKey val id: String,
    val name: String,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    val color: Long,
    @ColumnInfo(name = "look_hlc") val lookHlc: Long,
    @ColumnInfo(name = "look_device") val lookDevice: String,
    @ColumnInfo(name = "applies_to") val appliesTo: String,
    @ColumnInfo(name = "scope_hlc") val scopeHlc: Long,
    @ColumnInfo(name = "scope_device") val scopeDevice: String,
    @ColumnInfo(name = "sort_order") val sortOrder: Double,
    @ColumnInfo(name = "order_hlc") val orderHlc: Long,
    @ColumnInfo(name = "order_device") val orderDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "merged_into") val mergedInto: String?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Dao
internal interface LabelDao {
    @Query("SELECT * FROM label WHERE id IN (:ids)")
    suspend fun labels(ids: List<String>): List<LabelEntity>

    @Query("SELECT * FROM label ORDER BY id")
    suspend fun allLabels(): List<LabelEntity>

    @Upsert
    suspend fun putLabels(rows: List<LabelEntity>)

    @Query("DELETE FROM label WHERE id IN (:ids)")
    suspend fun deleteLabels(ids: List<String>)

    /** Live labels in their order, then by name and id. */
    @Query("SELECT * FROM label WHERE deleted_at IS NULL ORDER BY sort_order, name, id")
    suspend fun liveLabels(): List<LabelEntity>

    @Query("SELECT id FROM item WHERE label_id IN (:labelIds) AND deleted_at IS NULL")
    suspend fun itemsLabelled(labelIds: List<String>): List<String>

    @Query("SELECT id FROM tracker WHERE label_id IN (:labelIds) AND deleted_at IS NULL")
    suspend fun trackersLabelled(labelIds: List<String>): List<String>
}

internal fun labelTable(dao: LabelDao) =
    EntityTable(dao::labels, dao::allLabels, dao::putLabels, dao::deleteLabels, LabelEntity::toRow, Row::toLabelEntity) { emptyList() }

internal fun LabelEntity.toRow() = Row(LABEL, id, mapOf(
    NAME to Group(Stamp(nameHlc, nameDevice), mapOf("name" to name)),
    LOOK to Group(Stamp(lookHlc, lookDevice), mapOf("color" to color)),
    SCOPE to Group(Stamp(scopeHlc, scopeDevice), mapOf("applies_to" to appliesTo)),
    ORDER to Group(Stamp(orderHlc, orderDevice), mapOf("sort_order" to sortOrder)),
    GONE to Group(Stamp(goneHlc, goneDevice), mapOf("deleted_at" to deletedAt, "merged_into" to mergedInto)),
))

/** Throws when [this] is not a label this version can read. */
internal fun Row.toLabelEntity(): LabelEntity {
    val name = groups.getValue(NAME)
    val look = groups.getValue(LOOK)
    val scope = groups.getValue(SCOPE)
    val order = groups.getValue(ORDER)
    val gone = groups.getValue(GONE)
    return LabelEntity(
        id = id,
        name = name.values["name"] as String,
        nameHlc = name.stamp.hlc,
        nameDevice = name.stamp.device,
        color = look.values["color"] as Long,
        lookHlc = look.stamp.hlc,
        lookDevice = look.stamp.device,
        appliesTo = scope.values["applies_to"] as String,
        scopeHlc = scope.stamp.hlc,
        scopeDevice = scope.stamp.device,
        sortOrder = order.values["sort_order"] as Double,
        orderHlc = order.stamp.hlc,
        orderDevice = order.stamp.device,
        deletedAt = gone.values["deleted_at"] as Long?,
        mergedInto = gone.values["merged_into"] as String?,
        goneHlc = gone.stamp.hlc,
        goneDevice = gone.stamp.device,
    )
}
