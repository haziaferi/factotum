package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.openFactotumDatabase
import kotlinx.coroutines.runBlocking
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

/** ADR 13's cases (`decisions/cases/13-folder.jsonl`) through the real importer and exporter. */
class FolderSyncTest {

    @get:Rule val tmp = TemporaryFolder()

    private val worlds = mutableListOf<World>()

    private fun world(seed: Int = 1, segmentBytes: Int = 16 * 1024, snapshotEvery: Int = 64) =
        World(tmp.root, seed, segmentBytes, snapshotEvery).also { worlds += it }

    @After fun close() = worlds.forEach { it.close() }

    private val hour = 3_600_000L

    /**
     * [days] of a phone and a laptop editing while online and offline: each hour a device is online
     * with some chance, and two online devices meet in a session that is cut 5% of the time.
     */
    private fun ordinaryUse(w: World, days: Int, editsPerHour: Int, random: Random): List<World.Device> {
        val devices = listOf(w.Device("phone"), w.Device("laptop"))
        for (h in 0 until days * 24) {
            w.syncthing.now = h * hour
            val online = devices.filter { random.nextDouble() < 0.6 }
            for (d in devices) repeat(random.nextInt(editsPerHour + 1)) {
                val rows = d.table.rows.keys.toList()
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
        val devices = ordinaryUse(w, days = 30, editsPerHour = 2, Random(7))
        w.settle(devices)

        assertEquals(0, w.syncthing.conflictCopies)
    }

    @Test
    fun ffNothingLost_cutSessionsThenSettlingLeaveEveryDeviceWithTheJoin() {
        val w = world()
        val devices = ordinaryUse(w, days = 30, editsPerHour = 3, Random(11))
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
        b.edit(row, "b")
        w.syncthing.now = 20
        a.edit(row, "a")
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
        b.edit(row, "a")
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
        val devices = ordinaryUse(w, days = 365, editsPerHour = 1, Random(3))
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

        assertNotNull(a.table.rows[mine])
        assertNotNull(a.table.rows[theirs])
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
        repeat(3) { a.edit(kept, "a"); a.export() }

        val late = w.Device("C")
        w.settle(listOf(a, b, late))

        for (d in listOf(a, b, late)) {
            assertEquals(setOf(kept), d.table.rows.keys, d.name)
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

        assertTrue(b.table.rows.isEmpty())
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
        val lines = (0 until 2_500).map {
            RecordCodec.encode(RowRecord(Row(ITEM, "r$it", mapOf("a" to Group(Stamp(1, "A"), mapOf("v" to "$it")))))) + "\n"
        }
        w.syncthing.folder("B").replace(FolderLayout.segment("A", 0), lines.joinToString("").encodeToByteArray())
        val b = w.Device("B")

        b.table.savesLeft = 1
        assertFailsWith<IllegalStateException> { b.import() }
        assertEquals(2_000, b.table.rows.size)
        val firstChunk = lines.take(2_000).sumOf { it.encodeToByteArray().size }.toLong()
        assertEquals(firstChunk, runBlocking { b.db.syncDao().reads() }.single().readBytes)

        b.table.savesLeft = Int.MAX_VALUE
        b.import()
        assertEquals(2_500, b.table.rows.size)
    }

    @Test
    fun aLineStillBeingWrittenWaitsForItsNewline() {
        val w = world()
        val b = w.Device("B")
        val line = RecordCodec.encode(RowRecord(Row(ITEM, "x", mapOf("a" to Group(Stamp(1, "A"), mapOf("v" to "1"))))))
        val path = FolderLayout.segment("A", 0)
        val folder = w.syncthing.folder("B")

        folder.replace(path, line.encodeToByteArray())
        b.import()
        assertTrue(b.table.rows.isEmpty())

        folder.replace(path, "$line\n".encodeToByteArray())
        b.import()
        assertNotNull(b.table.rows["x"])
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

        val upgraded = w.Device("old", tables = setOf(ITEM, "page"))
        assertEquals(ImportReport(changed = 1, skipped = 1), upgraded.import())
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

        // A schedule group is the one that asks (ADR 01): both sides change it since their base.
        fun scheduleEdit(d: World.Device, due: String) {
            val r = d.table.rows.getValue(row)
            d.table.rows[row] = r.copy(groups = r.groups + ("schedule" to Group(d.clock.tick(), mapOf("due" to due))))
            runBlocking { d.db.syncDao().putOutbox(listOf(OutboxEntity(id = row, table = ITEM))) }
        }
        scheduleEdit(a, "monday")
        scheduleEdit(b, "tuesday")
        a.export()
        b.export()
        w.syncthing.session("A", "B")
        b.import()
        b.db.close()

        val reopened = openFactotumDatabase(File(tmp.root, "B.db")).database
        val asked = runBlocking { reopened.syncDao().asks(listOf(row)) }
        reopened.close()
        assertEquals(listOf("schedule"), asked.map { it.grp })
        assertEquals(mapOf("due" to "monday"), RecordCodec.decodeGroup(asked.single().theirs).values)
        assertEquals("tuesday", b.table.rows.getValue(row).groups.getValue("schedule").values["due"])
    }
}
