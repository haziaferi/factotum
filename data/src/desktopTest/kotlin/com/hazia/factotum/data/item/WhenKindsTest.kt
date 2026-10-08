package com.hazia.factotum.data.item

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.hazia.factotum.core.recurrence.GapUnit
import com.hazia.factotum.core.recurrence.Recurrence
import com.hazia.factotum.core.recurrence.TimeWindow
import com.hazia.factotum.core.recurrence.occurrences
import com.hazia.factotum.data.FactotumDatabase
import com.hazia.factotum.data.FixedSettings
import com.hazia.factotum.data.LocalWrites
import com.hazia.factotum.data.isConstraintViolation
import com.hazia.factotum.data.openFactotumDatabase
import com.hazia.factotum.data.reminder.ReminderRepository
import com.hazia.factotum.data.sync.loadClock
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
import kotlin.test.fail

/**
 * The When sheet's kinds on items (decision 17, owner 2026-10-08): several random times a day, random gaps in a
 * window, and their ends. New forms get kinds of their own, so a version that cannot read them leaves the row waiting
 * instead of reading it as Chronicle's or Mnemo's and dropping what it does not know; the old forms keep the old kinds.
 */
class WhenKindsTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private lateinit var reminders: ReminderRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "when.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        items = ItemRepository(db, writes, newId)
        reminders = ReminderRepository(db, writes, newId, FixedSettings())
    }

    @After fun close() = db.close()

    private val everyDay = DayOfWeek.entries.toSet()
    private val nineToFive = TimeWindow(LocalTime(9, 0), LocalTime(17, 0))

    private fun store(r: Recurrence): String = runBlocking { items.createTask("t", MONDAY, LocalTime(9, 0), recurrence = r) }

    private fun storedKind(id: String): String = runBlocking {
        db.useReaderConnection { c -> c.usePrepared("SELECT recurrence_kind FROM item WHERE id = '$id'") { s -> s.step(); s.getText(0) } }
    }

    @Test
    fun eachNewFormIsStoredAndReadBack() {
        val forms = listOf(
            Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 3),
            Recurrence.RandomWindow(setOf(DayOfWeek.FRIDAY), LocalTime(22, 0), LocalTime(2, 0)),
            Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(12, 0), count = 2, total = 10),
            Recurrence.RandomDays(20, 40, GapUnit.MINUTE, nineToFive),
            Recurrence.RandomDays(2, 4, GapUnit.DAY, TimeWindow(LocalTime(9, 0), LocalTime(12, 0)), until = LocalDateTime(2026, 12, 31, 23, 59, 59)),
            Recurrence.RandomDays(1, 3, GapUnit.WEEK),
        )
        for (r in forms) assertEquals(r, runBlocking { items.item(store(r)) }?.recurrence, "$r")
    }

    @Test
    fun theOldFormsKeepTheOldKindsAndTheNewOnesGetTheirOwn() {
        assertEquals("RANDOM_WINDOW", storedKind(store(Recurrence.RandomWindow(everyDay, LocalTime(10, 0), LocalTime(12, 0)))))
        assertEquals("RANDOM_DAYS", storedKind(store(Recurrence.RandomDays(2, 4))))
        assertEquals("RANDOM_TIMES", storedKind(store(Recurrence.RandomWindow(everyDay, LocalTime(10, 0), LocalTime(12, 0), count = 2))))
        assertEquals("RANDOM_TIMES", storedKind(store(Recurrence.RandomWindow(everyDay, LocalTime(22, 0), LocalTime(2, 0)))))
        assertEquals("RANDOM_TIMES", storedKind(store(Recurrence.RandomWindow(everyDay, LocalTime(10, 0), LocalTime(12, 0), total = 3))))
        assertEquals("RANDOM_GAPS", storedKind(store(Recurrence.RandomDays(2, 4, GapUnit.WEEK))))
        assertEquals("RANDOM_GAPS", storedKind(store(Recurrence.RandomDays(2, 4, until = LocalDateTime(2026, 11, 1, 0, 0)))))
    }

    @Test
    fun aSyncedRowCarriesTheNewColumnsAndReadsBack() {
        val r = Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 3, total = 12)
        val entity = runBlocking { db.itemDao().items(listOf(store(r))) }.single()
        val row = entity.toRow()
        val schedule = row.groups.getValue(SCHEDULE).values
        assertEquals(3L, schedule["window_count"])
        assertEquals(12L, schedule["rec_count"])
        assertEquals(r, row.toItemEntity().recurrence())
    }

    @Test
    fun aReminderFiresAtTheDrawnTimes() {
        val r = Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 3)
        val pills = runBlocking { reminders.createStandalone("stretch", MONDAY, LocalTime(9, 0), recurrence = r) }
        val drawn = r.occurrences(pills, LocalDateTime(MONDAY, LocalTime(9, 0)), LocalDateTime(MONDAY, LocalTime(0, 0)), LocalDateTime(2026, 10, 6, 0, 0))
        assertEquals(3, drawn.size)
        var after = LocalDateTime(MONDAY, LocalTime(0, 0))
        for (at in drawn) {
            val fired = runBlocking { reminders.firings(after = after) }.single().at
            assertEquals(at, fired)
            after = fired
        }
    }

    @Test
    fun eachNewKindKeepsToItsOwnColumns() {
        val id = runBlocking { items.createTask("t", MONDAY, LocalTime(9, 0)) }
        val times = "recurrence_kind = 'RANDOM_TIMES', window_days = 127, window_start = '09:00', window_end = '17:00'"
        refused("UPDATE item SET $times WHERE id = '$id'") // no count
        refused("UPDATE item SET $times, window_count = 0 WHERE id = '$id'")
        refused("UPDATE item SET $times, window_count = 49 WHERE id = '$id'")
        refused("UPDATE item SET $times, window_count = 2, rec_until = '2026-12-01T00:00', rec_count = 3 WHERE id = '$id'")
        refused("UPDATE item SET $times, window_count = 2, rec_count = 0 WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_TIMES', window_days = 127, window_start = '09:00', window_end = '09:00', window_count = 1 WHERE id = '$id'")
        // Mnemo's kind keeps its old rule: no window past midnight, no count, no end
        refused("UPDATE item SET recurrence_kind = 'RANDOM_WINDOW', window_days = 127, window_start = '22:00', window_end = '02:00' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_WINDOW', window_days = 127, window_start = '09:00', window_end = '17:00', window_count = 2 WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_WINDOW', window_days = 127, window_start = '09:00', window_end = '17:00', rec_count = 2 WHERE id = '$id'")
        val gaps = "recurrence_kind = 'RANDOM_GAPS', rand_min_days = 20, rand_max_days = 40"
        refused("UPDATE item SET $gaps WHERE id = '$id'") // no unit
        refused("UPDATE item SET $gaps, rand_unit = 'SECOND' WHERE id = '$id'")
        refused("UPDATE item SET $gaps, rand_unit = 'MINUTE' WHERE id = '$id'") // minutes need a window
        refused("UPDATE item SET $gaps, rand_unit = 'DAY', window_start = '09:00' WHERE id = '$id'") // half a window
        refused("UPDATE item SET $gaps, rand_unit = 'DAY', window_days = 127, window_start = '09:00', window_end = '12:00' WHERE id = '$id'")
        // Chronicle's kind keeps its old rule: no unit, no window, no end
        refused("UPDATE item SET recurrence_kind = 'RANDOM_DAYS', rand_min_days = 2, rand_max_days = 4, rand_unit = 'DAY' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_DAYS', rand_min_days = 2, rand_max_days = 4, window_start = '09:00', window_end = '12:00' WHERE id = '$id'")
        refused("UPDATE item SET recurrence_kind = 'RANDOM_DAYS', rand_min_days = 2, rand_max_days = 4, rec_count = 3 WHERE id = '$id'")
        // an end belongs to the random kinds alone (a rule carries its own UNTIL or COUNT)
        refused("UPDATE item SET recurrence_kind = 'RRULE', rrule = 'FREQ=DAILY', rec_count = 3 WHERE id = '$id'")
        // the columns are taken when they make a whole
        runBlocking { db.useWriterConnection { it.execSQL("UPDATE item SET $gaps, rand_unit = 'MINUTE', window_start = '09:00', window_end = '17:00', rec_count = 30 WHERE id = '$id'") } }
        assertEquals(Recurrence.RandomDays(20, 40, GapUnit.MINUTE, nineToFive, total = 30), runBlocking { items.item(id) }?.recurrence)
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
