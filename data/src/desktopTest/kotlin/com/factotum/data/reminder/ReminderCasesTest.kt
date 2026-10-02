package com.factotum.data.reminder

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.FixedSettings
import com.factotum.data.isConstraintViolation
import com.factotum.data.item.ItemKind
import com.factotum.data.item.ItemRepository
import com.factotum.data.item.TaskStatus
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.loadClock
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
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 03's cases (`decisions/cases/03-reminder.jsonl`) against the real database and repositories. */
class ReminderCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private lateinit var reminders: ReminderRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "reminders.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        items = ItemRepository(db, writes, newId)
        reminders = ReminderRepository(db, writes, newId, FixedSettings())
    }

    @After fun close() = db.close()

    private fun firesAt(reminderId: String): LocalDateTime? = runBlocking { reminders.firings() }.singleOrNull { it.reminderId == reminderId }?.at

    @Test
    fun tendrilFollowsItem_aReminderMovesWithItsTask() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }
        assertEquals(LocalDateTime(MONDAY, LocalTime(13, 55)), firesAt(reminder))

        runBlocking { items.reschedule(task, MONDAY, LocalTime(16, 0)) }

        assertEquals(LocalDateTime(MONDAY, LocalTime(15, 55)), firesAt(reminder))
    }

    @Test
    fun tendrilAnchorDateOnly_theDayBeforeAtNine() {
        val task = runBlocking { items.createTask("tax form", MONDAY) }

        val reminder = runBlocking { reminders.add(task, -24 * 60, anchor = LocalTime(9, 0)) }

        assertEquals(LocalDateTime(LocalDate(2026, 10, 4), LocalTime(9, 0)), firesAt(reminder))
    }

    @Test
    fun tendrilCascade_aDeletedTaskSilencesItsReminderAndAPurgedOneRemovesIt() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }

        runBlocking { items.delete(task) }
        assertEquals(null, firesAt(reminder))

        runBlocking { items.purge(task) }
        assertEquals(null, runBlocking { reminders.alertOf(reminder) })
    }

    @Test
    fun tendrilQuietWhenDone_aDoneTasksReminderNoLongerFires() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }

        runBlocking { items.setStatus(task, TaskStatus.DONE) }

        assertEquals(null, firesAt(reminder))
    }

    @Test
    fun chronicleStandalone_aReminderWithNothingOnTheCalendarFiresWithItsText() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }

        val item = runBlocking { items.item(pills) }!!
        assertEquals(ItemKind.REMINDER, item.kind)
        assertEquals("take pills", item.title)
        assertEquals(listOf(LocalDateTime(MONDAY, LocalTime(8, 0))), runBlocking { reminders.firings() }.map { it.at })
    }

    @Test
    fun chronicleAlertSettings_storedPerReminderAndUnknownValuesRefused() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val alarm = Alert(AlertKind.ALARM, nagRepeats = 3, nagMinutes = 10, sound = "", vibration = "long", mode = AlertMode.ALERT, skin = "dark", exact = true)

        val reminder = runBlocking { reminders.add(task, -5, alert = alarm) }

        assertEquals(alarm, runBlocking { reminders.alertOf(reminder) })
        refused("UPDATE reminder SET alert_kind = 'SIREN' WHERE id = '$reminder'")
        refused("UPDATE reminder SET mode = 'LOUD' WHERE id = '$reminder'")
        refused("UPDATE reminder SET nag_repeats = -1 WHERE id = '$reminder'")
    }

    @Test
    fun mnemoStandaloneDone_theRowStaysAndStopsFiring() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }

        runBlocking { items.setStatus(pills, TaskStatus.DONE) }

        assertEquals(TaskStatus.DONE, runBlocking { items.item(pills) }?.status)
        assertEquals(1, runBlocking { reminders.remindersOf(pills) }.size)
        assertEquals(emptyList(), runBlocking { reminders.firings() })
    }

    @Test
    fun sharedNoHalfLink_aReminderNamingNoItemOrAMissingOneIsRefused() {
        refused(
            "INSERT INTO reminder(id, item_id, offset_min, alert_kind, nag_repeats, mode, exact, alert_hlc, alert_device, status_hlc, status_device) " +
                "VALUES ('r', NULL, 0, 'NOTIFICATION', 0, 'SCHEDULE', 0, 1, 'A', 1, 'A')",
        )
        // ADR 02's tendril-reminder-fk: the foreign key refuses a reminder on an item that is not there.
        refused(
            "INSERT INTO reminder(id, item_id, offset_min, alert_kind, nag_repeats, mode, exact, alert_hlc, alert_device, status_hlc, status_device) " +
                "VALUES ('r', 'nothing', 0, 'NOTIFICATION', 0, 'SCHEDULE', 0, 1, 'A', 1, 'A')",
        )
    }

    @Test
    fun sharedOneRecurrenceHome_theReminderTableHoldsNoRepeat() {
        val columns = runBlocking {
            db.useReaderConnection { c -> c.usePrepared("PRAGMA table_info(reminder)") { s -> buildList { while (s.step()) add(s.getText(1)) } } }
        }

        // nag_repeats counts a nag's repeats within one firing; it is not a recurrence.
        assertTrue(columns.none { it.startsWith("repeat") || "rrule" in it || "recur" in it }, columns.toString())
    }

    @Test
    fun sharedTimelineUnchanged_standaloneRemindersShowOnlyWhenAsked() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }

        assertEquals(listOf(task), runBlocking { items.day(MONDAY, showReminders = false) }.map { it.id })
        assertEquals(listOf(pills, task), runBlocking { items.day(MONDAY, showReminders = true) }.map { it.id })
    }

    @Test
    fun aReminderOnAnItemWithNoDateIsRefused() {
        val task = runBlocking { items.createTask("someday") }

        assertFailsWith<IllegalArgumentException> { runBlocking { reminders.add(task, -5) } }
    }

    @Test
    fun aSnoozeMovesTheFiringAndLeavesTheItemsTimeAlone() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }

        runBlocking { reminders.snooze(reminder, firesAt(reminder)!!, LocalDateTime(MONDAY, LocalTime(14, 10))) }

        assertEquals(LocalDateTime(MONDAY, LocalTime(14, 10)), firesAt(reminder))
        assertEquals(LocalTime(14, 0), runBlocking { items.item(task) }?.at)
    }

    @Test
    fun aSnoozeFromBeforeARescheduleNoLongerApplies() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }
        runBlocking { reminders.snooze(reminder, firesAt(reminder)!!, LocalDateTime(MONDAY, LocalTime(14, 10))) }

        runBlocking { items.reschedule(task, LocalDate(2026, 10, 6), LocalTime(9, 0)) }

        assertEquals(LocalDateTime(LocalDate(2026, 10, 6), LocalTime(8, 55)), firesAt(reminder))
    }

    @Test
    fun aRescheduleThatDoesNotPassTheSnoozeStillMovesTheFiring() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }
        runBlocking { reminders.snooze(reminder, firesAt(reminder)!!, LocalDateTime(LocalDate(2026, 10, 6), LocalTime(9, 0))) }

        runBlocking { items.reschedule(task, MONDAY, LocalTime(18, 0)) }

        assertEquals(LocalDateTime(MONDAY, LocalTime(17, 55)), firesAt(reminder))
        // The snooze was of the old firing: it does not ring once the new one has.
        assertEquals(emptyList(), runBlocking { reminders.firings(after = LocalDateTime(MONDAY, LocalTime(17, 55))) })
    }

    @Test
    fun aRetimedReminderDropsItsSnooze() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }
        runBlocking { reminders.snooze(reminder, firesAt(reminder)!!, LocalDateTime(MONDAY, LocalTime(14, 30))) }

        runBlocking { reminders.retime(reminder, -60) }

        assertEquals(LocalDateTime(MONDAY, LocalTime(13, 0)), firesAt(reminder))
        assertEquals(emptyList(), runBlocking { reminders.firings(after = LocalDateTime(MONDAY, LocalTime(13, 0))) })
    }

    @Test
    fun anItemWithRemindersKeepsItsStartDate() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        runBlocking { reminders.add(task, -5) }

        assertFailsWith<IllegalArgumentException> { runBlocking { items.reschedule(task, null) } }
        assertEquals(MONDAY, runBlocking { items.item(task) }?.start)
    }

    @Test
    fun aReminderOnADeletedItemIsRefused() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        runBlocking { items.delete(task) }

        assertFailsWith<IllegalArgumentException> { runBlocking { reminders.add(task, -5) } }
    }

    @Test
    fun deletingAStandaloneRemindersOnlyReminderDeletesItsItem() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }

        runBlocking { reminders.delete(runBlocking { reminders.remindersOf(pills) }.single()) }

        assertTrue(runBlocking { items.item(pills) }!!.deleted)
    }

    @Test
    fun secondsSurviveTheOffset() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0, 30)) }

        val reminder = runBlocking { reminders.add(task, -5) }

        assertEquals(LocalDateTime(MONDAY, LocalTime(13, 55, 30)), firesAt(reminder))
    }

    @Test
    fun firingsAfterAMomentLeaveOutThePast() {
        val early = runBlocking { reminders.createStandalone("early", MONDAY, LocalTime(8, 0)) }
        val late = runBlocking { reminders.createStandalone("late", MONDAY, LocalTime(20, 0)) }

        val next = runBlocking { reminders.firings(after = LocalDateTime(MONDAY, LocalTime(12, 0))) }

        assertEquals(listOf(late), next.map { it.itemId })
        assertTrue(early != late)
    }

    @Test
    fun aDeletedReminderNoLongerFires() {
        val task = runBlocking { items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { reminders.add(task, -5) }

        runBlocking { reminders.delete(reminder) }

        assertEquals(null, firesAt(reminder))
    }

    @Test
    fun aStandaloneReminderNeedsATime() {
        val pills = runBlocking { reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }

        refused("UPDATE item SET start_time = NULL WHERE id = '$pills'")
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
