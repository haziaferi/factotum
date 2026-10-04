package com.factotum.data.chart

import com.factotum.core.chart.dailyGoalLine
import com.factotum.core.chart.readingValue
import com.factotum.core.habit.dayOf
import com.factotum.core.page.keyAfter
import com.factotum.core.page.keyBetween
import com.factotum.core.sync.Stamp
import com.factotum.core.time.GoalPeriod
import com.factotum.core.time.Span
import com.factotum.core.time.dayTotals
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.ItemKind
import com.factotum.data.settings.PersonalSettings
import kotlinx.datetime.DatePeriod
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.minus
import kotlinx.datetime.plus

data class SavedChart(val id: String, val type: ChartType, val name: String?, val rangeDays: Int, val sources: List<Pair<SourceKind, String>>)

/**
 * One source's days on a chart, oldest first. An activity's day is its whole minutes, 0 when none
 * were tracked, each span counting on the personal day it started (§3.7; Chronicle cut a session at
 * the day's edge); a tracker's day is the mean of its readings that day (Chronicle's values), null when it
 * had none, so a screen chooses how to draw a day with no reading (decision 14 waits on that). A
 * source deleted since has a null [name] and draws nothing. [goalLine] is its live recurring goal as
 * a daily value.
 */
data class ChartSeries(val kind: SourceKind, val sourceId: String, val name: String?, val days: List<Pair<LocalDate, Double?>>, val goalLine: Double?)

/**
 * Chronicle's saved charts (decision 14): a type, a name, the days back from today they show, and
 * sources that are rows of their own. A gallery has a manual order, a new chart first; a deletion
 * wins over an edit made apart, and is undone from the Trash. Days are personal days.
 */
internal class ChartRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val personal: PersonalSettings,
) {
    private val dao = db.chartDao()
    private val items = db.itemDao()
    private val trackers = db.trackerDao()
    private val times = db.timeDao()
    private val clock = writes.clock

    /** A new chart of [type] over the [rangeDays] days up to today, first in the gallery, with [sources] in order. */
    suspend fun create(type: ChartType, rangeDays: Int, sources: List<Pair<SourceKind, String>>, name: String? = null): String {
        val id = newId()
        require(rangeDays > 0) { "a chart shows at least one day" }
        require(sources.distinct().size == sources.size) { "a source is on a chart once" }
        var key = ""
        writes.write({
            sources.forEach { (kind, sourceId) -> source(kind, sourceId) }
            key = keyBetween(null, dao.allCharts().filter { it.deletedAt == null }.minOfOrNull { it.sortKey })
            mapOf(SAVED_CHART to listOf(id), CHART_SOURCE to sources.map { (k, s) -> chartSourceId(id, k, s) })
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, newChartRow(id, s, type, name?.trim()?.ifEmpty { null }, rangeDays.toLong(), key))
            var last: String? = null
            for ((kind, source) in sources) {
                last = keyBetween(last, null)
                writes.merger.created(store, newSourceRow(id, kind, source, s, last))
            }
        }
        return id
    }

    suspend fun rename(id: String, name: String?) = writes.edit(SAVED_CHART, id, NAME, { live(id) }) { mapOf("name" to name?.trim()?.ifEmpty { null }) }

    suspend fun setRange(id: String, rangeDays: Int) {
        require(rangeDays > 0) { "a chart shows at least one day" }
        writes.edit(SAVED_CHART, id, RANGE, { live(id) }) { mapOf("range_days" to rangeDays.toLong()) }
    }

    /** Moves [id] after [after] in the gallery (first when null). */
    suspend fun move(id: String, after: String?) {
        var key = ""
        writes.edit(SAVED_CHART, id, ORDER, {
            live(id)
            key = keyAfter(dao.allCharts().filter { it.deletedAt == null && it.id != id }.map { it.id to it.sortKey }, after)
        }) { mapOf("sort_key" to key) }
    }

    suspend fun delete(id: String) = writes.edit(SAVED_CHART, id, GONE, { live(id) }) { s -> mapOf("deleted_at" to s.hlc) }

    suspend fun restore(id: String) = writes.edit(SAVED_CHART, id, GONE, {
        requireNotNull(dao.charts(listOf(id)).singleOrNull()?.takeIf { it.deletedAt != null }) { "chart $id is not in the Trash" }
    }) { mapOf("deleted_at" to null) }

    /** Adds a source last, or brings back one taken off. */
    suspend fun addSource(chartId: String, kind: SourceKind, sourceId: String) {
        val id = chartSourceId(chartId, kind, sourceId)
        var key = ""
        writes.write({
            live(chartId)
            source(kind, sourceId)
            key = keyBetween(dao.sourcesOf(chartId).filter { it.deletedAt == null }.maxOfOrNull { it.sortKey }, null)
            mapOf(CHART_SOURCE to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            val row = store.row(id)
            if (row == null) writes.merger.created(store, newSourceRow(chartId, kind, sourceId, s, key))
            else if (row.groups.getValue(GONE).values["deleted_at"] != null) store.put(row.edit(GONE, s, mapOf("deleted_at" to null)).edit(ORDER, s, mapOf("sort_key" to key)))
        }
    }

    suspend fun removeSource(chartId: String, kind: SourceKind, sourceId: String) =
        writes.edit(CHART_SOURCE, chartSourceId(chartId, kind, sourceId), GONE, { live(chartId) }) { s -> mapOf("deleted_at" to s.hlc) }

    /** The live charts, in gallery order. */
    suspend fun charts(): List<SavedChart> = dao.allCharts().filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id })).map { c ->
        val sources = dao.sourcesOf(c.id).filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id }))
        SavedChart(c.id, ChartType.valueOf(c.chartType), c.name, c.rangeDays.toInt(), sources.map { SourceKind.valueOf(it.sourceKind) to it.sourceId })
    }

    /** Each source's days on chart [chartId] at [now]: the [SavedChart.rangeDays] personal days up to the one [now] is in. */
    suspend fun series(chartId: String, now: LocalDateTime): List<ChartSeries> {
        val c = live(chartId)
        val sources = dao.sourcesOf(chartId).filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id }))
        val chart = SavedChart(c.id, ChartType.valueOf(c.chartType), c.name, c.rangeDays.toInt(), sources.map { SourceKind.valueOf(it.sourceKind) to it.sourceId })
        val dayStart = personal.dayStart()
        val today = dayOf(now, dayStart)
        val first = today.minus(DatePeriod(days = chart.rangeDays - 1))
        val days = (0 until chart.rangeDays).map { first.plus(DatePeriod(days = it)) }
        val from = LocalDateTime(first, dayStart).toString()
        val to = LocalDateTime(today.plus(DatePeriod(days = 1)), dayStart).toString()
        return chart.sources.map { (kind, sourceId) ->
            when (kind) {
                SourceKind.ACTIVITY -> {
                    val item = items.items(listOf(sourceId)).singleOrNull()?.takeIf { it.deletedAt == null }
                    val spans = if (item == null) emptyList() else times.counted(from, to, sourceId).map { Span(LocalDateTime.parse(it.startedAt), it.endedAt?.let(LocalDateTime::parse)) }
                    val seconds = dayTotals(spans, now, dayStart)
                    ChartSeries(kind, sourceId, item?.title, days.map { d -> d to item?.let { ((seconds[d] ?: 0L) / 60).toDouble() } }, goalLine(kind, sourceId))
                }
                SourceKind.TRACKER -> {
                    val tracker = trackers.trackers(listOf(sourceId)).singleOrNull()?.takeIf { it.deletedAt == null }
                    val byDay = if (tracker == null) emptyMap() else trackers.liveReadingsBetween(listOf(sourceId), from, to)
                        .mapNotNull { r -> readingValue(r.numberValue, r.boolValue, r.ratingValue)?.let { dayOf(LocalDateTime.parse(r.at), dayStart) to it } }
                        .groupBy({ it.first }, { it.second })
                    ChartSeries(kind, sourceId, tracker?.name, days.map { d -> d to byDay[d]?.average() }, goalLine(kind, sourceId))
                }
            }
        }
    }

    /** The source's live recurring goal edited last, as a daily line (Chronicle took the first by its edit time). */
    private suspend fun goalLine(kind: SourceKind, sourceId: String): Double? =
        trackers.goalsOf(kind.name, sourceId).filter { it.kind == "RECURRING" }.maxWithOrNull(compareBy({ it.hlc }, { it.device }))
            ?.let { dailyGoalLine(GoalPeriod.valueOf(it.period), it.value) }

    private suspend fun source(kind: SourceKind, id: String) = when (kind) {
        SourceKind.ACTIVITY -> require(items.items(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }?.kind == ItemKind.ACTIVITY.name) { "no activity $id" }
        SourceKind.TRACKER -> require(trackers.trackers(listOf(id)).singleOrNull()?.let { it.deletedAt == null } == true) { "no tracker $id" }
    }

    private suspend fun live(id: String) = requireNotNull(dao.charts(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no chart $id" }
}
