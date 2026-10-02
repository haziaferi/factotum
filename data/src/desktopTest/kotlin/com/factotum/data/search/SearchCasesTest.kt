package com.factotum.data.search

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import androidx.sqlite.execSQL
import com.factotum.data.FactotumDatabase
import com.factotum.data.FixedSettings
import com.factotum.data.LocalWrites
import com.factotum.data.createAtVersion
import com.factotum.data.item.ItemRepository
import com.factotum.data.item.TaskStatus
import com.factotum.data.openFactotumDatabase
import com.factotum.data.reminder.ReminderRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import com.factotum.data.time.ActivityRepository
import com.factotum.data.time.TimeRepository
import com.factotum.data.tracker.TrackerRepository
import com.factotum.data.tracker.TrackerType
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * ADR 10's cases (`decisions/cases/10-search.jsonl`) that need no page, with the owner's 2026-10-03
 * answers; the page and block halves come with slice 12.
 */
class SearchCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var search: SearchRepository
    private lateinit var items: ItemRepository
    private lateinit var reminders: ReminderRepository
    private lateinit var trackers: TrackerRepository
    private lateinit var activities: ActivityRepository
    private lateinit var time: TimeRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "search.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        search = SearchRepository(db)
        items = ItemRepository(db, writes, newId)
        reminders = ReminderRepository(db, writes, newId, FixedSettings())
        trackers = TrackerRepository(db, writes, newId)
        activities = ActivityRepository(db, writes, newId, FixedSettings())
        time = TimeRepository(db, writes, newId, FixedSettings())
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun at(day: Int, hour: Int) = LocalDateTime(2026, 10, day, hour, 0)

    private val now = LocalDateTime(2026, 10, 6, 12, 0)

    private fun indexed() = runBlocking { db.useReaderConnection { c -> c.usePrepared("SELECT count(*) FROM search_key") { it.step(); it.getLong(0) } } }

    private fun find(query: String) = runBlocking { search.search(query, now) }

    private fun ids(query: String) = find(query).map { it.id }

    @Test
    fun chronicleAllKinds_anActivityAReminderATrackerALogAndASessionAreFoundByOneWord() {
        val walk = runBlocking { activities.create("Quantum walk") }
        val pills = runBlocking { reminders.createStandalone("quantum pills", monday, LocalTime(8, 0)) }
        val mood = runBlocking { trackers.create("Quantum mood", TrackerType.RATING) }
        val log = runBlocking { trackers.log(mood, at(5, 9), rating = 3, note = "felt quantum") }
        val span = runBlocking { time.logManual(walk, at(5, 7), at(5, 8), "a quantum leap") }

        assertEquals(setOf(walk, pills, mood, log, span), ids("quantum").toSet())
    }

    @Test
    fun chronicleTombstoneLeaves_aDeletedReminderIsNoLongerFound() {
        val pills = runBlocking { reminders.createStandalone("quantum pills", monday, LocalTime(8, 0)) }
        assertEquals(listOf(pills), ids("quantum"))

        runBlocking { items.delete(pills) }

        assertEquals(emptyList(), ids("quantum"))
        assertEquals(0L, indexed())
    }

    @Test
    fun chronicleAnyWritePath_aLogWrittenAroundTheRepositoriesOrArrivingFromAPeerIsFound() {
        val mood = runBlocking { trackers.create("Mood", TrackerType.RATING) }
        runBlocking {
            db.useWriterConnection {
                it.execSQL(
                    "INSERT INTO tracker_reading (id, tracker_id, at, rating_value, note, hlc, device) VALUES ('raw', '$mood', '2026-10-05T09:00', 3, 'quantum by hand', 1, 'X')",
                )
            }
        }
        assertEquals(listOf("raw"), ids("quantum"))

        val w = World(tmp.root, 1)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val walk = runBlocking { a.activities.create("Quantum walk") }
            w.settle(listOf(a, b))
            assertEquals(listOf(walk), runBlocking { SearchRepository(b.db).search("quantum", now) }.map { it.id })
        } finally {
            w.close()
        }
    }

    @Test
    fun chronicleAccentsFolded_perchéIsFoundAsPercheAndCaseNeverMatters() {
        val why = runBlocking { items.createTask("Perché no?", monday) }

        assertEquals(listOf(why), ids("perche"))
        assertEquals(listOf(why), ids("PERCHÉ"))
        assertEquals(listOf(why), ids("perc"))
        // Typed or pasted with each accent apart from its letter, inside a word as well as at its end.
        val summer = runBlocking { items.createTask("\u00c9t\u00e9 chaud", monday) }
        assertEquals(listOf(summer), ids("e\u0301te\u0301"))
    }

    @Test
    fun sharedOneSearch_itemsAndSessionsComeBackFromOneQueryNamesFirstThenNewest() {
        val older = runBlocking { items.createTask("Dune reread", LocalDate(2026, 10, 1)) }
        val newer = runBlocking { items.createTask("Dune notes", LocalDate(2026, 10, 7)) }
        val reading = runBlocking { activities.create("Reading") }
        val early = runBlocking { time.logManual(reading, at(5, 20), at(5, 21), "Dune chapter one") }
        val late = runBlocking { time.logManual(reading, at(6, 20), at(6, 21), "Dune chapter two") }

        assertEquals(listOf(newer, older, late, early), ids("dune"))
        assertEquals(listOf(late), ids("dune two"))
        assertEquals("Reading", find("chapter").first().owner)
    }

    @Test
    fun searchStartsAtTwoLetters() {
        runBlocking { items.createTask("Quantum", monday) }

        assertEquals(emptyList(), ids("q"))
        assertEquals(emptyList(), ids(" - "))
        assertEquals(1, ids("qu").size)
    }

    @Test
    fun whatWasWrittenUnderAnArchivedActivityStaysFindableButItsNameAndAnythingDeletedDoNot() {
        val walk = runBlocking { activities.create("Quantum walk") }
        val span = runBlocking { time.logManual(walk, at(5, 7), at(5, 8), "quantum park") }
        val mood = runBlocking { trackers.create("Quantum mood", TrackerType.RATING) }
        val log = runBlocking { trackers.log(mood, at(5, 9), rating = 3, note = "quantum note") }

        runBlocking { activities.setArchived(walk, true) }
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE tracker SET archived = 1 WHERE id = '$mood'") } }
        assertEquals(setOf(span to "Quantum walk", log to "Quantum mood"), find("quantum").map { it.id to it.owner }.toSet())

        runBlocking { activities.delete(walk) }
        runBlocking { trackers.delete(mood) }
        assertEquals(emptyList(), ids("quantum"))
    }

    @Test
    fun finishedTasksAreFoundAndMarked() {
        val done = runBlocking { items.createTask("Quantum done", monday) }
        val open = runBlocking { items.createTask("Quantum open", monday) }
        runBlocking { items.setStatus(done, TaskStatus.DONE) }

        assertEquals(mapOf(done to true, open to false), find("quantum").associate { it.id to it.done })
    }

    @Test
    fun aPastEventIsMarkedFinishedAndARepeatingOneIsNot() {
        val past = runBlocking { items.createEvent("Quantum talk", monday, LocalTime(10, 0)) }
        val later = runBlocking { items.createEvent("Quantum lunch", LocalDate(2026, 10, 9)) }

        assertEquals(mapOf(past to true, later to false), find("quantum").associate { it.id to it.done })
    }

    @Test
    fun aSubtaskUnderADeletedParentIsNotFound() {
        val parent = runBlocking { items.createTask("Plan", monday) }
        val child = runBlocking { items.createTask("Quantum step", monday, parentId = parent) }
        assertEquals(listOf(child), ids("quantum"))

        // As when another device deleted the parent before this subtask reached it.
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE item SET deleted_at = 1 WHERE id = '$parent'") } }

        assertEquals(emptyList(), ids("quantum"))
    }

    @Test
    fun aQueryWithMoreHitsThanSqliteTakesVariablesStillAnswers() {
        val mood = runBlocking { trackers.create("Mood", TrackerType.RATING) }
        runBlocking {
            db.useWriterConnection {
                it.execSQL(
                    "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 1200) " +
                        "INSERT INTO tracker_reading (id, tracker_id, at, rating_value, note, hlc, device) " +
                        "SELECT 'r' || i, '$mood', '2026-10-05T09:00', 3, 'quantum ' || i, 1, 'X' FROM n",
                )
            }
        }

        assertEquals(1200, ids("quantum").size)
    }

    @Test
    fun anIndexThatMissesRowsIsRebuiltOnOpenAndAnUpgradedDatabaseIsIndexed() {
        runBlocking { items.createTask("Quantum one", monday) }
        runBlocking { db.useWriterConnection { it.execSQL("DELETE FROM search_fts") } }
        db.close()
        open()
        assertEquals(1, ids("quantum").size)

        val file = File(tmp.root, "v11.db")
        createAtVersion(file, 11) { c ->
            c.execSQL(
                "INSERT INTO item (id, kind, title, details_hlc, details_device, schedule_hlc, schedule_device, importance, status, status_hlc, status_device) " +
                    "VALUES ('old', 'TASK', 'Quantum old', 1, 'A', 1, 'A', 0, 'PENDING', 1, 'A')",
            )
        }
        val upgraded = openFactotumDatabase(file).database
        try {
            assertEquals(listOf("old"), runBlocking { SearchRepository(upgraded).search("quantum", now) }.map { it.id })
        } finally {
            upgraded.close()
        }
    }

    @Test
    fun spike1_theDesktopSqliteMakesTheFts4IndexAndReportsFts5() {
        // Spike 1 on the desktop driver (bundled SQLite); the phones' framework SQLite is measured with the Android shell.
        val (version, fts5) = runBlocking {
            db.useReaderConnection { c ->
                c.usePrepared("SELECT sqlite_version(), sqlite_compileoption_used('ENABLE_FTS5')") { it.step(); it.getText(0) to it.getLong(1) }
            }
        }
        println("spike 1, desktop: SQLite $version, FTS5 compiled in: ${fts5 == 1L}")
        // What the index needs: FTS4 with unicode61 folding accents by remove_diacritics=2.
        val sql = runBlocking { db.useReaderConnection { c -> c.usePrepared("SELECT sql FROM sqlite_master WHERE name = 'search_fts'") { it.step(); it.getText(0) } } }
        kotlin.test.assertTrue("FTS4" in sql && "remove_diacritics=2" in sql, sql)
    }
}
