package com.factotum.data.page

import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import androidx.room.execSQL
import com.factotum.core.label.LabelScope
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.label.LabelRepository
import com.factotum.data.openFactotumDatabase
import com.factotum.data.search.SearchRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDateTime
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

/** ADR 12's cases (`decisions/cases/12-page-merge.jsonl`) for slice 12a, the owner's 2026-10-03 answers, and the page cases of ADR 08 and ADR 10. */
class PageCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var pages: PageRepository
    private lateinit var labels: LabelRepository
    private var wall = 1_000L

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "pages.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { wall } })
        val newId = { "id-${n++}" }
        pages = PageRepository(db, writes, newId, { wall })
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

    private fun World.Device.texts(page: String) = runBlocking { pages.outline(page) }.map { it.content }

    @Test
    fun theLaterTextWinsAndTheEarlierIsKeptInHistoryWithOneNoticeDismissedEverywhere() = two(1) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val hotel = runBlocking { a.pages.addBlock(page, content = "Hotel") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.setText(hotel, "Hotel Roma") }
        syncthing.now = 3_000
        runBlocking { b.pages.setText(hotel, "Hotel Milano") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf("Hotel Milano"), d.texts(page))
            val notices = runBlocking { d.pages.notices(page) }
            assertEquals(listOf(Triple(hotel, "Hotel Roma", page)), notices.map { Triple(it.rowId, it.lostText, it.pageId) })
            // tendril-loser-recoverable: the replaced text is in this device's History, linked to the notice.
            val merge = runBlocking { d.pages.revisions(page) }.single { it.reason == "MERGE" }
            assertEquals(notices.single().id, merge.noticeId)
            runBlocking { d.pages.restoreRevision(merge.id) }
            assertEquals(listOf("Hotel Roma"), d.texts(page))
        }
        settle(listOf(a, b))
        val notice = runBlocking { a.pages.notices(page) }.single().id
        runBlocking { b.pages.dismiss(notice) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(emptyList(), runBlocking { d.pages.notices(page) })
    }

    @Test
    fun aNoticeWrittenLateByTheOtherDeviceDoesNotUndoADismissal() = two(2) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.rename(page, "Trip to Rome") }
        syncthing.now = 3_000
        runBlocking { b.pages.rename(page, "Trip to Milan") }
        // A sees B's title first, keeps its own in History, and dismisses the notice before B has seen anything.
        a.export(); b.export()
        syncthing.session("A", "B")
        a.import()
        syncthing.now = 4_000
        runBlocking { a.pages.dismiss(a.pages.notices(page).single().id) }
        // Only now does B see A's title, and write the notice itself.
        syncthing.now = 5_000
        b.import()
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals("Trip to Milan", runBlocking { d.pages.page(page) }!!.title)
            assertEquals(emptyList(), runBlocking { d.pages.notices(page) })
        }
    }

    @Test
    fun editsToDifferentBlocksBothStandWithNoNotice() = two(3) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val flights = runBlocking { a.pages.addBlock(page, content = "Flights") }
        val budget = runBlocking { a.pages.addBlock(page, after = flights, content = "Budget") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.setText(flights, "Flights booked") }
        runBlocking { b.pages.setText(budget, "Budget 900") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf("Flights booked", "Budget 900"), d.texts(page))
            // tendril-block-uid-stable: the blocks are the ones that were made.
            assertEquals(listOf(flights, budget), runBlocking { d.pages.outline(page) }.map { it.id })
            assertEquals(emptyList(), runBlocking { d.pages.notices(page) })
        }
    }

    @Test
    fun concurrentInsertsAreBothOnThePageInOneOrderEverywhere() = two(4) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val flights = runBlocking { a.pages.addBlock(page, content = "Flights") }
        runBlocking { a.pages.addBlock(page, after = flights, content = "Budget") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.addBlock(page, after = flights, content = "Seats") }
        val last = runBlocking { b.pages.outline(page) }.last().id
        runBlocking { b.pages.addBlock(page, after = last, content = "Packing") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("Flights", "Seats", "Budget", "Packing"), d.texts(page))
    }

    @Test
    fun twoDevicesInsertingAtOneSpotKeepOneOrderByBlockId() = two(5) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val flights = runBlocking { a.pages.addBlock(page, content = "Flights") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.addBlock(page, after = flights, content = "from A") }
        runBlocking { b.pages.addBlock(page, after = flights, content = "from B") }
        settle(listOf(a, b))

        assertEquals(a.texts(page), b.texts(page))
        assertEquals(setOf("Flights", "from A", "from B"), a.texts(page).toSet())
    }

    @Test
    fun aLaterEditBringsATrashedPageBackAndAnEarlierOneDoesNot() = two(6) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val other = runBlocking { a.pages.create("Notes") }
        val hotel = runBlocking { a.pages.addBlock(page, content = "Hotel") }
        val note = runBlocking { a.pages.addBlock(other, content = "Note") }
        settle(listOf(a, b))
        // tendril-later-edit-beats-trash: B trashes at 5, A edits at 7.
        syncthing.now = 5_000
        runBlocking { b.pages.trash(page) }
        syncthing.now = 7_000
        runBlocking { a.pages.setText(hotel, "Hotel Roma") }
        // The other way round: A edits at 8, B trashes at 9.
        syncthing.now = 8_000
        runBlocking { a.pages.setText(note, "Note 2") }
        syncthing.now = 9_000
        runBlocking { b.pages.trash(other) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(false, runBlocking { d.pages.page(page) }!!.trashed)
            assertEquals(listOf("Hotel Roma"), d.texts(page))
            assertEquals(true, runBlocking { d.pages.page(other) }!!.trashed)
        }
    }

    @Test
    fun aLaterEditBringsADeletedBlockBack() = two(7) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val hotel = runBlocking { a.pages.addBlock(page, content = "Hotel") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { b.pages.deleteBlock(hotel) }
        syncthing.now = 3_000
        runBlocking { a.pages.setText(hotel, "Hotel Roma") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("Hotel Roma"), d.texts(page))
    }

    @Test
    fun aLaterEditToASubPageBringsBackItsTrashedParents() = two(8) { a, b ->
        syncthing.now = 1_000
        val trip = runBlocking { a.pages.create("Trip") }
        val rome = runBlocking { a.pages.create("Rome", parentId = trip) }
        val day = runBlocking { a.pages.create("Day 1", parentId = rome) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { b.pages.trash(trip) }
        syncthing.now = 3_000
        runBlocking { a.pages.rename(day, "Day one") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            for (p in listOf(trip, rome, day)) assertEquals(false, runBlocking { d.pages.page(p) }!!.trashed, p)
        }
    }

    @Test
    fun trashTakesSubPagesAndRestoreBringsBackOnlyThoseTrashedTogether() {
        val trip = runBlocking { pages.create("Trip") }
        val rome = runBlocking { pages.create("Rome", parentId = trip) }
        val milan = runBlocking { pages.create("Milan", parentId = trip) }
        wall = 2_000
        runBlocking { pages.trash(milan) }
        wall = 3_000
        runBlocking { pages.trash(trip) }
        assertEquals(listOf(true, true, true), listOf(trip, rome, milan).map { runBlocking { pages.page(it) }!!.trashed })
        assertEquals(listOf(trip), runBlocking { pages.trashed() }.map { it.id })

        runBlocking { pages.restore(trip) }

        assertEquals(listOf(false, false, true), listOf(trip, rome, milan).map { runBlocking { pages.page(it) }!!.trashed })
        assertEquals(listOf("Rome"), runBlocking { pages.children(trip) }.map { it.title })
    }

    @Test
    fun deleteForeverOnlyFromTheTrashAndItTakesSubPagesBlocksAndLabels() {
        val trip = runBlocking { pages.create("Trip") }
        val rome = runBlocking { pages.create("Rome", parentId = trip) }
        runBlocking { pages.addBlock(rome, content = "Colosseum") }
        val work = runBlocking { labels.create("work") }
        runBlocking { labels.labelPage(rome, work) }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.purge(trip) } }

        runBlocking { pages.trash(trip) }
        runBlocking { pages.purge(trip) }

        assertNull(runBlocking { pages.page(rome) })
        // tendril-page-delete-no-orphans
        val left = runBlocking {
            db.useReaderConnection { c ->
                c.usePrepared("SELECT (SELECT count(*) FROM block) + (SELECT count(*) FROM page_label) + (SELECT count(*) FROM page)") { it.step(); it.getLong(0) }
            }
        }
        assertEquals(0, left)
    }

    @Test
    fun aPageCannotGoUnderItself() {
        val trip = runBlocking { pages.create("Trip") }
        val rome = runBlocking { pages.create("Rome", parentId = trip) }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.move(trip, rome) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.move(trip, trip) } }
        runBlocking { pages.move(rome, null) }
        assertEquals(listOf("Rome", "Trip"), runBlocking { pages.children() }.map { it.title })
    }

    @Test
    fun blocksNestAndKeepTheirOrderAfterTheKeysRunOutOfRoom() {
        val page = runBlocking { pages.create("Trip") }
        val first = runBlocking { pages.addBlock(page, content = "first") }
        val last = runBlocking { pages.addBlock(page, after = first, content = "last") }
        // Each new block goes straight after the first, halving the gap until a Double cannot hold one.
        val added = (1..80).map { runBlocking { pages.addBlock(page, after = first, content = "n$it") } }
        val child = runBlocking { pages.addBlock(page, parent = last, content = "child", type = BlockType.TODO) }

        val outline = runBlocking { pages.outline(page) }
        assertEquals(listOf("first") + (80 downTo 1).map { "n$it" } + listOf("last", "child"), outline.map { it.content })
        assertEquals(1, outline.single { it.id == child }.depth)
        assertEquals(80, added.distinct().size)
        runBlocking { pages.moveBlock(last) }
        assertEquals(listOf("last", "child", "first"), runBlocking { pages.outline(page) }.map { it.content }.take(3))
    }

    @Test
    fun historyKeepsAnEditAtMostEveryTenMinutesFiftyKeptAndRestores() {
        val page = runBlocking { pages.create("Trip") }
        val hotel = runBlocking { pages.addBlock(page, content = "Hotel") }
        runBlocking { pages.setText(hotel, "Hotel Roma") }
        runBlocking { pages.setText(hotel, "Hotel Roma 2") }
        assertEquals(1, runBlocking { pages.revisions(page) }.size)

        wall += 10 * 60 * 1000
        runBlocking { pages.setText(hotel, "Hotel Milano") }
        val revisions = runBlocking { pages.revisions(page) }
        assertEquals(2, revisions.size)
        runBlocking { pages.restoreRevision(revisions.first().id) }
        assertEquals(listOf("Hotel Roma 2"), runBlocking { pages.outline(page) }.map { it.content })
        assertEquals("RESTORE", runBlocking { pages.revisions(page) }.first().reason)

        repeat(60) { wall += 10 * 60 * 1000; runBlocking { pages.setText(hotel, "v$it") } }
        assertEquals(50, runBlocking { pages.revisions(page) }.size)
    }

    @Test
    fun restoringAnOlderVersionDeletesBlocksItDidNotHaveAndBringsBackOnesItDid() {
        val page = runBlocking { pages.create("Trip") }
        val hotel = runBlocking { pages.addBlock(page, content = "Hotel") }
        wall += 10 * 60 * 1000
        runBlocking { pages.deleteBlock(hotel) }
        val before = runBlocking { pages.revisions(page) }.first()
        runBlocking { pages.addBlock(page, content = "Packing") }

        runBlocking { pages.restoreRevision(before.id) }

        assertEquals(listOf(hotel), runBlocking { pages.outline(page) }.map { it.id })
    }

    @Test
    fun aPageCarriesManyLabelsAndAMergedOrDeletedLabelReadsRight() {
        val page = runBlocking { pages.create("Trip") }
        val work = runBlocking { labels.create("work") }
        val urgent = runBlocking { labels.create("urgent") }
        val trackers = runBlocking { labels.create("moods", LabelScope.TRACKER) }
        // tendril-page-many-labels
        runBlocking { labels.labelPage(page, work); labels.labelPage(page, urgent); labels.labelPage(page, work) }
        assertEquals(listOf("work", "urgent"), runBlocking { labels.labelsOfPage(page) }.map { it.name })
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.labelPage(page, trackers) } }
        // tendril-database-doorway: a label's pages.
        assertEquals(listOf(page), runBlocking { labels.pagesLabelled(work) })

        runBlocking { labels.unlabelPage(page, urgent) }
        assertEquals(listOf("work"), runBlocking { labels.labelsOfPage(page) }.map { it.name })
        runBlocking { labels.labelPage(page, urgent) }
        runBlocking { labels.delete(urgent) }
        assertEquals(listOf("work"), runBlocking { labels.labelsOfPage(page) }.map { it.name })
        runBlocking { pages.trash(page) }
        assertEquals(emptyList(), runBlocking { labels.pagesLabelled(work) })
    }

    @Test
    fun aLabelPutOnAPageOnTwoDevicesIsOneRowAndMergedLabelsShowOnce() = two(9) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        settle(listOf(a, b))
        val mine = runBlocking { a.labels.create("Travel") }
        syncthing.now = 2_000
        val theirs = runBlocking { b.labels.create("travel") }
        runBlocking { a.labels.labelPage(page, mine) }
        runBlocking { b.labels.labelPage(page, theirs) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("Travel"), runBlocking { d.labels.labelsOfPage(page) }.map { it.name })
    }

    @Test
    fun aPageIsFoundByATitleWordAndABodyWordAccentsFoldedAndNothingUnderTheTrash() {
        val search = SearchRepository(db)
        val now = LocalDateTime(2026, 10, 5, 12, 0)
        val trip = runBlocking { pages.create("Viaggio a Roma") }
        val rome = runBlocking { pages.create("Giorno uno", parentId = trip) }
        runBlocking { pages.addBlock(rome, content = "Perché il Colosseo") }

        // tendril-title-and-body, chronicle-accents-folded
        assertEquals(listOf("PAGE" to trip), runBlocking { search.search("viag", now) }.map { it.kind to it.id })
        val body = runBlocking { search.search("perche", now) }.single()
        assertEquals("BLOCK" to "Giorno uno", body.kind to body.owner)

        runBlocking { pages.trash(trip) }
        assertEquals(emptyList(), runBlocking { search.search("perche", now) } + runBlocking { search.search("viag", now) })
        runBlocking { pages.restore(trip) }
        assertEquals(1, runBlocking { search.search("perche", now) }.size)
    }

    @Test
    fun aBlockStaysOnItsPage() {
        val page = runBlocking { pages.create("Trip") }
        val other = runBlocking { pages.create("Notes") }
        val hotel = runBlocking { pages.addBlock(page, content = "Hotel") }
        val failure = runCatching {
            runBlocking { db.useWriterConnection { it.execSQL("UPDATE block SET page_id = '$other' WHERE id = '$hotel'") } }
        }.exceptionOrNull()
        assertTrue(failure != null && "does not change" in failure.message.orEmpty(), failure.toString())
    }

    @Test
    fun aRenameKeepsTheIconAndAnIconOrFormatChangedApartRaisesNoNotice() = two(10) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip", icon = "plane") }
        val hotel = runBlocking { a.pages.addBlock(page, content = "Hotel") }
        runBlocking { a.pages.rename(page, "Trip to Rome") }
        assertEquals("plane", runBlocking { a.pages.page(page) }!!.icon)
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.setIcon(page, "train") }
        runBlocking { a.pages.setText(hotel, "Hotel", spans = "[bold]") }
        syncthing.now = 3_000
        runBlocking { b.pages.setIcon(page, "car") }
        runBlocking { b.pages.setText(hotel, "Hotel", spans = "[italic]") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals("car", runBlocking { d.pages.page(page) }!!.icon)
            assertEquals(emptyList(), runBlocking { d.pages.notices(page) })
        }
    }

    @Test
    fun deletingALabelLeavesATrashedPageThatCarriedItInTheTrash() = two(11) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val work = runBlocking { a.labels.create("work") }
        runBlocking { a.labels.labelPage(page, work) }
        syncthing.now = 2_000
        runBlocking { a.pages.trash(page) }
        syncthing.now = 3_000
        runBlocking { a.labels.delete(work) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(true, runBlocking { d.pages.page(page) }!!.trashed)
    }

    @Test
    fun placingBlocksNeverWritesOverAMoveOrADeletionMadeElsewhere() = two(12) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val first = runBlocking { a.pages.addBlock(page, content = "first") }
        val gone = runBlocking { a.pages.addBlock(page, after = first, content = "gone") }
        val moved = runBlocking { a.pages.addBlock(page, after = gone, content = "moved") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { b.pages.deleteBlock(gone) }
        runBlocking { b.pages.moveBlock(moved, parent = first) }
        syncthing.now = 3_000
        // Sixty blocks at one spot: a Double key ran out of room here and re-keyed every sibling.
        repeat(60) { runBlocking { a.pages.addBlock(page, after = first, content = "n$it") } }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            val outline = runBlocking { d.pages.outline(page) }
            assertTrue(outline.none { it.id == gone })
            assertEquals(first, outline.single { it.id == moved }.parentId)
        }
    }

    @Test
    fun aPurgeHoldsEvenWhenTheTrashArrivedFirstAndBroughtThePageBack() = two(13) { a, b ->
        syncthing.now = 1_000
        val page = runBlocking { a.pages.create("Trip") }
        val hotel = runBlocking { a.pages.addBlock(page, content = "Hotel") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.trash(page) }
        a.export()
        syncthing.session("A", "B")
        syncthing.now = 3_000
        runBlocking { a.pages.purge(page) }
        syncthing.now = 4_000
        runBlocking { b.pages.setText(hotel, "Hotel Roma") }
        // B reads the trash alone: its later edit brings the page back there.
        b.import()
        assertEquals(false, runBlocking { b.pages.page(page) }!!.trashed)
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertNull(runBlocking { d.pages.page(page) })
    }

    @Test
    fun aLivePageUnderATrashedOneIsShownAtTheTopAndADeleteForeverLeavesIt() {
        val trip = runBlocking { pages.create("Trip") }
        val rome = runBlocking { pages.create("Rome", parentId = trip) }
        runBlocking { pages.trash(trip) }
        // What a revive leaves: the sub-page live again, its parent still in the trash.
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE page SET deleted_at = NULL WHERE id = '$rome'") } }
        assertEquals(listOf("Rome"), runBlocking { pages.children() }.map { it.title })
        assertEquals(listOf(trip), runBlocking { pages.trashed() }.map { it.id })

        runBlocking { pages.purge(trip) }

        assertEquals(null to false, runBlocking { pages.page(rome) }!!.let { it.parentId to it.trashed })
    }

    @Test
    fun twoPagesMovedUnderEachOtherApartAreBothShownAtTheTop() = two(14) { a, b ->
        syncthing.now = 1_000
        val p = runBlocking { a.pages.create("P") }
        val q = runBlocking { a.pages.create("Q") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        runBlocking { a.pages.move(p, q) }
        runBlocking { b.pages.move(q, p) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf("P", "Q"), runBlocking { d.pages.children() }.map { it.title })
            runBlocking { d.pages.trash(p) }
            assertEquals(1, runBlocking { d.pages.trashed() }.size)
        }
    }

    @Test
    fun aBlockGoesOnlyUnderALiveBlockOfItsPageAndNeverUnderItself() {
        val page = runBlocking { pages.create("Trip") }
        val other = runBlocking { pages.create("Notes") }
        val a = runBlocking { pages.addBlock(page, content = "a") }
        val a1 = runBlocking { pages.addBlock(page, parent = a, content = "a1") }
        val elsewhere = runBlocking { pages.addBlock(other, content = "x") }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.addBlock(page, parent = elsewhere) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.moveBlock(a, parent = a1) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.moveBlock(a, parent = a) } }
        runBlocking { pages.deleteBlock(a1) }
        assertFailsWith<IllegalArgumentException> { runBlocking { pages.addBlock(page, parent = a1) } }
    }
}
