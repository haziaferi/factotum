package com.factotum.data.checkin

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.checkin.DemandLevel
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.MaskedLevel
import com.factotum.core.checkin.Outcome
import com.factotum.core.checkin.RecoveryLevel
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val SENSORY_LOG = "sensory_log"
internal const val MASKING_ENTRY = "masking_entry"
internal const val REGULATION_EVENT = "regulation_event"

/*
 * Equipoise's regulation module (decision 14). A sensory log and a regulation outcome are said once
 * and undone, as a check-in is; a ledger day holds its three felt scales apart, so taps on two
 * devices merge. None of it is searched: it is as private as a check-in's note (ADR 05).
 */
internal const val MADE = "made"
internal const val MASKED = "masked"
internal const val DEMAND = "demand"
internal const val RECOVERY = "recovery"

/** Five channels at one moment, each in 0..1 as a check-in's axes are (how many steps a screen offers waits for the screens). */
@Entity(tableName = SENSORY_LOG)
internal data class SensoryLogEntity(
    @PrimaryKey val id: String,
    val at: String,
    val sound: Double,
    val light: Double,
    val crowd: Double,
    val temperature: Double,
    val touch: Double,
    @ColumnInfo(name = "said_hlc") val saidHlc: Long,
    @ColumnInfo(name = "said_device") val saidDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/**
 * One personal day of the masking ledger, id [maskingId], so two devices write one day. Each scale
 * is its own group and stays empty until tapped (Equipoise wrote defaults for the scales not tapped).
 */
@Entity(tableName = MASKING_ENTRY)
internal data class MaskingEntryEntity(
    @PrimaryKey val id: String,
    val day: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val masked: String?,
    @ColumnInfo(name = "masked_hlc") val maskedHlc: Long,
    @ColumnInfo(name = "masked_device") val maskedDevice: String,
    val demand: String?,
    @ColumnInfo(name = "demand_hlc") val demandHlc: Long,
    @ColumnInfo(name = "demand_device") val demandDevice: String,
    val recovery: String?,
    @ColumnInfo(name = "recovery_hlc") val recoveryHlc: Long,
    @ColumnInfo(name = "recovery_device") val recoveryDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

internal fun maskingId(day: kotlinx.datetime.LocalDate) = "masking:$day"

/** One outcome tap for one check-in: which way, which tool (a stable key, not the sentence shown), and how it went. */
@Entity(
    tableName = REGULATION_EVENT,
    foreignKeys = [ForeignKey(CheckInEntity::class, ["id"], ["check_in_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("check_in_id")],
)
internal data class RegulationEventEntity(
    @PrimaryKey val id: String,
    val at: String,
    @ColumnInfo(name = "check_in_id") val checkInId: String,
    val direction: String,
    @ColumnInfo(name = "tool_key") val toolKey: String?,
    val outcome: String,
    @ColumnInfo(name = "said_hlc") val saidHlc: Long,
    @ColumnInfo(name = "said_device") val saidDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/**
 * The one outcome still owed on this device, until the next open (Equipoise's `pending_outcome`):
 * this device's alone, never synced, as a reminder firing writes nothing that syncs (§3.13); only
 * the outcome it becomes syncs.
 */
@Entity(tableName = "pending_outcome")
internal data class PendingOutcomeEntity(
    @PrimaryKey val id: Int = 1,
    @ColumnInfo(name = "check_in_id") val checkInId: String,
    val direction: String,
    @ColumnInfo(name = "tool_key") val toolKey: String?,
    val asked: Boolean,
)

/** An outcome as the direction engine learns from it: the state of the check-in it answered, which way, and how it went. */
internal data class Taught(val energy: Double, val pleasantness: Double, val stability: String?, val direction: String, val outcome: String)

@Dao
internal interface RegulationDao {
    @Query("SELECT * FROM sensory_log WHERE id IN (:ids)") suspend fun sensory(ids: List<String>): List<SensoryLogEntity>
    @Query("SELECT * FROM sensory_log ORDER BY id") suspend fun allSensory(): List<SensoryLogEntity>
    @Upsert suspend fun putSensory(rows: List<SensoryLogEntity>)
    @Query("DELETE FROM sensory_log WHERE id IN (:ids)") suspend fun deleteSensory(ids: List<String>)

    @Query("SELECT * FROM masking_entry WHERE id IN (:ids)") suspend fun masking(ids: List<String>): List<MaskingEntryEntity>
    @Query("SELECT * FROM masking_entry ORDER BY id") suspend fun allMasking(): List<MaskingEntryEntity>
    @Upsert suspend fun putMasking(rows: List<MaskingEntryEntity>)
    @Query("DELETE FROM masking_entry WHERE id IN (:ids)") suspend fun deleteMasking(ids: List<String>)

    @Query("SELECT * FROM regulation_event WHERE id IN (:ids)") suspend fun events(ids: List<String>): List<RegulationEventEntity>
    @Query("SELECT * FROM regulation_event ORDER BY id") suspend fun allEvents(): List<RegulationEventEntity>
    @Upsert suspend fun putEvents(rows: List<RegulationEventEntity>)
    @Query("DELETE FROM regulation_event WHERE id IN (:ids)") suspend fun deleteEvents(ids: List<String>)

    @Query("SELECT * FROM sensory_log WHERE deleted_at IS NULL AND at >= :from AND at < :to ORDER BY at, id") suspend fun sensoryBetween(from: String, to: String): List<SensoryLogEntity>
    @Query("SELECT * FROM masking_entry WHERE deleted_at IS NULL AND day >= :from AND day <= :to") suspend fun maskingBetween(from: String, to: String): List<MaskingEntryEntity>

    @Query("SELECT * FROM regulation_event WHERE check_in_id = :checkInId AND deleted_at IS NULL ORDER BY at, id")
    suspend fun eventsOf(checkInId: String): List<RegulationEventEntity>

    /** The outcomes the direction engine learns from, with the state they answered: live, on a live check-in with both axes (an undone one stops teaching, owner 2026-10-03). */
    @Query(
        "SELECT c.energy, c.pleasantness, c.stability, e.direction, e.outcome FROM regulation_event e JOIN check_in c ON c.id = e.check_in_id " +
            "WHERE e.deleted_at IS NULL AND c.deleted_at IS NULL AND c.energy IS NOT NULL AND c.pleasantness IS NOT NULL ORDER BY e.at, e.id",
    )
    suspend fun teaching(): List<Taught>

    @Query("SELECT * FROM pending_outcome WHERE id = 1") suspend fun pending(): PendingOutcomeEntity?
    @Upsert suspend fun putPending(row: PendingOutcomeEntity)
    @Query("DELETE FROM pending_outcome") suspend fun clearPending()
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun sensoryTable(dao: RegulationDao) =
    EntityTable(dao::sensory, dao::allSensory, dao::putSensory, dao::deleteSensory, SensoryLogEntity::toRow, Row::toSensoryEntity) { emptyList() }

internal fun maskingTable(dao: RegulationDao) =
    EntityTable(dao::masking, dao::allMasking, dao::putMasking, dao::deleteMasking, MaskingEntryEntity::toRow, Row::toMaskingEntity) { emptyList() }

internal fun regulationEventTable(dao: RegulationDao) =
    EntityTable(dao::events, dao::allEvents, dao::putEvents, dao::deleteEvents, RegulationEventEntity::toRow, Row::toEventEntity) { listOf(CHECK_IN to it.checkInId) }

internal fun SensoryLogEntity.toRow() = Row(SENSORY_LOG, id, mapOf(
    SAID to stamped(saidHlc, saidDevice, mapOf("at" to at, "sound" to sound, "light" to light, "crowd" to crowd, "temperature" to temperature, "touch" to touch)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toSensoryEntity(): SensoryLogEntity {
    val said = groups.getValue(SAID)
    val gone = groups.getValue(GONE)
    fun channel(name: String) = (said.values[name] as Double).also { require(it in 0.0..1.0) { "$name is in 0..1" } }
    return SensoryLogEntity(
        id, said.values["at"] as String, channel("sound"), channel("light"), channel("crowd"), channel("temperature"), channel("touch"),
        said.stamp.hlc, said.stamp.device, gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun MaskingEntryEntity.toRow() = Row(MASKING_ENTRY, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("day" to day)),
    MASKED to stamped(maskedHlc, maskedDevice, mapOf("masked" to masked)),
    DEMAND to stamped(demandHlc, demandDevice, mapOf("demand" to demand)),
    RECOVERY to stamped(recoveryHlc, recoveryDevice, mapOf("recovery" to recovery)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toMaskingEntity(): MaskingEntryEntity {
    val made = groups.getValue(MADE)
    val masked = groups.getValue(MASKED)
    val demand = groups.getValue(DEMAND)
    val recovery = groups.getValue(RECOVERY)
    val gone = groups.getValue(GONE)
    return MaskingEntryEntity(
        id, made.values["day"] as String, made.stamp.hlc, made.stamp.device,
        masked.values["masked"] as String?, masked.stamp.hlc, masked.stamp.device,
        demand.values["demand"] as String?, demand.stamp.hlc, demand.stamp.device,
        recovery.values["recovery"] as String?, recovery.stamp.hlc, recovery.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { e -> e.masked?.let(MaskedLevel::valueOf); e.demand?.let(DemandLevel::valueOf); e.recovery?.let(RecoveryLevel::valueOf) }
}

internal fun RegulationEventEntity.toRow() = Row(REGULATION_EVENT, id, mapOf(
    SAID to stamped(saidHlc, saidDevice, mapOf("at" to at, "check_in_id" to checkInId, "direction" to direction, "tool_key" to toolKey, "outcome" to outcome)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toEventEntity(): RegulationEventEntity {
    val said = groups.getValue(SAID)
    val gone = groups.getValue(GONE)
    return RegulationEventEntity(
        id, said.values["at"] as String, said.values["check_in_id"] as String, said.values["direction"] as String, said.values["tool_key"] as String?,
        said.values["outcome"] as String, said.stamp.hlc, said.stamp.device, gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { Direction.valueOf(it.direction); Outcome.valueOf(it.outcome) }
}
