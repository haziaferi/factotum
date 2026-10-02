package com.factotum.data.time

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.core.time.runsLong
import com.factotum.core.time.totalOf
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.PersonalSettings
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemKind
import com.factotum.data.item.MIDNIGHT
import com.factotum.data.item.SCHEDULE
import com.factotum.data.label.resolver
import com.factotum.data.sync.StagedStore
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.TimeZone
import kotlinx.datetime.plus
import kotlinx.datetime.toInstant
import kotlinx.datetime.toLocalDateTime
import kotlin.time.Clock
import kotlin.time.Duration

/** One span as read back: [end] is null while it runs; [keptAt] is when a long run was last kept going. */
data class TrackedSpan(
    val id: String,
    val itemId: String,
    val start: LocalDateTime,
    val end: LocalDateTime?,
    val comment: String?,
    val plannedRun: String?,
    val keptAt: LocalDateTime? = null,
)

/** The device's wall clock as a floating local date-time, as every Factotum time is. */
internal fun localNow(): LocalDateTime = Clock.System.now().toLocalDateTime(TimeZone.currentSystemDefault())

/**
 * Tracked time on tasks, habits and activities (ADR 07): timers, several at once, and spans
 * entered or edited by hand, on every owner. Totals count each span for the personal day it
 * started on (the personal day boundary) and overlapping spans once; a deleted span, or one whose owner is
 * deleted, does not count.
 */
internal class TimeRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    /** The day boundary and the long-timer limit, read on every call (ADR 09). */
    private val personal: PersonalSettings,
) {
    private val dao = db.timeDao()
    private val items = db.itemDao()
    private val labels = db.labelDao()
    private val clock = writes.clock

    /** Starts a timer on [itemId] at [at]; another running timer keeps running. */
    suspend fun start(itemId: String, at: LocalDateTime, plannedRun: String? = null): String = add(itemId, at, null, null, plannedRun)

    /** A span entered by hand. */
    suspend fun logManual(itemId: String, start: LocalDateTime, end: LocalDateTime, comment: String? = null): String {
        require(end > start) { "a span ends after it starts: $start..$end" }
        return add(itemId, start, end, comment, null)
    }

    /** Stops [spanId] at [at]; a span already stopped or deleted is left as it is. */
    suspend fun stop(spanId: String, at: LocalDateTime) = writes.write(mapOf(TIME_SPAN to listOf(spanId))) { store ->
        endRunning(store, listOf(spanId), at, clock.tick())
    }

    /** "End it at the limit": [spanId] ends the long-run limit after it started, or after it was last kept (owner, 2026-10-02). */
    suspend fun stopAtLimit(spanId: String) {
        val span = requireNotNull(dao.spans(listOf(spanId)).singleOrNull()) { "no span $spanId" }.toTracked()
        stop(spanId, limitOf(span, personal.longRun()))
    }

    /** "Keep it running": the answer to a long-running timer, asked again a full period later (owner, 2026-10-02). */
    suspend fun keep(spanId: String, at: LocalDateTime) = writes.write(mapOf(TIME_SPAN to listOf(spanId))) { store ->
        val row = requireNotNull(store.row(spanId)) { "no span $spanId" }
        require(row.value(END, "ended_at") == null && row.value(GONE, "deleted_at") == null) { "span $spanId is not running" }
        store.put(row.edit(KEPT, clock.tick(), mapOf("kept_at" to seconds(at))))
    }

    /**
     * Changes a span's times and comment; [end] null keeps it running. Only what differs is written,
     * each part on its own stamp, so an edit here never undoes a stop, a deletion or a comment made
     * on another device. A deleted span, or one whose owner is deleted, is not changed (Chronicle).
     */
    suspend fun edit(spanId: String, start: LocalDateTime, end: LocalDateTime?, comment: String?) {
        require(end == null || end >= start) { "a span ends no earlier than it starts: $start..$end" }
        val owner = requireNotNull(dao.spans(listOf(spanId)).singleOrNull()) { "no span $spanId" }.itemId
        writes.write(mapOf(TIME_SPAN to listOf(spanId), ITEM to listOf(owner))) { store ->
            val row = requireNotNull(store.row(spanId))
            require(row.value(GONE, "deleted_at") == null) { "span $spanId is deleted" }
            require(store.row(owner)?.groups?.getValue(SCHEDULE)?.values?.get("deleted_at") == null) { "span $spanId is on a deleted item" }
            val s = clock.tick()
            var edited = row
            fun set(group: String, field: String, value: Any?) {
                if (row.value(group, field) != value) edited = edited.edit(group, s, mapOf(field to value))
            }
            set(START, "started_at", seconds(start))
            set(END, "ended_at", end?.let(::seconds))
            set(NOTE, "comment", comment?.trim()?.ifEmpty { null })
            store.put(edited)
        }
    }

    /** Deletes [spanId]; deleting it again changes nothing. */
    suspend fun delete(spanId: String) = writes.write(mapOf(TIME_SPAN to listOf(spanId))) { store ->
        val row = requireNotNull(store.row(spanId)) { "no span $spanId" }
        if (row.value(GONE, "deleted_at") == null) {
            val s = clock.tick()
            store.put(row.edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        }
    }

    /**
     * Ends at [now] the timers whose task another device finished, or whose owner it deleted: a
     * timer stops when its task is finished (owner, 2026-10-02), here once this device learns of
     * it. Run after each import ([com.factotum.data.sync.FolderSync]'s `afterImport`).
     */
    suspend fun endFinished(now: LocalDateTime) = writes.write({ mapOf(TIME_SPAN to dao.runningOnFinished()) }) { store, targets ->
        val spans = targets.getValue(TIME_SPAN)
        if (spans.isNotEmpty()) endRunning(store, spans, now, clock.tick())
    }

    /** The timers running now, on owners not yet finished. */
    suspend fun running(): List<TrackedSpan> = dao.running().map { it.toTracked() }

    /** The running timers to ask about at [now]: past the limit since they started or were last kept. */
    suspend fun runningLong(now: LocalDateTime): List<TrackedSpan> {
        val limit = personal.longRun()
        return dao.running().filter { runsLong(it.toSpan(), it.keptAt?.let(LocalDateTime::parse), now, limit) }.map { it.toTracked() }
    }

    /** The spans that count, started on [day] (the personal day), of [itemId] or of everything. */
    suspend fun spansOn(day: LocalDate, itemId: String? = null): List<TrackedSpan> = counted(listOf(day), personal.dayStart(), itemId).map { it.toTracked() }

    /**
     * [days]' total in seconds at [now], of [itemId], of everything carrying [labelId] (Chronicle's
     * category total; a label merged into it counts as it), or of everything: overlaps once, each
     * day added. A deleted label has no time.
     */
    suspend fun total(days: List<LocalDate>, now: LocalDateTime, itemId: String? = null, labelId: String? = null): Long {
        val labelIds = labelId?.let { id -> labels.allLabels().let { all -> val r = resolver(all); all.map { it.id }.filter { r(it) == id } } }
        val dayStart = personal.dayStart()
        return totalOf(days, counted(days, dayStart, itemId, labelIds).map { it.toSpan() }, now, dayStart)
    }

    private suspend fun counted(days: List<LocalDate>, dayStart: LocalTime, itemId: String?, labelIds: List<String>? = null): List<TimeSpanEntity> {
        if (days.isEmpty()) return emptyList()
        // A personal day starting after midnight runs into the next date.
        val from = LocalDateTime(days.min(), dayStart).toString()
        val to = LocalDateTime(days.max().plus(1, DateTimeUnit.DAY), dayStart).toString()
        return dao.counted(from, to, itemId, labelIds != null, labelIds.orEmpty())
    }

    private suspend fun add(itemId: String, start: LocalDateTime, end: LocalDateTime?, comment: String?, plannedRun: String?): String {
        val owner = requireNotNull(items.items(listOf(itemId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no item $itemId" }
        require(owner.kind in OWNERS) { "a ${owner.kind} is not timed" }
        val id = newId()
        writes.write(mapOf(TIME_SPAN to listOf(id))) { store ->
            val s = clock.tick()
            writes.merger.created(store, Row(TIME_SPAN, id, mapOf(
                START to Group(s, mapOf("item_id" to itemId, "started_at" to seconds(start), "planned_run" to plannedRun)),
                END to Group(s, mapOf("ended_at" to end?.let(::seconds))),
                GONE to Group(s, mapOf("deleted_at" to null)),
                KEPT to Group(s, mapOf("kept_at" to null)),
                NOTE to Group(s, mapOf("comment" to comment?.trim()?.ifEmpty { null })),
            )))
        }
        return id
    }
}

private val OWNERS = setOf(ItemKind.TASK, ItemKind.HABIT, ItemKind.ACTIVITY).map { it.name }

/** Times are kept to the second. */
private fun seconds(t: LocalDateTime) = LocalDateTime(t.date, LocalTime(t.hour, t.minute, t.second)).toString()

private fun Row.value(group: String, field: String) = groups.getValue(group).values[field]

/** When a long run reaches its [limit]: that long after it started, or after it was last kept. */
internal fun limitOf(span: TrackedSpan, limit: Duration): LocalDateTime =
    maxOf(span.start, span.keptAt ?: span.start).toInstant(TimeZone.UTC).plus(limit).toLocalDateTime(TimeZone.UTC)

/**
 * Ends each of [spanIds] that still runs, at [at] or at its start if that is later, in a write
 * under way: a timer stops when its task is finished or its owner deleted (owner, 2026-10-02).
 * With [occurrence], only a timer started on or before that occurrence's date stops: resolving a
 * past occurrence of a repeating task leaves today's timer running.
 */
internal fun endRunning(store: StagedStore, spanIds: List<String>, at: LocalDateTime, s: Stamp, occurrence: LocalDate? = null) {
    for (id in spanIds) {
        val row = store.row(id) ?: continue
        if (row.value(END, "ended_at") != null || row.value(GONE, "deleted_at") != null) continue
        val started = LocalDateTime.parse(row.value(START, "started_at") as String)
        if (occurrence != null && started.date > occurrence) continue
        store.put(row.edit(END, s, mapOf("ended_at" to maxOf(started, LocalDateTime.parse(seconds(at))).toString())))
    }
}

private fun TimeSpanEntity.toTracked() =
    TrackedSpan(id, itemId, LocalDateTime.parse(startedAt), endedAt?.let(LocalDateTime::parse), comment, plannedRun, keptAt?.let(LocalDateTime::parse))
