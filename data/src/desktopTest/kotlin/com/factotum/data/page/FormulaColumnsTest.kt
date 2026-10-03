package com.factotum.data.page

import com.factotum.core.formula.RollupAggregation
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
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

/** Formulas and rollups (§7 step 3, Tendril's), with the owner's answers of 2026-10-03 (`decisions/14-sole-owner-modules.md`). */
class FormulaColumnsTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var pages: PageRepository
    private lateinit var databases: DatabaseRepository
    private lateinit var templates: TemplateRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "f.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        pages = PageRepository(db, writes, newId, { 1_000 })
        databases = DatabaseRepository(db, writes, newId, pages)
        templates = TemplateRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private fun cell(database: String, page: String, property: String) = go { databases.cells(database, page) }.getValue(property)

    @Test
    fun aFormulaWrittenWithNamesKeepsWorkingWhenAPropertyIsRenamed() {
        val trips = go { databases.create("Trips") }
        val nights = go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val rate = go { databases.addProperty(trips, "Rate", PropertyType.NUMBER) }
        val cost = go { databases.addFormula(trips, "Cost", """prop("Nights") * prop("Rate")""") }
        val rome = go { pages.create("Rome", parentId = trips) }
        go { databases.setNumber(rome, nights, 3.0) }
        go { databases.setNumber(rome, rate, 80.0) }
        assertEquals("240" to 240.0, cell(trips, rome, cost).let { it.text to it.number })

        go { databases.renameProperty(nights, "Nights stayed") }

        assertEquals("240", cell(trips, rome, cost).text)
        assertEquals("""prop("Nights stayed") * prop("Rate")""", go { databases.formulaText(cost) })
    }

    @Test
    fun aFormulaWithAnErrorIsRefusedWithItsMessageInNames() {
        val trips = go { databases.create("Trips") }
        val people = go { databases.create("People") }
        go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        go { databases.addProperty(trips, "Note", PropertyType.TEXT) }
        go { databases.addRelation(trips, "With", people) }
        fun refused(expression: String) = assertFailsWith<IllegalArgumentException> { go { databases.addFormula(trips, "F", expression) } }.message.orEmpty()

        assertTrue("no property named \"Rate\"" in refused("""prop("Rate") * 2"""))
        assertTrue("'-' needs two numbers, got text and number" in refused("""prop("Note") - 1"""))
        assertTrue("relation" in refused("""prop("With")"""))
        refused("""prop("Nights" * 2""")
        val a = go { databases.addFormula(trips, "A", """prop("Nights") + 1""") }
        go { databases.addFormula(trips, "B", """prop("A") + 1""") }
        assertTrue("circular" in assertFailsWith<IllegalArgumentException> { go { databases.setFormula(a, """prop("B") + 1""") } }.message.orEmpty())
        go { databases.addProperty(trips, "Note", PropertyType.TEXT) }
        assertTrue("two properties are named \"Note\"" in refused("""prop("Note")"""))
    }

    @Test
    fun aFormulaReadsEachTypeAndAnotherFormulaAndAViewSortsAndFiltersOnIt() {
        val tasks = go { databases.create("Tasks") }
        val points = go { databases.addProperty(tasks, "Points", PropertyType.NUMBER) }
        val done = go { databases.addProperty(tasks, "Done", PropertyType.CHECKBOX) }
        val due = go { databases.addProperty(tasks, "Due", PropertyType.DATE) }
        val status = go { databases.addProperty(tasks, "Status", PropertyType.SELECT) }
        val high = go { databases.addOption(status, "High") }
        val score = go { databases.addFormula(tasks, "Score", """if(prop("Done"), prop("Points") * 2, prop("Points"))""") }
        val label = go { databases.addFormula(tasks, "Label", """prop("Status") + ": " + prop("Score")""") }
        val late = go { databases.addFormula(tasks, "Late", """prop("Due") < prop("Due")""") }
        val names = listOf("Paint", "Sand", "Prime").map { go { pages.create(it, parentId = tasks) } }
        listOf(3.0, 10.0, 4.0).zip(names).forEach { (p, page) -> go { databases.setNumber(page, points, p) } }
        go { databases.setChecked(names[0], done, true) }
        go { databases.setOption(names[0], status, high) }
        go { databases.setDate(names[0], due, LocalDate(2026, 10, 5)) }

        assertEquals("High: 6", cell(tasks, names[0], label).text)
        assertEquals("false", cell(tasks, names[0], late).text)
        assertNull(cell(tasks, names[1], late).text)
        val view = go { databases.views(tasks) }.single().id
        go { databases.setSort(view, score, descending = true) }
        assertEquals(listOf("Sand", "Paint", "Prime"), go { databases.rows(view) }.map { it.title })
        go { databases.setFilter(view, score, com.factotum.data.page.FilterOp.EQUALS, "6") }
        assertEquals(listOf("Paint"), go { databases.rows(view) }.map { it.title })
    }

    @Test
    fun aRollupReadsTheLiveRelatedRowsOnly() {
        val trips = go { databases.create("Trips") }
        val stays = go { databases.create("Stays") }
        val with = go { databases.addRelation(trips, "Stays", stays) }
        val nights = go { databases.addProperty(stays, "Nights", PropertyType.NUMBER) }
        val from = go { databases.addProperty(stays, "From", PropertyType.DATE) }
        val kind = go { databases.addProperty(stays, "Kind", PropertyType.SELECT) }
        val hotel = go { databases.addOption(kind, "Hotel") }
        val count = go { databases.addRollup(trips, "Stays", with, RollupAggregation.COUNT) }
        val sum = go { databases.addRollup(trips, "Nights", with, RollupAggregation.SUM, nights) }
        val latest = go { databases.addRollup(trips, "Last", with, RollupAggregation.LATEST, from) }
        val kinds = go { databases.addRollup(trips, "Kinds", with, RollupAggregation.SHOW_ORIGINAL, kind) }
        val italy = go { pages.create("Italy", parentId = trips) }
        val (rome, milan, bari) = listOf("Rome", "Milan", "Bari").map { go { pages.create(it, parentId = stays) } }
        listOf(rome to 3.0, milan to 2.0, bari to 4.0).forEach { (p, n) -> go { databases.setNumber(p, nights, n); databases.link(italy, with, p) } }
        go { databases.setDate(milan, from, LocalDate(2026, 11, 2)) }
        go { databases.setOption(rome, kind, hotel) }

        assertEquals(listOf("3", "9", "2026-11-02", "Hotel"), listOf(count, sum, latest, kinds).map { cell(trips, italy, it).text })
        go { pages.trash(bari) }
        assertEquals(listOf("2", "5"), listOf(count, sum).map { cell(trips, italy, it).text })
        assertFailsWith<IllegalArgumentException> { go { databases.addRollup(trips, "X", with, RollupAggregation.SUM) } }
    }

    @Test
    fun aRollupReadsNoRollupAndTwoDatabasesReadingEachOtherDoNotLoop() {
        val a = go { databases.create("A") }
        val b = go { databases.create("B") }
        val ab = go { databases.addRelation(a, "Bs", b) }
        val ba = go { databases.properties(b) }.single().id
        val countA = go { databases.addRollup(a, "Count", ab, RollupAggregation.COUNT) }
        assertFailsWith<IllegalArgumentException> { go { databases.addRollup(b, "Theirs", ba, RollupAggregation.SHOW_ORIGINAL, countA) } }
        assertFailsWith<IllegalArgumentException> { go { databases.addRollup(b, "Theirs", ba, RollupAggregation.SHOW_ORIGINAL, ab) } }
        // B rolls up a formula of A that reads A's rollup of B: A is read without its rollups, so the formula reads blank there.
        val twice = go { databases.addFormula(a, "Twice", """prop("Count") * 2""") }
        val theirs = go { databases.addRollup(b, "Theirs", ba, RollupAggregation.SHOW_ORIGINAL, twice) }
        val x = go { pages.create("x", parentId = a) }
        val y = go { pages.create("y", parentId = b) }
        go { databases.link(x, ab, y) }
        assertEquals("1" to "2", cell(a, x, countA).text to cell(a, x, twice).text)
        assertNull(cell(b, y, theirs).text)
    }

    @Test
    fun aComputedColumnNeverChangesTypeAndATemplateCopyKeepsItsFormulaWorking() {
        val trips = go { databases.create("Trips") }
        val nights = go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val double = go { databases.addFormula(trips, "Double", """prop("Nights") * 2""") }
        assertFailsWith<IllegalArgumentException> { go { databases.setType(double, PropertyType.TEXT) } }
        assertFailsWith<IllegalArgumentException> { go { databases.setType(nights, PropertyType.COMPUTED) } }
        assertFailsWith<IllegalArgumentException> { go { databases.addProperty(trips, "C", PropertyType.COMPUTED) } }

        val copy = go { templates.create(templates.saveAsTemplate(trips), "Trips 2") }
        val (copiedNights, copiedDouble) = go { databases.properties(copy) }.map { it.id }
        val row = go { pages.create("Rome", parentId = copy) }
        go { databases.setNumber(row, copiedNights, 4.0) }
        assertEquals("8", cell(copy, row, copiedDouble).text)
        assertEquals("""prop("Nights") * 2""", go { databases.formulaText(copiedDouble) })
    }

    @Test
    fun aFormulaChangedOnTwoDevicesTakesTheLaterSilentlyAndARenameStands() {
        val w = World(tmp.root, 1)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            w.syncthing.now = 1_000
            val trips = go { a.databases.create("Trips") }
            go { a.databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
            val f = go { a.databases.addFormula(trips, "F", """prop("Nights") + 1""") }
            w.settle(listOf(a, b))
            w.syncthing.now = 2_000
            go { a.databases.setFormula(f, """prop("Nights") + 2""") }
            go { a.databases.renameProperty(f, "Plus") }
            w.syncthing.now = 3_000
            go { b.databases.setFormula(f, """prop("Nights") + 3""") }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertEquals("""prop("Nights") + 3""", go { d.databases.formulaText(f) })
                assertEquals("Plus", go { d.databases.properties(trips) }.single { it.id == f }.name)
                assertEquals(emptyList(), go { d.pages.notices(trips) })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aFormulaReadsARollupAndAnErrorPointsAtWhatThePersonTyped() {
        val trips = go { databases.create("Trips") }
        val stays = go { databases.create("Stays") }
        val with = go { databases.addRelation(trips, "Stays", stays) }
        val count = go { databases.addRollup(trips, "Count", with, RollupAggregation.COUNT) }
        val twice = go { databases.addFormula(trips, "Twice", """prop("Count") * 2""") }
        val italy = go { pages.create("Italy", parentId = trips) }
        go { databases.link(italy, with, go { pages.create("Rome", parentId = stays) }) }
        assertEquals("1" to "2", cell(trips, italy, count).text to cell(trips, italy, twice).text)

        go { databases.addProperty(trips, "A rather long name", PropertyType.TEXT) }
        val typed = """prop("A rather long name") - 1"""
        assertEquals(typed.indexOf("-"), assertFailsWith<FormulaInputException> { go { databases.addFormula(trips, "Bad", typed) } }.position)
        assertEquals(2, assertFailsWith<FormulaInputException> { go { databases.addFormula(trips, "Bad", "1 $ 2") } }.position)
    }

    @Test
    fun aFormulaNamingItselfIsACycleInNamesAndAnEditMayNotBreakAFormulaNamingIt() {
        val trips = go { databases.create("Trips") }
        go { databases.addProperty(trips, "Nights", PropertyType.NUMBER) }
        val a = go { databases.addFormula(trips, "A", """prop("Nights") + 1""") }
        go { databases.addFormula(trips, "B", """prop("A") * 2""") }

        val cycle = assertFailsWith<FormulaInputException> { go { databases.setFormula(a, """prop("A") + 1""") } }.message.orEmpty()
        assertTrue("circular formula reference: A -> A" in cycle, cycle)
        val broken = assertFailsWith<FormulaInputException> { go { databases.setFormula(a, "\"x\"") } }.message.orEmpty()
        assertTrue("breaks the formula B" in broken, broken)
    }

    @Test
    fun aCycleASyncMadeLeavesNothingToCheckAgainstSoANewFormulaIsRefused() {
        val w = World(tmp.root, 2)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            w.syncthing.now = 1_000
            val trips = go { a.databases.create("Trips") }
            val f1 = go { a.databases.addFormula(trips, "F1", "1") }
            val f2 = go { a.databases.addFormula(trips, "F2", "2") }
            w.settle(listOf(a, b))
            go { a.databases.setFormula(f1, """prop("F2") + 1""") }
            go { b.databases.setFormula(f2, """prop("F1") + 1""") }
            w.settle(listOf(a, b))

            val error = assertFailsWith<FormulaInputException> { go { a.databases.addFormula(trips, "X", """prop("Typo")""") } }.message.orEmpty()
            assertTrue("circular" in error, error)
        } finally {
            w.close()
        }
    }

    @Test
    fun aComputedColumnOfNumbersAndTextSortsNumbersFirstAndEqualsReadsTextToo() {
        // A rollup listing text holds numbers on some rows and text on others.
        val things = go { databases.create("Things") }
        val codes = go { databases.create("Codes") }
        val with = go { databases.addRelation(things, "Code", codes) }
        val text = go { databases.addProperty(codes, "Text", PropertyType.TEXT) }
        val shown = go { databases.addRollup(things, "Shown", with, RollupAggregation.SHOW_ORIGINAL, text) }
        val named = go { databases.addProperty(things, "Name", PropertyType.TEXT) }
        val echo = go { databases.addFormula(things, "Echo", """prop("Name")""") }
        listOf("10", "9", "1a", "b", "42").forEach { v ->
            val thing = go { pages.create(v, parentId = things) }
            val code = go { pages.create(v, parentId = codes) }
            go { databases.setText(code, text, v) }
            go { databases.link(thing, with, code) }
            go { databases.setText(thing, named, v) }
        }
        val view = go { databases.views(things) }.single().id
        go { databases.setSort(view, shown) }
        assertEquals(listOf("9", "10", "42", "1a", "b"), go { databases.rows(view) }.map { it.title })
        go { databases.setFilter(view, shown, FilterOp.EQUALS, "42") }
        assertEquals(listOf("42"), go { databases.rows(view) }.map { it.title })
        // A formula over text gives text, "42" included, which equals 42 as written.
        go { databases.setFilter(view, echo, FilterOp.EQUALS, "42") }
        assertEquals(listOf("42"), go { databases.rows(view) }.map { it.title })
    }
}
