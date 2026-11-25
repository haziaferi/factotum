package com.hazia.factotum.data.sync

import com.hazia.factotum.core.checkin.Direction
import com.hazia.factotum.core.checkin.MaskedLevel
import com.hazia.factotum.core.recurrence.RRule
import com.hazia.factotum.core.recurrence.Recurrence
import com.hazia.factotum.core.settings.Settings
import com.hazia.factotum.core.sync.Group
import com.hazia.factotum.core.sync.Row
import com.hazia.factotum.core.sync.Stamp
import com.hazia.factotum.core.time.GoalPeriod
import com.hazia.factotum.data.SYNCED_TABLES
import com.hazia.factotum.data.chart.ChartType
import com.hazia.factotum.data.chart.SourceKind
import com.hazia.factotum.data.item.Answer
import com.hazia.factotum.data.item.DETAILS
import com.hazia.factotum.data.item.ITEM
import com.hazia.factotum.data.item.Outcome
import com.hazia.factotum.data.item.Question
import com.hazia.factotum.data.item.SCHEDULE
import com.hazia.factotum.data.item.STATUS
import com.hazia.factotum.data.openFactotumDatabase
import com.hazia.factotum.data.page.PropertyType
import com.hazia.factotum.data.page.ViewType
import com.hazia.factotum.data.reminder.Alert
import com.hazia.factotum.data.reminder.AlertKind
import com.hazia.factotum.data.syncedTables
import com.hazia.factotum.data.tracker.TRACKER_CHOICE
import com.hazia.factotum.data.tracker.TrackerChoiceEntity
import com.hazia.factotum.data.tracker.TrackerType
import com.hazia.factotum.data.tracker.toRow
import com.hazia.factotum.core.checkin.Outcome as RegulationOutcome
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus
import org.junit.After
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
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

    /**
     * SPEC:R37: a clash in its own folder leaves the device owing a new id, held in its database
     * before the copy is deleted, so stopping before the shell takes one does not lose it. Built again
     * under a new id it owes nothing; its first export starts the new folder with a snapshot of
     * everything, since what it wrote under the old id is in no file a peer reads (the clone's writing
     * won the clash, and the copy is gone). It reads the old folder, still the clone's, as a peer's,
     * and no clash follows.
     */
    @Test
    fun aClonedIdIsOwedANewOneUntilTheDeviceRunsUnderAnother() {
        val w = world()
        val a = w.Device("A")
        val clone = w.Device("A'", id = "A")
        val mine = a.create()
        w.syncthing.now = 5
        val theirs = clone.create()
        a.export()
        clone.export()
        assertFalse(runBlocking { a.app.newIdOwed() })
        w.syncthing.session("A", "A'")

        a.import()

        assertTrue(runBlocking { a.app.newIdOwed() })
        assertEquals("A", runBlocking { a.db.syncDao().idOwedBy() })
        // The import changed nothing more, yet the debt stays until another id runs.
        a.import()
        assertTrue(runBlocking { a.app.newIdOwed() })

        // The shell writes a new id file and builds the device again, over the same database and folder.
        a.db.close()
        val renewed = w.Device("A", id = "A2", rowIds = "A2")
        assertFalse(runBlocking { renewed.app.newIdOwed() })

        w.syncthing.now = 9
        val later = renewed.create()
        val b = w.Device("B")
        val copies = w.syncthing.conflictCopies
        w.settle(listOf(renewed, clone, b))

        assertEquals(copies, w.syncthing.conflictCopies, "a clash after the new id")
        assertTrue(w.syncthing.paths("B").any { it.startsWith("devices/A2/snapshot-") })
        assertNull(runBlocking { renewed.db.syncDao().idOwedBy() }, "the debt outlived the first export under the new id")
        for (d in listOf(renewed, clone, b)) assertEquals(setOf(mine, theirs, later), d.rows().keys, d.name)
        // A copy in another device's folder is merged, and owes nothing.
        assertFalse(runBlocking { b.app.newIdOwed() })
    }

    /** SPEC:R37: the debt is in the database before the copy is deleted, so a stop at the delete keeps it. */
    @Test
    fun aClonedIdIsOwedBeforeItsConflictCopyIsDeleted() {
        val w = world()
        val a = w.Device("A")
        val clone = w.Device("A'", id = "A")
        a.create()
        w.syncthing.now = 5
        clone.create()
        a.export()
        clone.export()
        w.syncthing.session("A", "A'")
        val folder = w.syncthing.folder("A")
        val stopsAtDelete = object : SyncFolder by folder {
            override fun delete(path: String) = throw IllegalStateException("stopped at the delete")
        }

        assertFailsWith<IllegalStateException> {
            runBlocking { FolderSync(a.db, stopsAtDelete, "A", a.clock, a.db.syncedTables()).import() }
        }

        assertEquals("A", runBlocking { a.db.syncDao().idOwedBy() })
        assertTrue(w.syncthing.paths("A").any { ".sync-conflict-" in it })
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
        // The row is live on B when the purge arrives: the import applies it all the same.
        assertEquals(setOf(gone), b.rows().keys)
        assertEquals(false, runBlocking { b.items.item(gone) }?.deleted)
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
        val node = Row("future_table", "n", mapOf("a" to Group(Stamp(1, "A"), mapOf("title" to "notes"))))
        val lines = RecordCodec.encode(RowRecord(node)) + "\n{not json\n"
        w.syncthing.folder("old").replace(FolderLayout.segment("A", 0), lines.encodeToByteArray())

        val old = w.Device("old")
        assertEquals(ImportReport(changed = 0, skipped = 2), old.import())
        old.db.close()

        val upgraded = w.Device("old", extra = mapOf("future_table" to MemoryTable()))
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

    @Test
    fun aSnoozeOnOneDeviceAndAnAlertChangeOnAnotherBothStayWithoutAQuestion() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val task = runBlocking { a.items.createTask("call", MONDAY, LocalTime(14, 0)) }
        val reminder = runBlocking { a.reminders.add(task, -5) }
        w.settle(listOf(a, b))

        val snoozed = LocalDateTime(MONDAY, LocalTime(14, 10))
        runBlocking { a.reminders.snooze(reminder, LocalDateTime(MONDAY, LocalTime(13, 55)), snoozed) }
        runBlocking { b.reminders.setAlert(reminder, Alert(AlertKind.ALARM)) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(AlertKind.ALARM, runBlocking { d.reminders.alertOf(reminder) }?.kind, d.name)
            assertEquals(snoozed, runBlocking { d.reminders.firings() }.single().at, d.name)
            assertEquals(emptyList(), runBlocking { d.items.questions() }, d.name)
        }
    }

    @Test
    fun keepingBothTimesOfAStandaloneReminderKeepsBothFiring() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val pills = runBlocking { a.reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }
        w.settle(listOf(a, b))
        runBlocking { a.items.reschedule(pills, MONDAY, LocalTime(9, 0)) }
        runBlocking { b.items.reschedule(pills, MONDAY, LocalTime(10, 0)) }
        w.settle(listOf(a, b))

        runBlocking { b.items.answer(Question(pills, SCHEDULE), Answer.KEEP_BOTH) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            val times = runBlocking { d.reminders.firings() }.map { it.at.time }
            assertEquals(listOf(LocalTime(9, 0), LocalTime(10, 0)), times, d.name)
        }
    }

    /**
     * SPEC:R18: every synced table has its export trigger, and its rows reach a peer whole. A row is
     * made in each through the repositories (a CHOICE tracker's choice straight through the writes,
     * as no repository makes one), and a title changed on both devices makes the notice.
     */
    @Test
    fun everySyncedTableIsQueuedForExportAndRoundTrips() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val queued = mutableSetOf<String>()
        fun World.Device.queue() { queued += runBlocking { db.syncDao().outbox() }.mapNotNull { it.table } }
        val noon = LocalDateTime(MONDAY, LocalTime(12, 0))
        val notes = runBlocking {
            a.settings.set(Settings.CRISIS_CONTACTS, "Ada")
            val home = a.labels.create("Home")
            val mood = a.trackers.create("Mood", TrackerType.CHOICE)
            val calm = "choice-calm"
            a.writes.write(mapOf(TRACKER_CHOICE to listOf(calm))) { store ->
                val s = a.clock.tick()
                a.writes.merger.created(store, TrackerChoiceEntity(calm, mood, "calm", null, 0, null, s.hlc, s.device).toRow())
            }
            a.trackers.log(mood, noon, choiceId = calm)
            a.habits.addBlock(480, 540, "Morning")
            val walk = a.items.createTask("walk", MONDAY, LocalTime(9, 0), recurrence = Recurrence.Rule(requireNotNull(RRule.parse("FREQ=DAILY"))))
            a.items.resolve(walk, LocalDateTime(MONDAY, LocalTime(9, 0)), Outcome.DONE)
            a.reminders.add(walk, -5)
            a.occurrences.skip(walk, LocalDateTime(TUESDAY, LocalTime(9, 0)))
            val reading = a.activities.create("Reading")
            a.time.logManual(reading, LocalDateTime(MONDAY, LocalTime(8, 0)), LocalDateTime(MONDAY, LocalTime(9, 0)))
            a.activities.addGoal(reading, GoalPeriod.DAY, 30)
            val checkIn = a.checkIns.record(noon, energy = 0.2, pleasantness = 0.8)
            a.regulation.record(checkIn, Direction.DOWN, "rest", RegulationOutcome.HELPED, noon)
            a.ledger.logSensory(noon, 0.2, 0.4, 0.6, 0.5, 0.1)
            a.ledger.setMasked(MONDAY, MaskedLevel.SOME)
            val notes = a.pages.create("Notes")
            a.pages.addBlock(notes, content = "first line")
            a.labels.labelPage(notes, home)
            val trips = a.databases.create("Trips")
            val people = a.databases.create("People")
            val status = a.databases.addProperty(trips, "Status", PropertyType.SELECT)
            val done = a.databases.addOption(status, "done")
            val tags = a.databases.addProperty(trips, "Tags", PropertyType.MULTI_SELECT)
            val urgent = a.databases.addOption(tags, "urgent")
            val with = a.databases.addRelation(trips, "With", people)
            val rome = a.pages.create("Rome", parentId = trips)
            val ada = a.pages.create("Ada", parentId = people)
            a.databases.setOption(rome, status, done)
            a.databases.pick(rome, tags, urgent)
            a.databases.link(rome, with, ada)
            a.databases.addView(trips, "Board", ViewType.BOARD)
            a.relations.relate(notes, rome)
            val canvas = a.canvases.create("Ideas")
            val one = a.canvases.addText(canvas, 0.0, 0.0, "one")
            val two = a.canvases.addText(canvas, 100.0, 0.0, "two")
            a.canvases.addEdge(one, two)
            val packing = a.checklists.create("Packing")
            a.checklists.addItem(packing, "passport")
            a.charts.create(ChartType.LINE, 30, listOf(SourceKind.ACTIVITY to reading))
            notes
        }
        a.queue()
        w.settle(listOf(a, b))

        // A title changed on both devices: the earlier is kept, and its notice is a synced row.
        w.syncthing.now = 10
        runBlocking { a.pages.rename(notes, "Notes from A") }
        w.syncthing.now = 20
        runBlocking { b.pages.rename(notes, "Notes from B") }
        a.export()
        b.export()
        w.syncthing.session("A", "B")
        for (d in listOf(a, b)) {
            d.import()
            d.queue()
        }
        w.settle(listOf(a, b))

        assertEquals(SYNCED_TABLES.toSet(), queued)
        for (table in SYNCED_TABLES) {
            val held = runBlocking { a.db.syncedTables().getValue(table).all() }.sortedBy { it.id }
            assertTrue(held.isNotEmpty(), "no $table row was made")
            assertEquals(held, runBlocking { b.db.syncedTables().getValue(table).all() }.sortedBy { it.id }, table)
        }
    }

    /** SPEC:R27: the registry never shrinks, so it is looked up by id, never loaded whole: an import touching one purged id reads one registry row. */
    @Test
    fun anImportTouchingOnePurgedIdReadsOneRegistryRow() {
        val w = world()
        val a = w.Device("A")
        val reads = RegistryReads()
        val b = w.Device("B", open = reads::database)
        val ids = (0 until 30).map { a.create() }
        val late = a.rows().getValue(ids.first())
        ids.forEach(a::purge)
        a.export()
        w.syncthing.session("A", "B")
        b.import()
        assertEquals(30, runBlocking { b.db.syncDao().purges() }.size)

        // An old copy of one purged row turns up in another file: the import looks up that id alone.
        w.syncthing.folder("B").replace(FolderLayout.segment("X", 0), "${RecordCodec.encode(RowRecord(late))}\n".encodeToByteArray())
        reads.rows.set(0)
        assertEquals(ImportReport(changed = 0, skipped = 0), b.import())

        assertEquals(1, reads.rows.get())
        assertTrue(b.rows().isEmpty())
    }

    /**
     * SPEC:R27: an import re-checks only the registry entries it added or lowered. A purge this
     * device already holds, at its stamp or a later one, changes nothing and is not exported again;
     * an earlier one lowers the entry.
     */
    @Test
    fun aPurgeAlreadyHeldChangesNothingAndAnEarlierOneLowersIt() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val id = a.create()
        a.purge(id)
        a.export()
        w.syncthing.session("A", "B")
        b.import()
        fun registry() = runBlocking { b.db.syncDao().purges() }.map { it.id to it.stamp() }
        val held = registry().single().second
        val folder = w.syncthing.folder("B")
        fun arrives(seq: Long, stamp: Stamp): ImportReport {
            folder.replace(FolderLayout.segment("X", seq), "${RecordCodec.encode(PurgeRecord(id, stamp))}\n".encodeToByteArray())
            return b.import()
        }

        // The same purge again, as a replayed log brings it, and a later one made by a device that never heard of it.
        assertEquals(ImportReport(changed = 0, skipped = 0), arrives(0L, held))
        assertEquals(ImportReport(changed = 0, skipped = 0), arrives(1L, Stamp(held.hlc + 1, "X")))
        assertEquals(listOf(id to held), registry())

        val earlier = Stamp(held.hlc - 1, "X")
        assertEquals(ImportReport(changed = 1, skipped = 0), arrives(2L, earlier))
        assertEquals(listOf(id to earlier), registry())
    }

    /** SPEC:R36, requirement 1: a firing is device state, so working out the next firings writes nothing that syncs. */
    @Test
    fun aReminderFiringLeavesTheOutboxEmpty() {
        val w = world()
        val a = w.Device("A")
        val task = runBlocking { a.items.createTask("call", MONDAY, LocalTime(14, 0)) }
        runBlocking { a.reminders.add(task, -5) }
        runBlocking { a.reminders.createStandalone("take pills", MONDAY, LocalTime(8, 0)) }
        a.export()
        assertEquals(emptyList(), runBlocking { a.db.syncDao().outbox() })

        val due = runBlocking { a.reminders.firings() }
        val later = runBlocking { a.reminders.firings(after = due.first().at) }

        assertEquals(listOf(LocalTime(8, 0), LocalTime(13, 55)), due.map { it.at.time })
        assertEquals(listOf(LocalTime(13, 55)), later.map { it.at.time })
        assertEquals(emptyList(), runBlocking { a.db.syncDao().outbox() })
    }

    /** SPEC:R40: a file shorter than what was read was rewritten under the reader (a torn SAF write), so it is read again from its start. */
    @Test
    fun aFileThatShrankIsReadAgainFromTheStart() {
        val w = world()
        val memory = MemoryTable()
        val b = w.Device("B", extra = mapOf(ITEM to memory))
        val path = FolderLayout.segment("A", 0)
        val folder = w.syncthing.folder("B")
        folder.replace(path, "${line("first")}\n${line("second")}\n".encodeToByteArray())
        b.import()
        assertEquals(setOf("first", "second"), memory.rows.keys)

        val shorter = "${line("z")}\n".encodeToByteArray()
        folder.replace(path, shorter)
        b.import()

        assertNotNull(memory.rows["z"])
        assertEquals(shorter.size.toLong(), runBlocking { b.db.syncDao().reads() }.single().readBytes)
    }

    /** SPEC:R48: only the schedule asks; the details and status groups changed on two devices merge silently, the later write standing. */
    @Test
    fun theDetailsAndStatusGroupsChangedOnTwoDevicesMergeWithNoQuestion() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val row = a.create()
        w.settle(listOf(a, b))

        w.syncthing.now = 10
        runBlocking { a.items.rename(row, "from A"); a.items.setImportance(row, 1) }
        w.syncthing.now = 20
        runBlocking { b.items.rename(row, "from B"); b.items.setImportance(row, 3) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(emptyList(), runBlocking { d.items.questions() }, d.name)
            val item = assertNotNull(runBlocking { d.items.item(row) }, d.name)
            assertEquals("from B", item.title, d.name)
            assertEquals(3L, item.importance, d.name)
        }
    }

    /** SPEC:R50: one occurrence resolved on two devices leaves two log rows, and reads take the later stamp. */
    @Test
    fun oneOccurrenceResolvedOnTwoDevicesReadsOneResultTheLater() {
        val w = world()
        val a = w.Device("A")
        val b = w.Device("B")
        val nine = LocalDateTime(MONDAY, LocalTime(9, 0))
        val task = runBlocking { a.items.createTask("plants", MONDAY, LocalTime(9, 0)) }
        w.settle(listOf(a, b))

        w.syncthing.now = 10
        runBlocking { b.items.resolve(task, nine, Outcome.SKIPPED) }
        w.syncthing.now = 20
        runBlocking { a.items.resolve(task, nine, Outcome.DONE) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(2, runBlocking { d.db.itemDao().completionsOf(task) }.size, d.name)
            assertEquals(mapOf(nine to Outcome.DONE), runBlocking { d.items.outcomes(task) }, d.name)
        }
    }

    /** A record of a row in a table only [MemoryTable] would take: one group, no item fields. */
    private fun line(id: String) =
        RecordCodec.encode(RowRecord(Row(ITEM, id, mapOf("a" to Group(Stamp(1, "A"), mapOf("v" to id))))))

    private companion object {
        val MONDAY = LocalDate(2026, 10, 5)
        val TUESDAY = MONDAY.plus(1, DateTimeUnit.DAY)
    }
}
