package com.factotum.data.item

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.factotum.core.recurrence.EditChanges
import com.factotum.core.recurrence.Patch
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.data.isConstraintViolation
import com.factotum.data.sync.World
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 11 through the real database and folder sync: edits made on two devices, then synced. */
class OccurrenceEditSyncTest {

    @get:Rule val tmp = TemporaryFolder()

    private val worlds = mutableListOf<World>()

    @After fun close() = worlds.forEach { it.close() }

    private val monday = LocalDate(2026, 10, 5)
    private val from = LocalDateTime(monday, LocalTime(0, 0))
    private val to = LocalDateTime(LocalDate(2026, 10, 26), LocalTime(0, 0))

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    /** Two devices that both hold the item [make] creates on the first. */
    private fun pair(make: suspend World.Device.() -> String): Triple<World.Device, World.Device, String> {
        val w = World(tmp.root, 1).also { worlds += it }
        val a = w.Device("A")
        val b = w.Device("B")
        val id = runBlocking { a.make() }
        w.settle(listOf(a, b))
        return Triple(a, b, id)
    }

    private suspend fun World.Device.weeklyReport() =
        items.createTask("Report", monday, LocalTime(9, 0), recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=TU"))))

    private suspend fun World.Device.stretch() =
        items.createEvent("Stretch", monday, LocalTime(8, 0), recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=MO,WE,FR"))))

    private fun World.Device.shown(id: String) = runBlocking { occurrences.occurrences(id, from, to) }

    private fun settle(vararg d: World.Device) = worlds.last().settle(d.toList())

    @Test
    fun sharedConcurrentMovesOnce_twoDevicesMovingOneOccurrenceLeaveItOnceAndAreAsked() {
        val (a, b, report) = pair { weeklyReport() }
        runBlocking { a.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 14)) }
        runBlocking { b.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 15)) }
        settle(a, b)

        for (d in listOf(a, b)) {
            assertEquals(3, d.shown(report).size, d.name)
            assertEquals(1, runBlocking { d.occurrences.questions() }.size, d.name)
        }
        assertEquals(a.shown(report), b.shown(report))
    }

    @Test
    fun tendrilConcurrentFieldEdits_aRetimeAndARenameBothHoldWithoutAQuestion() {
        val (a, b, stretch) = pair { stretch() }
        runBlocking { a.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(7, 30))) }
        runBlocking { b.occurrences.change(stretch, at(9, 8), EditChanges(title = "Stretch, slowly")) }
        settle(a, b)

        for (d in listOf(a, b)) {
            val friday = d.shown(stretch).single { it.original == at(9, 8) }
            assertEquals(at(9, 7, 30), friday.at)
            assertEquals("Stretch, slowly", friday.title)
            assertEquals(emptyList(), runBlocking { d.occurrences.questions() })
        }
    }

    @Test
    fun ownerOccurrenceClashAsks_andKeepingOneSettlesItEverywhere() {
        val (a, b, stretch) = pair { stretch() }
        runBlocking { a.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(7, 30))) }
        val bEdit = runBlocking { b.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(6, 45))) }
        settle(a, b)
        val question = runBlocking { a.occurrences.questions() }.single()

        runBlocking { a.occurrences.answer(question, OccurrenceAnswer.Keep(bEdit)) }
        settle(a, b)

        for (d in listOf(a, b)) {
            assertEquals(emptyList(), runBlocking { d.occurrences.questions() }, d.name)
            assertEquals(at(9, 6, 45), d.shown(stretch).single { it.original == at(9, 8) }.at, d.name)
        }
    }

    @Test
    fun keepingBothKeepsTwoOccurrences() {
        val (a, b, report) = pair { weeklyReport() }
        runBlocking { a.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 14)) }
        runBlocking { b.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 15)) }
        settle(a, b)

        runBlocking { b.occurrences.answer(b.occurrences.questions().single(), OccurrenceAnswer.KeepBoth) }
        settle(a, b)

        for (d in listOf(a, b)) {
            assertEquals(listOf(6, 14, 15, 20), d.shown(report).map { it.at.date.day }, d.name)
            assertEquals(emptyList(), runBlocking { d.occurrences.questions() }, d.name)
        }
    }

    @Test
    fun twoDevicesAnsweringDifferentlyAreAskedAgain() {
        val (a, b, stretch) = pair { stretch() }
        val aEdit = runBlocking { a.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(7, 30))) }
        val bEdit = runBlocking { b.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(6, 45))) }
        settle(a, b)

        runBlocking { a.occurrences.answer(a.occurrences.questions().single(), OccurrenceAnswer.Keep(aEdit)) }
        runBlocking { b.occurrences.answer(b.occurrences.questions().single(), OccurrenceAnswer.Keep(bEdit)) }
        settle(a, b)

        for (d in listOf(a, b)) assertEquals(1, runBlocking { d.occurrences.questions() }.size, d.name)
        assertEquals(a.shown(stretch), b.shown(stretch))
    }

    @Test
    fun twoDevicesKeepingBothMakeOneAddedOccurrence() {
        val (a, b, report) = pair { weeklyReport() }
        runBlocking { a.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 14)) }
        runBlocking { b.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 15)) }
        settle(a, b)

        runBlocking { a.occurrences.answer(a.occurrences.questions().single(), OccurrenceAnswer.KeepBoth) }
        runBlocking { b.occurrences.answer(b.occurrences.questions().single(), OccurrenceAnswer.KeepBoth) }
        settle(a, b)

        for (d in listOf(a, b)) {
            assertEquals(listOf(6, 14, 15, 20), d.shown(report).map { it.at.date.day }, d.name)
            assertEquals(emptyList(), runBlocking { d.occurrences.questions() }, d.name)
        }
    }

    @Test
    fun keepingOneEditsTimeStillMergesTheOthersTitle() {
        val (a, b, stretch) = pair { stretch() }
        val aEdit = runBlocking { a.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(7, 30))) }
        runBlocking { b.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(6, 45), title = "Stretch, slowly")) }
        settle(a, b)

        runBlocking { a.occurrences.answer(a.occurrences.questions().single(), OccurrenceAnswer.Keep(aEdit)) }
        settle(a, b)

        val friday = b.shown(stretch).single { it.original == at(9, 8) }
        assertEquals(at(9, 7, 30), friday.at)
        assertEquals("Stretch, slowly", friday.title)
    }

    @Test
    fun anEditIsWrittenOnceAndUndoneOnce() {
        val (a, _, report) = pair { weeklyReport() }
        val skip = runBlocking { a.occurrences.skip(report, at(13, 9)) }

        refused(a, "UPDATE occurrence_edit SET changes = '{\"time\":\"11:00\"}' WHERE id = '$skip'")
        runBlocking { a.occurrences.undo(skip) }
        refused(a, "UPDATE occurrence_edit SET deleted_at = NULL WHERE id = '$skip'")
    }

    @Test
    fun twoOccurrencesOnOneDayAreResolvedApart() {
        val (a, _, meds) = pair {
            items.createTask("meds", monday, recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY;BYHOUR=8,20;BYMINUTE=0"))))
        }
        runBlocking { a.reminders.add(meds, 0) }

        runBlocking { a.items.resolve(meds, at(5, 8), Outcome.DONE) }

        assertEquals(at(5, 20), runBlocking { a.reminders.firings() }.single().at)
    }

    @Test
    fun anAddedOccurrenceOnAWholeDayItemFiresAtTheAnchor() {
        val (a, _, bins) = pair { items.createTask("bins", monday) }
        runBlocking { a.reminders.add(bins, -24 * 60, anchor = LocalTime(20, 0)) }

        runBlocking { a.occurrences.add(bins, LocalDateTime(LocalDate(2026, 10, 9), LocalTime(0, 0))) }

        assertEquals(listOf(at(4, 20), at(8, 20)), runBlocking { a.reminders.firings().map { it.at } + a.reminders.firings(after = at(4, 20)).map { it.at } })
    }

    @Test
    fun aRetimeMadeAfterSeeingTheOtherIsACorrectionNotAClash() {
        val (a, b, stretch) = pair { stretch() }
        runBlocking { a.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(7, 30))) }
        settle(a, b)
        runBlocking { b.occurrences.change(stretch, at(9, 8), EditChanges(time = LocalTime(6, 45))) }
        settle(a, b)

        assertEquals(emptyList(), runBlocking { a.occurrences.questions() })
        assertEquals(at(9, 6, 45), a.shown(stretch).single { it.original == at(9, 8) }.at)
    }

    @Test
    fun undoingASkipBringsTheOccurrenceBackEverywhere() {
        val (a, b, stretch) = pair { stretch() }
        val skip = runBlocking { a.occurrences.skip(stretch, at(7, 8)) }
        settle(a, b)
        assertTrue(b.shown(stretch).none { it.original == at(7, 8) })

        runBlocking { a.occurrences.undo(skip) }
        settle(a, b)

        assertTrue(b.shown(stretch).any { it.original == at(7, 8) })
    }

    @Test
    fun sharedOneMechanism_tasksEventsAndRemindersEditOneLog() {
        val (a, _, report) = pair { weeklyReport() }
        val stretch = runBlocking { a.stretch() }
        val pills = runBlocking { a.reminders.createStandalone("pills", monday, LocalTime(8, 0), recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY")))) }

        runBlocking {
            a.occurrences.skip(report, at(13, 9))
            a.occurrences.skip(stretch, at(7, 8))
            a.occurrences.skip(pills, at(6, 8))
        }

        assertEquals(setOf(report, stretch, pills), runBlocking { a.db.itemDao().liveEdits() }.map { it.itemId }.toSet())
    }

    @Test
    fun thisWeekAndFromNowOnWorkOnTasksToo() {
        val (a, _, report) = pair { weeklyReport() }
        runBlocking {
            a.occurrences.thisWeek(report, LocalDate(2026, 10, 12), EditChanges(time = LocalTime(11, 0)))
            a.occurrences.fromNowOn(report, LocalDate(2026, 10, 19), EditChanges(title = "Weekly report"))
        }

        val shown = a.shown(report)
        assertEquals(listOf(at(6, 9), at(13, 11), at(20, 9)), shown.map { it.at })
        assertEquals(listOf("Report", "Report", "Weekly report"), shown.map { it.title })
    }

    @Test
    fun aConfirmedWeekReplacesThatWeeksDays() {
        val (a, _, stretch) = pair { stretch() }

        runBlocking { a.occurrences.confirmWeek(stretch, monday, setOf(DayOfWeek.TUESDAY, DayOfWeek.SATURDAY)) }

        assertEquals(listOf(6, 10, 12, 14, 16), a.shown(stretch).map { it.at.date.day }.take(5))
    }

    @Test
    fun aSkippedOccurrenceDoesNotFireAndAMovedOneFiresAtItsNewTime() {
        val (a, _, report) = pair { weeklyReport() }
        val reminder = runBlocking { a.reminders.add(report, -15) }
        runBlocking {
            a.occurrences.skip(report, at(6, 9))
            a.occurrences.move(report, at(13, 9), LocalDate(2026, 10, 14), LocalTime(16, 0))
        }

        val first = runBlocking { a.reminders.firings() }.single { it.reminderId == reminder }.at
        val second = runBlocking { a.reminders.firings(after = first) }.single { it.reminderId == reminder }.at

        assertEquals(at(14, 15, 45), first)
        assertEquals(at(20, 8, 45), second)
    }

    @Test
    fun anEditMustNameWhatItsScopeCovers() {
        val (a, _, report) = pair { weeklyReport() }
        fun insert(scope: String, at: String?, date: String?, days: Int) =
            "INSERT INTO occurrence_edit(id, item_id, scope, at, date, days, changes, created_hlc, created_device, seen, hlc, device) " +
                "VALUES ('bad', '$report', '$scope', ${at?.let { "'$it'" } ?: "NULL"}, ${date?.let { "'$it'" } ?: "NULL"}, $days, '{}', 1, 'A', '', 1, 'A')"

        refused(a, insert("OCCURRENCE", null, null, 0))
        refused(a, insert("MONTH", "2026-10-13T09:00", null, 0))
        refused(a, insert("OCCURRENCE", "2026-10-13T09:00", null, 3))
        refused(a, insert("FROM", "2026-10-13T09:00", "2026-10-13", 0))
    }

    @Test
    fun habitFieldsThisVersionDoesNotApplyArriveIntact() {
        val changes = EditChanges(time = LocalTime(7, 0), block = Patch("Evening"), others = mapOf("sort_order" to "2.5", "rule_patch" to """{"n":3,"days":[1,3]}"""))

        val back = EditCodec.decode(EditCodec.encode(changes))

        assertEquals(changes, back)
    }

    private fun refused(d: World.Device, sql: String) {
        try {
            runBlocking { d.db.useWriterConnection { it.execSQL(sql) } }
        } catch (e: Exception) {
            if (isConstraintViolation(e)) return
            throw e
        }
        fail("the database took: $sql")
    }
}
