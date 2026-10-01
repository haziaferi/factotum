package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.Answer
import com.factotum.data.item.DETAILS
import com.factotum.data.item.ITEM
import com.factotum.data.item.Question
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.STATUS
import com.factotum.data.openFactotumDatabase
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.plus
import org.junit.After
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** ADR 13's cases (`decisions/cases/13-folder.jsonl`) through the real importer, exporter and item table. */
class FolderSyncTest {

    @get:Rule val tmp = TemporaryFolder()

    private val worlds = mutableListOf<World>()

    private fun world(seed: Int = 1, segmentBytes: Int = 16 * 1024, snapshotEvery: Int = 64) =
        World(tmp.root, seed, segmentBytes, snapshotEvery).also { worlds += it }

    @After fun close() = worlds.forEach { it.close() }

    private val hour = 3_600_000L

    /**
     * [days] of a phone and a laptop editing while online and offline: every [stepHours] a device is
     * online with some chance, and two online devices meet in a session that is cut 5% of the time.
     */
    private fun ordinaryUse(w: World, days: Int, editsPerStep: Int, random: Random, stepHours: Int = 1): List<World.Device> {
        val devices = listOf(w.Device("phone"), w.Device("laptop"))
        for (step in 0 until days * 24 / stepHours) {
            w.syncthing.now = step * stepHours * hour
            val online = devices.filter { random.nextDouble() < 0.6 }
            for (d in devices) repeat(random.nextInt(editsPerStep + 1)) {
                val rows = d.rows().keys.toList()
                if (rows.isEmpty() || random.nextDouble() < 0.1) d.create() else d.edit(rows.random(random), GROUPS.random(random))
            }
            online.forEach { it.import() }
            online.forEach { it.export() }
            if (online.size == 2) w.syncthing.session("phone", "laptop", cut = random.nextDouble() < 0.05)
        }
        return devices
    }

    @Test
    fun stNoConflictCopies_aMonthOfOrdinaryUseMakesNone() {
        val w = world()
        val devices = ordinaryUse(w, days = 30, editsPerStep = 2, Random(7))
        w.settle(devices)

        assertEquals(0, w.syncthing.conflictCopies)
    }

    @Test
    fun ffNothingLost_cutSessionsThenSettlingLeaveEveryDeviceWithTheJoin() {
        val w = world()
        val devices = ordinaryUse(w, days = 30, editsPerStep = 3, Random(11))
        w.settle(devices)

        w.assertJoined(devices)
        assertTrue(w.truth.size > 100, "the month wrote too little to test: ${w.truth.size}")
    }

    @Test
    fun stRetiredLoser_aWipedDevicesChangeSurvives() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val row = a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()

        w.syncthing.now = 10
        b.edit(row, STATUS)
        w.syncthing.now = 20
        a.edit(row, DETAILS)
        b.export()
        a.export()
        w.syncthing.session("A", "B")
        w.syncthing.forget("B")
        val c = w.Device("C")
        w.settle(listOf(a, c))

        w.assertJoined(listOf(a, c))
    }

    @Test
    fun aVersionOutlivesTheLossOfItsAuthorsFiles() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val row = b.create()
        b.edit(row, DETAILS)
        b.export()
        w.syncthing.session("A", "B")
        a.import()
        a.export()

        // B is wiped, and its files are lost from the folder too: only A's copy of B's versions is left.
        w.syncthing.forget("B")
        val folder = w.syncthing.folder("A")
        folder.list(FolderLayout.dir("B")).forEach { folder.delete("${FolderLayout.dir("B")}/$it") }
        val c = w.Device("C")
        w.settle(listOf(a, c))

        w.assertJoined(listOf(a, c))
    }

    @Test
    fun androidFiles1y_aYearKeepsEachDeviceToItsSegmentsAndOneSnapshot() {
        val w = world()
        // Steps of 4 hours: the file count follows how much is exported, not how often devices meet.
        val devices = ordinaryUse(w, days = 365, editsPerStep = 4, Random(3), stepHours = 4)
        w.settle(devices)

        val files = devices.flatMap { w.syncthing.paths(it.name) }.toSet()
        assertTrue(files.size < 10_000)
        for (d in devices) {
            val own = files.filter { it.startsWith("devices/${d.id}/") }
            assertTrue(own.size <= 64 + 1, "${d.id} holds ${own.size} files")
            assertTrue(own.any { "/snapshot-" in it }, "a year should have compacted ${d.id}'s log at least once")
        }
        w.assertJoined(devices)
    }

    @Test
    fun aClonedDeviceIdsClashIsMergedAndTheCopyRemoved() {
        val w = world()
        val a = w.Device("A")
        val clone = w.Device("A'", id = "A")
        val mine = a.create()
        w.syncthing.now = 5
        val theirs = clone.create()
        a.export()
        clone.export()
        w.syncthing.session("A", "A'")
        assertEquals(1, w.syncthing.conflictCopies)

        a.import()
        w.syncthing.forget("A'")

        assertNotNull(a.rows()[mine])
        assertNotNull(a.rows()[theirs])
        assertTrue(w.syncthing.paths("A").none { ".sync-conflict-" in it })
    }

    @Test
    fun aPurgeReachesAPeerAndOutlivesCompaction() {
        // Segments of one line, compacted every two, so three edits compact.
        val w = world(segmentBytes = 200, snapshotEvery = 2)
        val a = w.Device("A")
        val b = w.Device("B")
        val gone = a.create()
        val kept = a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()
        a.purge(gone)
        repeat(3) { a.edit(kept, DETAILS); a.export() }

        val late = w.Device("C")
        w.settle(listOf(a, b, late))

        for (d in listOf(a, b, late)) {
            assertEquals(setOf(kept), d.rows().keys, d.name)
            assertEquals(listOf(gone), runBlocking { d.db.syncDao().purges() }.map { it.id }, d.name)
        }
        assertTrue(w.syncthing.paths("A").any { "/snapshot-" in it })
    }

    @Test
    fun aPurgeReachesAPeerThroughTheLog() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val gone = a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()

        a.purge(gone)
        a.export()
        w.syncthing.session("A", "B")
        b.import()

        assertTrue(b.rows().isEmpty())
        assertTrue(w.syncthing.paths("A").none { "/snapshot-" in it })
    }

    @Test
    fun aPeerFileIsReadOnlyWhenItHasGrown() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()
        val before = w.syncthing.bytesRead

        b.import()

        assertEquals(before, w.syncthing.bytesRead)
    }

    @Test
    fun aBigFileIsMergedInChunksEachWithItsReadPosition() {
        val w = world()
        val lines = (0 until 2_500).map { "${line("r$it")}\n" }
        w.syncthing.folder("B").replace(FolderLayout.segment("A", 0), lines.joinToString("").encodeToByteArray())
        val memory = MemoryTable()
        val b = w.Device("B", extra = mapOf(ITEM to memory))

        memory.savesLeft = 1
        assertFailsWith<IllegalStateException> { b.import() }
        assertEquals(2_000, memory.rows.size)
        val firstChunk = lines.take(2_000).sumOf { it.encodeToByteArray().size }.toLong()
        assertEquals(firstChunk, runBlocking { b.db.syncDao().reads() }.single().readBytes)

        memory.savesLeft = Int.MAX_VALUE
        b.import()
        assertEquals(2_500, memory.rows.size)
    }

    @Test
    fun aLineStillBeingWrittenWaitsForItsNewline() {
        val w = world()
        val b = w.Device("B", extra = mapOf(ITEM to MemoryTable()))
        val path = FolderLayout.segment("A", 0)
        val folder = w.syncthing.folder("B")

        folder.replace(path, line("x").encodeToByteArray())
        b.import()
        assertTrue(b.rows().isEmpty())

        folder.replace(path, "${line("x")}\n".encodeToByteArray())
        b.import()
        assertNotNull(b.rows()["x"])
    }

    @Test
    fun aLineForATableThisVersionLacksIsReadAgainOnceItHasIt() {
        val w = world()
        val page = Row("page", "p", mapOf("a" to Group(Stamp(1, "A"), mapOf("title" to "notes"))))
        val lines = RecordCodec.encode(RowRecord(page)) + "\n{not json\n"
        w.syncthing.folder("old").replace(FolderLayout.segment("A", 0), lines.encodeToByteArray())

        val old = w.Device("old")
        assertEquals(ImportReport(changed = 0, skipped = 2), old.import())
        old.db.close()

        val upgraded = w.Device("old", extra = mapOf("page" to MemoryTable()))
        assertEquals(ImportReport(changed = 1, skipped = 1), upgraded.import())
    }

    @Test
    fun aRowThatDoesNotFitItsTableIsSkipped() {
        val w = world()
        w.syncthing.folder("B").replace(FolderLayout.segment("A", 0), "${line("x")}\n".encodeToByteArray())
        val b = w.Device("B")

        assertEquals(ImportReport(changed = 0, skipped = 1), b.import())
        assertTrue(b.rows().isEmpty())
    }

    @Test
    fun aPendingQuestionOutlivesAReopen() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val row = a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()

        // The schedule is the group that asks (ADR 01): both sides change it since their base.
        runBlocking { a.items.reschedule(row, MONDAY) }
        runBlocking { b.items.reschedule(row, TUESDAY) }
        a.export()
        b.export()
        w.syncthing.session("A", "B")
        b.import()
        b.db.close()

        val reopened = openFactotumDatabase(File(tmp.root, "B.db")).database
        val asked = runBlocking { reopened.syncDao().asks(listOf(row)) }
        reopened.close()
        assertEquals(listOf(SCHEDULE), asked.map { it.grp })
        assertEquals(MONDAY.toString(), RecordCodec.decodeGroup(asked.single().theirs).values["start_date"])
    }

    @Test
    fun anAnswerSettlesTheQuestionOnBothDevices() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val row = a.create()
        a.export()
        w.syncthing.session("A", "B")
        b.import()
        runBlocking { a.items.reschedule(row, MONDAY) }
        runBlocking { b.items.reschedule(row, TUESDAY) }
        w.settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(listOf(Question(row, SCHEDULE)), runBlocking { d.items.questions() }, d.name)

        runBlocking { b.items.answer(Question(row, SCHEDULE), Answer.KEEP_MINE) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(emptyList(), runBlocking { d.items.questions() }, d.name)
            assertEquals(TUESDAY, runBlocking { d.items.item(row) }?.start, d.name)
        }
    }

    @Test
    fun aSubtaskThatArrivesBeforeItsParentWaitsForIt() {
        val w = world()
        val a = w.Device("A")
        val parent = runBlocking { a.items.createTask("tax form") }
        val child = runBlocking { a.items.createTask("find receipts", parentId = parent) }
        a.export()
        val lines = w.syncthing.folder("A").read(FolderLayout.segment("A", 0))!!.decodeToString().lines().filter { it.isNotEmpty() }
        val (parentLine, childLine) = listOf(parent, child).map { id -> lines.single { "\"id\":\"$id\"" in it } }

        // The subtask reaches B in one device's file before the parent arrives in another's.
        val b = w.Device("B")
        val folder = w.syncthing.folder("B")
        folder.replace(FolderLayout.segment("X", 0), "$childLine\n".encodeToByteArray())
        b.import()
        assertEquals(emptySet(), b.rows().keys)
        assertEquals(1, runBlocking { b.db.syncDao().waiting() }.size)

        folder.replace(FolderLayout.segment("Y", 0), "$parentLine\n".encodeToByteArray())
        b.import()
        assertEquals(setOf(parent, child), b.rows().keys)
        assertEquals(emptyList(), runBlocking { b.db.syncDao().waiting() })
    }

    @Test
    fun aSubtaskWhoseParentWasPurgedIsDroppedNotKeptWaiting() {
        val w = world()
        val a = w.Device("A")
        val parent = runBlocking { a.items.createTask("tax form") }
        val child = runBlocking { a.items.createTask("find receipts", parentId = parent) }
        a.export()
        val childLine = w.syncthing.folder("A").read(FolderLayout.segment("A", 0))!!.decodeToString()
            .lines().single { "\"id\":\"$child\"" in it }
        a.purge(parent)
        a.export()
        val b = w.Device("B")
        w.syncthing.session("A", "B")
        b.import()

        w.syncthing.folder("B").replace(FolderLayout.segment("X", 0), "$childLine\n".encodeToByteArray())

        assertEquals(ImportReport(changed = 0, skipped = 1), b.import())
        assertEquals(emptyList(), runBlocking { b.db.syncDao().waiting() })
    }

    @Test
    fun aLineWaitingForItsParentIsKeptOnceThoughTwoFilesHoldIt() {
        val w = world()
        val a = w.Device("A")
        val parent = runBlocking { a.items.createTask("tax form") }
        val child = runBlocking { a.items.createTask("find receipts", parentId = parent) }
        a.export()
        val childLine = w.syncthing.folder("A").read(FolderLayout.segment("A", 0))!!.decodeToString()
            .lines().single { "\"id\":\"$child\"" in it }
        val b = w.Device("B")
        val folder = w.syncthing.folder("B")

        folder.replace(FolderLayout.segment("X", 0), "$childLine\n".encodeToByteArray())
        folder.replace(FolderLayout.segment("Y", 0), "$childLine\n".encodeToByteArray())
        b.import()

        assertEquals(1, runBlocking { b.db.syncDao().waiting() }.size)
    }

    @Test
    fun aRowThatBreaksItsKindsRulesIsDroppedNotKeptWaiting() {
        val w = world()
        val a = w.Device("A")
        val event = runBlocking { a.items.createEvent("standup", MONDAY) }
        val row = a.rows().getValue(event)
        val status = row.groups.getValue(STATUS)
        val bad = row.copy(groups = row.groups + (STATUS to status.copy(values = status.values + ("status" to "PENDING"))))
        val b = w.Device("B")
        w.syncthing.folder("B").replace(FolderLayout.segment("A", 0), "${RecordCodec.encode(RowRecord(bad))}\n".encodeToByteArray())

        assertEquals(ImportReport(changed = 0, skipped = 1), b.import())
        assertTrue(b.rows().isEmpty())
        assertEquals(emptyList(), runBlocking { b.db.syncDao().waiting() })
    }

    /** A record of a row in a table only [MemoryTable] would take: one group, no item fields. */
    private fun line(id: String) =
        RecordCodec.encode(RowRecord(Row(ITEM, id, mapOf("a" to Group(Stamp(1, "A"), mapOf("v" to id))))))

    private companion object {
        val MONDAY = LocalDate(2026, 10, 5)
        val TUESDAY = MONDAY.plus(1, DateTimeUnit.DAY)
    }
}
