package com.hazia.factotum.data

import com.hazia.factotum.core.recurrence.RRule
import com.hazia.factotum.core.recurrence.Recurrence
import com.hazia.factotum.data.chart.ChartType
import com.hazia.factotum.data.chart.SourceKind
import com.hazia.factotum.data.page.DateScope
import com.hazia.factotum.data.page.PropertyType
import com.hazia.factotum.data.page.TaskRole
import com.hazia.factotum.data.page.ViewType
import com.hazia.factotum.data.sync.World
import com.hazia.factotum.data.tracker.TrackerType
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
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/**
 * The screens' one vocabulary (owner, 2026-10-09, `docs/screens/t1/actions-inventory.md` draft 4):
 * Delete moves to the Trash, Restore brings back, Delete forever purges from the Trash, for every
 * kind that can be deleted; and two checks the inventory owed (a reminder on a row's task, Skip for
 * today on a standalone reminder).
 */
class VocabularyTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun <T> one(body: World.Device.() -> T): T {
        val w = World(tmp.root, 1)
        try {
            return w.Device("A").body()
        } finally {
            w.close()
        }
    }

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private val oct5 = LocalDate(2026, 10, 5)

    /** One deletable kind, through the data layer's own calls for each word. */
    private class Kind(
        val name: String,
        val make: suspend () -> String,
        val delete: suspend (String) -> Unit,
        val trashed: suspend () -> List<String>,
        val restore: suspend (String) -> Unit,
        val purge: suspend (String) -> Unit,
        val live: suspend (String) -> Boolean,
        val held: suspend (String) -> Boolean,
    )

    /**
     * The gate: every kind goes delete, in its Trash, restore, live again, delete, Delete forever,
     * gone and out of the Trash. A kind that lacks one of the three does not compile, or fails here.
     */
    @Test
    fun everyDeletableKindGoesToTheTrashComesBackAndIsDeletedForever() = one {
        val board = go { canvases.create("Plan") }
        val base = go { databases.create("Trips") }
        val select = go { databases.addProperty(base, "Status", PropertyType.SELECT) }
        val walk = go { activities.create("Walk") }
        val items = items
        val itemLive: suspend (String) -> Boolean = { items.item(it)?.deleted == false }
        val itemHeld: suspend (String) -> Boolean = { items.item(it) != null }
        fun itemKind(name: String, make: suspend () -> String) =
            Kind(name, make, items::delete, { items.trashed().map { it.id } }, items::restore, items::purge, itemLive, itemHeld)
        val pageLive: suspend (String) -> Boolean = { pages.page(it)?.trashed == false }
        val pageHeld: suspend (String) -> Boolean = { pages.page(it) != null }
        fun pageKind(name: String, make: suspend () -> String) =
            Kind(name, make, pages::trash, { pages.trashed().map { it.id } }, pages::restore, pages::purge, pageLive, pageHeld)
        fun cardKind(name: String, make: suspend () -> String) = Kind(
            name, make, canvases::deleteNode, { canvases.trashedNodes(board).map { it.id } }, canvases::restoreNode, canvases::purgeNode,
            { id -> canvases.nodes(board).any { it.id == id } }, { db.canvasDao().nodes(listOf(it)).isNotEmpty() },
        )

        val kinds = listOf(
            itemKind("task") { items.createTask("call", oct5) },
            itemKind("event") { items.createEvent("talk", oct5) },
            itemKind("standalone reminder") { reminders.createStandalone("pills", oct5, LocalTime(8, 0)) },
            itemKind("habit") { habits.create("water", oct5) },
            Kind(
                "tracker", { trackers.create("Mood", TrackerType.RATING) }, trackers::delete, { trackers.trashed().map { it.id } }, trackers::restore, trackers::purge,
                { id -> trackers.trackers().any { it.id == id } }, { db.trackerDao().trackers(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "activity", { activities.create("Reading") }, activities::delete, { activities.trashed().map { it.id } }, activities::restore, activities::purge,
                { id -> activities.activities().any { it.id == id } }, { db.itemDao().items(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "checklist", { checklists.create("Morning") }, checklists::delete, { checklists.trashed().map { it.id } }, checklists::restore, checklists::purge,
                { id -> checklists.checklists().any { it.id == id } }, { db.checklistDao().checklists(listOf(it)).isNotEmpty() },
            ),
            pageKind("page") { pages.create("Notes") },
            pageKind("database") { databases.create("Books") },
            pageKind("database row") { pages.create("Rome", parentId = base) },
            cardKind("canvas card") { canvases.addText(board, 0.0, 0.0, "idea") },
            cardKind("canvas frame") { canvases.addFrame(board, 0.0, 0.0, 200.0, 100.0, "group") },
            Kind(
                "label", { labels.create("Home") }, labels::delete, { labels.trashed().map { it.id } }, labels::restore, labels::purge,
                { id -> labels.labels().any { it.id == id } }, { db.labelDao().labels(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "chart", { charts.create(ChartType.BAR, 7, listOf(SourceKind.ACTIVITY to walk)) }, charts::delete, { charts.trashed().map { it.id } }, charts::restore, charts::purge,
                { id -> charts.charts().any { it.id == id } }, { db.chartDao().charts(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "database property", { databases.addProperty(base, "Note", PropertyType.TEXT) }, databases::deleteProperty, { databases.trashedProperties(base).map { it.id } },
                databases::restoreProperty, databases::purgeProperty, { id -> databases.properties(base).any { it.id == id } }, { db.databaseDao().properties(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "select option", { databases.addOption(select, "Booked") }, databases::deleteOption, { databases.trashedOptions(select).map { it.id } },
                databases::restoreOption, databases::purgeOption, { id -> databases.options(select).any { it.id == id } }, { db.databaseDao().options(listOf(it)).isNotEmpty() },
            ),
            Kind(
                "database view", { databases.addView(base, "Board", ViewType.BOARD) }, databases::deleteView, { databases.trashedViews(base).map { it.id } },
                databases::restoreView, databases::purgeView, { id -> databases.views(base).any { it.id == id } }, { db.databaseDao().views(listOf(it)).isNotEmpty() },
            ),
        )

        for (k in kinds) {
            val id = go { k.make() }
            assertTrue(go { k.live(id) }, "${k.name}: made live")
            go { k.delete(id) }
            assertFalse(go { k.live(id) }, "${k.name}: deleted is not live")
            assertTrue(id in go { k.trashed() }, "${k.name}: deleted is in its Trash")
            go { k.restore(id) }
            assertTrue(go { k.live(id) }, "${k.name}: restored is live")
            assertFalse(id in go { k.trashed() }, "${k.name}: restored is out of the Trash")
            assertFailsWith<IllegalArgumentException>("${k.name}: Delete forever is from the Trash only") { go { k.purge(id) } }
            go { k.delete(id) }
            go { k.purge(id) }
            assertFalse(go { k.held(id) }, "${k.name}: deleted forever is gone")
            assertFalse(id in go { k.trashed() }, "${k.name}: deleted forever is out of the Trash")
            assertTrue(id in go { db.syncDao().purges() }.map { it.id }, "${k.name}: the purge travels")
        }
    }

    @Test
    fun aLabelCountsTheLiveElementsCarryingItEachOnce() = one {
        val home = go { labels.create("Home") }
        val other = go { labels.create("Other") }
        val task = go { items.createTask("bins", oct5) }
        val walk = go { activities.create("Walk") }
        val mood = go { trackers.create("Mood", TrackerType.RATING) }
        val list = go { checklists.create("Morning") }
        val page = go { pages.create("Plants") }
        val base = go { databases.create("Chores") }
        val gone = go { items.createTask("old", oct5) }
        go { labels.label(task, home) }
        go { labels.label(walk, home) }
        go { labels.label(gone, home) }
        go { labels.labelTracker(mood, home) }
        go { labels.labelChecklist(list, home) }
        go { labels.labelPage(page, home) }
        // A database carries it by its doorway; its page carrying it too is still one element.
        go { databases.setDoorway(base, home) }
        go { labels.labelPage(base, home) }
        go { labels.labelPage(page, other) }
        go { items.delete(gone) }

        assertEquals(6, go { labels.carrying(home) })
        assertEquals(1, go { labels.carrying(other) })
        go { pages.trash(page) }
        assertEquals(5, go { labels.carrying(home) })
        go { labels.delete(home) }
        assertEquals(0, go { labels.carrying(home) })
    }

    @Test
    fun aLabelDeletedForeverReadsAsNoneEverywhere() = one {
        val home = go { labels.create("Home") }
        val task = go { items.createTask("bins", oct5) }
        val list = go { checklists.create("Morning") }
        val page = go { pages.create("Plants") }
        val base = go { databases.create("Chores") }
        go { labels.label(task, home) }
        go { labels.labelChecklist(list, home) }
        go { labels.labelPage(page, home) }
        go { databases.setDoorway(base, home) }
        assertEquals(listOf(page), go { databases.members(base) })

        go { labels.delete(home) }
        go { labels.purge(home) }

        assertEquals(null, go { labels.labelOf(task) })
        assertEquals(null, go { labels.checklistLabelOf(list) })
        assertEquals(emptyList(), go { labels.labelsOfPage(page) })
        assertEquals(emptyList(), go { databases.members(base) })
        assertEquals(emptyList(), go { labels.labels() })
    }

    @Test
    fun aReminderIsAddedToARowsTaskThroughTheTaskAndFiresUntilTheRowIsTrashed() = one {
        val base = go { databases.create("Chores") }
        val date = go { databases.addProperty(base, "Date", PropertyType.DATE) }
        val bins = go { pages.create("Bins", parentId = base) }
        go { rowTasks.setRowsAsTasks(base, true) }
        go { rowTasks.bind(date, TaskRole.DATE) }
        val task = assertNotNull(go { rowTasks.taskOf(bins) })
        // An undated row's task takes no reminder (ADR 03): it could never fire.
        assertFailsWith<IllegalArgumentException> { go { reminders.add(task, -60, anchor = LocalTime(9, 0)) } }

        go { rowTasks.setDate(bins, oct5, DateScope.SERIES) }
        val reminder = go { reminders.add(task, -60, anchor = LocalTime(9, 0)) }
        val fires = { go { reminders.firings() }.singleOrNull { it.reminderId == reminder }?.at }
        assertEquals(LocalDateTime(oct5, LocalTime(8, 0)), fires())

        // It follows its row: trashed with it, back with it.
        go { pages.trash(bins) }
        assertEquals(null, fires())
        go { pages.restore(bins) }
        assertEquals(LocalDateTime(oct5, LocalTime(8, 0)), fires())
    }

    @Test
    fun skipForTodayOnAStandaloneReminderThatFiresDailyLeavesTheNextDay() = one {
        val daily = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))
        val pills = go { reminders.createStandalone("pills", oct5, LocalTime(8, 0), recurrence = daily) }
        val reminder = go { reminders.remindersOf(pills) }.single()
        val next = { go { reminders.firings(after = LocalDateTime(oct5, LocalTime(7, 0))) }.single { it.reminderId == reminder }.at }
        assertEquals(LocalDateTime(oct5, LocalTime(8, 0)), next())

        go { occurrences.skip(pills, LocalDateTime(oct5, LocalTime(8, 0))) }

        assertEquals(LocalDateTime(LocalDate(2026, 10, 6), LocalTime(8, 0)), next())
        val week = go { occurrences.occurrences(pills, LocalDateTime(oct5, LocalTime(0, 0)), LocalDateTime(LocalDate(2026, 10, 8), LocalTime(0, 0))) }
        assertEquals(listOf(6, 7), week.map { it.at.day })
    }
}
