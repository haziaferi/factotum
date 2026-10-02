package com.factotum.data.settings

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val SETTING = "setting"

/** A personal setting's one ADR 01 group, and its one field: two devices that change it apart keep the later (ADR 09, silently). */
internal const val VALUE = "value"

/** A setting row's id: its key, marked so it can never be taken for another table's id (those are ULIDs, or a block's `block-…`). */
internal fun settingId(key: String) = "setting:$key"

/**
 * A PERSONAL setting (ADR 09), synced. Its id is [settingId] of its key, not a ULID, so two
 * devices that set one key apart write one row, which the merge settles. A null [value] is the default.
 * A key this version does not know is kept as it came, for the version that does.
 */
@Entity(tableName = SETTING)
internal data class SettingEntity(
    @PrimaryKey val id: String,
    val value: String?,
    val hlc: Long,
    val device: String,
)

/** A DEVICE_PREF or DEVICE_STATE setting (ADR 09): this device's alone, never exported to the folder. */
@Entity(tableName = "device_setting")
internal data class DeviceSettingEntity(
    @PrimaryKey val key: String,
    val value: String,
)

@Dao
internal interface SettingDao {
    @Query("SELECT * FROM setting WHERE id IN (:ids)")
    suspend fun settings(ids: List<String>): List<SettingEntity>

    @Query("SELECT * FROM setting ORDER BY id")
    suspend fun allSettings(): List<SettingEntity>

    @Upsert
    suspend fun putSettings(rows: List<SettingEntity>)

    @Query("DELETE FROM setting WHERE id IN (:ids)")
    suspend fun deleteSettings(ids: List<String>)

    @Query("SELECT value FROM device_setting WHERE `key` = :key")
    suspend fun deviceValue(key: String): String?

    @Upsert
    suspend fun putDeviceSetting(row: DeviceSettingEntity)

    @Query("DELETE FROM device_setting WHERE `key` = :key")
    suspend fun clearDeviceSetting(key: String)
}

internal fun settingTable(dao: SettingDao) =
    EntityTable(dao::settings, dao::allSettings, dao::putSettings, dao::deleteSettings, SettingEntity::toRow, Row::toSettingEntity) { emptyList() }

internal fun SettingEntity.toRow() = Row(SETTING, id, mapOf(VALUE to Group(Stamp(hlc, device), mapOf(VALUE to value))))

internal fun Row.toSettingEntity(): SettingEntity {
    val g = groups.getValue(VALUE)
    return SettingEntity(id, g.values[VALUE] as String?, g.stamp.hlc, g.stamp.device)
}

/**
 * Where SECRET settings live (ADR 09): the Android Keystore, or a DPAPI-wrapped file on Windows,
 * never the database, the sync folder or a backup. The shells give the real one (Tendril's
 * `SecretStore` and `FileAiKeyStore` are the code to port); a null value removes the secret.
 */
interface SecretStore {
    fun get(key: String): String?
    fun put(key: String, value: String?)
}
