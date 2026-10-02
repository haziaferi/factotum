package com.factotum.data.item

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.core.plan.PlanDay
import com.factotum.core.plan.WeekSuggestion
import com.factotum.core.recurrence.EditChanges
import com.factotum.core.recurrence.Patch
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.slotTime
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.createAtVersion
import com.factotum.data.isConstraintViolation
import com.factotum.data.openFactotumDatabase
import com.factotum.data.reminder.ReminderRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import com.factotum.data.tracker.TrackerRepository
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.DayOfWeek
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

/** ADR 06's part b on the real database: the time blocks, the PLANNED kind and the week's plan (Tendril's planner). */
class PlannerCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var habits: HabitRepository
    private lateinit var trackers: TrackerRepository
    private lateinit var occurrences: OccurrenceRepository
    private lateinit var reminders: ReminderRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "plan.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        habits = HabitRepository(db, writes, newId)
        trackers = TrackerRepository(db, writes, newId)
        occurrences = OccurrenceRepository(db, writes, newId)
        reminders = ReminderRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun day(d: Int) = LocalDate(2026, 10, d)

    private fun plan() = runBlocking { habits.planWeek(monday) }

    private fun PlanDay.where(id: String): List<String> =
        blocks.flatMap { b -> (b.timed + b.flexible).filter { it.itemId == id }.map { b.block.id } } +
            outside.filter { it.itemId == id }.map { "outside" } + anyTime.filter { it.itemId == id }.map { "any" }

    private fun onDay(d: Int, id: String) = plan().days.single { it.date == day(d) }.where(id)

    private fun daily() = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))

    private fun threeAWeek() = Recurrence.Planned(3, Recurrence.Planned.Per.WEEK, days = setOf(DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY))

    @Test
    fun aNewDatabaseHasTendrilsFiveBlocks() {
        val blocks = runBlocking { habits.blocks() }

        assertEquals(listOf("block-morning", "block-midday", "block-afternoon", "block-evening", "block-night"), blocks.map { it.id })
        assertEquals(listOf(390 to 540, 540 to 780, 780 to 1080, 1080 to 1290, 1290 to 1410), blocks.map { it.start to it.end })
    }

    @Test
    fun twoDevicesSeedTheSameBlocksAndAnEditOnOneReachesTheOther() {
        val w = World(tmp.root, 3)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            runBlocking { a.habits.retimeBlock("block-morning", 420, 540) }
            val walk = runBlocking { b.habits.addBlock(600, 660, "Walk") }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                val blocks = runBlocking { d.habits.blocks() }
                assertEquals(6, blocks.size)
                assertEquals(420, blocks.single { it.id == "block-morning" }.start)
                assertEquals(5, blocks.single { it.id == walk }.position)
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun aDatabaseUpgradedToTimeBlocksGetsTheDefaults() {
        // A version 7 file as Room's exported schema describes it, which Room then migrates on open.
        val file = File(tmp.root, "v7.db")
        createAtVersion(file, 7)

        val upgraded = openFactotumDatabase(file).database
        try {
            assertEquals(DEFAULT_BLOCKS, runBlocking { upgraded.itemDao().liveBlocks() })
        } finally {
            upgraded.close()
        }
    }

    @Test
    fun nADayIsSpreadOverTheBlocksAndATimedHabitSitsInTheBlockThatHoldsIt() {
        val water = runBlocking { habits.create("water", monday, recurrence = Recurrence.Planned(3, Recurrence.Planned.Per.DAY)) }
        val run = runBlocking { habits.create("run", monday, LocalTime(18, 30), daily()) }

        assertEquals(listOf("block-morning", "block-afternoon", "block-night"), onDay(6, water))
        assertEquals(listOf("block-evening"), onDay(6, run))
    }

    @Test
    fun aWeekdayTimeAndADeletedBlockMoveWhatSitsInThem() {
        val read = runBlocking { habits.create("read", monday, LocalTime(9, 30), daily()) }
        val stretch = runBlocking { habits.create("stretch", monday, recurrence = daily(), blockId = "block-evening") }

        runBlocking { habits.retimeBlock("block-morning", 480, 630, on = setOf(DayOfWeek.SATURDAY, DayOfWeek.SUNDAY)) }
        runBlocking { habits.deleteBlock("block-evening") }

        assertEquals(listOf("block-midday"), onDay(9, read))
        assertEquals(listOf("block-morning"), onDay(10, read))
        assertEquals(listOf("any"), onDay(9, stretch))
    }

    @Test
    fun anNAWeekHabitIsSuggestedUntilThisWeekIsConfirmedThenPlaced() {
        val gym = runBlocking { habits.create("gym", monday, recurrence = threeAWeek(), blockId = "block-evening", durationMin = 60) }
        runBlocking { occurrences.confirmWeek(gym, LocalDate(2026, 10, 12), setOf(DayOfWeek.MONDAY)) }
        val before = plan()

        assertEquals(listOf(WeekSuggestion(gym, listOf(day(5), day(9), day(10)))), before.suggestions)
        assertTrue(before.days.all { it.where(gym).isEmpty() })

        runBlocking { occurrences.confirmWeek(gym, monday, setOf(DayOfWeek.WEDNESDAY, DayOfWeek.SATURDAY)) }
        val after = plan()

        assertEquals(emptyList(), after.suggestions)
        assertEquals(listOf(7, 10), after.days.filter { it.where(gym).isNotEmpty() }.map { it.date.day })
    }

    @Test
    fun aSuggestionAvoidsTheDaysOtherHabitsFillAndThePausedOnes() {
        runBlocking { habits.create("swim", monday, recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=TU"))), durationMin = 90) }
        val gym = runBlocking { habits.create("gym", monday, recurrence = Recurrence.Planned(2, Recurrence.Planned.Per.WEEK), durationMin = 60) }
        runBlocking { habits.pause(gym, day(10)) }
        runBlocking { occurrences.thisDay(gym, day(8), EditChanges(skip = true)) }

        // Four days left (Monday to Friday less Thursday's skip); spread(4, 2) picks the 2nd and 4th,
        // Tuesday and Friday, and the rotation moves off Tuesday's swim to Wednesday and Monday.
        assertEquals(listOf(WeekSuggestion(gym, listOf(day(5), day(7)))), plan().suggestions)
    }

    @Test
    fun anOccurrencesBlockTravelsInItsEditAndNoneMeansAnyTime() {
        val pills = runBlocking { habits.create("pills", monday, recurrence = Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("block-morning", "block-night"))) }

        runBlocking { occurrences.change(pills, LocalDateTime(day(6), slotTime(0)), EditChanges(block = Patch("block-midday"))) }
        runBlocking { occurrences.change(pills, LocalDateTime(day(6), slotTime(1)), EditChanges(block = Patch(null))) }

        assertEquals(listOf("block-midday", "any"), onDay(6, pills))
        assertEquals(listOf("block-morning", "block-night"), onDay(7, pills))
        assertEquals(EditChanges(block = Patch(null)), EditCodec.decode(EditCodec.encode(EditChanges(block = Patch(null)))))
        assertEquals(EditChanges(), EditCodec.decode(EditCodec.encode(EditChanges())))
    }

    @Test
    fun aWholeDayOccurrenceIsPausedOnItsOwnDateWhenTheDayStartsLater() {
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val nightOwl = HabitRepository(db, writes, { "owl-${n++}" }, dayStart = LocalTime(4, 0))
        val pills = runBlocking { nightOwl.create("pills", monday, recurrence = Recurrence.Planned(2, Recurrence.Planned.Per.DAY)) }
        runBlocking { nightOwl.pause(pills, day(7)) }

        val days = runBlocking { nightOwl.planWeek(monday) }.days.filter { it.where(pills).isNotEmpty() }.map { it.date.day }

        assertEquals(listOf(5, 6), days)
    }

    @Test
    fun aPausedHabitAndOneWhoseTrackerIsDeletedAreNotPlanned() {
        val water = runBlocking { habits.create("water", monday, recurrence = daily(), blockId = "block-morning") }
        val tea = runBlocking { habits.create("tea", monday, recurrence = daily(), blockId = "block-morning") }
        runBlocking { habits.pause(water, day(8), day(9)) }
        runBlocking { trackers.delete(requireNotNull(db.itemDao().items(listOf(tea)).single().trackerId)) }

        assertEquals(listOf(5, 6, 7, 10, 11), plan().days.filter { it.where(water).isNotEmpty() }.map { it.date.day })
        assertTrue(plan().days.all { it.where(tea).isEmpty() })
    }

    @Test
    fun twoHabitsOnOneTrackerPauseOnTheirOwn() {
        val water = runBlocking { habits.create("water", monday, LocalTime(8, 0), daily()) }
        val tracker = requireNotNull(runBlocking { db.itemDao().items(listOf(water)) }.single().trackerId)
        val evening = runBlocking { habits.create("evening water", monday, LocalTime(20, 0), daily(), trackerId = tracker) }
        runBlocking { reminders.add(water, 0) }
        runBlocking { reminders.add(evening, 0) }

        runBlocking { habits.pause(water, monday) }

        assertEquals(emptyList(), runBlocking { occurrences.occurrences(water, LocalDateTime(day(5), LocalTime(0, 0)), LocalDateTime(day(6), LocalTime(0, 0))) })
        assertEquals(1, runBlocking { occurrences.occurrences(evening, LocalDateTime(day(5), LocalTime(0, 0)), LocalDateTime(day(6), LocalTime(0, 0))) }.size)
        assertEquals(listOf(evening), runBlocking { reminders.firings(LocalDateTime(day(5), LocalTime(0, 0))) }.map { it.itemId }.distinct())
    }

    private fun nextFirings(count: Int, from: LocalDateTime): List<LocalDateTime> = runBlocking {
        buildList {
            var after = from
            repeat(count) { after = reminders.firings(after).single().at.also(::add) }
        }
    }

    @Test
    fun anNADayHabitRemindsAtTheStartOfEachOfItsBlocks() {
        val water = runBlocking { habits.create("water", monday, recurrence = Recurrence.Planned(3, Recurrence.Planned.Per.DAY)) }
        runBlocking { reminders.add(water, -10, anchor = LocalTime(12, 0)) }

        assertEquals(
            listOf(LocalDateTime(day(5), LocalTime(6, 20)), LocalDateTime(day(5), LocalTime(12, 50)), LocalDateTime(day(5), LocalTime(21, 20)), LocalDateTime(day(6), LocalTime(6, 20))),
            nextFirings(4, LocalDateTime(day(5), LocalTime(0, 0))),
        )
    }

    @Test
    fun aLoggedOccurrenceIsQuietAndABlocksOwnDayAndOrderAreFollowed() {
        val pills = runBlocking { habits.create("pills", monday, recurrence = Recurrence.Planned(2, Recurrence.Planned.Per.DAY, blocks = listOf("block-night", "block-morning"))) }
        runBlocking { reminders.add(pills, 0) }
        runBlocking { habits.log(pills, LocalDateTime(day(5), LocalTime(7, 0)), occurrence = LocalDateTime(day(5), slotTime(1))) }
        runBlocking { habits.retimeBlock("block-morning", 480, 540, on = setOf(DayOfWeek.TUESDAY)) }

        assertEquals(
            listOf(LocalDateTime(day(5), LocalTime(21, 30)), LocalDateTime(day(6), LocalTime(8, 0)), LocalDateTime(day(6), LocalTime(21, 30))),
            nextFirings(3, LocalDateTime(day(5), LocalTime(0, 0))),
        )
    }

    @Test
    fun anOccurrenceWithNoBlockRemindsAtTheAnchor() {
        val water = runBlocking { habits.create("water", monday, recurrence = Recurrence.Planned(1, Recurrence.Planned.Per.DAY, blocks = listOf("block-evening"))) }
        runBlocking { reminders.add(water, 0, anchor = LocalTime(12, 0)) }
        runBlocking { habits.deleteBlock("block-evening") }

        assertEquals(listOf(LocalDateTime(day(5), LocalTime(12, 0))), nextFirings(1, LocalDateTime(day(5), LocalTime(0, 0))))
    }

    @Test
    fun plannedAndBlockRulesHold() {
        val gym = runBlocking { habits.create("gym", monday, recurrence = threeAWeek()) }
        val task = "INSERT INTO item (id, kind, title, details_hlc, details_device, start_date, schedule_hlc, schedule_device, status, importance, status_hlc, status_device, " +
            "recurrence_kind, plan_n, plan_per, plan_days) VALUES ('t', 'TASK', 't', 1, 'A', '2026-10-05', 1, 'A', 'PENDING', 0, 1, 'A', 'PLANNED', 2, 'WEEK', 127)"
        refused(task)
        refused("UPDATE item SET plan_n = 8 WHERE id = '$gym'")
        refused("UPDATE item SET plan_days = 0 WHERE id = '$gym'")
        refused("UPDATE item SET plan_blocks = 'block-morning' WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'MONTH' WHERE id = '$gym'")
        refused("UPDATE item SET recurrence_kind = 'RRULE', rrule = 'FREQ=DAILY' WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'DAY', plan_n = 2, plan_blocks = 'block-morning' WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'DAY', plan_n = 49 WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'DAY', plan_n = 2, start_time = '08:00' WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'DAY', plan_n = 2, plan_blocks = 'block-morning,' WHERE id = '$gym'")
        refused("UPDATE item SET plan_per = 'DAY', plan_n = 3, plan_blocks = 'block-morning,,block-night' WHERE id = '$gym'")
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE item SET plan_per = 'DAY', plan_n = 2, plan_blocks = 'block-morning,block-night' WHERE id = '$gym'") } }

        refused("UPDATE habit_block SET end_minute = 300 WHERE id = 'block-morning'")
        refused("UPDATE habit_block SET end_minute = 1441 WHERE id = 'block-night'")
        refused("UPDATE habit_block SET start_minute = -1 WHERE id = 'block-morning'")
        val kept = runBlocking { db.useReaderConnection { c -> c.usePrepared("SELECT count(*) FROM habit_block") { it.step(); it.getLong(0) } } }
        assertEquals(5, kept)
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
