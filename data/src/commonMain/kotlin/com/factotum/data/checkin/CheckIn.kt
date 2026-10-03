package com.factotum.data.checkin

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val CHECK_IN = "check_in"

/** What a check-in says, written once: when, about which day, and its values. */
internal const val SAID = "said"

/** Its note, apart: a note written later never touches the values. */
internal const val NOTE = "note"

/** Its deletion, apart, so a note edited on another device never brings a deleted check-in back (Tendril: delete wins). */
internal const val GONE = "gone"

/**
 * One check-in (ADR 05, own-axis). [mood] is Tendril's 1–5; [energy] and [pleasantness] are
 * Equipoise's 0..1, and a value that came from a scale of steps carries [sourceLevels], so it is
 * never mistaken for a continuous one. [at] is the floating local moment it was made; [day], when
 * set, is the day it is about, today or earlier (owner, 2026-10-03).
 */
@Entity(tableName = CHECK_IN, indices = [Index("at"), Index("day")])
internal data class CheckInEntity(
    @PrimaryKey val id: String,
    val at: String,
    val day: String?,
    val mood: Long?,
    val energy: Double?,
    val pleasantness: Double?,
    @ColumnInfo(name = "source_levels") val sourceLevels: Long?,
    val stability: String?,
    @ColumnInfo(name = "said_hlc") val saidHlc: Long,
    @ColumnInfo(name = "said_device") val saidDevice: String,
    val note: String?,
    @ColumnInfo(name = "note_hlc") val noteHlc: Long,
    @ColumnInfo(name = "note_device") val noteDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Dao
internal interface CheckInDao {
    @Query("SELECT * FROM check_in WHERE id IN (:ids)")
    suspend fun checkIns(ids: List<String>): List<CheckInEntity>

    @Query("SELECT * FROM check_in ORDER BY at, id")
    suspend fun allCheckIns(): List<CheckInEntity>

    @Upsert
    suspend fun putCheckIns(rows: List<CheckInEntity>)

    @Query("DELETE FROM check_in WHERE id IN (:ids)")
    suspend fun deleteCheckIns(ids: List<String>)

    /** Live check-ins made in `[from, to)`, or about a day in that range, in the order they were made. */
    @Query(
        "SELECT * FROM check_in WHERE deleted_at IS NULL AND ((at >= :from AND at < :to) OR (day >= :fromDay AND day < :toDay)) ORDER BY at, id",
    )
    suspend fun around(from: String, to: String, fromDay: String, toDay: String): List<CheckInEntity>

    /** Every live check-in with both of Equipoise's axes made before [before]: what its engines read. */
    @Query("SELECT * FROM check_in WHERE deleted_at IS NULL AND energy IS NOT NULL AND pleasantness IS NOT NULL AND at < :before ORDER BY at, id")
    suspend fun bothAxes(before: String): List<CheckInEntity>
}

internal fun checkInTable(dao: CheckInDao) =
    EntityTable(dao::checkIns, dao::allCheckIns, dao::putCheckIns, dao::deleteCheckIns, CheckInEntity::toRow, Row::toCheckInEntity) { emptyList() }

internal fun CheckInEntity.toRow() = Row(CHECK_IN, id, mapOf(
    SAID to Group(Stamp(saidHlc, saidDevice), mapOf(
        "at" to at, "day" to day, "mood" to mood, "energy" to energy, "pleasantness" to pleasantness,
        "source_levels" to sourceLevels, "stability" to stability,
    )),
    NOTE to Group(Stamp(noteHlc, noteDevice), mapOf("note" to note)),
    GONE to Group(Stamp(goneHlc, goneDevice), mapOf("deleted_at" to deletedAt)),
))

/** Throws when [this] is not a check-in this version can read. */
internal fun Row.toCheckInEntity(): CheckInEntity {
    val said = groups.getValue(SAID)
    val note = groups.getValue(NOTE)
    val gone = groups.getValue(GONE)
    return CheckInEntity(
        id = id,
        at = said.values["at"] as String,
        day = said.values["day"] as String?,
        mood = said.values["mood"] as Long?,
        energy = said.values["energy"] as Double?,
        pleasantness = said.values["pleasantness"] as Double?,
        sourceLevels = said.values["source_levels"] as Long?,
        stability = said.values["stability"] as String?,
        saidHlc = said.stamp.hlc,
        saidDevice = said.stamp.device,
        note = note.values["note"] as String?,
        noteHlc = note.stamp.hlc,
        noteDevice = note.stamp.device,
        deletedAt = gone.values["deleted_at"] as Long?,
        goneHlc = gone.stamp.hlc,
        goneDevice = gone.stamp.device,
    )
}
