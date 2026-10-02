package com.factotum.data.label

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.factotum.core.label.LabelScope
import com.factotum.core.label.colorForName
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.createAtVersion
import androidx.sqlite.execSQL
import com.factotum.data.isConstraintViolation
import com.factotum.data.item.HabitRepository
import com.factotum.data.item.ItemRepository
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import com.factotum.data.time.ActivityRepository
import com.factotum.data.time.TimeRepository
import com.factotum.data.tracker.TrackerRepository
import com.factotum.core.sync.Ulid
import com.factotum.data.tracker.TrackerType
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
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
import kotlin.test.fail

/** ADR 08's cases (`decisions/cases/08-tagging.jsonl`) that need no page, the owner's 2026-10-02 answers, and ADR 07's category total. */
class LabelCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var labels: LabelRepository
    private lateinit var items: ItemRepository
    private lateinit var habits: HabitRepository
    private lateinit var trackers: TrackerRepository
    private lateinit var activities: ActivityRepository
    private lateinit var time: TimeRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "labels.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        labels = LabelRepository(db, writes, newId)
        items = ItemRepository(db, writes, newId)
        habits = HabitRepository(db, writes, newId)
        trackers = TrackerRepository(db, writes, newId)
        activities = ActivityRepository(db, writes, newId)
        time = TimeRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    private fun labelOf(itemId: String) = runBlocking { labels.labelOf(itemId) }

    private fun trackerLabelOf(trackerId: String) = runBlocking { labels.trackerLabelOf(trackerId) }

    @Test
    fun tendrilHabitArea_aHabitCarriesOneLabel() {
        val health = runBlocking { labels.create("Health") }
        val water = runBlocking { habits.create("water", monday) }

        runBlocking { labels.label(water, health) }

        assertEquals(health, labelOf(water))
    }

    @Test
    fun chronicleOneCategoryPerRow_aSecondLabelReplacesTheFirstAndAnyKindElseCarriesNone() {
        val leisure = runBlocking { labels.create("Leisure") }
        val study = runBlocking { labels.create("Study") }
        val reading = runBlocking { activities.create("Reading") }
        val mood = runBlocking { trackers.create("Mood", TrackerType.RATING) }

        runBlocking { labels.label(reading, leisure) }
        runBlocking { labels.label(reading, study) }
        runBlocking { labels.labelTracker(mood, leisure) }

        assertEquals(study, labelOf(reading))
        assertEquals(leisure, trackerLabelOf(mood))
        val report = runBlocking { items.createTask("report", monday) }
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.label(report, study) } }
        refused("UPDATE item SET label_id = '$study' WHERE id = '$report'")
    }

    @Test
    fun chronicleRenameRecolourOnce_everyMemberSeesTheChange() {
        val leisure = runBlocking { labels.create("Leisure") }
        val reading = runBlocking { activities.create("Reading") }
        val mood = runBlocking { trackers.create("Mood", TrackerType.RATING) }
        runBlocking { labels.label(reading, leisure) }
        runBlocking { labels.labelTracker(mood, leisure) }

        runBlocking { labels.rename(leisure, "Free time") }
        runBlocking { labels.recolor(leisure, 0xFF112233) }

        assertEquals(listOf(Label(leisure, "Free time", 0xFF112233, LabelScope.ALL, 1.0)), runBlocking { labels.labels() })
        assertEquals(leisure, labelOf(reading))
        assertEquals(leisure, trackerLabelOf(mood))
    }

    @Test
    fun chronicleDeleteKeepsMembers_theyStayWithNoLabel() {
        val leisure = runBlocking { labels.create("Leisure") }
        val reading = runBlocking { activities.create("Reading") }
        val mood = runBlocking { trackers.create("Mood", TrackerType.RATING) }
        runBlocking { labels.label(reading, leisure) }
        runBlocking { labels.labelTracker(mood, leisure) }

        runBlocking { labels.delete(leisure) }

        assertEquals(emptyList(), runBlocking { labels.labels() })
        assertNull(labelOf(reading))
        assertNull(trackerLabelOf(mood))
        assertEquals(listOf(reading), runBlocking { activities.activities() }.map { it.id })
    }

    @Test
    fun chronicleCategoryOrder_labelsListInTheirOrderAndMove() {
        val a = runBlocking { labels.create("Work") }
        val b = runBlocking { labels.create("Leisure") }
        val c = runBlocking { labels.create("Health") }

        assertEquals(listOf(a, b, c), runBlocking { labels.labels() }.map { it.id })
        runBlocking { labels.setSortOrder(c, 0.5) }
        assertEquals(listOf(c, a, b), runBlocking { labels.labels() }.map { it.id })
    }

    @Test
    fun chronicleAppliesToScope_aLabelIsOfferedOnlyWhereItAppliesAndNarrowingHides() {
        val both = runBlocking { labels.create("Leisure") }
        val onlyActivities = runBlocking { labels.create("Sport", LabelScope.ACTIVITY) }
        val onlyTrackers = runBlocking { labels.create("Body", LabelScope.TRACKER) }
        val reading = runBlocking { activities.create("Reading") }
        val water = runBlocking { habits.create("water", monday) }

        assertEquals(listOf(both, onlyActivities), runBlocking { labels.offeredFor(LabelScope.ACTIVITY) }.map { it.id })
        assertEquals(listOf(both, onlyTrackers), runBlocking { labels.offeredFor(LabelScope.TRACKER) }.map { it.id })
        assertEquals(listOf(both), runBlocking { labels.offeredFor(LabelScope.ALL) }.map { it.id })
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.label(reading, onlyTrackers) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.label(water, onlyActivities) } }

        runBlocking { labels.label(reading, both) }
        runBlocking { labels.setScope(both, LabelScope.TRACKER) }

        assertEquals(both, labelOf(reading))
        assertEquals(listOf(onlyActivities), runBlocking { labels.offeredFor(LabelScope.ACTIVITY) }.map { it.id })
        refused("UPDATE label SET applies_to = 'PAGE' WHERE id = '$both'")
    }

    @Test
    fun sharedOneVocabulary_aHabitAndAnActivityShareOneLabelAndItsTotal() {
        val health = runBlocking { labels.create("Health") }
        val walk = runBlocking { activities.create("Walk") }
        val stretch = runBlocking { habits.create("stretch", monday) }
        runBlocking { labels.label(walk, health) }
        runBlocking { labels.label(stretch, health) }
        runBlocking { time.logManual(walk, at(5, 7), at(5, 7, 40)) }
        runBlocking { time.logManual(stretch, at(5, 7, 30), at(5, 7, 50)) }

        runBlocking { labels.rename(health, "Wellbeing") }
        assertEquals(listOf("Wellbeing"), runBlocking { labels.labels() }.map { it.name })
        assertEquals(health to health, labelOf(walk) to labelOf(stretch))
        // Owner, 2026-10-02: a habit's time counts in its label's total, overlapping time once.
        assertEquals(50, runBlocking { time.total(listOf(monday), at(6, 0), labelId = health) } / 60)
    }

    @Test
    fun chronicleActivityAndCategoryTotals_40MinutesOfReadingTotal40ForLeisure() {
        val leisure = runBlocking { labels.create("Leisure") }
        val reading = runBlocking { activities.create("Reading") }
        val chess = runBlocking { activities.create("Chess") }
        runBlocking { labels.label(reading, leisure) }
        runBlocking { time.logManual(reading, at(5, 20), at(5, 20, 40)) }
        runBlocking { time.logManual(chess, at(5, 21), at(5, 21, 30)) }

        assertEquals(40, runBlocking { time.total(listOf(monday), at(6, 0), itemId = reading) } / 60)
        assertEquals(40, runBlocking { time.total(listOf(monday), at(6, 0), labelId = leisure) } / 60)

        runBlocking { labels.delete(leisure) }
        assertEquals(0, runBlocking { time.total(listOf(monday), at(6, 0), labelId = leisure) })
    }

    @Test
    fun namesAreUniqueIgnoringCaseAndANewLabelTakesItsColourFromItsName() {
        val health = runBlocking { labels.create("  Health ") }
        runBlocking { labels.create("Work") }

        assertFailsWith<IllegalArgumentException> { runBlocking { labels.create("HEALTH") } }
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.rename(health, "work") } }
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.create("  ") } }
        // One name in two Unicode forms: a composed "é", and an "e" with a combining accent.
        runBlocking { labels.create("Caf\u00e9") }
        assertFailsWith<IllegalArgumentException> { runBlocking { labels.create("Cafe\u0301") } }
        runBlocking { labels.rename(health, "health") }
        assertEquals(
            listOf("health" to colorForName("Health"), "Work" to colorForName("Work"), "Caf\u00e9" to colorForName("Caf\u00e9")),
            runBlocking { labels.labels() }.map { it.name to it.color },
        )
    }

    /** A device's labels with ids that begin with the time, as ULIDs do, so the one made first has the lowest. */
    private fun World.Device.timedLabels(w: World) = LabelRepository(db, writes) { Ulid.next(w.syncthing.now) }

    @Test
    fun aNameStoredInAnotherUnicodeFormStillCountsAsTheSameName() {
        // As a label row written by another program, or an older one, could hold it.
        runBlocking {
            db.useWriterConnection {
                it.execSQL(
                    "INSERT INTO label (id, name, name_hlc, name_device, color, look_hlc, look_device, applies_to, scope_hlc, scope_device, " +
                        "sort_order, order_hlc, order_device, gone_hlc, gone_device) VALUES ('old', 'Cafe\u0301', 1, 'X', 1, 1, 'X', 'ALL', 1, 'X', 1.0, 1, 'X', 1, 'X')",
                )
            }
        }

        assertFailsWith<IllegalArgumentException> { runBlocking { labels.create("Caf\u00e9") } }
    }

    @Test
    fun twoLabelsOfOneNameMadeApartMergeIntoTheOneMadeFirstWithWhatCarriedThem() {
        val w = World(tmp.root, 9)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            w.syncthing.now = 1_000
            val first = runBlocking { b.timedLabels(w).create("health", LabelScope.TRACKER, color = 0xFF000002) }
            w.syncthing.now = 2_000
            val second = runBlocking { a.timedLabels(w).create("Health", color = 0xFF000001) }
            val walk = runBlocking { a.activities.create("Walk") }
            runBlocking { a.labels.label(walk, second) }
            val mood = runBlocking { b.trackers.create("Mood", TrackerType.RATING) }
            runBlocking { b.labels.labelTracker(mood, first) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertEquals(listOf(Label(first, "health", 0xFF000002, LabelScope.TRACKER, 1.0)), runBlocking { d.labels.labels() })
                assertEquals(first to first, runBlocking { d.labels.trackerLabelOf(mood) to d.labels.labelOf(walk) })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aRenameOntoAnotherDevicesNameMergesTheSameWay() {
        val w = World(tmp.root, 13)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val fitness = runBlocking { a.labels.create("Fitness") }
            w.settle(listOf(a, b))
            val health = runBlocking { a.labels.create("Health") }
            val walk = runBlocking { a.activities.create("Walk") }
            runBlocking { a.labels.label(walk, health) }

            runBlocking { b.labels.rename(fitness, "HEALTH") }
            w.settle(listOf(a, b))

            // "Fitness" was made first, so it is the one that stays, under its new name.
            for (d in listOf(a, b)) {
                assertEquals(listOf(fitness to "HEALTH"), runBlocking { d.labels.labels() }.map { it.id to it.name })
                assertEquals(fitness, runBlocking { d.labels.labelOf(walk) })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aMergeWritesNothingOnWhatCarriedTheMergedLabelSoAChoiceMadeMeanwhileStands() {
        val w = World(tmp.root, 14)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val first = runBlocking { a.labels.create("Health") }
            val second = runBlocking { b.labels.create("health") }
            val walk = runBlocking { b.activities.create("Walk") }
            runBlocking { b.labels.label(walk, second) }
            val written = runBlocking { b.db.itemDao().items(listOf(walk)) }.single().let { it.labelId to it.labelHlc }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertEquals(written, runBlocking { d.db.itemDao().items(listOf(walk)) }.single().let { it.labelId to it.labelHlc })
                assertEquals(first, runBlocking { d.labels.labelOf(walk) })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun somethingLabelledOnAPeerThatHadNotSeenTheMergeReadsAsTheSurvivor() {
        val w = World(tmp.root, 10)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val c = w.Device("C")
            val first = runBlocking { a.labels.create("Health") }
            val second = runBlocking { b.labels.create("Health") }
            w.settle(listOf(b, c))
            val walk = runBlocking { c.activities.create("Walk") }
            runBlocking { c.labels.label(walk, second) }

            w.settle(listOf(a, b))
            w.settle(listOf(a, b, c))

            for (d in listOf(a, b, c)) {
                assertEquals(listOf(first), runBlocking { d.labels.labels() }.map { it.id })
                assertEquals(first, runBlocking { d.labels.labelOf(walk) })
                assertEquals(listOf(walk), runBlocking { d.activities.activities() }.filter { it.labelId == first }.map { it.id })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited() {
        val w = World(tmp.root, 15)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val first = runBlocking { a.labels.create("Health") }
            val second = runBlocking { b.labels.create("Health") }
            val walk = runBlocking { b.activities.create("Walk") }
            runBlocking { b.labels.label(walk, second) }
            runBlocking { b.time.logManual(walk, at(5, 7), at(5, 7, 30)) }
            w.settle(listOf(a, b))
            assertEquals(30, runBlocking { a.time.total(listOf(monday), at(6, 0), labelId = first) } / 60)

            runBlocking { a.labels.delete(first) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertNull(runBlocking { d.labels.labelOf(walk) })
                assertEquals(null, runBlocking { d.db.itemDao().items(listOf(walk)) }.single().labelId)
            }
            assertFailsWith<IllegalArgumentException> { runBlocking { a.labels.rename(first, "Wellness") } }
            assertFailsWith<IllegalArgumentException> { runBlocking { a.labels.recolor(second, 1) } }
            assertFailsWith<IllegalArgumentException> { runBlocking { a.labels.label(walk, second) } }
        } finally {
            w.close()
        }
    }

    @Test
    fun aMergeChainReadsToItsEndAndAChainEndingInADeletedLabelReadsAsNone() {
        fun label(id: String, deleted: Boolean = false, into: String? = null) =
            LabelEntity(id, id, 0, "", 0, 0, "", "ALL", 0, "", 0.0, 0, "", if (deleted || into != null) 1 else null, into, 0, "")
        val read = resolver(listOf(label("x"), label("y", into = "x"), label("z", into = "y"), label("q", deleted = true), label("r", into = "q")))

        assertEquals(listOf("x", "x", "x", null, null, null), listOf("x", "y", "z", "q", "r", "unknown").map(read))
        assertNull(read(null))
    }

    @Test
    fun aRenameAndARecolourMadeApartBothSurvive() {
        val w = World(tmp.root, 11)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val leisure = runBlocking { a.labels.create("Leisure") }
            w.settle(listOf(a, b))

            runBlocking { a.labels.rename(leisure, "Free time") }
            runBlocking { b.labels.recolor(leisure, 0xFF112233) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) assertEquals("Free time" to 0xFF112233, runBlocking { d.labels.labels() }.single().let { it.name to it.color })
        } finally {
            w.close()
        }
    }

    @Test
    fun aLabelDeletedOnOneDeviceDoesNotReviveATrackerDeletedOnAnother() {
        val w = World(tmp.root, 12)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val body = runBlocking { a.labels.create("Body") }
            val mood = runBlocking { a.trackers.create("Mood", TrackerType.RATING) }
            runBlocking { a.labels.labelTracker(mood, body) }
            w.settle(listOf(a, b))

            runBlocking { a.labels.delete(body) }
            runBlocking { b.trackers.delete(mood) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                val t = runBlocking { d.db.trackerDao().trackers(listOf(mood)) }.single()
                assertTrue(t.deletedAt != null)
                assertNull(t.labelId)
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aVersion9DatabaseKeepsItsItemsAndTrackersWhenLabelsArrive() {
        val file = File(tmp.root, "v9.db")
        createAtVersion(file, 9) { c ->
            // What a version 9 database also holds once opened: its span rule names `item`, which a
            // migration that rebuilt `item` would trip over (SQLite checks triggers on a rename).
            c.execSQL(
                "CREATE TRIGGER time_span_rules_insert BEFORE INSERT ON time_span WHEN NOT (COALESCE((SELECT kind FROM item WHERE id = NEW.item_id) " +
                    "IN ('TASK', 'HABIT', 'ACTIVITY'), 1)) BEGIN SELECT RAISE(ABORT, 'time_span: a row breaks its rules'); END",
            )
            c.execSQL(
                "INSERT INTO item (id, kind, title, details_hlc, details_device, schedule_hlc, schedule_device, importance, status_hlc, status_device, archived) " +
                    "VALUES ('walk', 'ACTIVITY', 'Walk', 1, 'A', 1, 'A', 0, 1, 'A', 0)",
            )
            c.execSQL(
                "INSERT INTO tracker (id, name, type, polarity, archived, sort_order, hlc, device) VALUES ('mood', 'Mood', 'RATING', 'NEUTRAL', 0, 0, 1, 'A')",
            )
            c.execSQL(
                "INSERT INTO time_span (id, item_id, started_at, ended_at, start_hlc, start_device, end_hlc, end_device, gone_hlc, gone_device, " +
                    "kept_hlc, kept_device, note_hlc, note_device) VALUES ('s', 'walk', '2026-10-05T07:00', '2026-10-05T07:30', 1, 'A', 1, 'A', 1, 'A', 1, 'A', 1, 'A')",
            )
        }

        val upgraded = openFactotumDatabase(file).database
        try {
            val walk = runBlocking { upgraded.itemDao().items(listOf("walk")) }.single()
            val mood = runBlocking { upgraded.trackerDao().trackers(listOf("mood")) }.single()
            assertEquals(Triple(null, 0L, ""), Triple(walk.labelId, walk.labelHlc, walk.labelDevice))
            assertEquals(Triple(null, 0L, ""), Triple(mood.labelId, mood.labelHlc, mood.labelDevice))
            assertEquals(listOf("s"), runBlocking { upgraded.timeDao().allSpans() }.map { it.id })
        } finally {
            upgraded.close()
        }
    }

    private fun refused(sql: String) {
        try {
            runBlocking { db.useWriterConnection { it.execSQL(sql) } }
        } catch (e: Exception) {
            if (isConstraintViolation(e)) return
            throw e
        }
        fail("the database took: $sql")
    }
}
