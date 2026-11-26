package com.hazia.factotum.data

import com.hazia.factotum.core.sync.Ulid
import com.hazia.factotum.data.image.DesktopImageScaler
import com.hazia.factotum.data.image.MemoryBlobStore
import com.hazia.factotum.data.item.ITEM
import com.hazia.factotum.data.settings.MemorySecretStore
import com.hazia.factotum.data.settings.RefusingSecretStore
import com.hazia.factotum.data.sync.DirectorySyncFolder
import com.hazia.factotum.data.sync.FolderSync
import com.hazia.factotum.data.sync.IdOwedEntity
import com.hazia.factotum.data.sync.SyncFolder
import com.hazia.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDateTime
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import java.io.RandomAccessFile
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** SPEC:R205: the Windows app's sync pass, run as the app runs it, over real files and a real folder. */
class SyncPassTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun device(name: String) = DeviceFiles.inFolder(File(tmp.root, name))

    private fun pass(files: DeviceFiles, folder: File? = null) =
        syncPass(files, ::openFactotumDatabase, DesktopImageScaler(), folder?.path)

    private fun <T> withDatabase(files: DeviceFiles, block: suspend (FactotumDatabase) -> T): T {
        val db = openFactotumDatabase(files.database).database
        try {
            return runBlocking { block(db) }
        } finally {
            db.close()
        }
    }

    /** A task written on [files]' device as a screen would write it, between passes; it waits in the outbox. */
    private fun writeTask(files: DeviceFiles, title: String): String = withDatabase(files) { db ->
        val id = deviceId(files.deviceId)
        val wall = System::currentTimeMillis
        val app = Factotum(
            db, DirectorySyncFolder(tmp.newFolder()), id, db.syncDao().loadClock(id, wall), MemorySecretStore(), MemoryBlobStore(),
            DesktopImageScaler(), { Ulid.next(wall()) }, wall, { LocalDateTime(2026, 11, 26, 12, 0) },
        )
        app.items.createTask(title)
    }

    private fun items(files: DeviceFiles): Set<String> = withDatabase(files) { db -> db.syncedTables().getValue(ITEM).all().map { it.id }.toSet() }

    @Test
    fun aPassWithNoFolderOnlyOpensTheDatabaseAndMakesTheDeviceId() {
        val a = device("A")

        val report = pass(a)

        assertNull(report.folder)
        assertFalse(report.renewed)
        assertTrue(a.database.isFile, "no database")
        assertEquals(report.device, a.deviceId.readText().trim())
    }

    @Test
    fun aFolderGivenOnceIsSavedAndEveryLaterPassSyncsWithIt() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        val b = device("B")
        val first = writeTask(a, "first")

        pass(a, folder)
        val bFirst = pass(b, folder)
        val second = writeTask(a, "second")
        pass(a)
        val bSecond = pass(b)

        assertEquals(folder.path, bSecond.folder)
        assertEquals(1, bFirst.changed)
        assertEquals(1, bSecond.changed)
        assertEquals(setOf(first, second), items(b))
    }

    @Test
    fun aFolderThatDoesNotExistIsRefusedNeitherMadeNorSaved() {
        val a = device("A")
        val missing = File(tmp.root, "unplugged/Factotum")

        val refused = assertFailsWith<SyncPassRefused> { pass(a, missing) }

        assertEquals("No sync folder at ${missing.path}.", refused.message)
        assertFalse(missing.exists(), "the pass made the folder")
        assertNull(pass(a).folder, "the refused folder was saved")
    }

    /**
     * A pass started while another runs (by hand during a scheduled one) is refused, and touches nothing.
     * The lock is held here in the same process; another process's lock refuses the same way, checked
     * by hand on Windows on 2026-11-26 (R205's Evidence).
     */
    @Test
    fun aSecondPassWhileOneRunsIsRefused() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        pass(a, folder)

        val refused = RandomAccessFile(File(a.database.parentFile, PASS_LOCK), "rw").channel.use { running ->
            running.lock().use { assertFailsWith<SyncPassRefused> { pass(a) } }
        }

        assertEquals("Another sync pass is running.", refused.message)
        assertEquals(folder.path, pass(a).folder, "the lock outlived the pass that held it")
    }

    /** SPEC:R37: a clone's conflict copy in this device's own folder makes the pass take a new id and publish everything under it. */
    @Test
    fun aClonedIdFoundByTheImportIsRenewedAndEverythingPublishedUnderTheNewOne() {
        val folderA = tmp.newFolder("syncA")
        val folderClone = tmp.newFolder("syncClone")
        val a = device("A")
        val clone = device("clone")
        val old = pass(a, folderA).device
        clone.deviceId.parentFile.mkdirs()
        a.deviceId.copyTo(clone.deviceId)
        val mine = writeTask(a, "mine")
        val theirs = writeTask(clone, "theirs")
        pass(a)
        pass(clone, folderClone)
        // Syncthing keeps the clone's file beside A's as a conflict copy.
        val theirFiles = File(folderClone, "devices/$old").listFiles()!!
        for (f in theirFiles) f.copyTo(File(folderA, "devices/$old/${f.nameWithoutExtension}.sync-conflict-20261126-120000-CLONE77.jsonl"))

        val report = pass(a)

        assertTrue(report.renewed)
        assertNotEquals(old, report.device)
        assertEquals(report.device, a.deviceId.readText().trim())
        assertTrue(File(folderA, "devices/${report.device}").list()!!.any { it.startsWith("snapshot-") }, "no snapshot under the new id")
        assertFalse(File(folderA, "devices/$old").list()!!.any { "sync-conflict" in it }, "the copy was left")
        assertEquals(setOf(mine, theirs), items(a))
        assertNull(withDatabase(a) { it.syncDao().idOwedBy() }, "the debt outlived the pass")
        assertFalse(pass(a).renewed, "a second pass renewed again")
    }

    /** SPEC:R37: a pass stopped before its new id leaves the debt in the database; the next pass pays it. */
    @Test
    fun aDebtLeftByAStoppedPassIsPaidByTheNext() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        val old = pass(a, folder).device
        withDatabase(a) { it.syncDao().oweNewId(IdOwedEntity(device = old)) }

        val report = pass(a)

        assertTrue(report.renewed)
        assertNotEquals(old, report.device)
        assertTrue(File(folder, "devices/${report.device}").list()!!.any { it.startsWith("snapshot-") }, "no snapshot under the new id")
        assertNull(withDatabase(a) { it.syncDao().idOwedBy() })
    }

    /**
     * SPEC:R37: the old id's files hold the clone's writing, which won the clash. A debt is paid before
     * the import, so that import reads them as a peer's, in the same pass; under the old id it would
     * skip them as its own.
     */
    @Test
    fun aDebtIsPaidBeforeTheImportSoTheClonesWritingArrivesInTheSamePass() {
        val folder = tmp.newFolder("sync")
        val folderClone = tmp.newFolder("syncClone")
        val a = device("A")
        val clone = device("clone")
        val old = pass(a, folder).device
        clone.deviceId.parentFile.mkdirs()
        a.deviceId.copyTo(clone.deviceId)
        val theirs = writeTask(clone, "theirs")
        pass(clone, folderClone)
        // Syncthing kept the clone's files as the winners; the pass that found the copy stopped before its new id.
        File(folderClone, "devices/$old").copyRecursively(File(folder, "devices/$old"), overwrite = true)
        withDatabase(a) { it.syncDao().oweNewId(IdOwedEntity(device = old)) }

        val report = pass(a)

        assertTrue(report.renewed)
        assertEquals(setOf(theirs), items(a))
    }

    /** A folder given as a relative path is saved whole: a later pass, a scheduled one above all, starts elsewhere. */
    @Test
    fun aRelativeFolderIsSavedAsAWholePath() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        val relative = File("").absoluteFile.toPath().relativize(folder.toPath()).toString()

        val report = pass(a, File(relative))

        assertEquals(folder.absolutePath, report.folder)
        assertEquals(folder.absolutePath, pass(a).folder)
    }

    /** Another program holding the lock file itself (Windows then refuses to open it) refuses the pass with its own sentence. */
    @Test
    fun aLockFileAnotherProgramHoldsRefusesThePass() {
        val a = device("A")
        a.database.parentFile.mkdirs()
        val lock = File(a.database.parentFile, PASS_LOCK)
        // A folder in the lock file's place opens no more than a file another program holds, on every system.
        lock.mkdir()

        val refused = assertFailsWith<SyncPassRefused> { pass(a) }

        assertEquals("Another program holds ${lock.path} open.", refused.message)
    }

    /**
     * SPEC:R34: a corrupt database is set aside, and with it this device's `sync_folder`, so the pass
     * that recovers knows no folder. The first pass that knows one again still reads the device's own
     * files, and its rows come back with no peer.
     */
    @Test
    fun aRecoveredDatabaseGetsItsRowsBackAtTheFirstPassThatKnowsTheFolder() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        val task = writeTask(a, "tax form")
        pass(a, folder)
        a.database.writeBytes("this is not a database\n".toByteArray())

        val recovering = pass(a)
        val next = pass(a, folder)

        assertNull(recovering.folder, "the folder outlived the corrupt database")
        assertEquals(setOf(task), items(a))
        assertTrue(next.changed > 0)
    }

    /** SPEC:R34: a first import stopped part way leaves its own files unread, and the next import reads them. */
    @Test
    fun aFirstImportStoppedPartWayReadsItsOwnFilesAgain() {
        val folder = tmp.newFolder("sync")
        val a = device("A")
        val task = writeTask(a, "tax form")
        pass(a, folder)
        a.database.delete()
        val stopsAtRead = object : SyncFolder by DirectorySyncFolder(folder) {
            override fun read(path: String): ByteArray? = throw IllegalStateException("stopped at the read")
        }
        withDatabase(a) { db ->
            val id = deviceId(a.deviceId)
            assertFailsWith<IllegalStateException> {
                FolderSync(db, stopsAtRead, id, db.syncDao().loadClock(id, System::currentTimeMillis), db.syncedTables()).import()
            }
        }

        pass(a, folder)

        assertEquals(setOf(task), items(a))
    }

    @Test
    fun theShellsSecretStoreHoldsNoneAndRefusesToSaveOne() {
        assertNull(RefusingSecretStore.get("ai_key"))
        RefusingSecretStore.put("ai_key", null)
        assertFailsWith<IllegalStateException> { RefusingSecretStore.put("ai_key", "sk-test") }
    }
}
