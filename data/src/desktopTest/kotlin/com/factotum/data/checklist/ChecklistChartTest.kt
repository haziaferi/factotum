package com.factotum.data.checklist

import com.factotum.core.time.GoalPeriod
import com.factotum.data.FactotumDatabase
import com.factotum.data.FixedSettings
import com.factotum.data.LocalWrites
import com.factotum.data.chart.ChartRepository
import com.factotum.data.chart.ChartType
import com.factotum.data.chart.SourceKind
import com.factotum.data.openFactotumDatabase
import com.factotum.data.search.SearchRepository
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
import kotlin.test.assertFailsWith
import kotlin.test.assertNull

/** Chronicle's checklists and saved charts (§7 step 3), with the owner's answers of 2026-10-03 (decision 14). */
class ChecklistChartTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var checklists: ChecklistRepository
    private lateinit var charts: ChartRepository
    private lateinit var activities: ActivityRepository
    private lateinit var time: TimeRepository
    private lateinit var trackers: TrackerRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "c.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        val settings = FixedSettings(LocalTime(4, 0))
        checklists = ChecklistRepository(db, writes, newId)
        charts = ChartRepository(db, writes, newId, settings)
        activities = ActivityRepository(db, writes, newId, settings)
        time = TimeRepository(db, writes, newId, settings)
        trackers = TrackerRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private fun <T> two(seed: Int, body: World.(World.Device, World.Device) -> T): T {
        val w = World(tmp.root, seed)
        try {
            return w.body(w.Device("A"), w.Device("B"))
        } finally {
            w.close()
        }
    }

    // Checklists

    @Test
    fun aResetClearsATickMadeBeforeItEvenWhenTheTickSyncsAfter() = two(1) { a, b ->
        syncthing.now = 1_000
        val list = go { a.checklists.create("Morning") }
        val (tea, walk) = listOf("Tea", "Walk").map { go { a.checklists.addItem(list, it) } }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.checklists.check(tea, true) }
        syncthing.now = 3_000
        go { b.checklists.reset(list) }
        syncthing.now = 4_000
        go { b.checklists.check(walk, true) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("Tea" to false, "Walk" to true), go { d.checklists.items(list) }.map { it.text to it.checked })
    }

    @Test
    fun aDeleteWinsOverAnEditMadeApartAndARestoreBringsBackItsItems() = two(2) { a, b ->
        syncthing.now = 1_000
        val list = go { a.checklists.create("Packing") }
        val socks = go { a.checklists.addItem(list, "Socks") }
        val gone = go { a.checklists.addItem(list, "Old") }
        go { a.checklists.deleteItem(gone) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.checklists.delete(list) }
        syncthing.now = 3_000
        go { b.checklists.rename(list, "Packing list") }
        go { b.checklists.check(socks, true) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(emptyList(), go { d.checklists.checklists() })
        assertEquals(true, go { a.db.checklistDao().itemsOf(list) }.all { it.deletedAt != null })
        assertFailsWith<IllegalArgumentException> { go { a.checklists.addItem(list, "Hat") } }
        assertFailsWith<IllegalArgumentException> { go { a.checklists.check(socks, false) } }
        go { a.checklists.restore(list) }
        assertEquals(listOf("Packing list"), go { a.checklists.checklists() }.map { it.name })
        assertEquals(listOf("Socks"), go { a.checklists.items(list) }.map { it.text })
    }

    @Test
    fun aNewChecklistComesFirstAndListsAndItemsKeepTheirOrder() {
        val first = go { checklists.create("First") }
        val second = go { checklists.create("Second") }
        assertEquals(listOf("Second", "First"), go { checklists.checklists() }.map { it.name })
        go { checklists.move(second, first) }
        assertEquals(listOf("First", "Second"), go { checklists.checklists() }.map { it.name })

        val a = go { checklists.addItem(first, "a") }
        go { checklists.addItem(first, "c") }
        go { checklists.addItem(first, "b", after = a) }
        assertEquals(listOf("a", "b", "c"), go { checklists.items(first) }.map { it.text })
        go { checklists.moveItem(a, go { checklists.items(first) }.last().id) }
        assertEquals(listOf("b", "c", "a"), go { checklists.items(first) }.map { it.text })
        go { checklists.moveItem(a, null) }
        assertEquals(listOf("a", "b", "c"), go { checklists.items(first) }.map { it.text })
        assertFailsWith<IllegalArgumentException> { go { checklists.addItem(first, " ") } }
        assertFailsWith<IllegalArgumentException> { go { checklists.create("  ") } }
    }

    @Test
    fun checklistNamesComeFirstInSearchThenTheirItems() {
        val list = go { checklists.create("Harbour walk") }
        go { checklists.addItem(list, "Harbour map") }
        val hits = go { SearchRepository(db).search("harbour", LocalDateTime(2026, 10, 5, 12, 0)) }
        assertEquals(listOf("CHECKLIST" to null, "CHECKLIST_ITEM" to "Harbour walk"), hits.map { it.kind to it.owner })
        go { checklists.delete(list) }
        assertEquals(emptyList(), go { SearchRepository(db).search("harbour", LocalDateTime(2026, 10, 5, 12, 0)) })
    }

    // Saved charts

    @Test
    fun aChartShowsAnActivitysMinutesAndATrackersMeanPerPersonalDay() {
        val walk = go { activities.create("Walk") }
        go { activities.addGoal(walk, GoalPeriod.WEEK, 140) }
        val mood = go { trackers.create("Mood", TrackerType.RATING) }
        // 03:00 on the 5th counts for the 4th: the day starts at 04:00.
        go { time.logManual(walk, LocalDateTime(2026, 10, 5, 3, 0), LocalDateTime(2026, 10, 5, 3, 30)) }
        go { time.logManual(walk, LocalDateTime(2026, 10, 5, 9, 0), LocalDateTime(2026, 10, 5, 10, 0)) }
        go { trackers.log(mood, LocalDateTime(2026, 10, 5, 9, 0), rating = 2) }
        go { trackers.log(mood, LocalDateTime(2026, 10, 5, 20, 0), rating = 4) }
        val chart = go { charts.create(ChartType.LINE, 3, listOf(SourceKind.ACTIVITY to walk, SourceKind.TRACKER to mood), "Week") }

        val (minutes, moods) = go { charts.series(chart, LocalDateTime(2026, 10, 5, 21, 0)) }
        assertEquals(listOf(0.0, 30.0, 60.0), minutes.days.map { it.second })
        assertEquals(20.0, minutes.goalLine)
        assertEquals(listOf(null, null, 3.0), moods.days.map { it.second })
        assertEquals("Mood", moods.name)
        go { trackers.delete(mood) }
        val deleted = go { charts.series(chart, LocalDateTime(2026, 10, 5, 21, 0)) }.last()
        // At 02:00 on the 6th it is still the 5th's personal day.
        assertEquals(LocalDate(2026, 10, 5), go { charts.series(chart, LocalDateTime(2026, 10, 6, 2, 0)) }.first().days.last().first)
        assertNull(deleted.name)
        assertEquals(listOf(null, null, null), deleted.days.map { it.second })
    }

    @Test
    fun sourcesAddedOnTwoDevicesBothStayAndADeleteWinsOverAnEdit() = two(3) { a, b ->
        syncthing.now = 1_000
        val walk = go { a.activities.create("Walk") }
        val read = go { a.activities.create("Read") }
        val mood = go { a.trackers.create("Mood", TrackerType.RATING) }
        val chart = go { a.charts.create(ChartType.BAR, 7, listOf(SourceKind.ACTIVITY to walk)) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.charts.addSource(chart, SourceKind.ACTIVITY, read) }
        go { b.charts.addSource(chart, SourceKind.TRACKER, mood) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(setOf(walk, read, mood), go { d.charts.charts() }.single().sources.map { it.second }.toSet())

        syncthing.now = 3_000
        go { a.charts.delete(chart) }
        syncthing.now = 4_000
        go { b.charts.setRange(chart, 30) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(emptyList(), go { d.charts.charts() })
    }

    @Test
    fun aNewChartComesFirstAndASourceIsOnAChartOnce() {
        val walk = go { activities.create("Walk") }
        val first = go { charts.create(ChartType.LINE, 7, listOf(SourceKind.ACTIVITY to walk)) }
        val second = go { charts.create(ChartType.PIE, 7, listOf(SourceKind.ACTIVITY to walk)) }
        assertEquals(listOf(second, first), go { charts.charts() }.map { it.id })
        assertFailsWith<IllegalArgumentException> { go { charts.create(ChartType.LINE, 7, listOf(SourceKind.ACTIVITY to walk, SourceKind.ACTIVITY to walk)) } }
        assertFailsWith<IllegalArgumentException> { go { charts.create(ChartType.LINE, 0, emptyList()) } }
        assertFailsWith<IllegalArgumentException> { go { charts.create(ChartType.LINE, 7, listOf(SourceKind.TRACKER to walk)) } }
        go { charts.removeSource(first, SourceKind.ACTIVITY, walk) }
        assertEquals(emptyList(), go { charts.charts() }.single { it.id == first }.sources)
        go { charts.addSource(first, SourceKind.ACTIVITY, walk) }
        assertEquals(listOf(walk), go { charts.charts() }.single { it.id == first }.sources.map { it.second })
    }

    @Test
    fun anItemDeletedByHandComesBackFromTheTrashAndAListsRestoreTakesBackOnlyWhatItsDeletionTook() = two(4) { a, b ->
        syncthing.now = 1_000
        val list = go { a.checklists.create("Packing") }
        val socks = go { a.checklists.addItem(list, "Socks") }
        val hat = go { a.checklists.addItem(list, "Hat") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.checklists.deleteItem(hat) }
        assertEquals(listOf("Hat"), go { a.checklists.trashedItems(list) }.map { it.text })
        go { a.checklists.restoreItem(hat) }
        go { a.checklists.deleteItem(hat) }
        // A adds an item B has not seen, then both delete the list.
        val scarf = go { a.checklists.addItem(list, "Scarf") }
        syncthing.now = 3_000
        go { a.checklists.delete(list) }
        syncthing.now = 3_100
        go { b.checklists.delete(list) }
        settle(listOf(a, b))

        go { a.checklists.restore(list) }
        assertEquals(listOf(socks, scarf), go { a.checklists.items(list) }.map { it.id })
    }

    @Test
    fun anItemAddedElsewhereToAListDeletedHereIsNotFound() = two(5) { a, b ->
        syncthing.now = 1_000
        val list = go { a.checklists.create("Errands") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.checklists.delete(list) }
        val stamps = go { b.checklists.addItem(list, "Harbour stamps") }
        settle(listOf(a, b))
        assertEquals(emptyList(), go { SearchRepository(a.db).search("harbour", LocalDateTime(2026, 10, 5, 12, 0)) })
        // Live itself, but on a list in the Trash: it is not edited.
        assertFailsWith<IllegalArgumentException> { go { a.checklists.check(stamps, true) } }
        Unit
    }
}
