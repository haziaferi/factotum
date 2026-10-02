package com.factotum.data.time

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.factotum.core.time.GoalPeriod
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.FixedSettings
import com.factotum.data.isConstraintViolation
import com.factotum.data.item.HabitRepository
import com.factotum.data.item.ItemRepository
import com.factotum.data.item.Outcome
import com.factotum.data.item.TaskStatus
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import com.factotum.data.tracker.TrackerRepository
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

/** ADR 07's cases (`decisions/cases/07-timelog.jsonl`) and the owner's 2026-10-02 answers, on the real database. */
class TimeCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private lateinit var habits: HabitRepository
    private lateinit var trackers: TrackerRepository
    private lateinit var time: TimeRepository
    private lateinit var activities: ActivityRepository
    private var now = at(5, 12)

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "time.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        items = ItemRepository(db, writes, newId, now = { now })
        habits = HabitRepository(db, writes, newId, FixedSettings())
        trackers = TrackerRepository(db, writes, newId, now = { now })
        time = TimeRepository(db, writes, newId, FixedSettings())
        activities = ActivityRepository(db, writes, newId, FixedSettings())
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    private fun minutes(days: List<LocalDate> = listOf(monday), itemId: String? = null) = runBlocking { time.total(days, now, itemId) } / 60

    private fun task(title: String = "write report") = runBlocking { items.createTask(title, monday) }

    @Test
    fun tendrilTimeOnTask_25MinutesOnATaskTotal25() {
        val report = task()
        runBlocking { time.logManual(report, at(5, 9), at(5, 9, 25)) }

        assertEquals(25, minutes(itemId = report))
    }

    @Test
    fun tendrilTimeOnHabit_10MinutesOnAHabitTotal10() {
        val stretch = runBlocking { habits.create("stretch", monday) }
        runBlocking { time.logManual(stretch, at(5, 7), at(5, 7, 10)) }

        assertEquals(10, minutes(itemId = stretch))
    }

    @Test
    fun tendrilExactlyOneOwner_aSpanHasOneOwnerOfAKindThatIsTimed() {
        val event = runBlocking { items.createEvent("dentist", monday) }
        assertFailsWith<IllegalArgumentException> { runBlocking { time.start(event, at(5, 9)) } }

        refused("INSERT INTO time_span (id, item_id, started_at, start_hlc, start_device, end_hlc, end_device, gone_hlc, gone_device, kept_hlc, kept_device, note_hlc, note_device) VALUES ('x', NULL, '2026-10-05T09:00', 1, 'A', 1, 'A', 1, 'A', 1, 'A', 1, 'A')")
        refused("INSERT INTO time_span (id, item_id, started_at, start_hlc, start_device, end_hlc, end_device, gone_hlc, gone_device, kept_hlc, kept_device, note_hlc, note_device) VALUES ('x', '$event', '2026-10-05T09:00', 1, 'A', 1, 'A', 1, 'A', 1, 'A', 1, 'A')")
        val report = task()
        val span = runBlocking { time.logManual(report, at(5, 9), at(5, 10)) }
        assertFailsWith<IllegalArgumentException> { runBlocking { time.edit(span, at(5, 9), at(5, 8), null) } }
        refused("UPDATE time_span SET item_id = '${task("other")}' WHERE id = '$span'")
    }

    @Test
    fun tendrilTaskDeleteCascades_deletingATaskForGoodTakesItsTime() {
        val report = task()
        runBlocking { time.logManual(report, at(5, 9), at(5, 10)) }

        runBlocking { items.purge(report) }

        assertEquals(emptyList(), runBlocking { db.timeDao().allSpans() })
    }

    @Test
    fun chronicleActivityTotals_40MinutesOfReadingTotal40() {
        // The category half of this case needs ADR 08's label, which comes with slice 08.
        val reading = runBlocking { activities.create("Reading", icon = "book", color = 0xFF336699) }
        runBlocking { time.logManual(reading, at(5, 20), at(5, 20, 40)) }

        assertEquals(40, minutes(itemId = reading))
        assertEquals(listOf(Activity(reading, "Reading", "book", 0xFF336699, false, null)), runBlocking { activities.activities() })
    }

    @Test
    fun chronicleCommentAndPlannedRun_aSpanKeepsBoth() {
        val reading = runBlocking { activities.create("Reading") }
        val run = "1;1500;4;1,1,1,1"
        val span = runBlocking { time.start(reading, at(5, 20), plannedRun = run) }
        runBlocking { time.stop(span, at(5, 21)) }
        runBlocking { time.edit(span, at(5, 20), at(5, 21), "  chapter 3  ") }

        assertEquals(TrackedSpan(span, reading, at(5, 20), at(5, 21), "chapter 3", run), runBlocking { time.spansOn(monday) }.single())
    }

    @Test
    fun chronicleActivityDeleteRefused_anActivityIsNeverDeletedForGoodButIsDeletedWithItsTime() {
        val reading = runBlocking { activities.create("Reading") }
        val span = runBlocking { time.logManual(reading, at(5, 20), at(5, 20, 40)) }
        val goal = runBlocking { activities.addGoal(reading, GoalPeriod.WEEK, 180) }
        val untimed = runBlocking { activities.create("Chess") }

        // Owner, 2026-10-02: not even one with no time, so a purge can never take time another device logged.
        assertFailsWith<IllegalArgumentException> { runBlocking { items.purge(reading) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { items.purge(untimed) } }
        refused("DELETE FROM item WHERE id = '$reading'")
        refused("DELETE FROM item WHERE id = '$untimed'")

        runBlocking { activities.delete(reading) }
        val left = runBlocking { db.timeDao().spans(listOf(span)) }.single()
        assertTrue(left.deletedAt != null)
        assertTrue(runBlocking { db.trackerDao().goals(listOf(goal)) }.single().deletedAt != null)
        assertEquals(listOf(untimed), runBlocking { activities.activities(withArchived = true) }.map { it.id })
    }

    @Test
    fun chronicleActivityGoal_aWeekly3HourGoalReads40Of180() {
        val reading = runBlocking { activities.create("Reading") }
        runBlocking { time.logManual(reading, at(5, 20), at(5, 20, 25)) }
        runBlocking { time.logManual(reading, at(7, 21), at(7, 21, 15)) }
        runBlocking { time.logManual(reading, at(4, 21), at(4, 22)) }
        val goal = runBlocking { activities.addGoal(reading, GoalPeriod.WEEK, 180) }
        now = at(8, 12)

        assertEquals(TimeGoalProgress(40, 180), runBlocking { activities.progress(goal, LocalDate(2026, 10, 8), now) })
    }

    @Test
    fun sharedOneTimeHome_theDaysTotalOverEveryOwnerIsOneRead() {
        runBlocking { time.logManual(task(), at(5, 9), at(5, 9, 25)) }
        runBlocking { time.logManual(habits.create("stretch", monday), at(5, 7), at(5, 7, 10)) }
        runBlocking { time.logManual(activities.create("Reading"), at(5, 20), at(5, 20, 40)) }

        assertEquals(75, minutes())
    }

    @Test
    fun twoTimersRunAtOnceAndTheirOverlapCountsOnce() {
        val report = task()
        val reading = runBlocking { activities.create("Reading") }
        runBlocking { time.start(report, at(5, 9)) }
        runBlocking { time.start(reading, at(5, 9, 30)) }
        now = at(5, 10)

        assertEquals(2, runBlocking { time.running() }.size)
        assertEquals(60, minutes())
        assertEquals(30, minutes(itemId = reading))
    }

    @Test
    fun aTimerPastTwelveHoursIsAskedAboutUntilKept() {
        val reading = runBlocking { activities.create("Reading") }
        val span = runBlocking { time.start(reading, at(5, 8)) }

        assertEquals(emptyList(), runBlocking { time.runningLong(at(5, 20)) })
        assertEquals(listOf(span), runBlocking { time.runningLong(at(5, 21)) }.map { it.id })

        runBlocking { time.keep(span, at(5, 21)) }
        assertEquals(emptyList(), runBlocking { time.runningLong(at(6, 9)) })
        assertEquals(listOf(span), runBlocking { time.runningLong(at(6, 9, 1)) }.map { it.id })

        runBlocking { time.stop(span, at(5, 20)) }
        assertEquals(emptyList(), runBlocking { time.runningLong(at(7, 0)) })
    }

    @Test
    fun finishingOrDeletingATaskOrHabitStopsItsTimerAndALogDoesNot() {
        val done = task("done")
        val resolved = task("resolved")
        val deleted = task("deleted")
        val stretch = runBlocking { habits.create("stretch", monday) }
        val spans = listOf(done, resolved, deleted, stretch).associateWith { runBlocking { time.start(it, at(5, 9)) } }
        now = at(5, 10)

        runBlocking { items.setStatus(done, TaskStatus.DONE) }
        runBlocking { items.resolve(resolved, LocalDateTime(monday, kotlinx.datetime.LocalTime(0, 0)), Outcome.SKIPPED) }
        runBlocking { items.delete(deleted) }
        runBlocking { habits.log(stretch, at(5, 10)) }

        val ends = runBlocking { db.timeDao().spans(spans.values.toList()) }.associate { it.itemId to it.endedAt }
        assertEquals(mapOf(done to "2026-10-05T10:00", resolved to "2026-10-05T10:00", deleted to "2026-10-05T10:00", stretch to null), ends)

        now = at(5, 11)
        runBlocking { trackers.delete(requireNotNull(db.itemDao().items(listOf(stretch)).single().trackerId)) }
        assertEquals("2026-10-05T11:00", runBlocking { db.timeDao().spans(listOf(spans.getValue(stretch))) }.single().endedAt)
    }

    @Test
    fun aDeletedOwnerOrADeletedTrackersHabitDropsOutOfTotals() {
        val report = task()
        val stretch = runBlocking { habits.create("stretch", monday) }
        runBlocking { time.logManual(report, at(5, 9), at(5, 10)) }
        runBlocking { time.logManual(stretch, at(5, 7), at(5, 7, 30)) }

        runBlocking { items.delete(report) }
        runBlocking { trackers.delete(requireNotNull(db.itemDao().items(listOf(stretch)).single().trackerId)) }

        assertEquals(0, minutes())
    }

    @Test
    fun aDeletedSpanOrOneOnADeletedOwnerIsNotEditedAndDeletingTwiceChangesNothing() {
        val report = task()
        val gone = runBlocking { time.logManual(report, at(5, 9), at(5, 10)) }
        runBlocking { time.delete(gone) }
        val stamp = runBlocking { db.timeDao().spans(listOf(gone)) }.single().goneHlc
        runBlocking { time.delete(gone) }

        assertEquals(stamp, runBlocking { db.timeDao().spans(listOf(gone)) }.single().goneHlc)
        assertFailsWith<IllegalArgumentException> { runBlocking { time.edit(gone, at(5, 9), at(5, 11), null) } }

        val other = task("other")
        val kept = runBlocking { time.logManual(other, at(5, 9), at(5, 10)) }
        runBlocking { items.delete(other) }
        assertFailsWith<IllegalArgumentException> { runBlocking { time.edit(kept, at(5, 9), at(5, 11), null) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { time.logManual(report, at(5, 10), at(5, 10)) } }
    }

    @Test
    fun aCommentWrittenOnOneDeviceDoesNotReopenATimerStoppedOnAnother() {
        val w = World(tmp.root, 4)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val reading = runBlocking { a.activities.create("Reading") }
            val span = runBlocking { a.time.start(reading, at(5, 20)) }
            w.settle(listOf(a, b))

            runBlocking { a.time.stop(span, at(5, 21)) }
            runBlocking { b.db.timeDao().spans(listOf(span)) }.single().let { assertNull(it.endedAt) }
            runBlocking { b.time.edit(span, at(5, 20), null, "chapter 3") }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                val s = runBlocking { d.db.timeDao().spans(listOf(span)) }.single()
                assertEquals("2026-10-05T21:00" to "chapter 3", s.endedAt to s.comment)
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aStaleKeepOrStartEditDoesNotReopenOrReviveASpan() {
        val w = World(tmp.root, 6)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val reading = runBlocking { a.activities.create("Reading") }
            val stopped = runBlocking { a.time.start(reading, at(5, 8)) }
            val deleted = runBlocking { a.time.start(reading, at(5, 9)) }
            w.settle(listOf(a, b))

            runBlocking { a.time.stop(stopped, at(5, 12)) }
            runBlocking { a.time.delete(deleted) }
            runBlocking { b.time.keep(stopped, at(5, 21)) }
            runBlocking { b.time.edit(deleted, at(5, 9, 30), null, null) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                val (s, gone) = runBlocking { d.db.timeDao().spans(listOf(stopped, deleted)) }.sortedBy { it.id != stopped }
                assertEquals("2026-10-05T12:00", s.endedAt)
                assertTrue(gone.deletedAt != null)
                assertEquals(emptyList(), runBlocking { d.time.running() })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aTaskFinishedOnAnotherDeviceStopsTheTimerHereWhenItArrives() {
        val w = World(tmp.root, 7)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val report = runBlocking { a.items.createTask("report", monday) }
            w.settle(listOf(a, b))
            val span = runBlocking { b.time.start(report, at(5, 9)) }

            runBlocking { a.items.setStatus(report, TaskStatus.DONE) }
            // Each device ends it when it learns of the other's write: B when "done" arrives, A when the timer does.
            a.now = at(5, 11)
            b.now = at(5, 11)
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) assertEquals("2026-10-05T11:00", runBlocking { d.db.timeDao().spans(listOf(span)) }.single().endedAt)
        } finally {
            w.close()
        }
    }

    @Test
    fun aHabitMadeOnATrackerDeletedElsewhereDropsOutOfTotals() {
        val w = World(tmp.root, 8)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val water = runBlocking { a.habits.create("water", monday) }
            w.settle(listOf(a, b))
            val tracker = requireNotNull(runBlocking { a.db.itemDao().items(listOf(water)) }.single().trackerId)

            runBlocking { a.trackers.delete(tracker) }
            val juice = runBlocking { b.habits.create("juice", monday, trackerId = tracker) }
            runBlocking { b.time.logManual(juice, at(5, 7), at(5, 7, 30)) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertEquals(null, runBlocking { d.db.itemDao().items(listOf(juice)) }.single().deletedAt)
                assertEquals(0L, runBlocking { d.time.total(listOf(monday), at(6, 0)) })
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun endingAtTheLimitCountsFromTheLastKeep() {
        val reading = runBlocking { activities.create("Reading") }
        val span = runBlocking { time.start(reading, at(5, 8)) }
        runBlocking { time.keep(span, at(5, 21)) }

        runBlocking { time.stopAtLimit(span) }

        assertEquals(at(6, 9), runBlocking { time.spansOn(monday) }.single().end)
        assertFailsWith<IllegalArgumentException> { runBlocking { time.keep(span, at(6, 10)) } }
    }

    @Test
    fun resolvingAPastOccurrenceLeavesTodaysTimerRunning() {
        val report = task()
        val span = runBlocking { time.start(report, at(7, 9)) }
        now = at(7, 10)

        runBlocking { items.resolve(report, at(5, 0), Outcome.SKIPPED) }
        assertNull(runBlocking { db.timeDao().spans(listOf(span)) }.single().endedAt)

        runBlocking { items.resolve(report, at(7, 0), Outcome.DONE) }
        assertEquals("2026-10-07T10:00", runBlocking { db.timeDao().spans(listOf(span)) }.single().endedAt)
    }

    @Test
    fun aPersonalDayStartingLaterCountsAnEarlySpanForTheDayBefore() {
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val owl = TimeRepository(db, writes, { "owl-${n++}" }, FixedSettings(kotlinx.datetime.LocalTime(4, 0)))
        val reading = runBlocking { activities.create("Reading") }
        runBlocking { owl.logManual(reading, at(6, 2), at(6, 3)) }
        runBlocking { owl.logManual(reading, at(6, 5), at(6, 6)) }

        assertEquals(60 * 60L, runBlocking { owl.total(listOf(monday), at(7, 0)) })
        assertEquals(60 * 60L, runBlocking { owl.total(listOf(LocalDate(2026, 10, 6)), at(7, 0)) })
    }

    @Test
    fun activitiesArchiveAndKeepTheirOrderAndTheirColumnsStayTheirs() {
        val chess = runBlocking { activities.create("Chess") }
        val reading = runBlocking { activities.create("Reading") }
        val piano = runBlocking { activities.create("Piano") }
        runBlocking { items.setSortOrder(piano, 1.0) }
        runBlocking { items.setSortOrder(reading, 1.5) }
        runBlocking { items.setSortOrder(chess, 2.0) }
        runBlocking { activities.setArchived(chess, true) }

        assertEquals(listOf(piano, reading), runBlocking { activities.activities() }.map { it.id })
        assertEquals(listOf(piano, reading, chess), runBlocking { activities.activities(withArchived = true) }.map { it.id })
        val report = task()
        assertFailsWith<IllegalArgumentException> { runBlocking { activities.setArchived(report, true) } }
        refused("UPDATE item SET icon = 'book' WHERE id = '$report'")
        refused("UPDATE item SET color = 1 WHERE id = '$report'")
        refused("UPDATE item SET archived = 0 WHERE id = '$report'")
        refused("UPDATE item SET sort_order = 1.0 WHERE id = '$report'")
        refused("UPDATE item SET archived = NULL WHERE id = '$reading'")
        refused("UPDATE item SET start_date = '2026-10-05' WHERE id = '$reading'")
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
