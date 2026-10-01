package com.factotum.data.sync

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.HybridClock
import com.factotum.core.sync.Stamp

/** ADR 01's permanent purge registry: one row per purged id, never expired. Ids are ULIDs, unique across tables. */
@Entity(tableName = "purge_registry")
internal data class PurgeEntity(
    @PrimaryKey val id: String,
    val hlc: Long,
    val device: String,
)

/** The highest clock value this device has issued or seen; one row, local only. */
@Entity(tableName = "clock")
internal data class ClockEntity(
    @PrimaryKey val id: Int = 0,
    @ColumnInfo(name = "last_hlc") val lastHlc: Long,
)

@Dao
internal interface SyncDao {
    @Query("SELECT * FROM purge_registry")
    suspend fun purges(): List<PurgeEntity>

    @Upsert
    suspend fun putPurge(purge: PurgeEntity)

    @Query("DELETE FROM purge_registry WHERE id = :id")
    suspend fun removePurge(id: String)

    @Query("SELECT last_hlc FROM clock WHERE id = 0")
    suspend fun lastHlc(): Long?

    @Upsert
    suspend fun saveClock(clock: ClockEntity)
}

internal fun PurgeEntity.stamp() = Stamp(hlc, device)

/** A clock that resumes from the last value stored, so a wall clock set backwards cannot reissue an older stamp. */
internal suspend fun SyncDao.loadClock(device: String, wallMillis: () -> Long) =
    HybridClock(device, wallMillis, last = lastHlc() ?: 0)

internal suspend fun SyncDao.saveClock(clock: HybridClock) = saveClock(ClockEntity(lastHlc = clock.last))
