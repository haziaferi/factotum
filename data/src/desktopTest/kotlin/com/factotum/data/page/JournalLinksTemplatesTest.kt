package com.factotum.data.page

import com.factotum.data.FactotumDatabase
import com.factotum.data.FixedSettings
import com.factotum.data.LocalWrites
import com.factotum.data.label.LabelRepository
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.DatePeriod
import kotlinx.datetime.plus
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Slice 12d: the journal, Road Map links, database relations and templates, with the owner's answers of 2026-10-03. */
class JournalLinksTemplatesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var pages: PageRepository
    private lateinit var databases: DatabaseRepository
    private lateinit var canvases: CanvasRepository
    private lateinit var templates: TemplateRepository
    private lateinit var journal: JournalRepository
    private lateinit var relations: RelationRepository
    private lateinit var labels: LabelRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "d.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        pages = PageRepository(db, writes, newId, { 1_000 })
        databases = DatabaseRepository(db, writes, newId, pages)
        canvases = CanvasRepository(db, writes, newId, pages)
        templates = TemplateRepository(db, writes, newId)
        journal = JournalRepository(db, writes, FixedSettings(LocalTime(4, 0)))
        relations = RelationRepository(db, writes)
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

    private val day = LocalDate(2026, 10, 5)

    // The journal

    @Test
    fun twoDevicesOpeningOneDayMakeOneDayUnderOneJournal() = two(1) { a, b ->
        syncthing.now = 1_000
        val onA = go { a.journal.day(day) }
        go { a.pages.addBlock(onA, content = "from A") }
        syncthing.now = 2_000
        val onB = go { b.journal.day(day) }
        go { b.pages.addBlock(onB, content = "from B") }
        settle(listOf(a, b))

        assertEquals(onA, onB)
        for (d in listOf(a, b)) {
            assertEquals(listOf(onA), go { d.pages.children(JOURNAL_ROOT) }.map { it.id })
            assertEquals(listOf("Journal"), go { d.pages.children() }.map { it.title })
            assertEquals(setOf("from A", "from B"), go { d.pages.outline(onA) }.map { it.content }.toSet())
            assertEquals("", go { d.pages.page(onA) }!!.title)
            assertEquals(emptyList(), go { d.pages.notices(onA) })
        }
        assertEquals(day, journalDate(onA))
        assertNull(journalDate(JOURNAL_ROOT))
    }

    @Test
    fun todayIsThePersonalDayAndARenamedDayStaysTheDay() {
        val early = go { journal.today(LocalDateTime(2026, 10, 6, 3, 0)) }
        assertEquals(day, journalDate(early))
        go { pages.rename(early, "Moving day") }
        assertEquals(early, go { journal.day(day) })
        assertEquals("Moving day", go { pages.page(early) }!!.title)
    }

    @Test
    fun openingADayTrashedElsewhereLeavesItInTheTrashAndWritingInItBringsItBack() = two(2) { a, b ->
        syncthing.now = 1_000
        val page = go { a.journal.day(day) }
        go { a.pages.addBlock(page, content = "note") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(page) }
        syncthing.now = 3_000
        go { b.journal.day(day) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(true, go { d.pages.page(page) }!!.trashed)

        // B has never had the day, and makes it after A trashed it: making it is no edit, so the trash stands.
        val third = go { a.journal.day(day.plus(DatePeriod(days = 2))) }
        syncthing.now = 3_500
        go { a.pages.trash(third) }
        syncthing.now = 3_600
        go { b.journal.day(day.plus(DatePeriod(days = 2))) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(true, go { d.pages.page(third) }!!.trashed)

        // Written in on B before B heard of the trash: the writing is newer, and brings the day back.
        val next = go { a.journal.day(day.plus(DatePeriod(days = 1))) }
        settle(listOf(a, b))
        syncthing.now = 4_000
        go { a.pages.trash(next) }
        syncthing.now = 5_000
        go { b.pages.addBlock(go { b.journal.day(day.plus(DatePeriod(days = 1))) }, content = "more") }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(false, go { d.pages.page(next) }!!.trashed)
    }

    @Test
    fun aDayDeletedForGoodAndOpenedAgainIsAPageEveryDeviceGets() = two(3) { a, b ->
        syncthing.now = 1_000
        val page = go { a.journal.day(day) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(page) }
        go { a.pages.purge(page) }
        settle(listOf(a, b))
        syncthing.now = 3_000
        go { b.journal.day(day) }
        go { b.pages.addBlock(page, content = "again") }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("again"), go { d.pages.outline(page) }.map { it.content })
    }

    // Road Map links

    @Test
    fun aRoadMapLinkIsOnePerPairCanBeTakenOffAndComesBackWhenMadeAgain() = two(4) { a, b ->
        syncthing.now = 1_000
        val rome = go { a.pages.create("Rome") }
        val milan = go { a.pages.create("Milan") }
        settle(listOf(a, b))
        go { a.relations.relate(rome, milan) }
        go { b.relations.relate(milan, rome) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(listOf(milan) to listOf(rome), go { d.relations.related(rome) to d.relations.related(milan) })
        assertEquals(1, go { a.db.linkDao().allRelations() }.size)

        syncthing.now = 2_000
        go { a.relations.unrelate(rome, milan) }
        settle(listOf(a, b))
        assertEquals(emptyList(), go { b.relations.related(rome) })
        syncthing.now = 3_000
        go { b.relations.relate(rome, milan) }
        settle(listOf(a, b))
        assertEquals(listOf(milan), go { a.relations.related(rome) })
        assertFailsWith<IllegalArgumentException> { go { a.relations.relate(rome, rome) } }
        Unit
    }

    @Test
    fun aLinkMadeToAPageTrashedElsewhereBringsItBack() = two(5) { a, b ->
        syncthing.now = 1_000
        val rome = go { a.pages.create("Rome") }
        val milan = go { a.pages.create("Milan") }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(milan) }
        syncthing.now = 3_000
        go { b.relations.relate(rome, milan) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(false, go { d.pages.page(milan) }!!.trashed)
    }

    // Database relations

    @Test
    fun aRelationIsTwoColumnsReadingOneLinkAndLinksMadeApartBothStay() = two(6) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val people = go { a.databases.create("People") }
        val with = go { a.databases.addRelation(trips, "With", people) }
        val rome = go { a.pages.create("Rome", parentId = trips) }
        val ann = go { a.pages.create("Ann", parentId = people) }
        val bob = go { a.pages.create("Bob", parentId = people) }
        settle(listOf(a, b))
        val back = go { a.databases.properties(people) }.single()
        assertEquals("Trips" to PropertyType.RELATION, back.name to back.type)

        syncthing.now = 2_000
        go { a.databases.link(rome, with, ann) }
        go { b.databases.link(bob, back.id, rome) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(setOf(ann, bob), go { d.databases.cells(trips, rome) }.getValue(with).pages.toSet())
            assertEquals(listOf(rome), go { d.databases.cells(people, ann) }.getValue(back.id).pages)
            assertEquals(listOf(rome), go { d.databases.cells(people, bob) }.getValue(back.id).pages)
        }
        syncthing.now = 3_000
        go { b.databases.unlink(ann, back.id, rome) }
        settle(listOf(a, b))
        assertEquals(listOf(bob), go { a.databases.cells(trips, rome) }.getValue(with).pages)
        go { a.databases.link(rome, with, ann) }
        assertEquals(setOf(ann, bob), go { a.databases.cells(trips, rome) }.getValue(with).pages.toSet())
    }

    @Test
    fun aRelationWithinOneDatabaseReadsEachWayInItsTwoColumnsAndSaysWhatBlocks() {
        val tasks = go { databases.create("Tasks") }
        val blockedBy = go { databases.addRelation(tasks, "Blocked by", tasks) }
        val blocks = go { databases.properties(tasks) }.single { it.id != blockedBy }.id
        val paint = go { pages.create("Paint", parentId = tasks) }
        val sand = go { pages.create("Sand", parentId = tasks) }
        go { databases.link(paint, blockedBy, sand) }
        assertEquals(listOf(sand) to listOf(paint), go { databases.cells(tasks, paint).getValue(blockedBy).pages to databases.cells(tasks, sand).getValue(blocks).pages })

        go { databases.setBlockedBy(tasks, blockedBy) }
        assertEquals(setOf(paint), go { databases.blocked(tasks) })
        go { pages.trash(sand) }
        assertEquals(PageState.TRASHED, go { databases.pageStates(listOf(sand)) }.getValue(sand))
        assertEquals(emptySet(), go { databases.blocked(tasks) })
    }

    @Test
    fun aRelationNeverChangesTypeAndGoesWithItsPair() {
        val trips = go { databases.create("Trips") }
        val people = go { databases.create("People") }
        val with = go { databases.addRelation(trips, "With", people) }
        val text = go { databases.addProperty(trips, "Note", PropertyType.TEXT) }
        assertFailsWith<IllegalArgumentException> { go { databases.setType(with, PropertyType.TEXT) } }
        assertFailsWith<IllegalArgumentException> { go { databases.setType(text, PropertyType.RELATION) } }
        assertFailsWith<IllegalArgumentException> { go { databases.addProperty(trips, "R", PropertyType.RELATION) } }
        val rome = go { pages.create("Rome", parentId = trips) }
        val ann = go { pages.create("Ann", parentId = people) }
        assertFailsWith<IllegalArgumentException> { go { databases.link(rome, with, rome) } }
        go { databases.link(rome, with, ann) }

        go { databases.deleteProperty(with) }

        assertEquals(emptyList(), go { databases.properties(people) })
        assertEquals(emptyList(), go { db.linkDao().allLinks() })
    }

    @Test
    fun aLinkToAPageDeletedForGoodReadsAsAPlaceholder() {
        val trips = go { databases.create("Trips") }
        val people = go { databases.create("People") }
        val with = go { databases.addRelation(trips, "With", people) }
        val rome = go { pages.create("Rome", parentId = trips) }
        val ann = go { pages.create("Ann", parentId = people) }
        go { databases.link(rome, with, ann) }
        go { pages.trash(ann) }
        go { pages.purge(ann) }

        assertEquals(listOf(ann), go { databases.cells(trips, rome) }.getValue(with).pages)
        assertEquals(PageState.DELETED, go { databases.pageStates(listOf(ann)) }.getValue(ann))
    }

    // Templates

    @Test
    fun aTemplateCopiesBlocksAndIsKeptOutOfTheTreeAndACopyIsIndependent() {
        val page = go { pages.create("Weekly review") }
        val head = go { pages.addBlock(page, content = "Wins", type = BlockType.HEADING_2) }
        go { pages.addBlock(page, parent = head, content = "one") }
        val template = go { templates.saveAsTemplate(page) }
        assertEquals(listOf("Weekly review"), go { pages.children() }.map { it.title })
        assertEquals(listOf(template), go { templates.templates() }.map { it.id })
        assertFailsWith<IllegalArgumentException> { go { relations.relate(page, template) } }

        val copy = go { templates.create(template, "Week 41") }
        val outline = go { pages.outline(copy) }
        assertEquals(listOf("Wins" to 0, "one" to 1), outline.map { it.content to it.depth })
        assertTrue(outline.none { b -> b.id in go { pages.outline(template) }.map { it.id } })
        go { pages.setText(go { pages.outline(template) }.first().id, "Wins!") }
        assertEquals("Wins", go { pages.outline(copy) }.first().content)
        assertFailsWith<IllegalArgumentException> { go { templates.create(page, "x") } }
    }

    @Test
    fun aDatabaseTemplateCopiesItsSchemaViewsAndColourButNoRowsOrDoorway() {
        val trips = go { databases.create("Trips") }
        val people = go { databases.create("People") }
        val status = go { databases.addProperty(trips, "Status", PropertyType.SELECT) }
        go { databases.addOption(status, "Booked") }
        go { databases.addRelation(trips, "With", people) }
        go { databases.setHue(trips, 200) }
        go { databases.setDoorway(trips, labels.create("travel")) }
        val board = go { databases.addView(trips, "Board", ViewType.BOARD) }
        go { databases.setLayout(board, ViewType.BOARD, groupBy = status) }
        go { pages.create("Rome", parentId = trips) }
        val template = go { templates.saveAsTemplate(trips) }

        val copy = go { templates.create(template, "Trips 2027") }

        val props = go { databases.properties(copy) }
        assertEquals(listOf("Status", "With"), props.map { it.name })
        val copiedStatus = props.first().id
        assertNotEquals(status, copiedStatus)
        assertEquals(listOf("Booked"), go { databases.options(copiedStatus) }.map { it.name })
        assertEquals(copiedStatus, go { databases.views(copy) }.single { it.type == ViewType.BOARD }.groupBy)
        assertEquals(emptyList(), go { databases.members(copy) })
        assertEquals(200L, go { db.databaseDao().databases(listOf(shellId(copy))) }.single().hue)
        assertNull(go { db.databaseDao().databases(listOf(shellId(copy))) }.single().labelId)
        // The relation relates to the same database, with a new matching column there, named after the copy;
        // the template itself made none (a template is kept out of every database).
        assertEquals(listOf("Trips", "Trips 2027"), go { databases.properties(people) }.map { it.name }.sorted())
    }

    @Test
    fun aCanvasTemplateCopiesTheWholeBoardMindMapIncluded() {
        val board = go { canvases.create("Plan") }
        val root = go { canvases.addText(board, 0.0, 0.0, "root") }
        val child = go { canvases.addText(board, 10.0, 0.0, "child", parent = root) }
        go { canvases.addEdge(root, child, EdgeDirection.ONE_WAY, "next") }
        val template = go { templates.saveAsTemplate(board) }

        val copy = go { templates.create(template, "Plan 2") }

        val nodes = go { canvases.nodes(copy) }
        val copiedRoot = nodes.single { it.text == "root" }
        assertEquals(copiedRoot.id, nodes.single { it.text == "child" }.parentId)
        assertEquals(listOf("next"), go { canvases.edges(copy) }.map { it.label })
        assertTrue(nodes.none { it.id == root || it.id == child })
    }

    @Test
    fun aLinkedPageDeletedForGoodIsAPlaceholderFromEitherSide() {
        val trips = go { databases.create("Trips") }
        val people = go { databases.create("People") }
        val with = go { databases.addRelation(trips, "With", people) }
        val back = go { databases.properties(people) }.single().id
        val rome = go { pages.create("Rome", parentId = trips) }
        val ann = go { pages.create("Ann", parentId = people) }
        go { databases.link(rome, with, ann) }
        go { pages.trash(rome) }
        go { pages.purge(rome) }

        assertEquals(listOf(rome), go { databases.cells(people, ann) }.getValue(back).pages)
        assertEquals(PageState.DELETED, go { databases.pageStates(listOf(rome)) }.getValue(rome))
    }

    @Test
    fun aRelationColumnKeptAfterItsPairWasDeletedElsewhereStillLinks() = two(7) { a, b ->
        syncthing.now = 1_000
        val trips = go { a.databases.create("Trips") }
        val people = go { a.databases.create("People") }
        val with = go { a.databases.addRelation(trips, "With", people) }
        val back = go { a.databases.properties(people) }.single().id
        val rome = go { a.pages.create("Rome", parentId = trips) }
        val ann = go { a.pages.create("Ann", parentId = people) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.databases.deleteProperty(with) }
        syncthing.now = 3_000
        go { b.databases.renameProperty(back, "Trips taken") }
        settle(listOf(a, b))

        go { a.databases.link(ann, back, rome) }
        assertEquals(listOf(rome), go { a.databases.cells(people, ann) }.getValue(back).pages)
    }

    @Test
    fun aLinkTakenOffAfterATrashElsewhereLeavesThePageInTheTrash() = two(8) { a, b ->
        syncthing.now = 1_000
        val rome = go { a.pages.create("Rome") }
        val milan = go { a.pages.create("Milan") }
        go { a.relations.relate(rome, milan) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(milan) }
        syncthing.now = 3_000
        go { b.relations.unrelate(rome, milan) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(true, go { d.pages.page(milan) }!!.trashed)
    }

    @Test
    fun choosingWhatBlocksADatabaseTrashedElsewhereBringsItBack() = two(9) { a, b ->
        syncthing.now = 1_000
        val tasks = go { a.databases.create("Tasks") }
        val blockedBy = go { a.databases.addRelation(tasks, "Blocked by", tasks) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(tasks) }
        syncthing.now = 3_000
        go { b.databases.setBlockedBy(tasks, blockedBy) }
        settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(false, go { d.pages.page(tasks) }!!.trashed)
    }

    @Test
    fun aTemplateIsNotFoundNorAParentAndATrashedOneIsInTheTrash() {
        val page = go { pages.create("Weekly review") }
        go { pages.addBlock(page, content = "Wins of the week") }
        val template = go { templates.saveAsTemplate(page) }
        val search = com.factotum.data.search.SearchRepository(db)
        val now = LocalDateTime(2026, 10, 5, 12, 0)
        assertEquals(setOf(page), go { search.search("review", now) }.map { it.id }.toSet())
        assertEquals(1, go { search.search("wins", now) }.size)
        assertFailsWith<IllegalArgumentException> { go { pages.create("Under", parentId = template) } }
        assertFailsWith<IllegalArgumentException> { go { databases.create("Under", parentId = template) } }
        go { pages.trash(template) }
        assertEquals(listOf(template), go { pages.trashed() }.map { it.id })
    }

    @Test
    fun aJournalDaysWritingIsFoundUnderItsDate() {
        val dayPage = go { journal.day(day) }
        go { pages.addBlock(dayPage, content = "Walked to the harbour") }
        val hit = go { com.factotum.data.search.SearchRepository(db).search("harbour", LocalDateTime(2026, 10, 5, 12, 0)) }.single()
        assertEquals("2026-10-05", hit.owner)
    }
}
