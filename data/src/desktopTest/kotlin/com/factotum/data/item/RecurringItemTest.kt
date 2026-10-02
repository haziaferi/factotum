package com.factotum.data.item

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.core.recurrence.Cron
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.FixedSettings
import com.factotum.data.SYNCED_TABLES
import com.factotum.data.isConstraintViolation
import com.factotum.data.openFactotumDatabase
import com.factotum.data.reminder.ReminderRepository
import com.factotum.data.sync.loadClock
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
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 04 on items: the recurrence columns, their rules, expansion, and reminders on repeating items. */
class RecurringItemTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private lateinit var reminders: ReminderRepository
    private lateinit var occurrences: OccurrenceRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "recurring.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        items = ItemRepository(db, writes, newId)
        reminders = ReminderRepository(db, writes, newId, FixedSettings())
        occurrences = OccurrenceRepository(db, writes, newId, FixedSettings())
    }

    private fun occurrencesOf(id: String, from: LocalDateTime, to: LocalDateTime) = runBlocking { occurrences.occurrences(id, from, to) }.map { it.at }

    @After fun close() = db.close()

    private fun rule(text: String) = Recurrence.Rule(requireNotNull(RRule.parse(text)))

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    @Test
    fun eachKindIsStoredAndReadBack() {
        val kinds = listOf(
            rule("FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261101T235900"),
            requireNotNull(Cron.toRecurrence("0 9 1 * 1")),
            Recurrence.RandomDays(2, 4),
            Recurrence.RandomWindow(setOf(DayOfWeek.MONDAY, DayOfWeek.FRIDAY), LocalTime(10, 0), LocalTime(12, 0)),
        )
        for (r in kinds) {
            val id = runBlocking { items.createTask("t", MONDAY, LocalTime(9, 0), recurrence = r) }
            assertEquals(r, runBlocking { items.item(id) }?.recurrence)
        }
    }

    @Test
    fun aRepeatingItemExpandsFromItsStart() {
        val id = runBlocking { items.createEvent("standup", MONDAY, LocalTime(10, 0), recurrence = rule("FREQ=WEEKLY;BYDAY=MO,WE")) }

        val got = occurrencesOf(id, at(5, 0), at(15, 0))

        assertEquals(listOf(at(5, 10), at(7, 10), at(12, 10), at(14, 10)), got)
    }

    @Test
    fun aOneOffItemHasItsStartAsItsOnlyOccurrence() {
        val id = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }

        assertEquals(listOf(at(5, 14)), occurrencesOf(id, at(1, 0), at(30, 0)))
    }

    @Test
    fun reschedulingKeepsTheRecurrenceAndMovesItsStart() {
        val id = runBlocking { items.createTask("plants", MONDAY, LocalTime(9, 0), recurrence = rule("FREQ=DAILY;INTERVAL=3")) }

        runBlocking { items.reschedule(id, LocalDate(2026, 10, 6), LocalTime(9, 0)) }

        assertEquals(listOf(at(6, 9), at(9, 9)), occurrencesOf(id, at(1, 0), at(10, 0)))
    }

    @Test
    fun anUndatedItemCannotRepeat() {
        val id = runBlocking { items.createTask("someday") }

        assertFailsWith<IllegalArgumentException> { runBlocking { items.setRecurrence(id, rule("FREQ=DAILY")) } }
    }

    @Test
    fun eachKindKeepsToItsOwnColumns() {
        val id = runBlocking { items.createTask("t", MONDAY, LocalTime(9, 0)) }

        refused("UPDATE item SET recurrence_kind = 'RRULE' WHERE id = '$id'")
        refused("UPDATE item SET rrule = 'FREQ=DAILY' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_DAYS', rand_min_days = 0, rand_max_days = 2 WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_DAYS', rand_min_days = 3, rand_max_days = 2 WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_WINDOW', window_days = 0, window_start = '10:00', window_end = '12:00' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'CRON', rrule = '* * * * *' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RRULE', rrule = 'FREQ=DAILY', rand_min_days = 2, rand_max_days = 3 WHERE id = '$id'")
        refused("UPDATE item SET start_date = NULL, start_time = NULL, recurrence_kind = 'RRULE', rrule = 'FREQ=DAILY' WHERE id = '$id'")
    }

    @Test
    fun sharedOneRecurrenceHome_onlyTheItemTableHoldsARepeat() {
        val holding = SYNCED_TABLES.filter { table ->
            val columns = runBlocking { db.useReaderConnection { c -> c.usePrepared("PRAGMA table_info($table)") { s -> buildList { while (s.step()) add(s.getText(1)) } } } }
            columns.any { it == "rrule" || it == "recurrence_kind" }
        }

        assertEquals(listOf(ITEM), holding)
    }

    @Test
    fun chronicleStandaloneRepeats_aDailyReminderFiresAgainTomorrow() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0), recurrence = rule("FREQ=DAILY")) }

        assertEquals(rule("FREQ=DAILY"), runBlocking { items.item(pills) }?.recurrence)
        assertEquals(at(5, 8), runBlocking { reminders.firings() }.single().at)
        assertEquals(at(6, 8), runBlocking { reminders.firings(after = at(5, 8)) }.single().at)
    }

    @Test
    fun aResolvedOccurrenceDoesNotFire() {
        val task = runBlocking { items.createTask("plants", MONDAY, LocalTime(9, 0), recurrence = rule("FREQ=DAILY")) }
        val reminder = runBlocking { reminders.add(task, -15) }

        runBlocking { items.resolve(task, at(5, 9), Outcome.DONE) }

        assertEquals(at(6, 8, 45), runBlocking { reminders.firings() }.single { it.reminderId == reminder }.at)
    }

    @Test
    fun aSnoozeOfOneOccurrenceLeavesTheNextAlone() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0), recurrence = rule("FREQ=DAILY")) }
        val reminder = runBlocking { reminders.remindersOf(pills) }.single()

        runBlocking { reminders.snooze(reminder, at(5, 8), at(5, 8, 30)) }

        assertEquals(at(5, 8, 30), runBlocking { reminders.firings(after = at(5, 8)) }.single().at)
        assertEquals(at(6, 8), runBlocking { reminders.firings(after = at(5, 8, 30)) }.single().at)
    }

    @Test
    fun aWholeDayRepeatingTaskFiresAtTheReminderAnchor() {
        val task = runBlocking { items.createTask("bins", MONDAY, recurrence = rule("FREQ=WEEKLY")) }
        runBlocking { reminders.add(task, -24 * 60, anchor = LocalTime(20, 0)) }

        assertEquals(LocalDateTime(2026, 10, 11, 20, 0), runBlocking { reminders.firings(after = at(4, 21)) }.single().at)
    }

    @Test
    fun aWholeDayItemRemindedBeforeItsAnchorStillFiresLaterThatDay() {
        val task = runBlocking { items.createTask("water plants", MONDAY, recurrence = rule("FREQ=DAILY")) }
        runBlocking { reminders.add(task, -10, anchor = LocalTime(12, 0)) }

        assertEquals(at(5, 11, 50), runBlocking { reminders.firings(after = at(5, 8)) }.single().at)
    }

    @Test
    fun aWholeDayItemWhoseRuleSetsTimesFiresAtThem() {
        val task = runBlocking { items.createTask("meds", MONDAY, recurrence = rule("FREQ=DAILY;BYHOUR=8,20;BYMINUTE=0")) }
        runBlocking { reminders.add(task, 0) }

        assertEquals(at(5, 8), runBlocking { reminders.firings() }.single().at)
        assertEquals(at(5, 20), runBlocking { reminders.firings(after = at(5, 8)) }.single().at)
    }

    @Test
    fun aRuleThisVersionCannotReadSilencesOnlyItsOwnReminder() {
        val good = runBlocking { reminders.createStandalone("good", MONDAY, LocalTime(8, 0)) }
        val bad = runBlocking { reminders.createStandalone("from a newer peer", MONDAY, LocalTime(9, 0), recurrence = rule("FREQ=DAILY")) }
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE item SET rrule = 'FREQ=DAILY;BYWEEKNO=3' WHERE id = '$bad'") } }

        assertEquals(listOf(good), runBlocking { reminders.firings() }.map { it.itemId })
    }

    @Test
    fun noColumnOfARecurrenceKindStandsAlone() {
        val id = runBlocking { items.createTask("t", MONDAY, LocalTime(9, 0)) }

        refused("UPDATE item SET rand_min_days = 3 WHERE id = '$id'")
        refused("UPDATE item SET window_start = '10:00' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RULE_SET', rrule = 'FREQ=DAILY' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_WINDOW', window_days = 1, window_start = '12:00', window_end = '10:00' WHERE id = '$id'")
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

    private companion object {
        val MONDAY = LocalDate(2026, 10, 5)
    }
}
