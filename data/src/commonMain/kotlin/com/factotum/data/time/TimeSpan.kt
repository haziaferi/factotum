package com.factotum.data.time

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
import com.factotum.core.time.Span
import com.factotum.data.item.EntityTable
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemEntity
import kotlinx.datetime.LocalDateTime

internal const val TIME_SPAN = "time_span"

/*
 * A span's ADR 01 groups, one per thing written apart, each on its own stamp, so a device that
 * has not yet seen another's change never writes over it: when it started (with its owner and
 * planned run, written once), when it ended, whether it is deleted, when a long run was last kept,
 * and its comment. A stop on one device and a comment, a start time or a "keep" on another all
 * survive the merge, and nothing reopens or revives a span. A rule across groups (an end before
 * the start, after two such edits merge) is therefore not a database rule: writes refuse it, and
 * totals count such a span as nothing.
 */
internal const val START = "start"
internal const val END = "end"
internal const val GONE = "gone"
internal const val KEPT = "kept"
internal const val NOTE = "note"

/**
 * One span of tracked time on a task, habit or activity (ADR 07): Tendril's time logs and
 * Chronicle's sessions in one table. [endedAt] is null while it runs; several may run at once.
 * Times are floating local date-times, to the second. [plannedRun] is Chronicle's `RunStamp` text,
 * kept as written. [keptAt] is when the person last said to keep a long-running timer going.
 */
@Entity(
    tableName = TIME_SPAN,
    foreignKeys = [ForeignKey(ItemEntity::class, ["id"], ["item_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("item_id", "started_at"), Index("started_at")],
)
internal data class TimeSpanEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "item_id") val itemId: String,
    @ColumnInfo(name = "started_at") val startedAt: String,
    @ColumnInfo(name = "planned_run") val plannedRun: String?,
    @ColumnInfo(name = "start_hlc") val startHlc: Long,
    @ColumnInfo(name = "start_device") val startDevice: String,
    @ColumnInfo(name = "ended_at") val endedAt: String?,
    @ColumnInfo(name = "end_hlc") val endHlc: Long,
    @ColumnInfo(name = "end_device") val endDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
    @ColumnInfo(name = "kept_at") val keptAt: String?,
    @ColumnInfo(name = "kept_hlc") val keptHlc: Long,
    @ColumnInfo(name = "kept_device") val keptDevice: String,
    val comment: String?,
    @ColumnInfo(name = "note_hlc") val noteHlc: Long,
    @ColumnInfo(name = "note_device") val noteDevice: String,
) {
    fun toSpan() = Span(LocalDateTime.parse(startedAt), endedAt?.let(LocalDateTime::parse))
}

@Dao
internal interface TimeDao {
    @Query("SELECT * FROM time_span WHERE id IN (:ids)")
    suspend fun spans(ids: List<String>): List<TimeSpanEntity>

    /** Owners first, as a snapshot is written. */
    @Query("SELECT * FROM time_span ORDER BY item_id, started_at, id")
    suspend fun allSpans(): List<TimeSpanEntity>

    @Upsert
    suspend fun putSpans(rows: List<TimeSpanEntity>)

    @Query("DELETE FROM time_span WHERE id IN (:ids)")
    suspend fun deleteSpans(ids: List<String>)

    /** Every span of [itemIds], deleted ones too: a purge takes them all. */
    @Query("SELECT id FROM time_span WHERE item_id IN (:itemIds)")
    suspend fun everySpanOf(itemIds: List<String>): List<String>

    @Query("SELECT id FROM time_span WHERE item_id IN (:itemIds) AND deleted_at IS NULL")
    suspend fun liveSpansOf(itemIds: List<String>): List<String>

    @Query("SELECT id FROM time_span WHERE item_id IN (:itemIds) AND deleted_at IS NULL AND ended_at IS NULL")
    suspend fun runningOf(itemIds: List<String>): List<String>

    /**
     * The live spans that count: started in `[from, to)`, on a live owner, not a habit whose
     * tracker is deleted (ADR 06), and, when [itemId] is given, on that owner alone.
     */
    @Query(
        "SELECT s.* FROM time_span s JOIN item i ON i.id = s.item_id LEFT JOIN tracker t ON t.id = i.tracker_id " +
            "WHERE s.deleted_at IS NULL AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') " +
            "AND s.started_at >= :from AND s.started_at < :to AND (:itemId IS NULL OR s.item_id = :itemId) ORDER BY s.started_at, s.id",
    )
    suspend fun counted(from: String, to: String, itemId: String?): List<TimeSpanEntity>

    /** The running spans that count, as [counted] reads them, on owners not yet finished. */
    @Query(
        "SELECT s.* FROM time_span s JOIN item i ON i.id = s.item_id LEFT JOIN tracker t ON t.id = i.tracker_id " +
            "WHERE s.deleted_at IS NULL AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') " +
            "AND (i.status IS NULL OR i.status = 'PENDING') AND s.ended_at IS NULL ORDER BY s.started_at, s.id",
    )
    suspend fun running(): List<TimeSpanEntity>

    /** Running spans whose task is finished or whose owner (or a habit's tracker) is deleted: what a peer did that this device ends. */
    @Query(
        "SELECT s.id FROM time_span s JOIN item i ON i.id = s.item_id LEFT JOIN tracker t ON t.id = i.tracker_id " +
            "WHERE s.deleted_at IS NULL AND s.ended_at IS NULL " +
            "AND (i.deleted_at IS NOT NULL OR t.deleted_at IS NOT NULL OR i.status IN ('DONE', 'SKIPPED'))",
    )
    suspend fun runningOnFinished(): List<String>
}

internal fun timeSpanTable(dao: TimeDao) =
    EntityTable(dao::spans, dao::allSpans, dao::putSpans, dao::deleteSpans, TimeSpanEntity::toRow, Row::toSpanEntity) {
        listOf(ITEM to it.itemId)
    }

internal fun TimeSpanEntity.toRow() = Row(TIME_SPAN, id, mapOf(
    START to Group(Stamp(startHlc, startDevice), mapOf("item_id" to itemId, "started_at" to startedAt, "planned_run" to plannedRun)),
    END to Group(Stamp(endHlc, endDevice), mapOf("ended_at" to endedAt)),
    GONE to Group(Stamp(goneHlc, goneDevice), mapOf("deleted_at" to deletedAt)),
    KEPT to Group(Stamp(keptHlc, keptDevice), mapOf("kept_at" to keptAt)),
    NOTE to Group(Stamp(noteHlc, noteDevice), mapOf("comment" to comment)),
))

/** Throws when [this] is not a span this version can read. */
internal fun Row.toSpanEntity(): TimeSpanEntity {
    val start = groups.getValue(START)
    val end = groups.getValue(END)
    val gone = groups.getValue(GONE)
    val kept = groups.getValue(KEPT)
    val note = groups.getValue(NOTE)
    return TimeSpanEntity(
        id = id,
        itemId = start.values["item_id"] as String,
        startedAt = start.values["started_at"] as String,
        plannedRun = start.values["planned_run"] as String?,
        startHlc = start.stamp.hlc,
        startDevice = start.stamp.device,
        endedAt = end.values["ended_at"] as String?,
        endHlc = end.stamp.hlc,
        endDevice = end.stamp.device,
        deletedAt = gone.values["deleted_at"] as Long?,
        goneHlc = gone.stamp.hlc,
        goneDevice = gone.stamp.device,
        keptAt = kept.values["kept_at"] as String?,
        keptHlc = kept.stamp.hlc,
        keptDevice = kept.stamp.device,
        comment = note.values["comment"] as String?,
        noteHlc = note.stamp.hlc,
        noteDevice = note.stamp.device,
    ).also { it.toSpan() }
}
