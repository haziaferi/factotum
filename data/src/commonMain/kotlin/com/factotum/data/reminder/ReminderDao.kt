package com.factotum.data.reminder

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Embedded
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.data.item.RecurrenceColumns
import com.factotum.data.item.ItemEntity

/**
 * ADR 03's reminder row, hung off any item; a standalone reminder hangs off an item of kind
 * REMINDER. Two groups: `alert` (when, relative to the item, and how) and `status`, which holds
 * only the snooze and the firing it snoozed, so a snooze on one device and an alert change on
 * another both stay.
 */
@Entity(
    tableName = "reminder",
    foreignKeys = [ForeignKey(ItemEntity::class, ["id"], ["item_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("item_id")],
)
internal data class ReminderEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "item_id") val itemId: String,
    @ColumnInfo(name = "offset_min") val offsetMin: Long,
    @ColumnInfo(name = "anchor_time") val anchorTime: String?,
    @ColumnInfo(name = "alert_kind") val alertKind: String,
    @ColumnInfo(name = "nag_repeats") val nagRepeats: Long,
    @ColumnInfo(name = "nag_minutes") val nagMinutes: Long?,
    val sound: String?,
    val vibration: String?,
    val mode: String,
    val skin: String?,
    val exact: Boolean,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "alert_hlc") val alertHlc: Long,
    @ColumnInfo(name = "alert_device") val alertDevice: String,
    @ColumnInfo(name = "snoozed_until") val snoozedUntil: String?,
    @ColumnInfo(name = "snoozed_from") val snoozedFrom: String?,
    @ColumnInfo(name = "status_hlc") val statusHlc: Long,
    @ColumnInfo(name = "status_device") val statusDevice: String,
)

/** What a firing is computed from: a live reminder on a live, pending item with a start date. */
internal data class FiringSource(
    val reminderId: String,
    val itemId: String,
    val startDate: String,
    val startTime: String?,
    val offsetMin: Long,
    val anchorTime: String?,
    val snoozedUntil: String?,
    val snoozedFrom: String?,
    @Embedded val repeat: RecurrenceColumns,
    val trackerId: String?,
    val blockId: String?,
    val pauseFrom: String?,
    val pauseUntil: String?,
)

@Dao
internal interface ReminderDao {
    @Query("SELECT * FROM reminder WHERE id IN (:ids)")
    suspend fun reminders(ids: List<String>): List<ReminderEntity>

    @Query("SELECT * FROM reminder ORDER BY id")
    suspend fun allReminders(): List<ReminderEntity>

    @Upsert
    suspend fun putReminders(reminders: List<ReminderEntity>)

    @Query("DELETE FROM reminder WHERE id IN (:ids)")
    suspend fun deleteReminders(ids: List<String>)

    @Query("SELECT * FROM reminder WHERE item_id = :itemId AND deleted_at IS NULL ORDER BY id")
    suspend fun remindersOf(itemId: String): List<ReminderEntity>

    @Query(
        "SELECT r.id AS reminderId, i.id AS itemId, i.start_date AS startDate, i.start_time AS startTime, " +
            "r.offset_min AS offsetMin, r.anchor_time AS anchorTime, r.snoozed_until AS snoozedUntil, r.snoozed_from AS snoozedFrom, " +
            "i.recurrence_kind, i.rrule, i.rand_min_days, i.rand_max_days, i.window_days, i.window_start, i.window_end, " +
            "i.roll_every, i.roll_unit, i.plan_n, i.plan_per, i.plan_days, i.plan_blocks, " +
            "i.tracker_id AS trackerId, i.block_id AS blockId, i.pause_from AS pauseFrom, i.pause_until AS pauseUntil " +
            "FROM reminder r JOIN item i ON i.id = r.item_id LEFT JOIN tracker t ON t.id = i.tracker_id " +
            "WHERE r.deleted_at IS NULL AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.start_date IS NOT NULL " +
            "AND (i.status IS NULL OR i.status = 'PENDING')",
    )
    suspend fun firingSources(): List<FiringSource>
}
