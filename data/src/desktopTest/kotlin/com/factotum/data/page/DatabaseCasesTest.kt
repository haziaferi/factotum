package com.factotum.data.page

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.label.LabelRepository
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** ADR 12's database cases (`decisions/cases/12-page-merge.jsonl`) and the owner's answers on databases, 2026-10-03 (slice 12b). */
class DatabaseCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var pages: PageRepository
    private lateinit var databases: DatabaseRepository
    private lateinit var labels: LabelRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "databases.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        pages = PageRepository(db, writes, newId, { 1_000 })
        databases = DatabaseRepository(db, writes, newId, pages)
        labels = LabelRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private fun <T> two(seed: Int, body: World.(World.Device, World.Device) -> T): T {
        val w = World(tmp.root, seed)
        try {
            return w.body(w.Device("A"), w.Device("B"))
        } finally {
            w.close()
        }
    }

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    @Test
    fun aCellAndTheBodyEditedApartBothStand() = two(1) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        val hotel = go { a.pages.addBlock(rome, content = "Hotel") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.setText(rome, status, "Booked") }
        go { b.pages.setText(hotel, "Hotel Roma") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals("Booked", go { d.databases.cells(trips, rome) }.getValue(status).text)
            assertEquals(listOf("Hotel Roma"), go { d.pages.outline(rome) }.map { it.content })
        }
    }

    @Test
    fun aCellSetApartKeepsTheLaterAndTheEarlierIsInHistoryWithANotice() = two(2) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val booked = go { a.databases.addOption(status, "Booked") }
        val cancelled = go { a.databases.addOption(status, "Cancelled") }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.setOption(rome, status, booked) }
        syncthing.now = 3_000
        go { b.databases.setOption(rome, status, cancelled) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf(cancelled), go { d.databases.cells(trips, rome) }.getValue(status).options)
            // shared-cell-loser-recoverable
            assertEquals(listOf("Booked"), go { d.pages.notices(rome) }.map { it.lostText })
        }
        val merge = go { a.pages.revisions(rome) }.single { it.reason == "MERGE" }
        go { a.pages.restoreRevision(merge.id) }
        assertEquals(listOf(booked), go { a.databases.cells(trips, rome) }.getValue(status).options)
    }

    @Test
    fun aDeletedOptionReadsAsEmptyKeepsThePickAndComesBackWhenPickedLaterElsewhere() = two(3) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val booked = go { a.databases.addOption(status, "Booked") }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        val milan = go { a.pages.create("Milan", parentId = trips) }
        go { a.databases.setOption(rome, status, booked) }
        val board = go { a.databases.addView(trips, "Board", ViewType.BOARD) }
        go { a.databases.setLayout(board, ViewType.BOARD, groupBy = status) }
        settle(listOf(a, b))

        syncthing.now = 2_000
        go { a.databases.deleteOption(booked) }
        assertEquals(emptyList(), go { a.databases.cells(trips, rome) }.getValue(status).options)
        assertEquals(listOf<String?>(null), go { a.databases.board(board) }!!.map { it.optionId })
        assertEquals(setOf(rome, milan), go { a.databases.board(board) }!!.single().rows.map { it.pageId }.toSet())

        syncthing.now = 3_000
        go { b.databases.setOption(milan, status, booked) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf("Booked"), go { d.databases.options(status) }.map { it.name })
            // The pick kept through the deletion reads again too.
            assertEquals(listOf(booked), go { d.databases.cells(trips, rome) }.getValue(status).options)
        }
    }

    @Test
    fun aTypeChangeRewritesNoValueAndChangingBackReadsAsBefore() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val nights = go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val rome = go { pages.create("Rome", parentId = trips) }
        val milan = go { pages.create("Milan", parentId = trips) }
        go { databases.setText(rome, status, "Booked") }
        go { databases.setText(milan, status, "booked") }
        go { databases.setNumber(rome, nights, 3.0) }
        val stamps = { go { db.databaseDao().allValues() }.map { it.cellHlc } }
        val before = stamps()

        go { databases.setType(status, PropertyType.SELECT) }
        go { databases.setType(nights, PropertyType.TEXT) }

        assertEquals(before, stamps())
        val booked = go { databases.options(status) }.single()
        assertEquals("Booked", booked.name)
        assertEquals(listOf(booked.id), go { databases.cells(trips, milan) }.getValue(status).options)
        assertEquals("3", go { databases.cells(trips, rome) }.getValue(nights).text)
        go { databases.setType(status, PropertyType.TEXT) }
        go { databases.setType(nights, PropertyType.NUMBER) }
        assertEquals("Booked" to 3.0, go { databases.cells(trips, rome) }.let { it.getValue(status).text to it.getValue(nights).number })
    }

    @Test
    fun aSortAndAFilterChangedApartBothStand() = two(4) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val nights = go { a.databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val view = go { a.databases.views(trips) }.single().id
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.setSort(view, nights, descending = true) }
        go { b.databases.setFilter(view, nights, FilterOp.IS_NOT_EMPTY) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            val v = go { d.databases.views(trips) }.single()
            assertEquals(Triple(nights, true, FilterOp.IS_NOT_EMPTY), Triple(v.sortProperty, v.sortDescending, v.filterOp))
        }
    }

    @Test
    fun multiSelectPicksMadeApartBothStay() = two(5) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val tags = go { a.databases.addProperty(trips, "Tags", PropertyType.MULTI_SELECT) }
        val urgent = go { a.databases.addOption(tags, "urgent") }
        val work = go { a.databases.addOption(tags, "work") }
        val home = go { a.databases.addOption(tags, "home") }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        go { a.databases.pick(rome, tags, home) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.pick(rome, tags, urgent) }
        go { b.databases.pick(rome, tags, work) }
        go { b.databases.unpick(rome, tags, home) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(setOf(urgent, work), go { d.databases.cells(trips, rome) }.getValue(tags).options.toSet())
            assertEquals(emptyList(), go { d.pages.notices(rome) })
        }
    }

    @Test
    fun theRowsAreThePagesMadeInItAndThePagesCarryingItsLabel() {
        val trips = go { databases.create("Trips") }
        val rome = go { pages.create("Rome", parentId = trips) }
        val notes = go { pages.create("Packing notes") }
        val travel = go { labels.create("travel") }
        go { labels.labelPage(notes, travel) }
        assertEquals(listOf(rome), go { databases.members(trips) })

        go { databases.setDoorway(trips, travel) }
        assertEquals(listOf(rome, notes).sorted(), go { databases.members(trips) })
        go { labels.unlabelPage(notes, travel) }
        assertEquals(listOf(rome), go { databases.members(trips) })
        go { labels.labelPage(notes, travel) }
        go { labels.delete(travel) }
        assertEquals(listOf(rome), go { databases.members(trips) })
        val status = go { databases.addProperty(trips, "Status", PropertyType.TEXT) }
        assertFailsWith<IllegalArgumentException> { go { databases.setText(notes, status, "x") } }
        assertFailsWith<IllegalArgumentException> { go { databases.setNumber(rome, status, 1.0) } }
    }

    @Test
    fun twoOptionsOfOneNameMadeApartMergeIntoTheFirst() = two(6) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        settle(listOf(a, b))
        val first = go { a.databases.addOption(status, "Done") }
        syncthing.now = 2_000
        val second = go { b.databases.addOption(status, "done") }
        go { b.databases.setOption(rome, status, second) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf(first), go { d.databases.options(status) }.map { it.id })
            assertEquals(listOf(first), go { d.databases.cells(trips, rome) }.getValue(status).options)
        }
    }

    @Test
    fun aViewSortsByTypeWithEmptyLastAndFiltersByType() {
        val trips = go { databases.create("Trips") }
        val nights = go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val start = go { databases.addProperty(trips, "Start", PropertyType.DATE) }
        val name = go { databases.addProperty(trips, "Note", PropertyType.TEXT) }
        val ids = listOf("Rome", "Milan", "Bari", "Pisa").map { t -> go { pages.create(t, parentId = trips) } }
        listOf(9.0, 10.0, null, 2.5).zip(ids).forEach { (n, p) -> go { databases.setNumber(p, nights, n) } }
        go { databases.setDate(ids[0], start, LocalDate(2026, 11, 2)) }
        go { databases.setDate(ids[1], start, LocalDate(2026, 10, 30)) }
        go { databases.setText(ids[3], name, "Leaning tower") }
        val view = go { databases.views(trips) }.single().id
        val titles = { go { databases.rows(view) }.map { it.title } }

        go { databases.setSort(view, nights) }
        assertEquals(listOf("Pisa", "Rome", "Milan", "Bari"), titles())
        go { databases.setSort(view, nights, descending = true) }
        assertEquals(listOf("Milan", "Rome", "Pisa", "Bari"), titles())
        go { databases.setSort(view, start) }
        assertEquals(listOf("Milan", "Rome"), titles().take(2))

        go { databases.setFilter(view, nights, FilterOp.EQUALS, "10") }
        assertEquals(listOf("Milan"), titles())
        go { databases.setFilter(view, name, FilterOp.CONTAINS, "TOWER") }
        assertEquals(listOf("Pisa"), titles())
        go { databases.setFilter(view, nights, FilterOp.IS_EMPTY) }
        assertEquals(listOf("Bari"), titles())
        // A setting naming a property deleted since reads as none.
        go { databases.deleteProperty(nights) }
        assertEquals(4, titles().size)
    }

    @Test
    fun aBoardHasANoneColumnFirstThenTheOptionsInOrderAndMovingACardIsAPick() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val date = go { databases.addProperty(trips, "When", PropertyType.DATE) }
        val todo = go { databases.addOption(status, "To do") }
        val done = go { databases.addOption(status, "Done") }
        go { databases.moveOption(done, null) }
        val rome = go { pages.create("Rome", parentId = trips) }
        val board = go { databases.addView(trips, "Board", ViewType.BOARD) }
        assertNull(go { databases.board(board) })
        assertFailsWith<IllegalArgumentException> { go { databases.setLayout(board, ViewType.BOARD, groupBy = date) } }
        go { databases.setLayout(board, ViewType.BOARD, groupBy = status) }

        go { databases.setOption(rome, status, todo) }
        assertEquals(listOf(null to emptyList(), done to emptyList(), todo to listOf(rome)), go { databases.board(board) }!!.map { it.optionId to it.rows.map { r -> r.pageId } })
        assertFailsWith<IllegalArgumentException> { go { databases.addOption(status, " to DO ") } }
    }

    @Test
    fun aCellOrASchemaEditAfterATrashBringsThePageBack() = two(7) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        val other = go { a.databases.create("Books") }
        val author = go { a.databases.addProperty(other, "Author", PropertyType.TEXT) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(rome) }
        go { a.pages.trash(other) }
        syncthing.now = 3_000
        go { b.databases.setText(rome, status, "Booked") }
        go { b.databases.renameProperty(author, "Writer") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(false, go { d.pages.page(rome) }!!.trashed)
            assertEquals(false, go { d.pages.page(other) }!!.trashed)
        }
    }

    @Test
    fun trashingADatabaseTakesItsRowsAndDeletingItForeverTakesEverything() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val booked = go { databases.addOption(status, "Booked") }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.setOption(rome, status, booked) }
        go { pages.trash(trips) }
        assertEquals(true, go { pages.page(rome) }!!.trashed)
        go { pages.restore(trips) }
        assertEquals(false, go { pages.page(rome) }!!.trashed)

        go { pages.trash(trips) }
        go { pages.purge(trips) }

        val left = go {
            db.useReaderConnection { c ->
                c.usePrepared(
                    "SELECT (SELECT count(*) FROM page) + (SELECT count(*) FROM page_database) + (SELECT count(*) FROM property) + " +
                        "(SELECT count(*) FROM property_option) + (SELECT count(*) FROM property_value) + (SELECT count(*) FROM page_view)",
                ) { it.step(); it.getLong(0) }
            }
        }
        assertEquals(0, left)
    }

    @Test
    fun deletingAPropertyIsForGoodWithItsValues() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.setText(rome, status, "Booked") }
        go { databases.deleteProperty(status) }
        assertEquals(emptyList(), go { databases.properties(trips) })
        assertEquals(emptyList(), go { db.databaseDao().allValues() })
        assertEquals(1, go { db.syncDao().purges() }.count { it.id == status })
    }

    @Test
    fun aCellStaysOnItsPageAndProperty() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val rome = go { pages.create("Rome", parentId = trips) }
        val milan = go { pages.create("Milan", parentId = trips) }
        go { databases.setText(rome, status, "Booked") }
        val failure = runCatching {
            go { db.useWriterConnection { it.execSQL("UPDATE property_value SET page_id = '$milan'") } }
        }.exceptionOrNull()
        assertTrue(failure != null && "does not change" in failure.message.orEmpty(), failure.toString())
    }

    @Test
    fun anOptionMergeIsNoEditThatBringsATrashedDatabaseBack() = two(8) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.SELECT) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.addOption(status, "Red") }
        go { b.databases.addOption(status, "red") }
        syncthing.now = 3_000
        go { a.pages.trash(trips) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(true, go { d.pages.page(trips) }!!.trashed)
    }

    @Test
    fun aRevivedDatabaseBringsBackTheRowsTrashedWithIt() = two(9) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(trips) }
        syncthing.now = 3_000
        go { b.databases.renameProperty(status, "State") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(false to false, go { d.pages.page(trips)!!.trashed to d.pages.page(rome)!!.trashed })
    }

    @Test
    fun clearingACellNoOneFilledHereWritesNothingOverAValueFilledElsewhere() = two(10) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val city = go { a.databases.addProperty(trips, "City", PropertyType.TEXT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { b.databases.setText(rome, city, "Paris") }
        syncthing.now = 3_000
        go { a.databases.setText(rome, city, " ") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals("Paris", go { d.databases.cells(trips, rome) }.getValue(city).text)
            assertEquals(emptyList(), go { d.pages.notices(rome) })
        }
    }

    @Test
    fun picksReadFromAnotherTypesValueCanBeTakenOutAndAMultiSelectReadsAsASelect() {
        val trips = go { databases.create("Trips") }
        val tags = go { databases.addProperty(trips, "Tags", PropertyType.TEXT) }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.setText(rome, tags, "Red, Blue") }
        go { databases.setType(tags, PropertyType.MULTI_SELECT) }
        val (red, blue) = go { databases.options(tags) }.map { it.id }
        assertEquals(setOf(red, blue), go { databases.cells(trips, rome) }.getValue(tags).options.toSet())

        go { databases.unpick(rome, tags, red) }
        assertEquals(listOf(blue), go { databases.cells(trips, rome) }.getValue(tags).options)

        val milan = go { pages.create("Milan", parentId = trips) }
        go { databases.pick(milan, tags, red) }
        go { databases.setType(tags, PropertyType.SELECT) }
        assertEquals(listOf(red), go { databases.cells(trips, milan) }.getValue(tags).options)
    }

    @Test
    fun aFilterOnAnOptionMergedSinceStillMatches() = two(11) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val status = go { a.databases.addProperty(trips, "Status", PropertyType.SELECT) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        val first = go { a.databases.addOption(status, "Done") }
        val second = go { b.databases.addOption(status, "done") }
        go { b.databases.setOption(rome, status, second) }
        val view = go { b.databases.views(trips) }.single().id
        go { b.databases.setFilter(view, status, FilterOp.EQUALS, second) }
        settle(listOf(a, b))

        assertEquals(first to listOf(rome), go { a.databases.options(status).single().id to a.databases.rows(view).map { it.pageId } })
    }

    @Test
    fun historyGivesBackAMultiSelectsPicks() {
        val trips = go { databases.create("Trips") }
        val tags = go { databases.addProperty(trips, "Tags", PropertyType.MULTI_SELECT) }
        val red = go { databases.addOption(tags, "Red") }
        val blue = go { databases.addOption(tags, "Blue") }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.pick(rome, tags, red) }
        val before = go { pages.revisions(rome) }.size
        // The snapshot before the next change, ten minutes on, holds Red.
        go { db.useWriterConnection { it.execSQL("UPDATE page_revision SET at = at - 600000") } }
        go { databases.unpick(rome, tags, red) }
        go { databases.pick(rome, tags, blue) }
        val kept = go { pages.revisions(rome) }.first()
        assertTrue(go { pages.revisions(rome) }.size > before)

        go { pages.restoreRevision(kept.id) }

        assertEquals(listOf(red), go { databases.cells(trips, rome) }.getValue(tags).options)
    }

    @Test
    fun aDeletedOptionsNameIsFreeForATypeChange() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.SELECT) }
        go { databases.deleteOption(databases.addOption(status, "Red")) }
        go { databases.setType(status, PropertyType.TEXT) }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.setText(rome, status, "Red") }
        go { databases.setType(status, PropertyType.SELECT) }

        assertEquals("Red", go { databases.cells(trips, rome) }.getValue(status).text)
    }

    @Test
    fun aDatabaseKeepsOneViewAndATrashedOnesSchemaIsNotEdited() {
        val trips = go { databases.create("Trips") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.TEXT) }
        val table = go { databases.views(trips) }.single().id
        assertFailsWith<IllegalArgumentException> { go { databases.deleteView(table) } }
        assertFailsWith<IllegalArgumentException> { go { databases.setShown(table, listOf(status, status)) } }
        assertFailsWith<IllegalArgumentException> { go { databases.addView(trips, " ", ViewType.TABLE) } }
        go { databases.addView(trips, "Board", ViewType.BOARD) }
        go { databases.deleteView(table) }
        go { pages.trash(trips) }
        assertFailsWith<IllegalArgumentException> { go { databases.renameProperty(status, "State") } }
    }
}
