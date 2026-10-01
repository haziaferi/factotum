package com.factotum.data.sync

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Index
import androidx.room.Insert
import androidx.room.OnConflictStrategy
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

/** The last stamp both sides agreed on for an asking group (ADR 01); local only. */
@Entity(tableName = "sync_base", primaryKeys = ["id", "grp"])
internal data class BaseEntity(
    val id: String,
    val grp: String,
    val hlc: Long,
    val device: String,
)

/** A clash waiting for a person: the other side's group, as a folder record encodes it; local only. */
@Entity(tableName = "sync_ask", primaryKeys = ["id", "grp"])
internal data class AskEntity(
    val id: String,
    val grp: String,
    val theirs: String,
)

/** How far into a peer's file the importer has read, in bytes (ADR 13); local only. */
@Entity(tableName = "sync_read")
internal data class ReadEntity(
    @PrimaryKey val path: String,
    @ColumnInfo(name = "read_bytes") val readBytes: Long,
)

/**
 * A row or purge to export, queued by triggers on every synced table and on the purge registry
 * ([com.factotum.data.SchemaTriggers]), and cleared once the export is in the folder. [table] is
 * null for a purge.
 */
@Entity(tableName = "sync_outbox")
internal data class OutboxEntity(
    @PrimaryKey(autoGenerate = true) val n: Long = 0,
    val id: String,
    @ColumnInfo(name = "tbl") val table: String?,
)

/**
 * The synced tables the last import knew, as sorted names; one row, local only. When they change,
 * the read positions are dropped, so lines skipped for a table this version lacked are read again.
 */
@Entity(tableName = "sync_tables")
internal data class KnownTablesEntity(
    @PrimaryKey val id: Int = 0,
    val names: String,
)

/**
 * A folder line whose parent has not arrived yet, such as a subtask or completion read before
 * the item it names; local only. Retried after every import, applied once its parent is here.
 */
@Entity(tableName = "sync_waiting", indices = [Index("line", unique = true)])
internal data class WaitingEntity(
    @PrimaryKey(autoGenerate = true) val n: Long = 0,
    val line: String,
)

@Dao
internal interface SyncDao {
    @Query("SELECT * FROM purge_registry")
    suspend fun purges(): List<PurgeEntity>

    @Query("SELECT * FROM purge_registry WHERE id IN (:ids)")
    suspend fun purges(ids: List<String>): List<PurgeEntity>

    @Upsert
    suspend fun putPurge(purge: PurgeEntity)

    @Query("DELETE FROM purge_registry WHERE id = :id")
    suspend fun removePurge(id: String)

    @Query("SELECT last_hlc FROM clock WHERE id = 0")
    suspend fun lastHlc(): Long?

    @Upsert
    suspend fun saveClock(clock: ClockEntity)

    @Query("SELECT * FROM sync_base WHERE id IN (:ids)")
    suspend fun bases(ids: List<String>): List<BaseEntity>

    @Upsert
    suspend fun putBases(bases: List<BaseEntity>)

    @Query("SELECT * FROM sync_ask WHERE id IN (:ids)")
    suspend fun asks(ids: List<String>): List<AskEntity>

    @Upsert
    suspend fun putAsks(asks: List<AskEntity>)

    @Query("DELETE FROM sync_ask WHERE id = :id AND grp = :group")
    suspend fun removeAsk(id: String, group: String)

    @Query("SELECT * FROM sync_read")
    suspend fun reads(): List<ReadEntity>

    @Query("DELETE FROM sync_read")
    suspend fun clearReads()

    @Upsert
    suspend fun putRead(read: ReadEntity)

    /** Forgets positions in files no longer in the folder. */
    @Query("DELETE FROM sync_read WHERE path NOT IN (:present)")
    suspend fun keepReads(present: List<String>)

    /** A line already waiting (a peer's snapshot repeats it) is not added twice. */
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun wait(lines: List<WaitingEntity>)

    @Query("SELECT * FROM sync_waiting ORDER BY n")
    suspend fun waiting(): List<WaitingEntity>

    @Query("DELETE FROM sync_waiting WHERE n = :n")
    suspend fun stopWaiting(n: Long)

    @Query("SELECT id, grp FROM sync_ask ORDER BY id, grp")
    suspend fun allAsks(): List<AskKey>

    @Query("SELECT names FROM sync_tables WHERE id = 0")
    suspend fun knownTables(): String?

    @Upsert
    suspend fun saveKnownTables(tables: KnownTablesEntity)

    @Query("SELECT * FROM sync_outbox ORDER BY n")
    suspend fun outbox(): List<OutboxEntity>

    @Query("DELETE FROM sync_outbox WHERE n <= :upTo")
    suspend fun clearOutbox(upTo: Long)
}

internal fun PurgeEntity.stamp() = Stamp(hlc, device)

/** A clock that resumes from the last value stored, so a wall clock set backwards cannot reissue an older stamp. */
internal suspend fun SyncDao.loadClock(device: String, wallMillis: () -> Long) =
    HybridClock(device, wallMillis, last = lastHlc() ?: 0)

internal suspend fun SyncDao.saveClock(clock: HybridClock) = saveClock(ClockEntity(lastHlc = clock.last))

internal fun BaseEntity.stamp() = Stamp(hlc, device)

internal data class AskKey(val id: String, val grp: String)
