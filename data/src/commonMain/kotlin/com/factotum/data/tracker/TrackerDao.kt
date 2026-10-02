package com.factotum.data.tracker

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert

/**
 * Chronicle's trackers, which move across as they are (SPEC §0.1.5): `TrackerEntity`,
 * `TrackerChoiceEntity`, `EntryEntity` (now `tracker_reading`, ADR 02's name) and `GoalEntity`.
 * Chronicle stamps whole rows, so each table is one ADR 01 group. Two changes: a reading's time
 * is a floating local date-time, as every time in Factotum is (§3.4), and the creation time is
 * the ULID's own. A tracker's category is ADR 08's label.
 */
@Entity(tableName = "tracker", indices = [Index("label_id")])
internal data class TrackerEntity(
    @PrimaryKey val id: String,
    val name: String,
    /** NUMBER, BOOLEAN, RATING or CHOICE. */
    val type: String,
    /** HOURS, KM, TIMES, PAGES, REPS, STEPS, CALORIES or CUSTOM; NUMBER trackers only. */
    val unit: String?,
    /** The CUSTOM unit's own word, and only then. */
    @ColumnInfo(name = "unit_label") val unitLabel: String?,
    /** At most one default, matching the type; a CHOICE tracker has none. */
    @ColumnInfo(name = "default_number") val defaultNumber: Double?,
    @ColumnInfo(name = "default_bool") val defaultBool: Boolean?,
    @ColumnInfo(name = "default_rating") val defaultRating: Long?,
    /** HIGHER_IS_BETTER, LOWER_IS_BETTER or NEUTRAL. */
    val polarity: String,
    val archived: Boolean,
    @ColumnInfo(name = "sort_order") val sortOrder: Long,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
    /** Its label (ADR 08, Chronicle's category), in a group of its own; no foreign key, as on an item. */
    @ColumnInfo(name = "label_id") val labelId: String? = null,
    @ColumnInfo(name = "label_hlc", defaultValue = "0") val labelHlc: Long = 0,
    @ColumnInfo(name = "label_device", defaultValue = "''") val labelDevice: String = "",
)

@Entity(
    tableName = "tracker_choice",
    foreignKeys = [ForeignKey(TrackerEntity::class, ["id"], ["tracker_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("tracker_id")],
)
internal data class TrackerChoiceEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "tracker_id") val trackerId: String,
    val label: String,
    @ColumnInfo(name = "color_argb") val colorArgb: Long?,
    @ColumnInfo(name = "sort_order") val sortOrder: Long,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
)

/**
 * One Log on a tracker: exactly one value, as its type allows. [occurrence] names the habit
 * occurrence it was logged for, when a habit has several a day (Tendril's occurrence key).
 */
@Entity(
    tableName = "tracker_reading",
    foreignKeys = [ForeignKey(TrackerEntity::class, ["id"], ["tracker_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("tracker_id", "at")],
)
internal data class TrackerReadingEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "tracker_id") val trackerId: String,
    val at: String,
    @ColumnInfo(name = "number_value") val numberValue: Double?,
    @ColumnInfo(name = "bool_value") val boolValue: Boolean?,
    @ColumnInfo(name = "rating_value") val ratingValue: Long?,
    /** A loose reference, as in Chronicle: a choice deleted later leaves the reading readable. */
    @ColumnInfo(name = "choice_id") val choiceId: String?,
    val label: String?,
    val note: String?,
    val occurrence: String?,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
)

/** A goal on a tracker or an activity, polymorphic as in Chronicle (ADR 07: an activity goal names the item). */
@Entity(tableName = "goal")
internal data class GoalEntity(
    @PrimaryKey val id: String,
    /** ACTIVITY or TRACKER. */
    @ColumnInfo(name = "target_type") val targetType: String,
    @ColumnInfo(name = "target_id") val targetId: String,
    /** DAY, WEEK or MONTH. */
    val period: String,
    val value: Double,
    /** RECURRING or MILESTONE. */
    val kind: String,
    /** AUTO or MANUAL. */
    @ColumnInfo(name = "completion_mode") val completionMode: String,
    @ColumnInfo(name = "achieved_at") val achievedAt: String?,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
)

internal data class TrackerTime(val trackerId: String, val at: String)

@Dao
internal interface TrackerDao {
    @Query("SELECT * FROM tracker WHERE id IN (:ids)")
    suspend fun trackers(ids: List<String>): List<TrackerEntity>

    @Query("SELECT * FROM tracker ORDER BY id")
    suspend fun allTrackers(): List<TrackerEntity>

    @Upsert
    suspend fun putTrackers(rows: List<TrackerEntity>)

    @Query("DELETE FROM tracker WHERE id IN (:ids)")
    suspend fun deleteTrackers(ids: List<String>)

    @Query("SELECT * FROM tracker_choice WHERE id IN (:ids)")
    suspend fun choices(ids: List<String>): List<TrackerChoiceEntity>

    @Query("SELECT * FROM tracker_choice ORDER BY id")
    suspend fun allChoices(): List<TrackerChoiceEntity>

    @Upsert
    suspend fun putChoices(rows: List<TrackerChoiceEntity>)

    @Query("DELETE FROM tracker_choice WHERE id IN (:ids)")
    suspend fun deleteChoices(ids: List<String>)

    @Query("SELECT * FROM tracker_reading WHERE id IN (:ids)")
    suspend fun readings(ids: List<String>): List<TrackerReadingEntity>

    /** Readings of trackers before their dependants: the order a snapshot is written in. */
    @Query("SELECT * FROM tracker_reading ORDER BY tracker_id, at, id")
    suspend fun allReadings(): List<TrackerReadingEntity>

    @Upsert
    suspend fun putReadings(rows: List<TrackerReadingEntity>)

    @Query("DELETE FROM tracker_reading WHERE id IN (:ids)")
    suspend fun deleteReadings(ids: List<String>)

    @Query("SELECT * FROM tracker_reading WHERE tracker_id IN (:trackerIds) AND deleted_at IS NULL ORDER BY at, id")
    suspend fun liveReadingsOf(trackerIds: List<String>): List<TrackerReadingEntity>

    /** The latest presence Log of each tracker: a "yes", a rating, or a number above 0 (owner, 2026-10-02). */
    @Query(
        "SELECT tracker_id AS trackerId, MAX(at) AS at FROM tracker_reading WHERE tracker_id IN (:trackerIds) AND deleted_at IS NULL " +
            "AND (bool_value = 1 OR rating_value IS NOT NULL OR number_value > 0) GROUP BY tracker_id",
    )
    suspend fun lastPresence(trackerIds: List<String>): List<TrackerTime>

    @Query(
        "SELECT * FROM tracker_reading WHERE tracker_id IN (:trackerIds) AND deleted_at IS NULL AND at >= :from AND at < :to " +
            "AND (bool_value = 1 OR rating_value IS NOT NULL OR number_value > 0) ORDER BY at, id",
    )
    suspend fun presenceBetween(trackerIds: List<String>, from: String, to: String): List<TrackerReadingEntity>

    @Query("SELECT * FROM goal WHERE id IN (:ids)")
    suspend fun goals(ids: List<String>): List<GoalEntity>

    @Query("SELECT * FROM goal ORDER BY id")
    suspend fun allGoals(): List<GoalEntity>

    @Upsert
    suspend fun putGoals(rows: List<GoalEntity>)

    @Query("DELETE FROM goal WHERE id IN (:ids)")
    suspend fun deleteGoals(ids: List<String>)

    /** The live goals on a tracker or an activity ([targetType] TRACKER or ACTIVITY). */
    @Query("SELECT * FROM goal WHERE target_type = :targetType AND target_id = :targetId AND deleted_at IS NULL")
    suspend fun goalsOf(targetType: String, targetId: String): List<GoalEntity>

    /** Deleted ones too: a purge takes them all. */
    @Query("SELECT id FROM goal WHERE target_type = :targetType AND target_id = :targetId")
    suspend fun everyGoalOf(targetType: String, targetId: String): List<String>
}
