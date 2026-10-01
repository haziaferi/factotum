package com.factotum.data.item

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert

/**
 * ADR 02's one `item` table, in ADR 01's three groups, each with its own stamp:
 * - details: `kind`, `title`, `parent_id`;
 * - schedule (asks a person on a clash): dates, times, `due_date`, `deleted_at`;
 * - status: `status`, `importance`, `capacity_rank`.
 *
 * Room cannot declare CHECK constraints, so the kind rules are triggers ([SchemaTriggers]).
 * The parent key is deferred: a sync import may bring a subtask before its parent.
 */
@Entity(
    tableName = "item",
    foreignKeys = [ForeignKey(ItemEntity::class, ["id"], ["parent_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("kind", "start_date", name = "item_kind_date"), Index("parent_id")],
)
internal data class ItemEntity(
    @PrimaryKey val id: String,
    val kind: String,
    val title: String,
    @ColumnInfo(name = "parent_id") val parentId: String?,
    @ColumnInfo(name = "details_hlc") val detailsHlc: Long,
    @ColumnInfo(name = "details_device") val detailsDevice: String,
    @ColumnInfo(name = "start_date") val startDate: String?,
    @ColumnInfo(name = "start_time") val startTime: String?,
    @ColumnInfo(name = "end_date") val endDate: String?,
    @ColumnInfo(name = "end_time") val endTime: String?,
    @ColumnInfo(name = "due_date") val dueDate: String?,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
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
}
