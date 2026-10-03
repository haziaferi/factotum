package com.factotum.data.item

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.RollUnit
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.FixedSettings
import com.factotum.data.isConstraintViolation
import com.factotum.data.openFactotumDatabase
import com.factotum.data.reminder.ReminderRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
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
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 06's cases (`decisions/cases/06-habit.jsonl`) and the owner's 2026-10-02 answers, on the real database. */
class HabitCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private lateinit var habits: HabitRepository
    private lateinit var trackers: TrackerRepository
    private lateinit var occurrences: OccurrenceRepository
    private lateinit var reminders: ReminderRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "habits.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        items = ItemRepository(db, writes, newId)
        habits = HabitRepository(db, writes, newId, FixedSettings())
        trackers = TrackerRepository(db, writes, newId)
        occurrences = OccurrenceRepository(db, writes, newId, FixedSettings())
        reminders = ReminderRepository(db, writes, newId, FixedSettings())
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    private fun shown(id: String, from: Int = 5, to: Int = 20) = runBlocking { occurrences.occurrences(id, at(from, 0), at(to, 0)) }.map { it.at }

    private fun everyTwoDays() = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY;INTERVAL=2")))

    @Test
    fun tendrilCadenceAndTime_waterEveryTwoDaysAtEight() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }

        assertEquals(listOf(at(5, 8), at(7, 8), at(9, 8)), shown(water, to = 10))
    }

    @Test
    fun tendrilCountingAndUndo_eightGlassesMeetTheDayAndUndoLeavesSeven() {
        val water = runBlocking { habits.create("water", monday, type = TrackerType.NUMBER, unit = "CUSTOM", unitLabel = "glasses", amountPerLog = 1.0, dailyGoal = 8.0) }
        runBlocking { repeat(8) { habits.log(water, at(5, 8 + it)) } }
        assertEquals(Progress(8.0, 8.0), runBlocking { habits.progress(water, monday) })

        runBlocking { habits.undo(water, monday) }

        assertEquals(Progress(7.0, 8.0), runBlocking { habits.progress(water, monday) })
    }

    @Test
    fun tendrilPauseWindow_noOccurrencesWhilePausedAndOnlyHabitsPause() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }

        runBlocking { habits.pause(water, LocalDate(2026, 10, 12), LocalDate(2026, 10, 14)) }

        assertEquals(listOf(at(9, 8), at(11, 8), at(15, 8), at(17, 8)), shown(water, from = 9, to = 18))
        val task = runBlocking { items.createTask("call", monday) }
        refused("UPDATE item SET pause_from = '2026-10-12' WHERE id = '$task'")
    }

    @Test
    fun chronicleTrackerPresence_threeMorningsOfYesAreThreePresences() {
        val meditate = runBlocking { habits.create("meditate", monday) }
        runBlocking { listOf(5, 6, 7).forEach { habits.log(meditate, at(it, 7)) } }

        val p = runBlocking { habits.presence(meditate, LocalDate(2026, 10, 14)) }

        assertEquals(3, p.daysThisMonth)
    }

    @Test
    fun ownerNoStreak_noStreakLastCompletedOrMissedColumnAnywhere() {
        val tables = runBlocking { db.useReaderConnection { c -> c.usePrepared("SELECT name FROM sqlite_master WHERE type = 'table'") { s -> buildList { while (s.step()) add(s.getText(0)) } } } }
        val columns = tables.flatMap { t ->
            runBlocking { db.useReaderConnection { c -> c.usePrepared("PRAGMA table_info($t)") { s -> buildList { while (s.step()) add(s.getText(1)) } } } }
        }

        // By whole words of a column's name: a notice's `dismissed_at` is not a missed day.
        assertTrue(columns.none { c -> c.split('_').let { "streak" in it || "missed" in it } || "last_completed" in c }, columns.toString())
    }

    @Test
    fun sharedOneReminderPath_aHabitsReminderIsAReminderRowAndQuietOnceLogged() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }
        val reminder = runBlocking { reminders.add(water, 0) }
        assertEquals(at(5, 8), runBlocking { reminders.firings() }.single { it.reminderId == reminder }.at)

        runBlocking { habits.log(water, at(5, 7, 30)) }

        assertEquals(at(7, 8), runBlocking { reminders.firings() }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun tendrilPlannerFields_aHabitKeepsItsBlockAndLengthAndATaskMayNot() {
        val stretch = runBlocking { habits.create("stretch", monday, blockId = "block-morning", durationMin = 15) }

        val read = runBlocking { items.item(stretch) }!!
        assertEquals("block-morning", read.blockId)
        assertEquals(15L, read.durationMin)
        val task = runBlocking { items.createTask("call", monday) }
        refused("UPDATE item SET block_id = 'block-morning' WHERE id = '$task'")
        refused("UPDATE item SET duration_min = 15 WHERE id = '$task'")
    }

    @Test
    fun aHabitAndItsTrackerAreMadeTogether() {
        val water = runBlocking { habits.create("water", monday) }

        val tracker = runBlocking { db.trackerDao().trackers(listOf(items.item(water)!!.trackerId!!)) }.single()
        assertEquals("water", tracker.name)
        assertEquals("BOOLEAN", tracker.type)
    }

    @Test
    fun aHabitCanUseATrackerThatAlreadyExists() {
        val steps = runBlocking { trackers.create("steps", TrackerType.NUMBER, unit = "STEPS") }

        val walk = runBlocking { habits.create("walk", monday, trackerId = steps) }

        assertEquals(steps, runBlocking { items.item(walk) }!!.trackerId)
        assertEquals(1, runBlocking { db.trackerDao().allTrackers() }.size)
    }

    @Test
    fun deletingATrackerDeletesItsHabitsAndDeletingAHabitKeepsTheTracker() {
        val water = runBlocking { habits.create("water", monday) }
        val tea = runBlocking { habits.create("tea", monday) }
        runBlocking { habits.log(tea, at(5, 9)) }

        runBlocking { items.delete(tea) }
        val teaTracker = runBlocking { items.item(tea) }!!.trackerId!!
        assertEquals(1, runBlocking { trackers.logs(teaTracker) }.size)

        runBlocking { trackers.delete(runBlocking { items.item(water) }!!.trackerId!!) }
        assertTrue(runBlocking { items.item(water) }!!.deleted)
    }

    @Test
    fun purgingATrackerPurgesItsHabits() {
        val water = runBlocking { habits.create("water", monday) }
        val tracker = runBlocking { items.item(water) }!!.trackerId!!

        runBlocking { trackers.purge(tracker) }

        assertEquals(null, runBlocking { items.item(water) })
    }

    @Test
    fun aRollingHabitIsDueTwoDaysAfterItsLastLog() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), Recurrence.Rolling(2, RollUnit.DAY)) }
        val reminder = runBlocking { reminders.add(water, 0) }

        runBlocking { habits.log(water, at(8, 21)) }

        assertEquals(listOf(at(10, 8), at(11, 8), at(12, 8)), shown(water, from = 9, to = 13))
        assertEquals(at(10, 8), runBlocking { reminders.firings(after = at(8, 22)) }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun aPausedHabitsReminderIsQuietUntilThePauseEnds() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }
        val reminder = runBlocking { reminders.add(water, 0) }

        runBlocking { habits.pause(water, monday, LocalDate(2026, 10, 10)) }

        assertEquals(at(11, 8), runBlocking { reminders.firings() }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun anOpenEndedPauseHoldsUntilResumed() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }

        runBlocking { habits.pause(water, LocalDate(2026, 10, 8)) }
        assertEquals(listOf(at(5, 8), at(7, 8)), shown(water))

        runBlocking { habits.resume(water) }
        assertEquals(8, shown(water).size)
    }

    @Test
    fun aLogAfterMidnightCountsForYesterdayWhenTheDayStartsLater() {
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 2_000 } })
        var n = 100
        val nightOwl = HabitRepository(db, writes, { "late-${n++}" }, FixedSettings(LocalTime(4, 0)))
        val read = runBlocking { nightOwl.create("read", monday) }

        runBlocking { nightOwl.log(read, at(6, 1, 30)) }

        assertEquals(LocalDate(2026, 10, 5), runBlocking { nightOwl.presence(read, LocalDate(2026, 10, 6)) }.lastDate)
    }

    @Test
    fun aRatingOrChoiceHabitMustBeGivenAValue() {
        val mood = runBlocking { habits.create("mood", monday, type = TrackerType.RATING) }

        try {
            runBlocking { habits.log(mood, at(5, 9)) }
            fail("a rating habit took a Log with no rating")
        } catch (_: IllegalArgumentException) {
        }
        runBlocking { habits.log(mood, at(5, 9), rating = 4) }
    }

    @Test
    fun trackerAndReadingRulesHold() {
        val water = runBlocking { habits.create("water", monday, type = TrackerType.NUMBER, amountPerLog = 1.0) }
        val tracker = runBlocking { items.item(water) }!!.trackerId!!
        val log = runBlocking { habits.log(water, at(5, 9)) }

        refused("UPDATE tracker_reading SET bool_value = 1 WHERE id = '$log'")
        refused("UPDATE tracker_reading SET number_value = NULL WHERE id = '$log'")
        refused("UPDATE tracker SET type = 'TEXT' WHERE id = '$tracker'")
        refused("UPDATE tracker SET unit = 'CUSTOM' WHERE id = '$tracker'")
        refused("UPDATE item SET tracker_id = NULL WHERE id = '$water'")
    }

    @Test
    fun aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays() {
        val meds = runBlocking { habits.create("meds", monday, LocalTime(9, 0), Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY;BYHOUR=9,13,18;BYMINUTE=0")))) }
        val reminder = runBlocking { reminders.add(meds, 0) }

        runBlocking { habits.log(meds, at(5, 9, 5)) }

        assertEquals(at(5, 13), runBlocking { reminders.firings(after = at(5, 8)) }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun anOverdueRollingHabitFiresToday() {
        val clean = runBlocking { habits.create("clean", LocalDate(2026, 8, 1), LocalTime(9, 0), Recurrence.Rolling(7, RollUnit.DAY)) }
        val reminder = runBlocking { reminders.add(clean, 0) }
        runBlocking { habits.log(clean, LocalDateTime(2026, 9, 1, 10, 0)) }

        assertEquals(LocalDateTime(2026, 10, 2, 9, 0), runBlocking { reminders.firings(after = LocalDateTime(2026, 10, 2, 0, 0)) }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun aHabitMadeOnATrackerDeletedElsewhereCountsAsDeleted() {
        val w = World(tmp.root, 2)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val water = runBlocking { a.habits.create("water", monday, LocalTime(8, 0), everyTwoDays()) }
            w.settle(listOf(a, b))
            val tracker = runBlocking { a.items.item(water) }!!.trackerId!!

            runBlocking { a.trackers.delete(tracker) }
            val juice = runBlocking { b.habits.create("juice", monday, LocalTime(9, 0), everyTwoDays(), trackerId = tracker) }
            runBlocking { b.reminders.add(juice, 0) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                assertEquals(emptyList(), runBlocking { d.occurrences.occurrences(juice, at(5, 0), at(20, 0)) }, d.name)
                assertEquals(emptyList(), runBlocking { d.reminders.firings() }, d.name)
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aTrackersGoalsGoWithIt() {
        val water = runBlocking { habits.create("water", monday, type = TrackerType.NUMBER, amountPerLog = 1.0, dailyGoal = 8.0) }
        val tracker = runBlocking { items.item(water) }!!.trackerId!!

        runBlocking { trackers.delete(tracker) }
        assertEquals(emptyList(), runBlocking { trackers.goalsOf(tracker) })

        runBlocking { trackers.purge(tracker) }
        assertEquals(emptyList(), runBlocking { db.trackerDao().allGoals() })
    }

    @Test
    fun aSecondDailyGoalAChoiceHabitAndAValueOfTheWrongKindAreRefused() {
        val water = runBlocking { habits.create("water", monday, type = TrackerType.NUMBER, amountPerLog = 1.0, dailyGoal = 8.0) }
        val tracker = runBlocking { items.item(water) }!!.trackerId!!

        for (attempt in listOf<suspend () -> Unit>(
            { habits.create("juice", monday, trackerId = tracker, dailyGoal = 4.0) },
            { habits.create("colour", monday, type = TrackerType.CHOICE) },
            { habits.log(water, at(5, 9), yes = true) },
        )) {
            try {
                runBlocking { attempt() }
                fail("taken")
            } catch (_: IllegalArgumentException) {
            }
        }
    }

    @Test
    fun undoTakesTheLogMadeLastNotTheLatestTime() {
        val water = runBlocking { habits.create("water", monday, type = TrackerType.NUMBER, amountPerLog = 1.0) }
        runBlocking { habits.log(water, at(5, 20)) }
        runBlocking { habits.log(water, at(5, 9), number = 2.0) }

        runBlocking { habits.undo(water, monday) }

        assertEquals(Progress(1.0, null), runBlocking { habits.progress(water, monday) })
    }

    @Test
    fun aTaskWithoutAStatusIsRefused() {
        val task = runBlocking { items.createTask("call", monday) }

        refused("UPDATE item SET status = NULL WHERE id = '$task'")
    }

    @Test
    fun aHabitAndItsLogsReachAnotherDevice() {
        val w = World(tmp.root, 1)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val water = runBlocking { a.habits.create("water", monday, type = TrackerType.NUMBER, amountPerLog = 1.0, dailyGoal = 8.0) }
            runBlocking { repeat(3) { a.habits.log(water, at(5, 8 + it)) } }

            w.settle(listOf(a, b))

            assertEquals(Progress(3.0, 8.0), runBlocking { b.habits.progress(water, monday) })
        } finally {
            w.close()
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
