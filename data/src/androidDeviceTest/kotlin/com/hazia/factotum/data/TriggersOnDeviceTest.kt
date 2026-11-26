package com.hazia.factotum.data

import androidx.room.useReaderConnection
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hazia.factotum.data.search.searchTriggers
import com.hazia.factotum.data.tracker.TrackerType
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.runner.RunWith
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * SPEC:R196: the triggers the database callback installs, on the Android framework driver: every
 * kind is there after an open, and each kind fires as it does on the desktop's bundled driver.
 */
@RunWith(AndroidJUnit4::class)
class TriggersOnDeviceTest {

    private val d = DeviceDatabase()

    @After fun close() = d.close()

    private fun triggers() = d.read("SELECT name FROM sqlite_master WHERE type = 'trigger'") { it.getText(0) }.toSet()

    @Test
    fun everyTriggerTheOpenMakesIsThere() {
        val outbox = SYNCED_TABLES.flatMap { t -> listOf("insert", "update", "delete").map { "${t}_outbox_$it" } } + listOf("purge_outbox_insert", "purge_outbox_update")
        val search = searchTriggers.mapNotNull { Regex("^CREATE TRIGGER (\\w+)").find(it)?.groupValues?.get(1) }
        val rules = listOf("item_rules_insert", "reminder_rules_update", "occurrence_edit_once", "time_span_owner_fixed", "block_made_fixed")
        val held = triggers()
        report("R196 triggers=${held.size} sqlite=${d.read("SELECT sqlite_version()") { it.getText(0) }.single()}")

        assertTrue(held.containsAll(outbox + search + rules), "missing: ${(outbox + search + rules) - held}")
    }

    @Test
    fun aRuleTriggerRefusesARowThatBreaksItsRules() {
        runBlocking { d.reminders.createStandalone("pills", LocalDate(2026, 10, 5), LocalTime(8, 0)) }

        assertTrue("reminder: a row breaks its rules" in d.refused("UPDATE reminder SET alert_kind = 'BEEP'"))
    }

    @Test
    fun aSpanStaysOnItsOwner() {
        val walk = runBlocking { d.activities.create("Walk") }
        val read = runBlocking { d.activities.create("Read") }
        val span = runBlocking { d.time.logManual(walk, LocalDateTime(2026, 10, 5, 7, 0), LocalDateTime(2026, 10, 5, 8, 0)) }

        assertTrue("a span stays on its owner" in d.refused("UPDATE time_span SET item_id = '$read' WHERE id = '$span'"))
    }

    /** A row written around the repositories, as a peer's import writes, still reaches the outbox and the index. */
    @Test
    fun aRawWriteReachesTheOutboxAndTheIndex() {
        val mood = runBlocking { d.trackers.create("Mood", TrackerType.RATING) }
        d.write("INSERT INTO tracker_reading (id, tracker_id, at, rating_value, note, hlc, device) VALUES ('raw', '$mood', '2026-10-05T09:00', 3, 'quantum by hand', 1, 'X')")

        assertEquals(listOf("tracker_reading"), d.read("SELECT tbl FROM sync_outbox WHERE id = 'raw'") { it.getText(0) })
        assertEquals(1, d.read("SELECT docid FROM search_fts WHERE search_fts MATCH 'quantum'") { it.getLong(0) }.size)
    }

    /** The triggers are made again on every open (SchemaTriggers.onOpen), so a second open finds the same set. */
    @Test
    fun aSecondOpenKeepsTheSameTriggers() {
        val first = triggers()
        d.db.close()
        val again = openFactotumDatabase(context).database
        try {
            val second = runBlocking {
                again.useReaderConnection { c -> c.usePrepared("SELECT name FROM sqlite_master WHERE type = 'trigger'") { s -> buildSet { while (s.step()) add(s.getText(0)) } } }
            }
            assertEquals(first, second)
        } finally {
            again.close()
        }
    }
}
