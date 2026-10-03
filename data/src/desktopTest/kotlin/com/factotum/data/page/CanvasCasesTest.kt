package com.factotum.data.page

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** ADR 12's canvas case (`decisions/cases/12-page-merge.jsonl`) and the owner's answers on the canvas, 2026-10-03 (slice 12c). */
class CanvasCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var pages: PageRepository
    private lateinit var canvases: CanvasRepository
    private var wall = 1_000L

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "canvas.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { wall } })
        val newId = { "id-${n++}" }
        pages = PageRepository(db, writes, newId, { wall })
        canvases = CanvasRepository(db, writes, newId, pages)
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

    private fun World.Device.card(board: String, id: String) = go { canvases.nodes(board) }.single { it.id == id }

    @Test
    fun twoCardsMovedApartAndACardMovedAndRetypedApartAllStand() = two(1) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val one = go { a.canvases.addText(board, 0.0, 0.0, "one") }
        val two = go { a.canvases.addText(board, 100.0, 0.0, "two") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.moveNode(one, 10.0, 10.0) }
        go { b.canvases.moveNode(two, 110.0, 50.5) }
        go { b.canvases.setText(one, "one, retyped") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(Triple(10.0, 10.0, "one, retyped"), d.card(board, one).let { Triple(it.x, it.y, it.text) })
            assertEquals(110.0 to 50.5, d.card(board, two).let { it.x to it.y })
        }
    }

    @Test
    fun aCardMovedOnTwoDevicesTakesTheLaterPosition() = two(2) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val one = go { a.canvases.addText(board, 0.0, 0.0, "one") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.moveNode(one, 10.0, 10.0) }
        syncthing.now = 3_000
        go { b.canvases.moveNode(one, 30.0, 30.0) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(30.0 to 30.0, d.card(board, one).let { it.x to it.y })
            assertEquals(emptyList(), go { d.pages.notices(board) })
        }
    }

    @Test
    fun movingACardCarriesItsSubtreeButNotItsFrames() {
        val board = go { canvases.create("Plan") }
        val root = go { canvases.addText(board, 0.0, 0.0, "root") }
        val child = go { canvases.addText(board, 50.0, 0.0, "child", parent = root) }
        val grandchild = go { canvases.addText(board, 100.0, 0.0, "grandchild", parent = child) }
        val frame = go { canvases.addFrame(board, -10.0, -10.0, 200.0, 50.0, "Group") }
        go { canvases.setParent(frame, root) }

        go { canvases.moveNode(root, 5.0, 7.0) }

        val at = go { canvases.nodes(board) }.associate { it.id to (it.x to it.y) }
        assertEquals(mapOf(root to (5.0 to 7.0), child to (55.0 to 7.0), grandchild to (105.0 to 7.0), frame to (-10.0 to -10.0)), at)
    }

    @Test
    fun deletingACardTakesItsLinesAndFramesLiftsItsChildrenAndALaterEditBringsThemAllBack() = two(3) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val top = go { a.canvases.addText(board, 0.0, 0.0, "top") }
        val card = go { a.canvases.addText(board, 50.0, 0.0, "card", parent = top) }
        val child = go { a.canvases.addText(board, 100.0, 0.0, "child", parent = card) }
        val other = go { a.canvases.addText(board, 0.0, 100.0, "other") }
        val line = go { a.canvases.addEdge(card, other, EdgeDirection.ONE_WAY) }
        val frame = go { a.canvases.addFrame(board, 40.0, -10.0, 100.0, 40.0) }
        go { a.canvases.setParent(frame, card) }
        settle(listOf(a, b))

        syncthing.now = 2_000
        go { a.canvases.deleteNode(card) }
        assertEquals(setOf(top, child, other), go { a.canvases.nodes(board) }.map { it.id }.toSet())
        assertEquals(top, a.card(board, child).parentId)
        assertEquals(emptyList(), go { a.canvases.edges(board) })

        syncthing.now = 3_000
        go { b.canvases.setHue(card, 120) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(setOf(top, card, child, other, frame), go { d.canvases.nodes(board) }.map { it.id }.toSet())
            assertEquals(listOf(line), go { d.canvases.edges(board) }.map { it.id })
            assertEquals(card to card, d.card(board, child).parentId to d.card(board, frame).parentId)
        }
    }

    @Test
    fun aLineOrAChildAddedToACardDeletedElsewhereBringsItBack() = two(4) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val one = go { a.canvases.addText(board, 0.0, 0.0, "one") }
        val two = go { a.canvases.addText(board, 100.0, 0.0, "two") }
        val three = go { a.canvases.addText(board, 200.0, 0.0, "three") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.deleteNode(one) }
        go { a.canvases.deleteNode(three) }
        syncthing.now = 3_000
        val line = go { b.canvases.addEdge(two, one) }
        val child = go { b.canvases.addText(board, 250.0, 50.0, "under three", parent = three) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(setOf(one, two, three, child), go { d.canvases.nodes(board) }.map { it.id }.toSet())
            assertEquals(listOf(line), go { d.canvases.edges(board) }.map { it.id })
            assertEquals(three, d.card(board, child).parentId)
        }
    }

    @Test
    fun aPageCardShowsAPageInTheTrashAndOneDeletedForeverAndIsNeverDeletedWithIt() {
        val board = go { canvases.create("Plan") }
        val rome = go { pages.create("Rome") }
        val card = go { canvases.addPageCard(board, rome, 0.0, 0.0) }
        assertEquals(PageState.LIVE, go { canvases.nodes(board) }.single().pageState)
        go { pages.trash(rome) }
        assertEquals(PageState.TRASHED, go { canvases.nodes(board) }.single().pageState)
        go { pages.purge(rome) }
        assertEquals(card to PageState.DELETED, go { canvases.nodes(board) }.single().let { it.id to it.pageState })
        assertFailsWith<IllegalArgumentException> { go { canvases.setText(card, "x") } }
    }

    @Test
    fun aCardsTextAndALinesLabelChangedApartKeepTheEarlierInHistoryWithANotice() = two(5) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val one = go { a.canvases.addText(board, 0.0, 0.0, "Idea") }
        val two = go { a.canvases.addText(board, 100.0, 0.0, "Other") }
        val line = go { a.canvases.addEdge(one, two, label = "leads to") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.setText(one, "Idea A") }
        go { a.canvases.setLabel(line, "causes") }
        syncthing.now = 3_000
        go { b.canvases.setText(one, "Idea B") }
        go { b.canvases.setLabel(line, "follows") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals("Idea B" to "follows", d.card(board, one).text to go { d.canvases.edges(board) }.single().label)
            assertEquals(setOf("Idea A", "causes"), go { d.pages.notices(board) }.map { it.lostText }.toSet())
        }
        val merge = go { a.pages.revisions(board) }.first { it.reason == "MERGE" && it.noticeId!!.contains(one) }
        go { a.pages.restoreRevision(merge.id) }
        assertEquals("Idea A", a.card(board, one).text)
    }

    @Test
    fun aCanvasEditAfterTheTrashBringsTheCanvasBack() = two(6) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val one = go { a.canvases.addText(board, 0.0, 0.0, "one") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(board) }
        syncthing.now = 3_000
        go { b.canvases.moveNode(one, 9.0, 9.0) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(false, go { d.pages.page(board) }!!.trashed)
    }

    @Test
    fun historyGivesBackACanvasAsItWas() {
        val board = go { canvases.create("Plan") }
        val one = go { canvases.addText(board, 0.0, 0.0, "one") }
        wall += 10 * 60 * 1000
        go { canvases.moveNode(one, 50.0, 50.0) }
        val before = go { pages.revisions(board) }.first()
        go { canvases.addText(board, 5.0, 5.0, "later") }

        go { pages.restoreRevision(before.id) }

        assertEquals(listOf(one to (0.0 to 0.0)), go { canvases.nodes(board) }.map { it.id to (it.x to it.y) })
    }

    @Test
    fun theTreeAndLinesRefuseWhatTendrilRefuses() {
        val board = go { canvases.create("Plan") }
        val other = go { canvases.create("Other") }
        val a = go { canvases.addText(board, 0.0, 0.0, "a") }
        val a1 = go { canvases.addText(board, 0.0, 0.0, "a1", parent = a) }
        val frame = go { canvases.addFrame(board, 0.0, 0.0, 10.0, 10.0) }
        val elsewhere = go { canvases.addText(other, 0.0, 0.0, "x") }
        assertFailsWith<IllegalArgumentException> { go { canvases.setParent(a, a1) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.setParent(a, a) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.setParent(a1, frame) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.setParent(a1, elsewhere) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.addEdge(a, a) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.addEdge(a, elsewhere) } }
        assertFailsWith<IllegalArgumentException> { go { canvases.moveNode(a, Double.NaN, 0.0) } }
        go { pages.trash(board) }
        assertFailsWith<IllegalArgumentException> { go { canvases.moveNode(a, 1.0, 1.0) } }
    }

    @Test
    fun framesAreDrawnFirstAndBringToFrontPutsACardOnTop() {
        val board = go { canvases.create("Plan") }
        val one = go { canvases.addText(board, 0.0, 0.0, "one") }
        val two = go { canvases.addText(board, 0.0, 0.0, "two") }
        val frame = go { canvases.addFrame(board, 0.0, 0.0, 10.0, 10.0) }
        assertEquals(listOf(frame, one, two), go { canvases.nodes(board) }.map { it.id })
        go { canvases.bringToFront(one) }
        assertEquals(listOf(frame, two, one), go { canvases.nodes(board) }.map { it.id })
    }

    @Test
    fun aLineStaysBetweenTheCardsItWasDrawnBetween() {
        val board = go { canvases.create("Plan") }
        val one = go { canvases.addText(board, 0.0, 0.0, "one") }
        val two = go { canvases.addText(board, 0.0, 0.0, "two") }
        val three = go { canvases.addText(board, 0.0, 0.0, "three") }
        go { canvases.addEdge(one, two) }
        val failure = runCatching { go { db.useWriterConnection { it.execSQL("UPDATE canvas_edge SET to_node_id = '$three'") } } }.exceptionOrNull()
        assertTrue(failure != null && "does not change" in failure.message.orEmpty(), failure.toString())
    }

    @Test
    fun aCardAndItsParentDeletedOnTwoDevicesBothStayDeleted() = two(7) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val p = go { a.canvases.addText(board, 0.0, 0.0, "p") }
        val c = go { a.canvases.addText(board, 0.0, 0.0, "c", parent = p) }
        val k = go { a.canvases.addText(board, 0.0, 0.0, "k", parent = c) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.deleteNode(p) }
        syncthing.now = 3_000
        go { b.canvases.deleteNode(c) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf(k), go { d.canvases.nodes(board) }.map { it.id })
    }

    @Test
    fun aCardCarriedOrTidiedAfterItWasDeletedElsewhereStaysDeleted() = two(8) { a, b ->
        syncthing.now = 1_000
        val board = go { a.canvases.create("Plan") }
        val p = go { a.canvases.addText(board, 0.0, 0.0, "p") }
        val k = go { a.canvases.addText(board, 10.0, 0.0, "k", parent = p) }
        val loose = go { a.canvases.addText(board, 50.0, 50.0, "loose") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.canvases.deleteNode(k) }
        go { a.canvases.deleteNode(loose) }
        syncthing.now = 3_000
        go { b.canvases.moveNode(p, 100.0, 100.0) }
        go { b.canvases.moveNodes(board, mapOf(loose to (0.0 to 0.0))) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf(p), go { d.canvases.nodes(board) }.map { it.id })
    }

    @Test
    fun aFrameFollowingADeletedCardTakesItsLinesWithIt() {
        val board = go { canvases.create("Plan") }
        val card = go { canvases.addText(board, 0.0, 0.0, "card") }
        val other = go { canvases.addText(board, 0.0, 0.0, "other") }
        val frame = go { canvases.addFrame(board, 0.0, 0.0, 10.0, 10.0) }
        go { canvases.setParent(frame, card) }
        val line = go { canvases.addEdge(frame, other) }
        go { canvases.deleteNode(card) }
        assertFailsWith<IllegalArgumentException> { go { canvases.setLabel(line, "x") } }
    }

    @Test
    fun aPageCardWhosePageIsNotHereYetIsNotADeletedPage() {
        val board = go { canvases.create("Plan") }
        val rome = go { pages.create("Rome") }
        go { canvases.addPageCard(board, rome, 0.0, 0.0) }
        go { db.useWriterConnection { it.execSQL("DELETE FROM page WHERE id = '$rome'") } }
        assertEquals(PageState.ABSENT, go { canvases.nodes(board) }.single().pageState)
    }
}
