package com.factotum.data.item

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Embedded
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.data.tracker.TrackerEntity

/**
 * ADR 02's one `item` table, in ADR 01's three groups, each with its own stamp:
 * - details: `kind`, `title`, `parent_id`, and a habit's `tracker_id` and `block_id`;
 * - schedule (asks a person on a clash): dates, times, `due_date`, `deleted_at`, and ADR 04's
 *   recurrence columns ([recurrenceValues]), and a habit's pause and `duration_min`;
 * - status: `status`, `importance`, `capacity_rank`.
 *
 * Room cannot declare CHECK constraints, so the kind rules are triggers ([SchemaTriggers]).
 * The parent key is deferred: a sync import may bring a subtask before its parent.
 */
@Entity(
    tableName = "item",
    foreignKeys = [
        ForeignKey(ItemEntity::class, ["id"], ["parent_id"], onDelete = ForeignKey.CASCADE, deferred = true),
        // A habit goes with its tracker (owner, 2026-10-02).
        ForeignKey(TrackerEntity::class, ["id"], ["tracker_id"], onDelete = ForeignKey.CASCADE, deferred = true),
    ],
    indices = [Index("kind", "start_date", name = "item_kind_date"), Index("parent_id"), Index("tracker_id")],
)
internal data class ItemEntity(
    @PrimaryKey val id: String,
    val kind: String,
    val title: String,
    @ColumnInfo(name = "parent_id") val parentId: String?,
    /** A HABIT's tracker, which its Logs are readings on (ADR 06); required on a habit, absent elsewhere. */
    @ColumnInfo(name = "tracker_id") val trackerId: String?,
    /** A HABIT's default time block (ADR 06, amended): where the planner places it. */
    @ColumnInfo(name = "block_id") val blockId: String?,
    @ColumnInfo(name = "details_hlc") val detailsHlc: Long,
    @ColumnInfo(name = "details_device") val detailsDevice: String,
    @ColumnInfo(name = "start_date") val startDate: String?,
    @ColumnInfo(name = "start_time") val startTime: String?,
    @ColumnInfo(name = "end_date") val endDate: String?,
    @ColumnInfo(name = "end_time") val endTime: String?,
    @ColumnInfo(name = "due_date") val dueDate: String?,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @Embedded val repeat: RecurrenceColumns,
    /** A HABIT's pause; no end means until resumed (Tendril). */
    @ColumnInfo(name = "pause_from") val pauseFrom: String?,
    @ColumnInfo(name = "pause_until") val pauseUntil: String?,
    /** A HABIT's length, which the planner balances days by (ADR 06, amended). */
    @ColumnInfo(name = "duration_min") val durationMin: Long?,
    @ColumnInfo(name = "schedule_hlc") val scheduleHlc: Long,
    @ColumnInfo(name = "schedule_device") val scheduleDevice: String,
    @ColumnInfo(name = "schedule_settles_hlc") val scheduleSettlesHlc: Long?,
    @ColumnInfo(name = "schedule_settles_device") val scheduleSettlesDevice: String?,
    val status: String?,
    val importance: Long,
    @ColumnInfo(name = "capacity_rank") val capacityRank: Long?,
    @ColumnInfo(name = "status_hlc") val statusHlc: Long,
    @ColumnInfo(name = "status_device") val statusDevice: String,
)

/** One resolved occurrence of a recurring task (ADR 02): an append-only log, one group. */
@Entity(
    tableName = "completion",
    foreignKeys = [ForeignKey(ItemEntity::class, ["id"], ["item_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("item_id")],
)
internal data class CompletionEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "item_id") val itemId: String,
    val occurrence: String,
    val status: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
)

/** Equipoise's G04 day: today's pending top-level tasks by capacity rank, at most N. Kept here so a test can read its plan. */
internal const val CAPACITY_QUERY =
    "SELECT * FROM item WHERE kind = 'TASK' AND start_date = :date AND status = 'PENDING' AND parent_id IS NULL " +
        "AND deleted_at IS NULL ORDER BY capacity_rank IS NULL, capacity_rank LIMIT :n"

@Dao
internal interface ItemDao {
    @Query("SELECT * FROM item WHERE id IN (:ids)")
    suspend fun items(ids: List<String>): List<ItemEntity>

    /** Parents before their subtasks, so a peer reading a snapshot meets a parent first. */
    @Query("SELECT * FROM item ORDER BY parent_id IS NOT NULL, id")
    suspend fun allItems(): List<ItemEntity>

    @Upsert
    suspend fun putItems(items: List<ItemEntity>)

    @Query("DELETE FROM item WHERE id IN (:ids)")
    suspend fun deleteItems(ids: List<String>)

    @Query("SELECT id FROM item WHERE parent_id = :id AND deleted_at IS NULL")
    suspend fun liveChildren(id: String): List<String>

    @Query("SELECT id FROM item WHERE tracker_id = :trackerId AND deleted_at IS NULL")
    suspend fun liveHabitsOf(trackerId: String): List<String>

    /** One day's timeline: timed items in time order, then the whole-day ones; standalone reminders only when asked (ADR 03). */
    @Query(
        "SELECT * FROM item WHERE start_date = :date AND deleted_at IS NULL AND (kind <> 'REMINDER' OR :showReminders) " +
            "ORDER BY start_time IS NULL, start_time, id",
    )
    suspend fun day(date: String, showReminders: Boolean): List<ItemEntity>

    @Query(CAPACITY_QUERY)
    suspend fun capacity(date: String, n: Int): List<ItemEntity>

    @Query("SELECT * FROM completion WHERE id IN (:ids)")
    suspend fun completions(ids: List<String>): List<CompletionEntity>

    @Query("SELECT * FROM completion ORDER BY id")
    suspend fun allCompletions(): List<CompletionEntity>

    @Query("SELECT * FROM completion WHERE item_id = :itemId AND deleted_at IS NULL ORDER BY occurrence")
    suspend fun completionsOf(itemId: String): List<CompletionEntity>

    @Upsert
    suspend fun putCompletions(completions: List<CompletionEntity>)

    @Query("DELETE FROM completion WHERE id IN (:ids)")
    suspend fun deleteCompletions(ids: List<String>)

    @Query("SELECT * FROM occurrence_edit WHERE id IN (:ids)")
    suspend fun edits(ids: List<String>): List<OccurrenceEditEntity>

    @Query("SELECT * FROM occurrence_edit ORDER BY created_hlc, created_device")
    suspend fun allEdits(): List<OccurrenceEditEntity>

    @Upsert
    suspend fun putEdits(edits: List<OccurrenceEditEntity>)

    @Query("DELETE FROM occurrence_edit WHERE id IN (:ids)")
    suspend fun deleteEdits(ids: List<String>)

    /** Undone edits too: an edit's base is the newest one its author had seen, live or not. */
    @Query("SELECT * FROM occurrence_edit WHERE item_id = :itemId")
    suspend fun editsOf(itemId: String): List<OccurrenceEditEntity>

    @Query("SELECT * FROM occurrence_edit WHERE item_id = :itemId AND deleted_at IS NULL")
    suspend fun liveEditsOf(itemId: String): List<OccurrenceEditEntity>

    @Query("SELECT * FROM occurrence_edit WHERE deleted_at IS NULL")
    suspend fun liveEdits(): List<OccurrenceEditEntity>

    @Query("SELECT * FROM habit_block WHERE id IN (:ids)")
    suspend fun blocks(ids: List<String>): List<HabitBlockEntity>

    @Query("SELECT * FROM habit_block ORDER BY id")
    suspend fun allBlocks(): List<HabitBlockEntity>

    @Upsert
    suspend fun putBlocks(rows: List<HabitBlockEntity>)

    @Query("DELETE FROM habit_block WHERE id IN (:ids)")
    suspend fun deleteBlocks(ids: List<String>)

    @Query("SELECT * FROM habit_block WHERE deleted_at IS NULL ORDER BY position, id")
    suspend fun liveBlocks(): List<HabitBlockEntity>

    /** Live habits whose tracker is live too: a habit on a deleted tracker reads as deleted (ADR 06). */
    @Query(
        "SELECT i.* FROM item i JOIN tracker t ON t.id = i.tracker_id " +
            "WHERE i.kind = 'HABIT' AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.start_date IS NOT NULL ORDER BY i.id",
    )
    suspend fun liveHabits(): List<ItemEntity>
}
