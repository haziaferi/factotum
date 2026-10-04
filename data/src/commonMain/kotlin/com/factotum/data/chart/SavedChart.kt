package com.factotum.data.chart

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

internal const val SAVED_CHART = "saved_chart"
internal const val CHART_SOURCE = "chart_source"

internal const val MADE = "made"
internal const val NAME = "name"
internal const val RANGE = "range"
internal const val ORDER = "order"
internal const val GONE = "gone"

/** How a chart draws (Chronicle's three on offer); more can come with the screens (decision 14). */
enum class ChartType { LINE, BAR, PIE }

/** What a chart plots: an activity's minutes or a tracker's readings. */
enum class SourceKind { ACTIVITY, TRACKER }

/**
 * A saved chart (Chronicle's): its type, written once, a name, the days it spans, its place in the
 * gallery, and a deletion that wins over an edit made apart (owner, 2026-10-03). Its sources are rows
 * of their own ([ChartSourceEntity]), so two devices each adding one keep both.
 */
@Entity(tableName = SAVED_CHART)
internal data class SavedChartEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "chart_type") val chartType: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val name: String?,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    @ColumnInfo(name = "range_days") val rangeDays: Long,
    @ColumnInfo(name = "range_hlc") val rangeHlc: Long,
    @ColumnInfo(name = "range_device") val rangeDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "order_hlc") val orderHlc: Long,
    @ColumnInfo(name = "order_device") val orderDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/**
 * One source of a chart, id [chartSourceId], so the same source added on two devices is one row;
 * removing it is a deletion, adding it again brings it back. [sourceId] has no foreign key: it names
 * an activity or a tracker, and one deleted later stays on the chart and draws nothing.
 */
@Entity(
    tableName = CHART_SOURCE,
    foreignKeys = [ForeignKey(SavedChartEntity::class, ["id"], ["chart_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("chart_id")],
)
internal data class ChartSourceEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "chart_id") val chartId: String,
    @ColumnInfo(name = "source_kind") val sourceKind: String,
    @ColumnInfo(name = "source_id") val sourceId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "order_hlc") val orderHlc: Long,
    @ColumnInfo(name = "order_device") val orderDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

internal fun chartSourceId(chartId: String, kind: SourceKind, sourceId: String) = "chart_source:$chartId:$kind:$sourceId"

@Dao
internal interface ChartDao {
    @Query("SELECT * FROM saved_chart WHERE id IN (:ids)") suspend fun charts(ids: List<String>): List<SavedChartEntity>
    @Query("SELECT * FROM saved_chart ORDER BY id") suspend fun allCharts(): List<SavedChartEntity>
    @Upsert suspend fun putCharts(rows: List<SavedChartEntity>)
    @Query("DELETE FROM saved_chart WHERE id IN (:ids)") suspend fun deleteCharts(ids: List<String>)

    @Query("SELECT * FROM chart_source WHERE id IN (:ids)") suspend fun sources(ids: List<String>): List<ChartSourceEntity>
    @Query("SELECT * FROM chart_source ORDER BY chart_id, id") suspend fun allSources(): List<ChartSourceEntity>
    @Upsert suspend fun putSources(rows: List<ChartSourceEntity>)
    @Query("DELETE FROM chart_source WHERE id IN (:ids)") suspend fun deleteSources(ids: List<String>)

    @Query("SELECT * FROM chart_source WHERE chart_id = :chartId") suspend fun sourcesOf(chartId: String): List<ChartSourceEntity>
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun chartTable(dao: ChartDao) =
    EntityTable(dao::charts, dao::allCharts, dao::putCharts, dao::deleteCharts, SavedChartEntity::toRow, Row::toChartEntity) { emptyList() }

internal fun chartSourceTable(dao: ChartDao) =
    EntityTable(dao::sources, dao::allSources, dao::putSources, dao::deleteSources, ChartSourceEntity::toRow, Row::toSourceEntity) { listOf(SAVED_CHART to it.chartId) }

internal fun newChartRow(id: String, s: Stamp, type: ChartType, name: String?, rangeDays: Long, key: String) = Row(SAVED_CHART, id, mapOf(
    MADE to Group(s, mapOf("chart_type" to type.name)),
    NAME to Group(s, mapOf("name" to name)),
    RANGE to Group(s, mapOf("range_days" to rangeDays)),
    ORDER to Group(s, mapOf("sort_key" to key)),
    GONE to Group(s, mapOf("deleted_at" to null)),
))

internal fun newSourceRow(chartId: String, kind: SourceKind, sourceId: String, s: Stamp, key: String) = Row(CHART_SOURCE, chartSourceId(chartId, kind, sourceId), mapOf(
    MADE to Group(s, mapOf("chart_id" to chartId, "source_kind" to kind.name, "source_id" to sourceId)),
    ORDER to Group(s, mapOf("sort_key" to key)),
    GONE to Group(s, mapOf("deleted_at" to null)),
))

internal fun SavedChartEntity.toRow() = Row(SAVED_CHART, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("chart_type" to chartType)),
    NAME to stamped(nameHlc, nameDevice, mapOf("name" to name)),
    RANGE to stamped(rangeHlc, rangeDevice, mapOf("range_days" to rangeDays)),
    ORDER to stamped(orderHlc, orderDevice, mapOf("sort_key" to sortKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toChartEntity(): SavedChartEntity {
    val made = groups.getValue(MADE)
    val name = groups.getValue(NAME)
    val range = groups.getValue(RANGE)
    val order = groups.getValue(ORDER)
    val gone = groups.getValue(GONE)
    return SavedChartEntity(
        id, made.values["chart_type"] as String, made.stamp.hlc, made.stamp.device, name.values["name"] as String?, name.stamp.hlc, name.stamp.device,
        range.values["range_days"] as Long, range.stamp.hlc, range.stamp.device, order.values["sort_key"] as String, order.stamp.hlc, order.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { ChartType.valueOf(it.chartType) }
}

internal fun ChartSourceEntity.toRow() = Row(CHART_SOURCE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("chart_id" to chartId, "source_kind" to sourceKind, "source_id" to sourceId)),
    ORDER to stamped(orderHlc, orderDevice, mapOf("sort_key" to sortKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toSourceEntity(): ChartSourceEntity {
    val made = groups.getValue(MADE)
    val order = groups.getValue(ORDER)
    val gone = groups.getValue(GONE)
    return ChartSourceEntity(
        id, made.values["chart_id"] as String, made.values["source_kind"] as String, made.values["source_id"] as String, made.stamp.hlc, made.stamp.device,
        order.values["sort_key"] as String, order.stamp.hlc, order.stamp.device, gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { SourceKind.valueOf(it.sourceKind) }
}
