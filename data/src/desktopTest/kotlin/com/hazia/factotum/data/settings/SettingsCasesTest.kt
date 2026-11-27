package com.hazia.factotum.data.settings

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.hazia.factotum.core.checkin.MixedMode
import com.hazia.factotum.core.checkin.OnboardingAnswer
import com.hazia.factotum.core.settings.Setting
import com.hazia.factotum.core.settings.SettingScope
import com.hazia.factotum.core.settings.Settings
import com.hazia.factotum.data.sync.World
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.seconds

/**
 * ADR 09's cases (`decisions/cases/09-settings.jsonl`) as the contest simulated them: A and B share
 * a folder, and C is a new phone restored from A's backup; with the owner's 2026-10-02 answers.
 */
class SettingsCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun <T> World.with(block: World.(World.Device, World.Device, World.Device) -> T): T = try {
        block(Device("A"), Device("B"), Device("C"))
    } finally {
        close()
    }

    /** Everything A has written to the folder, as text. */
    private fun World.folderText(device: String = "A"): String =
        syncthing.paths(device).joinToString("\n") { syncthing.folder(device).read(it)?.decodeToString().orEmpty() }

    /** A's settings set, synced to B, and C restored from A's backup. */
    private fun World.setUp(a: World.Device, b: World.Device, c: World.Device) = runBlocking {
        a.settings.set(Settings.AI_KEY, "sk-secret-123")
        a.settings.set(Settings.WINDOW_FRAME, "10,10,1200,800")
        a.settings.set(Settings.DEFAULT_ALERT_MODE, "SCHEDULE")
        a.settings.set(Settings.SHOW_REMINDERS_ON_DAY, true)
        a.settings.set(Settings.SYNC_FOLDER, "content://tree/factotum")
        a.settings.set(Settings.BURNOUT_THRESHOLD, 0.7)
        a.settings.set(Settings.CRISIS_CONTACTS, "Ada 555-0100")
        a.settings.set(Settings.LLM_MODEL, "/models/gemma.gguf")
        a.settings.set(Settings.FIRST_RUN_DONE, true)
        b.settings.set(Settings.DEFAULT_ALERT_MODE, "ALERT")
        settle(listOf(a, b))
        c.settings.restore(a.settings.export())
    }

    @Test
    fun tendrilSecretNeverLeaves_theAiKeyIsInNoFolderBackupOrOtherDevice() = World(tmp.root, 1).with { a, b, c ->
        setUp(a, b, c)

        assertFalse("sk-secret-123" in folderText())
        assertFalse("sk-secret-123" in runBlocking { a.settings.export() }.toString())
        assertEquals("" to "", runBlocking { b.settings.get(Settings.AI_KEY) to c.settings.get(Settings.AI_KEY) })
        assertEquals("sk-secret-123", runBlocking { a.settings.get(Settings.AI_KEY) })
        // Tendril's key and Equipoise's endpoint key are two secrets: setting one leaves the other.
        runBlocking { a.settings.set(Settings.LLM_ENDPOINT_KEY, "ep-456") }
        assertEquals("sk-secret-123" to "ep-456", runBlocking { a.settings.get(Settings.AI_KEY) to a.settings.get(Settings.LLM_ENDPOINT_KEY) })
    }

    @Test
    fun tendrilLayoutPerDevice_aWindowFrameReachesNoOtherDevice() = World(tmp.root, 2).with { a, b, c ->
        setUp(a, b, c)

        assertFalse("1200,800" in folderText())
        assertEquals("" to "", runBlocking { b.settings.get(Settings.WINDOW_FRAME) to c.settings.get(Settings.WINDOW_FRAME) })
    }

    @Test
    fun chronicleDeviceIdOwn_theDeviceIdIsNoSettingAndRidesInNoBackup() = World(tmp.root, 3).with { a, b, c ->
        setUp(a, b, c)

        val backup = runBlocking { a.settings.export() }
        assertEquals(setOf(SettingScope.PERSONAL), backup.personal.keys.map { Settings.byKey(it)!!.scope }.toSet())
        assertEquals(setOf(SettingScope.DEVICE_PREF), backup.device.keys.map { Settings.byKey(it)!!.scope }.toSet())
        // The restored phone writes under its own id, which no backup carries.
        runBlocking { c.settings.set(Settings.CRISIS_CONTACTS, "from C") }
        assertEquals(c.id, runBlocking { c.db.settingDao().settings(listOf("setting:crisis_contacts")) }.single().device)
    }

    @Test
    fun mnemoModePerDevice_eachDeviceKeepsItsDefaultModeAfterASync() = World(tmp.root, 4).with { a, b, c ->
        setUp(a, b, c)

        assertEquals("SCHEDULE" to "ALERT", runBlocking { a.settings.get(Settings.DEFAULT_ALERT_MODE) to b.settings.get(Settings.DEFAULT_ALERT_MODE) })
        assertEquals(true to false, runBlocking { a.settings.get(Settings.SHOW_REMINDERS_ON_DAY) to b.settings.get(Settings.SHOW_REMINDERS_ON_DAY) })
    }

    @Test
    fun mnemoBackupRestoresPrefs_aRestoredPhoneGetsTheDeviceChoicesOfTheBackup() = World(tmp.root, 5).with { a, b, c ->
        setUp(a, b, c)

        assertEquals("SCHEDULE" to true, runBlocking { c.settings.get(Settings.DEFAULT_ALERT_MODE) to c.settings.get(Settings.SHOW_REMINDERS_ON_DAY) })
    }

    @Test
    fun mnemoFolderNotRestored_aRestoredPhoneDoesNotInheritTheFolderGrant() = World(tmp.root, 6).with { a, b, c ->
        setUp(a, b, c)
        // Even a backup written by something that carried it.
        runBlocking { c.settings.restore(SettingsBackup(emptyMap(), mapOf(Settings.SYNC_FOLDER.key to "content://tree/factotum"))) }

        assertEquals("", runBlocking { c.settings.get(Settings.SYNC_FOLDER) })
    }

    @Test
    fun equipoisePersonalTravels_theThresholdAndContactsReachEveryDeviceAndTheRestoredPhone() = World(tmp.root, 7).with { a, b, c ->
        setUp(a, b, c)

        for (d in listOf(b, c)) assertEquals(0.7 to "Ada 555-0100", runBlocking { d.settings.get(Settings.BURNOUT_THRESHOLD) to d.settings.get(Settings.CRISIS_CONTACTS) })
    }

    @Test
    fun equipoiseLlmStays_theModelPathNeverLeavesTheDevice() = World(tmp.root, 8).with { a, b, c ->
        setUp(a, b, c)

        assertFalse("gemma.gguf" in folderText())
        assertEquals("" to "", runBlocking { b.settings.get(Settings.LLM_MODEL) to c.settings.get(Settings.LLM_MODEL) })
    }

    @Test
    fun sharedFirstRunNotRestored_aNewPhoneAsksItsFirstRunQuestions() = World(tmp.root, 9).with { a, b, c ->
        setUp(a, b, c)
        runBlocking {
            c.settings.restore(SettingsBackup(emptyMap(), mapOf(Settings.FIRST_RUN_DONE.key to "true", Settings.AI_KEY.key to "stolen", "unknown_key" to "x")))
        }

        assertEquals(false to "", runBlocking { c.settings.get(Settings.FIRST_RUN_DONE) to c.settings.get(Settings.AI_KEY) })
    }

    @Test
    fun aPersonalSettingChangedOnTwoDevicesKeepsTheLaterAndTheDefaultClearsIt() = World(tmp.root, 10).with { a, b, _ ->
        runBlocking { a.settings.set(Settings.CRISIS_CONTACTS, "first") }
        syncthing.now += 10
        runBlocking { b.settings.set(Settings.CRISIS_CONTACTS, "second") }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals("second", runBlocking { d.settings.get(Settings.CRISIS_CONTACTS) })

        runBlocking { b.settings.set(Settings.CRISIS_CONTACTS, "") }
        settle(listOf(a, b))
        assertEquals(listOf<String?>(null), runBlocking { a.db.settingDao().allSettings() }.map { it.value })
        assertEquals(listOf("setting:crisis_contacts"), runBlocking { a.db.settingDao().allSettings() }.map { it.id })
    }

    @Test
    fun theDayStartSetOnOneDeviceDecidesTheDayOnAnotherAtOnce() = World(tmp.root, 11).with { a, b, _ ->
        val reading = runBlocking { a.activities.create("Reading") }
        runBlocking { a.time.logManual(reading, LocalDateTime(2026, 10, 6, 2, 0), LocalDateTime(2026, 10, 6, 3, 0)) }
        settle(listOf(a, b))
        val monday = LocalDate(2026, 10, 5)
        val later = LocalDateTime(2026, 10, 7, 0, 0)
        assertEquals(0L, runBlocking { b.time.total(listOf(monday), later) })

        runBlocking { a.settings.set(Settings.DAY_START, LocalTime(4, 0)) }
        settle(listOf(a, b))

        assertEquals(3_600L, runBlocking { b.time.total(listOf(monday), later) })
    }

    @Test
    fun theLongTimerLimitIsOneSettingForEveryDevice() = World(tmp.root, 12).with { a, b, _ ->
        val reading = runBlocking { a.activities.create("Reading") }
        val span = runBlocking { a.time.start(reading, LocalDateTime(2026, 10, 5, 8, 0)) }
        runBlocking { a.settings.set(Settings.LONG_RUN, 2.hours) }
        settle(listOf(a, b))

        assertEquals(listOf(span), runBlocking { b.time.runningLong(LocalDateTime(2026, 10, 5, 10, 1)) }.map { it.id })
        runBlocking { b.time.stopAtLimit(span) }
        assertEquals(LocalDateTime(2026, 10, 5, 10, 0), runBlocking { b.time.spansOn(LocalDate(2026, 10, 5)) }.single().end)
    }

    @Test
    fun aValueThatDoesNotReadReadsAsTheDefaultAndOneOutOfRangeIsRefused() = World(tmp.root, 13).with { a, _, _ ->
        runBlocking {
            a.db.useWriterConnection {
                it.execSQL(
                    "INSERT INTO setting (id, value, hlc, device) VALUES ('setting:day_start', '25:99', 1, 'X'), " +
                        "('setting:long_run_hours', '0', 1, 'X'), ('setting:burnout_threshold', 'high', 1, 'X')",
                )
            }
        }

        assertEquals(LocalTime(0, 0), runBlocking { a.settings.get(Settings.DAY_START) })
        assertEquals(12.hours, runBlocking { a.settings.get(Settings.LONG_RUN) })
        assertEquals(0.5, runBlocking { a.settings.get(Settings.BURNOUT_THRESHOLD) })
        assertFailsWith<IllegalArgumentException> { runBlocking { a.settings.set(Settings.LONG_RUN, 0.hours) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { a.settings.set(Settings.LONG_RUN, 90.seconds) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { a.settings.set(Settings.DEFAULT_ALERT_MODE, "FOCUS") } }
        // No upper bound was decided: a long limit a newer device allows reads here too.
        runBlocking { a.settings.set(Settings.LONG_RUN, 72.hours) }
        assertEquals(72.hours, runBlocking { a.settings.get(Settings.LONG_RUN) })
        runBlocking { a.settings.set(Settings.APP_LOCK_GRACE, 30.seconds) }
        assertEquals(30.seconds, runBlocking { a.settings.get(Settings.APP_LOCK_GRACE) })
    }

    @Test
    fun appLockIsPerDeviceAndNeverOnWithoutThisDevicesPin() = World(tmp.root, 14).with { a, b, c ->
        assertFailsWith<IllegalArgumentException> { runBlocking { a.settings.set(Settings.APP_LOCK, true) } }
        runBlocking { a.settings.set(Settings.APP_LOCK_PIN, "salt:hash") }
        runBlocking { a.settings.set(Settings.APP_LOCK, true) }
        runBlocking { a.settings.set(Settings.APP_LOCK_GRACE, 30.seconds) }
        settle(listOf(a, b))
        runBlocking { c.settings.restore(a.settings.export()) }

        assertEquals(false to "", runBlocking { b.settings.get(Settings.APP_LOCK) to b.settings.get(Settings.APP_LOCK_PIN) })
        // The restored phone gets the grace period, as every device choice, but not a lock it has no PIN for.
        assertEquals(Triple(false, "", 30.seconds), runBlocking { Triple(c.settings.get(Settings.APP_LOCK), c.settings.get(Settings.APP_LOCK_PIN), c.settings.get(Settings.APP_LOCK_GRACE)) })
    }

    @Test
    fun anOldBackupNeverOutranksANewerPersonalValue() = World(tmp.root, 15).with { a, b, c ->
        runBlocking { a.settings.set(Settings.CRISIS_CONTACTS, "Ada") }
        val january = runBlocking { a.settings.export() }
        syncthing.now += 1_000
        runBlocking { a.settings.set(Settings.CRISIS_CONTACTS, "Bob") }
        settle(listOf(a, b))

        runBlocking { c.settings.restore(january) }
        assertEquals("Ada", runBlocking { c.settings.get(Settings.CRISIS_CONTACTS) })
        settle(listOf(a, b, c))

        for (d in listOf(a, b, c)) assertEquals("Bob", runBlocking { d.settings.get(Settings.CRISIS_CONTACTS) })
    }

    @Test
    fun aRestoreClearsADevicePreferenceThatIsTheDefault() = World(tmp.root, 16).with { _, _, c ->
        runBlocking { c.settings.restore(SettingsBackup(emptyMap(), mapOf(Settings.DEFAULT_ALERT_MODE.key to "SCHEDULE"))) }

        assertNull(runBlocking { c.db.settingDao().deviceValue(Settings.DEFAULT_ALERT_MODE.key) })
    }

    @Test
    fun aPersonalSettingThisVersionDoesNotKnowTravelsAsItCame() = World(tmp.root, 17).with { a, b, _ ->
        runBlocking {
            a.db.useWriterConnection { it.execSQL("INSERT INTO setting (id, value, hlc, device) VALUES ('setting:from_the_future', '42', 5, 'Z')") }
        }
        settle(listOf(a, b))

        assertEquals(listOf("42"), runBlocking { b.db.settingDao().settings(listOf("setting:from_the_future")) }.map { it.value })
    }

    @Test
    fun aDeviceWhoseDatabaseWasRecoveredGetsItsSettingsBackFromItsOwnFiles() {
        val w = World(tmp.root, 18)
        try {
            val a = w.Device("A")
            runBlocking { a.settings.set(Settings.DAY_START, LocalTime(4, 0)) }
            runBlocking { a.settings.set(Settings.CRISIS_CONTACTS, "Ada") }
            runBlocking { a.sync.export() }
            a.db.close()
            java.io.File(tmp.root, "A.db").delete()

            val again = w.Device("A")
            runBlocking { again.sync.import() }

            assertEquals(LocalTime(4, 0) to "Ada", runBlocking { again.settings.get(Settings.DAY_START) to again.settings.get(Settings.CRISIS_CONTACTS) })
        } finally {
            w.close()
        }
    }

    /** SPEC:R34: a database made anew reads this device's own files, so its rows come back with no peer, and its DEVICE settings start at their defaults. */
    @Test
    fun aRecoveredDeviceGetsItsRowsBackFromItsOwnFilesAndItsDeviceSettingsStartAtTheirDefaults() {
        val w = World(tmp.root, 21)
        try {
            val a = w.Device("A")
            val task = runBlocking { a.items.createTask("tax form", LocalDate(2026, 10, 5)) }
            val label = runBlocking { a.labels.create("Home") }
            runBlocking { a.labels.label(task, label) }
            runBlocking { a.settings.set(Settings.SHOW_REMINDERS_ON_DAY, true) }
            runBlocking { a.settings.set(Settings.WINDOW_FRAME, "10,10,1200,800") }
            runBlocking { a.sync.export() }
            a.db.close()
            java.io.File(tmp.root, "A.db").delete()

            val again = w.Device("A")
            runBlocking { again.sync.import() }

            assertEquals("tax form", runBlocking { again.items.item(task) }?.title)
            assertEquals(label, runBlocking { again.labels.labelOf(task) })
            assertEquals(false to "", runBlocking { again.settings.get(Settings.SHOW_REMINDERS_ON_DAY) to again.settings.get(Settings.WINDOW_FRAME) })
        } finally {
            w.close()
        }
    }

    /** SPEC:R120: each key in the spec's table, with its scope and default; the PERSONAL ones sync. */
    @Test
    fun eachSettingKeyHasItsScopeAndDefaultAndThePersonalOnesSync() = World(tmp.root, 19).with { a, b, _ ->
        fun <T> declared(setting: Setting<T>, key: String, scope: SettingScope, default: T) {
            assertEquals(key to scope, setting.key to setting.scope, key)
            assertEquals(default, runBlocking { a.settings.get(setting) }, key)
        }
        declared(Settings.DAY_START, "day_start", SettingScope.PERSONAL, LocalTime(0, 0))
        declared(Settings.LONG_RUN, "long_run_hours", SettingScope.PERSONAL, 12.hours)
        declared(Settings.SHOW_REMINDERS_ON_DAY, "show_reminders_on_day", SettingScope.DEVICE_PREF, false)
        declared(Settings.APP_LOCK, "app_lock", SettingScope.DEVICE_PREF, false)
        declared(Settings.APP_LOCK_GRACE, "app_lock_grace_seconds", SettingScope.DEVICE_PREF, Duration.ZERO)
        declared(Settings.APP_LOCK_PIN, "app_lock_pin", SettingScope.SECRET, "")
        declared(Settings.ONBOARDING_ANSWER, "onboarding_answer", SettingScope.PERSONAL, OnboardingAnswer.MIXED)
        declared(Settings.MIXED_MODE, "mixed_mode", SettingScope.PERSONAL, MixedMode.EVERY_TIME)
        declared(Settings.SLEEP_TRACKER, "sleep_tracker", SettingScope.PERSONAL, "")
        declared(Settings.AI_KEY, "ai_key", SettingScope.SECRET, "")
        declared(Settings.LLM_ENDPOINT_KEY, "llm_endpoint_key", SettingScope.SECRET, "")
        declared(Settings.BURNOUT_THRESHOLD, "burnout_threshold", SettingScope.PERSONAL, 0.5)
        declared(Settings.CRISIS_CONTACTS, "crisis_contacts", SettingScope.PERSONAL, "")
        declared(Settings.DEFAULT_ALERT_MODE, "default_alert_mode", SettingScope.DEVICE_PREF, "SCHEDULE")
        declared(Settings.FIRST_RUN_DONE, "first_run_done", SettingScope.DEVICE_STATE, false)
        declared(Settings.SYNC_FOLDER, "sync_folder", SettingScope.DEVICE_STATE, "")
        declared(Settings.WINDOW_FRAME, "window_frame", SettingScope.DEVICE_STATE, "")
        declared(Settings.LLM_MODEL, "llm_model", SettingScope.DEVICE_STATE, "")

        runBlocking {
            a.settings.set(Settings.DAY_START, LocalTime(5, 0))
            a.settings.set(Settings.ONBOARDING_ANSWER, OnboardingAnswer.LESS)
            a.settings.set(Settings.MIXED_MODE, MixedMode.AUTO)
            a.settings.set(Settings.SLEEP_TRACKER, "sleep")
            a.settings.set(Settings.BURNOUT_THRESHOLD, 0.7)
            a.settings.set(Settings.CRISIS_CONTACTS, "Ada 555-0100")
        }
        settle(listOf(a, b))

        assertEquals(
            listOf(LocalTime(5, 0), OnboardingAnswer.LESS, MixedMode.AUTO, "sleep", 0.7, "Ada 555-0100"),
            runBlocking {
                listOf(
                    b.settings.get(Settings.DAY_START), b.settings.get(Settings.ONBOARDING_ANSWER), b.settings.get(Settings.MIXED_MODE),
                    b.settings.get(Settings.SLEEP_TRACKER), b.settings.get(Settings.BURNOUT_THRESHOLD), b.settings.get(Settings.CRISIS_CONTACTS),
                )
            },
        )
    }

    /** SPEC:R121: DEVICE_PREF values live in the local `device_setting` table, which no export reads; a PERSONAL one beside them does travel. */
    @Test
    fun aDevicePreferenceNeverReachesTheFolder() = World(tmp.root, 20).with { a, b, _ ->
        val prefs = listOf(Settings.SHOW_REMINDERS_ON_DAY.key, Settings.DEFAULT_ALERT_MODE.key, Settings.APP_LOCK_GRACE.key)
        runBlocking {
            a.settings.set(Settings.SHOW_REMINDERS_ON_DAY, true)
            a.settings.set(Settings.DEFAULT_ALERT_MODE, "ALERT")
            a.settings.set(Settings.APP_LOCK_GRACE, 45.seconds)
            a.settings.set(Settings.CRISIS_CONTACTS, "Ada")
        }
        settle(listOf(a, b))

        val folder = folderText()
        assertTrue(Settings.CRISIS_CONTACTS.key in folder)
        for (key in prefs) {
            assertFalse(key in folder, key)
            assertEquals(emptyList(), runBlocking { a.db.settingDao().settings(listOf("setting:$key")) }, key)
        }
        assertEquals(listOf("true", "ALERT", "45"), runBlocking { prefs.map { a.db.settingDao().deviceValue(it) } })
        assertEquals(
            Triple(false, "SCHEDULE", Duration.ZERO),
            runBlocking { Triple(b.settings.get(Settings.SHOW_REMINDERS_ON_DAY), b.settings.get(Settings.DEFAULT_ALERT_MODE), b.settings.get(Settings.APP_LOCK_GRACE)) },
        )
    }
}
