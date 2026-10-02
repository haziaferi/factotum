package com.factotum.core.settings

import kotlinx.datetime.LocalTime
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.seconds

/**
 * Where a setting lives (ADR 09, scoped-live): PERSONAL follows you to every device and into a
 * backup; DEVICE_PREF stays on its device but rides in a backup; DEVICE_STATE never leaves the
 * device; SECRET never leaves its device's secret store, not even into a backup.
 */
enum class SettingScope { PERSONAL, DEVICE_PREF, DEVICE_STATE, SECRET }

/**
 * One setting: its [key], [scope] and [default], and how its value is kept as text. [decode]
 * answers null for a value it will not take (unreadable, or out of range), and the default is
 * read instead, as Chronicle's day boundary and Mnemo's nag interval are read.
 */
class Setting<T>(
    val key: String,
    val scope: SettingScope,
    val default: T,
    val encode: (T) -> String,
    val decode: (String) -> T?,
)

private fun text(key: String, scope: SettingScope, default: String = "") = Setting(key, scope, default, { it }, { it })

private fun flag(key: String, scope: SettingScope, default: Boolean) =
    Setting(key, scope, default, { it.toString() }, { it.toBooleanStrictOrNull() })

/** ADR 03's alert modes, as `AlertMode` names them. */
private val ALERT_MODES = setOf("EASE", "SCHEDULE", "ALERT")

/** The settings Factotum has so far, each placed by ADR 09 or the owner (2026-10-02). */
object Settings {
    /** Which day a Log or a span counts for (ADR 06): before this on the wall clock, it is still yesterday. */
    val DAY_START = Setting("day_start", SettingScope.PERSONAL, LocalTime(0, 0), { it.toString() }, { runCatching { LocalTime.parse(it) }.getOrNull() })

    /** How long a timer runs before it is asked about (ADR 07), in whole hours, one at least. */
    val LONG_RUN = Setting("long_run_hours", SettingScope.PERSONAL, com.factotum.core.time.LONG_RUN, { it.inWholeHours.toString() }, { v -> v.toIntOrNull()?.takeIf { it >= 1 }?.hours })

    /** Equipoise's burnout threshold, between 0 and 1. */
    val BURNOUT_THRESHOLD = Setting("burnout_threshold", SettingScope.PERSONAL, 0.5, { it.toString() }, { v -> v.toDoubleOrNull()?.takeIf { it in 0.0..1.0 } })

    /** Equipoise's crisis contacts, as the person wrote them. */
    val CRISIS_CONTACTS = text("crisis_contacts", SettingScope.PERSONAL)

    /** Whether the day view shows standalone reminders (ADR 03), per device (owner, 2026-10-02). */
    val SHOW_REMINDERS_ON_DAY = flag("show_reminders_on_day", SettingScope.DEVICE_PREF, false)

    /** Mnemo's default alert mode for a new reminder (ADR 03's `AlertMode` by name), SCHEDULE as a new reminder's is. */
    val DEFAULT_ALERT_MODE = Setting("default_alert_mode", SettingScope.DEVICE_PREF, "SCHEDULE", { it }, { it.takeIf { m -> m in ALERT_MODES } })

    /** App lock, per device (owner, 2026-10-02): on or off, and how long the app stays open after leaving it. */
    val APP_LOCK = flag("app_lock", SettingScope.DEVICE_PREF, false)
    val APP_LOCK_GRACE: Setting<Duration> = Setting("app_lock_grace_seconds", SettingScope.DEVICE_PREF, Duration.ZERO, { it.inWholeSeconds.toString() }, { v ->
        v.toLongOrNull()?.takeIf { it >= 0 }?.seconds
    })

    /** Whether first-run questions were asked here: a new device asks again, so a restore does not carry it. */
    val FIRST_RUN_DONE = flag("first_run_done", SettingScope.DEVICE_STATE, false)

    /** The sync folder this device writes to (a SAF tree URI on Android, a path on Windows). */
    val SYNC_FOLDER = text("sync_folder", SettingScope.DEVICE_STATE)

    /** The desktop window's place and size. */
    val WINDOW_FRAME = text("window_frame", SettingScope.DEVICE_STATE)

    /** Where this device's language model is (Equipoise): a file here, or an endpoint. */
    val LLM_MODEL = text("llm_model", SettingScope.DEVICE_STATE)

    /** Tendril's Anthropic API key. */
    val AI_KEY = text("ai_key", SettingScope.SECRET)

    /** Equipoise's language-model endpoint key: another service than Tendril's, so another secret (ADR 09). */
    val LLM_ENDPOINT_KEY = text("llm_endpoint_key", SettingScope.SECRET)

    /** The app lock's PIN, as Chronicle keeps it (salt and hash), never the PIN itself. */
    val APP_LOCK_PIN = text("app_lock_pin", SettingScope.SECRET)

    val all: List<Setting<*>> = listOf(
        DAY_START, LONG_RUN, BURNOUT_THRESHOLD, CRISIS_CONTACTS, SHOW_REMINDERS_ON_DAY, DEFAULT_ALERT_MODE, APP_LOCK, APP_LOCK_GRACE,
        FIRST_RUN_DONE, SYNC_FOLDER, WINDOW_FRAME, LLM_MODEL, AI_KEY, LLM_ENDPOINT_KEY, APP_LOCK_PIN,
    )

    fun byKey(key: String): Setting<*>? = all.firstOrNull { it.key == key }
}
