package com.factotum.data.page

import com.factotum.core.recurrence.Interval
import com.factotum.core.recurrence.IntervalUnit
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Frequency
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.WeekdayNum
import com.factotum.data.item.Answer
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.TaskStatus
import com.factotum.data.sync.World
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Tendril's database rows as tasks (decision 14, answers 15-30). */
class RowTasksTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun <T> two(seed: Int, body: World.(World.Device, World.Device) -> T): T {
        val w = World(tmp.root, seed)
        try {
            return w.body(w.Device("A"), w.Device("B"))
        } finally {
            w.close()
        }
    }

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private val oct5 = LocalDate(2026, 10, 5)

    /** A database "Chores" with rows as tasks on and Done, Date, Due and Every bound, and a row "Bins". */
    private class Chores(val db: String, val done: String, val date: String, val due: String, val every: String, val bins: String)

    private fun World.Device.chores(): Chores = runBlocking {
        val db = databases.create("Chores")
        val done = databases.addProperty(db, "Done", PropertyType.CHECKBOX)
        val date = databases.addProperty(db, "Date", PropertyType.DATE, after = done)
        val due = databases.addProperty(db, "Due", PropertyType.DATE, after = date)
        val every = databases.addProperty(db, "Every", PropertyType.INTERVAL, after = due)
        val bins = pages.create("Bins", parentId = db)
        rowTasks.setRowsAsTasks(db, true)
        rowTasks.bind(done, TaskRole.DONE)
        rowTasks.bind(date, TaskRole.DATE)
        rowTasks.bind(due, TaskRole.DUE)
        rowTasks.bind(every, TaskRole.RECURRENCE)
        Chores(db, done, date, due, every, bins)
    }

    @Test
    fun everyRowIsATaskWithOneTitleAndItsCellsShowTheTask() = two(1) { a, _ ->
        val c = a.chores()
        val task = assertNotNull(go { a.rowTasks.taskOf(c.bins) })
        assertEquals("Bins", go { a.items.item(task) }?.title)

        go { a.pages.rename(c.bins, "Bins out") }
        assertEquals("Bins out", go { a.items.item(task) }?.title)
        go { a.items.rename(task, "Recycling") }
        assertEquals("Recycling", go { a.pages.page(c.bins) }?.title)

        // A row made later, and a page carrying the doorway label, are tasks too (answer 16).
        val later = go { a.pages.create("Laundry", parentId = c.db) }
        val label = go { a.labels.create("Home") }
        go { a.databases.setDoorway(c.db, label) }
        val loose = go { a.pages.create("Plants") }
        go { a.labels.labelPage(loose, label) }
        // A row's own edit seeds its task when none has been made yet.
        go { a.rowTasks.setDue(later, oct5) }
        assertEquals(oct5, go { a.items.item(requireNotNull(a.rowTasks.taskOf(later))) }?.due)
        assertNotNull(go { a.rowTasks.taskOf(loose) })

        go { a.rowTasks.setDone(c.bins, true) }
        go { a.rowTasks.setDate(c.bins, oct5, DateScope.SERIES) }
        go { a.rowTasks.setDue(c.bins, LocalDate(2026, 10, 9)) }
        val cells = go { a.databases.cells(c.db, c.bins) }
        assertTrue(cells.getValue(c.done).checked)
        assertEquals(oct5, cells.getValue(c.date).date)
        assertEquals(LocalDate(2026, 10, 9), cells.getValue(c.due).date)
        assertEquals(TaskStatus.DONE, go { a.items.item(task) }?.status)
        // A bound column is set through the task, and keeps its type while bound.
        assertFailsWith<IllegalArgumentException> { go { a.databases.setChecked(c.bins, c.done, false) } }
        assertFailsWith<IllegalArgumentException> { go { a.databases.setType(c.date, PropertyType.TEXT) } }
        Unit
    }

    @Test
    fun formulasSortsAndFiltersReadTheTask() = two(2) { a, _ ->
        val c = a.chores()
        val late = go { a.pages.create("Gutters", parentId = c.db) }
        go { a.rowTasks.settle() }
        go { a.rowTasks.setDate(c.bins, LocalDate(2026, 10, 7), DateScope.SERIES) }
        go { a.rowTasks.setDate(late, LocalDate(2026, 10, 6), DateScope.SERIES) }
        go { a.rowTasks.setDone(late, true) }
        val f = go { a.databases.addFormula(c.db, "Score", """if(prop("Done"), 1, 0)""") }
        assertEquals("1", go { a.databases.cells(c.db, late) }.getValue(f).text)
        val view = go { a.databases.views(c.db) }.single().id
        go { a.databases.setSort(view, c.date) }
        assertEquals(listOf(late, c.bins), go { a.databases.rows(view) }.map { it.pageId })
        go { a.databases.setFilter(view, c.done, FilterOp.EQUALS, "true") }
        assertEquals(listOf(late), go { a.databases.rows(view) }.map { it.pageId })
    }

    @Test
    fun deletingTheTaskTrashesTheRowAndTheRowCarriesItsTask() = two(3) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        go { a.items.delete(task) }
        assertEquals(true, go { a.pages.page(c.bins) }?.trashed)
        assertEquals(true, go { a.items.item(task) }?.deleted)
        go { a.pages.restore(c.bins) }
        assertEquals(false, go { a.items.item(task) }?.deleted)

        // Trashing the database trashes its rows' tasks (Tendril left them live), and stops their timers.
        val span = go { a.time.start(task, LocalDateTime(2026, 10, 5, 11, 0)) }
        go { a.pages.trash(c.db) }
        assertEquals(true, go { a.items.item(task) }?.deleted)
        assertNotNull(go { a.db.timeDao().spans(listOf(span)) }.single().endedAt)
        go { a.pages.restore(c.db) }
        assertEquals(false, go { a.items.item(task) }?.deleted)

        go { a.items.delete(task) }
        go { a.items.purge(task) }
        assertNull(go { a.pages.page(c.bins) })
        assertNull(go { a.items.item(task) })
    }

    @Test
    fun aTaskEditedAfterItsRowWasTrashedElsewhereBringsTheRowBack() = two(4) { a, b ->
        syncthing.now = 1_000
        val c = a.chores()
        settle(listOf(a, b))
        val task = requireNotNull(go { b.rowTasks.taskOf(c.bins) })

        syncthing.now = 2_000
        go { a.pages.trash(c.bins) }
        syncthing.now = 3_000
        go { b.rowTasks.setDate(c.bins, oct5, DateScope.SERIES) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) {
            assertEquals(false, go { d.pages.page(c.bins) }?.trashed, d.name)
            assertEquals(false, go { d.items.item(task) }?.deleted, d.name)
            assertEquals(oct5, go { d.items.item(task) }?.start, d.name)
        }
        assertEquals(emptyList(), go { a.items.questions() } + go { b.items.questions() })

        // An edit made before the trash loses to it, and is kept in the trash.
        syncthing.now = 4_000
        go { b.rowTasks.setDue(c.bins, oct5) }
        syncthing.now = 5_000
        go { a.pages.trash(c.bins) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) {
            assertEquals(true, go { d.pages.page(c.bins) }?.trashed, d.name)
            assertEquals(true, go { d.items.item(task) }?.deleted, d.name)
            assertEquals(oct5, go { d.items.item(task) }?.due, d.name)
        }

        // A tick made after a trash brings the row back too.
        syncthing.now = 6_000
        go { a.pages.restore(c.bins) }
        settle(listOf(a, b))
        syncthing.now = 7_000
        go { a.pages.trash(c.bins) }
        syncthing.now = 8_000
        go { b.rowTasks.setDone(c.bins, true) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) {
            assertEquals(false, go { d.pages.page(c.bins) }?.trashed, d.name)
            assertEquals(false, go { d.items.item(task) }?.deleted, d.name)
            assertEquals(TaskStatus.DONE, go { d.items.item(task) }?.status, d.name)
        }
    }

    @Test
    fun twoDevicesSeedingOneRowMakeOneTaskAndADateClashOffersNoKeepBoth() = two(5) { a, b ->
        syncthing.now = 1_000
        val db = go { a.databases.create("Chores") }
        val bins = go { a.pages.create("Bins", parentId = db) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.rowTasks.setRowsAsTasks(db, true) }
        go { b.rowTasks.setRowsAsTasks(db, true) }
        settle(listOf(a, b))
        val task = requireNotNull(go { a.rowTasks.taskOf(bins) })
        assertEquals(task, go { b.rowTasks.taskOf(bins) })
        assertEquals(1, go { a.db.itemDao().rowTasks() }.size)

        syncthing.now = 3_000
        go { a.rowTasks.setDate(bins, oct5, DateScope.SERIES) }
        go { b.rowTasks.setDate(bins, LocalDate(2026, 10, 6), DateScope.SERIES) }
        settle(listOf(a, b))
        val question = go { a.items.questions() }.single()
        assertEquals(SCHEDULE, question.group)
        assertFailsWith<IllegalArgumentException> { go { a.items.answer(question, Answer.KEEP_BOTH) } }
        go { a.items.answer(question, Answer.KEEP_MINE) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(oct5, go { d.items.item(task) }?.start, d.name)
    }

    @Test
    fun turningRowsAsTasksOffTrashesTheTasksAndTheColumnsKeepTheirValues() = two(6) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        go { a.rowTasks.setDone(c.bins, true) }
        go { a.rowTasks.setDate(c.bins, oct5, DateScope.SERIES) }
        go { a.rowTasks.setInterval(c.bins, Interval(2, IntervalUnit.WEEK)) }
        go { a.rowTasks.setRowsAsTasks(c.db, false) }
        assertEquals(true, go { a.items.item(task) }?.deleted)
        assertEquals(emptyMap(), go { a.rowTasks.bindings(c.db) })
        val cells = go { a.databases.cells(c.db, c.bins) }
        // A repeating row was never done: its next occurrence is open.
        assertFalse(cells.getValue(c.done).checked)
        assertEquals(oct5, cells.getValue(c.date).date)
        assertEquals("2:WEEK", cells.getValue(c.every).text)
        // The cells are the person's now.
        go { a.databases.setChecked(c.bins, c.done, true) }
        assertTrue(go { a.databases.cells(c.db, c.bins) }.getValue(c.done).checked)

        // On again: the same task comes back, and binding a column gives the tasks its values.
        go { a.rowTasks.setRowsAsTasks(c.db, true) }
        assertEquals(false, go { a.items.item(task) }?.deleted)
        go { a.databases.setDate(c.bins, c.due, LocalDate(2026, 10, 9)) }
        go { a.rowTasks.bind(c.due, TaskRole.DUE) }
        assertEquals(LocalDate(2026, 10, 9), go { a.items.item(task) }?.due)
    }

    @Test
    fun unbindingFreezesTheValueAndARicherRepeatShowsReadOnlyAndFreezesEmpty() = two(7) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        go { a.rowTasks.setDue(c.bins, oct5) }
        go { a.rowTasks.unbind(c.due) }
        assertEquals(oct5, go { a.databases.cells(c.db, c.bins) }.getValue(c.due).date)
        go { a.rowTasks.setDue(c.bins, LocalDate(2026, 10, 9)) }
        assertEquals(oct5, go { a.databases.cells(c.db, c.bins) }.getValue(c.due).date)

        go { a.rowTasks.setDate(c.bins, oct5, DateScope.SERIES) }
        val mondaysAndThursdays = Recurrence.Rule(RRule(Frequency.WEEKLY, byDay = listOf(DayOfWeek.MONDAY, DayOfWeek.THURSDAY).map { WeekdayNum(null, it) }))
        go { a.items.setRecurrence(task, mondaysAndThursdays) }
        val every = go { a.databases.cells(c.db, c.bins) }.getValue(c.every)
        assertTrue(every.fixed)
        assertNull(Interval.parse(every.text))
        go { a.rowTasks.unbind(c.every) }
        assertNull(go { a.databases.cells(c.db, c.bins) }.getValue(c.every).text)
        assertEquals(mondaysAndThursdays, go { a.items.item(task) }?.recurrence)
    }

    @Test
    fun aRepeatingRowShowsItsNextOpenOccurrenceAndTickingResolvesIt() = two(8) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        // No date yet: an interval starts it today (answer 28).
        go { a.rowTasks.setInterval(c.bins, Interval(1, IntervalUnit.WEEK)) }
        assertEquals(oct5, go { a.items.item(task) }?.start)
        fun cells() = go { a.databases.cells(c.db, c.bins) }
        assertEquals(oct5, cells().getValue(c.date).date)
        assertFalse(cells().getValue(c.done).checked)

        go { a.rowTasks.setDone(c.bins, true) }
        assertEquals(LocalDate(2026, 10, 12), cells().getValue(c.date).date)
        assertEquals(mapOf(LocalDateTime(2026, 10, 5, 0, 0) to com.factotum.data.item.Outcome.DONE), go { a.items.outcomes(task) })
        assertFailsWith<IllegalArgumentException> { go { a.rowTasks.setDone(c.bins, false) } }

        // Answer 26: the next occurrence alone moves, or the series.
        go { a.rowTasks.setDate(c.bins, LocalDate(2026, 10, 14), DateScope.NEXT) }
        assertEquals(LocalDate(2026, 10, 14), cells().getValue(c.date).date)
        assertEquals(oct5, go { a.items.item(task) }?.start)
        go { a.rowTasks.setDone(c.bins, true) }
        assertEquals(LocalDate(2026, 10, 19), cells().getValue(c.date).date)
        go { a.rowTasks.setDate(c.bins, LocalDate(2026, 10, 21), DateScope.SERIES) }
        assertEquals(LocalDate(2026, 10, 21), go { a.items.item(task) }?.start)
        assertFailsWith<IllegalArgumentException> { go { a.rowTasks.setDate(c.bins, null, DateScope.SERIES) } }
        Unit
    }

    @Test
    fun aPageThatStopsBeingARowHasItsTaskTrashed() = two(9) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        go { a.pages.move(c.bins, null) }
        go { a.rowTasks.settle() }
        assertEquals(true, go { a.items.item(task) }?.deleted)
        go { a.pages.move(c.bins, c.db) }
        go { a.rowTasks.settle() }
        assertEquals(false, go { a.items.item(task) }?.deleted)
    }

    @Test
    fun aRowDeletedForGoodThatAnEditElsewhereBringsBackKeepsItsTask() = two(11) { a, b ->
        syncthing.now = 1_000
        val c = a.chores()
        settle(listOf(a, b))
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        syncthing.now = 2_000
        go { b.rowTasks.setDate(c.bins, oct5, DateScope.SERIES) }
        go { a.pages.trash(c.bins) }
        go { a.pages.purge(c.bins) }
        assertNull(go { a.items.item(task) })
        syncthing.now = 3_000
        // An edit of the page that leaves the task alone, so only the page outlives the purge.
        go { b.pages.setIcon(c.bins, "bin") }
        settle(listOf(a, b))
        for (d in listOf(a, b)) {
            assertEquals(false, go { d.pages.page(c.bins) }?.trashed, d.name)
            assertEquals(oct5, go { d.items.item(task) }?.start, d.name)
        }
    }

    @Test
    fun aTaskItsRowLetGoOfIsDeletedAloneAndARestoreLeavesIt() = two(12) { a, _ ->
        val c = a.chores()
        val task = requireNotNull(go { a.rowTasks.taskOf(c.bins) })
        go { a.pages.move(c.bins, null) }
        go { a.rowTasks.settle() }
        assertEquals(true, go { a.items.item(task) }?.deleted)
        go { a.pages.trash(c.bins) }
        go { a.pages.restore(c.bins) }
        assertEquals(true, go { a.items.item(task) }?.deleted)
        go { a.items.purge(task) }
        assertNull(go { a.items.item(task) })
        assertEquals(false, go { a.pages.page(c.bins) }?.trashed)
    }

    @Test
    fun bindingOnADeviceThatHadNotSeenATrashDoesNotBringTheRowBack() = two(13) { a, b ->
        syncthing.now = 1_000
        val c = a.chores()
        val note = go { a.databases.addProperty(c.db, "Planned", PropertyType.DATE) }
        go { a.rowTasks.unbind(c.date) }
        go { a.databases.setDate(c.bins, note, LocalDate(2026, 10, 9)) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { a.pages.trash(c.bins) }
        syncthing.now = 3_000
        go { b.rowTasks.bind(note, TaskRole.DATE) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(true, go { d.pages.page(c.bins) }?.trashed, d.name)
    }

    @Test
    fun turningRowsAsTasksOffLetsGoOfAColumnASyncLeftBound() = two(14) { a, b ->
        syncthing.now = 1_000
        val c = a.chores()
        val other = go { a.databases.addProperty(c.db, "Ticked", PropertyType.CHECKBOX) }
        settle(listOf(a, b))
        syncthing.now = 2_000
        go { b.rowTasks.bind(other, TaskRole.DONE) }
        syncthing.now = 3_000
        go { a.rowTasks.unbind(c.done) }
        go { a.rowTasks.bind(c.done, TaskRole.DONE) }
        settle(listOf(a, b))
        assertEquals(c.done, go { a.rowTasks.bindings(c.db) }[TaskRole.DONE])
        go { a.rowTasks.setRowsAsTasks(c.db, false) }
        go { a.rowTasks.setRowsAsTasks(c.db, true) }
        assertEquals(emptyMap(), go { a.rowTasks.bindings(c.db) })
        go { a.databases.setType(other, PropertyType.TEXT) }
    }

    @Test
    fun anIntervalCellIsEveryNDaysWeeksOrMonths() = two(10) { a, _ ->
        val db = go { a.databases.create("Plans") }
        val every = go { a.databases.addProperty(db, "Every", PropertyType.INTERVAL) }
        val row = go { a.pages.create("Water", parentId = db) }
        go { a.databases.setInterval(row, every, Interval(3, IntervalUnit.DAY)) }
        assertEquals(Interval(3, IntervalUnit.DAY), Interval.parse(go { a.databases.cells(db, row) }.getValue(every).text))
        val longer = go { a.pages.create("Repot", parentId = db) }
        go { a.databases.setInterval(longer, every, Interval(10, IntervalUnit.DAY)) }
        val shorter = go { a.pages.create("Mist", parentId = db) }
        go { a.databases.setInterval(shorter, every, Interval(2, IntervalUnit.WEEK)) }
        val view = go { a.databases.views(db) }.single().id
        go { a.databases.setSort(view, every) }
        assertEquals(listOf(row, longer, shorter), go { a.databases.rows(view) }.map { it.pageId })
        // A column of another type cannot show the repeat.
        val text = go { a.databases.addProperty(db, "Note", PropertyType.TEXT) }
        go { a.rowTasks.setRowsAsTasks(db, true) }
        assertFailsWith<IllegalArgumentException> { go { a.rowTasks.bind(text, TaskRole.RECURRENCE) } }
        Unit
    }
}
