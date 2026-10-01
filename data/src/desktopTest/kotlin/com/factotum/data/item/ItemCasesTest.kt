package com.factotum.data.item

import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.isConstraintViolation
import com.factotum.data.openFactotumDatabase
import com.factotum.data.sync.AskEntity
import com.factotum.data.sync.RecordCodec
import com.factotum.data.sync.loadClock
import com.factotum.data.syncedTables
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 02's cases (`decisions/cases/02-task.jsonl`) against the real database and repository. */
class ItemCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var items: ItemRepository
    private var now = 1_000L

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "items.db")).database
        var n = 0
        val clock = runBlocking { db.syncDao().loadClock("A") { now } }
        items = ItemRepository(db, LocalWrites(db, clock)) { "id-$now-${n++}" }
    }

    @After fun close() = db.close()

    /** ADR 02's fixture: an event, a timed task, two whole-day tasks, and a subtask with no date. */
    private class Monday(val event: String, val call: String, val tax: String, val plants: String)

    private fun monday() = runBlocking {
        val event = items.createEvent("standup", MONDAY, LocalTime(10, 0), MONDAY, LocalTime(11, 0))
        val call = items.createTask("call", MONDAY, LocalTime(14, 0), capacityRank = 3)
        val tax = items.createTask("tax form", MONDAY, due = LocalDate(2026, 10, 9), capacityRank = 1)
        val plants = items.createTask("plants", MONDAY, capacityRank = 2)
        items.createTask("find receipts", parentId = tax)
        Monday(event, call, tax, plants)
    }

    @Test
    fun tendrilTimeline_timedItemsInTimeOrderThenWholeDayOnes() {
        val m = monday()

        val day = runBlocking { items.day(MONDAY) }.map { it.id }

        assertEquals(listOf(m.event, m.call, m.tax, m.plants), day)
    }

    @Test
    fun tendrilSubtaskCascade_aDeletedParentTakesItsSubtasks() {
        val parent = runBlocking { items.createTask("tax form", MONDAY) }
        val child = runBlocking { items.createTask("find receipts", parentId = parent) }

        runBlocking { items.delete(parent) }

        assertTrue(runBlocking { items.item(child) }!!.deleted)
    }

    @Test
    fun tendrilSubtaskCascade_aPurgedParentTakesItsSubtasksAndCompletions() {
        val parent = runBlocking { items.createTask("tax form", MONDAY) }
        val child = runBlocking { items.createTask("find receipts", parentId = parent) }
        runBlocking { items.resolve(parent, MONDAY, Outcome.DONE) }

        runBlocking { items.purge(parent) }

        assertNull(runBlocking { items.item(child) })
        assertEquals(emptyMap(), runBlocking { items.outcomes(parent) })
    }

    @Test
    fun tendrilCompletionLog_eachOccurrenceKeepsItsOutcomeAndNoOtherStatusIsTaken() {
        val task = runBlocking { items.createTask("plants", MONDAY) }
        runBlocking {
            items.resolve(task, MONDAY, Outcome.DONE)
            items.resolve(task, LocalDate(2026, 10, 12), Outcome.SKIPPED)
        }

        assertEquals(mapOf(MONDAY to Outcome.DONE, LocalDate(2026, 10, 12) to Outcome.SKIPPED), runBlocking { items.outcomes(task) })
        refused("UPDATE completion SET status = 'PENDING'")
    }

    @Test
    fun tendrilPlannedAndDue_aTaskHasAPlannedDayAndASeparateDeadline() {
        val task = runBlocking { items.createTask("tax form", MONDAY, due = LocalDate(2026, 10, 9)) }

        val read = runBlocking { items.item(task) }!!

        assertEquals(MONDAY, read.start)
        assertEquals(LocalDate(2026, 10, 9), read.due)
    }

    @Test
    fun equipoiseCapacityQuery_oneSlotGetsTheRankOneTask() {
        val m = monday()

        assertEquals(listOf(m.tax), runBlocking { items.capacity(MONDAY, 1) }.map { it.id })
        assertEquals(listOf(m.tax, m.plants, m.call), runBlocking { items.capacity(MONDAY, 5) }.map { it.id })
    }

    @Test
    fun equipoiseCapacityIgnoresEvents_theQueryNeverScansTheTable() {
        monday()
        val sql = CAPACITY_QUERY.replace(":date", "'$MONDAY'").replace(":n", "1")

        val plan = runBlocking {
            db.useReaderConnection { c ->
                c.usePrepared("EXPLAIN QUERY PLAN $sql") { s -> buildList { while (s.step()) add(s.getText(3)) } }
            }
        }

        assertTrue(plan.any { "USING INDEX item_kind_date" in it }, plan.toString())
        assertTrue(plan.none { it.startsWith("SCAN item") }, plan.toString())
    }

    @Test
    fun sharedEventHasNoTaskState_theDatabaseRefusesIt() {
        val m = monday()

        refused("UPDATE item SET status = 'PENDING' WHERE id = '${m.event}'")
        refused("UPDATE item SET due_date = '2026-10-09' WHERE id = '${m.event}'")
        refused("UPDATE item SET capacity_rank = 1 WHERE id = '${m.event}'")
        refused("UPDATE item SET end_time = '15:00' WHERE id = '${m.call}'")
        refused("UPDATE item SET kind = 'NOTE' WHERE id = '${m.call}'")
    }

    @Test
    fun sharedOneIdSpace_theSyncLayerFindsATaskOrEventByIdAlone() {
        val m = monday()

        val found = runBlocking { db.syncedTables().getValue(ITEM).load(listOf(m.event, m.call)) }

        assertEquals(setOf(m.event, m.call), found.map { it.id }.toSet())
    }

    @Test
    fun theKindRulesHoldAfterAReopen() {
        val m = monday()
        db.close()
        open()

        refused("UPDATE item SET status = 'DONE' WHERE id = '${m.event}'")
    }

    @Test
    fun eachWriteSavesTheClockWithIt() {
        now = 50_000
        runBlocking { items.createTask("call") }
        db.close()
        now = 0
        open()

        val id = runBlocking { items.createTask("later") }

        assertTrue(runBlocking { items.item(id) } != null)
        assertTrue(runBlocking { db.syncedTables().getValue(ITEM).load(listOf(id)) }.single().newest.hlc > 50_000)
    }

    @Test
    fun aTaskMarkedDoneLeavesTheCapacityDayAndARankMovesItUp() {
        val m = monday()

        runBlocking {
            items.setStatus(m.tax, TaskStatus.DONE)
            items.setCapacityRank(m.call, 0)
        }

        assertEquals(TaskStatus.DONE, runBlocking { items.item(m.tax) }?.status)
        assertEquals(listOf(m.call, m.plants), runBlocking { items.capacity(MONDAY, 5) }.map { it.id })
    }

    @Test
    fun aPurgedParentTakesItsSubtasksPendingQuestionWithIt() {
        val parent = runBlocking { items.createTask("tax form", MONDAY) }
        val child = runBlocking { items.createTask("find receipts", parentId = parent) }
        val theirs = runBlocking { db.syncedTables().getValue(ITEM).load(listOf(child)) }.single().groups.getValue(SCHEDULE)
        runBlocking { db.syncDao().putAsks(listOf(AskEntity(child, SCHEDULE, RecordCodec.encodeGroup(theirs)))) }

        runBlocking { items.purge(parent) }

        assertEquals(emptyList(), runBlocking { items.questions() })
    }

    @Test
    fun rescheduleLeavesADeletedItemDeleted() {
        val task = runBlocking { items.createTask("call", MONDAY) }
        runBlocking { items.delete(task) }

        runBlocking { items.reschedule(task, LocalDate(2026, 10, 6)) }

        assertTrue(runBlocking { items.item(task) }!!.deleted)
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
