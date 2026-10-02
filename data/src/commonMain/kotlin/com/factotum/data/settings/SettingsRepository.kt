package com.factotum.data.settings

import com.factotum.core.settings.Setting
import com.factotum.core.settings.SettingScope
import com.factotum.core.settings.Settings
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import kotlinx.datetime.LocalTime
import kotlin.time.Duration

/** A PERSONAL setting as a backup keeps it: with the stamp it was written under, so a restore never outranks a newer value. */
data class BackedUpSetting(val value: String?, val hlc: Long, val device: String)

/**
 * The settings part of a backup (owner, 2026-10-02): the PERSONAL settings with their stamps, and
 * this device's DEVICE_PREF ones. DEVICE_STATE and SECRET never ride in one, nor does the device id,
 * which is not a setting.
 */
data class SettingsBackup(val personal: Map<String, BackedUpSetting>, val device: Map<String, String>)

/**
 * Settings by scope (ADR 09, scoped-live): PERSONAL in the synced `setting` table, DEVICE_PREF
 * and DEVICE_STATE in this device's own table, SECRET in [secrets]. A value that does not read
 * (unreadable, out of range, or never set) reads as the setting's default.
 */
internal class SettingsRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val secrets: SecretStore,
) : PersonalSettings {
    private val dao = db.settingDao()
    private val clock = writes.clock

    suspend fun <T> get(setting: Setting<T>): T = raw(setting)?.let(setting.decode) ?: setting.default

    override suspend fun dayStart(): LocalTime = get(Settings.DAY_START)

    override suspend fun longRun(): Duration = get(Settings.LONG_RUN)

    /**
     * Sets [setting]; its default clears it, so a later change of the default reaches it. App lock
     * goes on only once this device has its PIN, which never leaves the device (owner, 2026-10-02).
     */
    suspend fun <T> set(setting: Setting<T>, value: T) {
        require(setting.decode(setting.encode(value)) == value) { "${setting.key} does not take $value" }
        if (setting === Settings.APP_LOCK && value == true) require(get(Settings.APP_LOCK_PIN).isNotEmpty()) { "set this device's PIN before the lock" }
        write(setting.key, setting.scope, if (value == setting.default) null else setting.encode(value))
    }

    suspend fun reset(setting: Setting<*>) = write(setting.key, setting.scope, null)

    suspend fun export(): SettingsBackup {
        val personal = Settings.all.filter { it.scope == SettingScope.PERSONAL }.map { settingId(it.key) }
        return SettingsBackup(
            personal = dao.settings(personal).associate { it.id.removePrefix(PREFIX) to BackedUpSetting(it.value, it.hlc, it.device) },
            device = Settings.all.filter { it.scope == SettingScope.DEVICE_PREF }.mapNotNull { s -> dao.deviceValue(s.key)?.let { s.key to it } }.toMap(),
        )
    }

    /**
     * Restores [backup]: only the PERSONAL and DEVICE_PREF settings this version knows, and only
     * values they take. A PERSONAL value merges under its own stamp, as an import would, so a newer
     * value here or on a peer stays. App lock is not turned on: the PIN does not come back with it.
     */
    suspend fun restore(backup: SettingsBackup) {
        val personal = backup.personal.filter { (key, v) -> Settings.byKey(key)?.scope == SettingScope.PERSONAL && v.value.reads(key) }
        if (personal.isNotEmpty()) {
            writes.write(mapOf(SETTING to personal.keys.map(::settingId))) { store ->
                val rows = personal.map { (key, v) -> Row(SETTING, settingId(key), mapOf(VALUE to Group(Stamp(v.hlc, v.device), mapOf(VALUE to v.value)))) }
                writes.merger.import(store, rows, emptyMap())
            }
        }
        for ((key, value) in backup.device) {
            val setting = Settings.byKey(key)?.takeIf { it.scope == SettingScope.DEVICE_PREF && it !== Settings.APP_LOCK } ?: continue
            if (value.reads(key)) write(key, setting.scope, value.takeUnless { setting.decode(it) == setting.default })
        }
    }

    private fun String?.reads(key: String) = this == null || Settings.byKey(key)?.decode?.invoke(this) != null

    private suspend fun raw(setting: Setting<*>): String? = when (setting.scope) {
        SettingScope.PERSONAL -> dao.settings(listOf(settingId(setting.key))).singleOrNull()?.value
        SettingScope.DEVICE_PREF, SettingScope.DEVICE_STATE -> dao.deviceValue(setting.key)
        SettingScope.SECRET -> secrets.get(setting.key)
    }

    private suspend fun write(key: String, scope: SettingScope, value: String?) {
        when (scope) {
            SettingScope.PERSONAL -> writes.write(mapOf(SETTING to listOf(settingId(key)))) { store ->
                val s = clock.tick()
                val row = store.row(settingId(key))
                if (row == null) writes.merger.created(store, Row(SETTING, settingId(key), mapOf(VALUE to Group(s, mapOf(VALUE to value)))))
                else store.put(row.edit(VALUE, s, mapOf(VALUE to value)))
            }
            SettingScope.DEVICE_PREF, SettingScope.DEVICE_STATE ->
                if (value == null) dao.clearDeviceSetting(key) else dao.putDeviceSetting(DeviceSettingEntity(key, value))
            SettingScope.SECRET -> secrets.put(key, value)
        }
    }
}

private const val PREFIX = "setting:"
