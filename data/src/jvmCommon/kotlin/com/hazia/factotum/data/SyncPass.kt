package com.hazia.factotum.data

import com.hazia.factotum.core.settings.Settings
import com.hazia.factotum.core.sync.Ulid
import com.hazia.factotum.data.image.DirectoryBlobStore
import com.hazia.factotum.data.image.ImageScaler
import com.hazia.factotum.data.settings.RefusingSecretStore
import com.hazia.factotum.data.settings.SecretStore
import com.hazia.factotum.data.settings.SettingsRepository
import com.hazia.factotum.data.sync.DirectorySyncFolder
import com.hazia.factotum.data.sync.loadClock
import com.hazia.factotum.data.time.localNow
import kotlinx.coroutines.runBlocking
import java.io.File
import java.io.FileNotFoundException
import java.io.RandomAccessFile
import java.nio.channels.OverlappingFileLockException

/** The pictures folder's name, beside the database on Windows (SPEC:R204). */
const val PICTURES_FOLDER = "pictures"

/** The file a running sync pass holds locked, beside the database (SPEC:R204). */
const val PASS_LOCK = "sync-pass.lock"

/** Where one device keeps what is not in the sync folder (SPEC:R204): its database, its id and its pictures. */
class DeviceFiles(val database: File, val deviceId: File, val pictures: File) {
    companion object {
        /** All three in one folder, as the Windows app keeps them in `%LOCALAPPDATA%\Factotum`. */
        fun inFolder(dir: File) = DeviceFiles(File(dir, DATABASE_NAME), File(dir, DEVICE_ID_FILE), File(dir, PICTURES_FOLDER))
    }
}

/** A pass that did not run, with the sentence the app prints (SPEC:R205). */
class SyncPassRefused(message: String) : Exception(message)

/**
 * What a sync pass did. [folder] is null when none was given or saved, and the pass then only
 * opened the database; [changed] counts the rows its import changed; [renewed] says the device
 * took a new id, which is [device].
 */
class SyncPassReport(val device: String, val folder: String?, val changed: Int, val renewed: Boolean)

/**
 * One sync pass, as the Windows app runs it until the screens (SPEC:R205): open the database,
 * import from the sync folder, take a new device id while one is owed (SPEC:R37), export, close.
 * A [folder] given is saved as this device's `sync_folder` and used by later passes.
 *
 * Throws [SyncPassRefused] when another pass is running (one started by hand while a scheduled one
 * runs: two would fight over the database, and both could take a new id), or when the folder does
 * not exist, which is never made: a drive that is not plugged in must not become a new, empty sync
 * folder. Blocks; call it off the main thread.
 */
fun syncPass(
    files: DeviceFiles,
    open: (File) -> DatabaseOpen<FactotumDatabase>,
    scaler: ImageScaler,
    folder: String? = null,
    secrets: SecretStore = RefusingSecretStore,
    wallMillis: () -> Long = System::currentTimeMillis,
): SyncPassReport {
    val dir = requireNotNull(files.database.absoluteFile.parentFile) { "no folder for ${files.database}" }.apply { mkdirs() }
    val lock = File(dir, PASS_LOCK)
    // Another pass opens the file too and only its lock refuses; another program (a virus scanner,
    // a backup) can hold the file itself, and Windows then refuses to open it at all.
    val file = try {
        RandomAccessFile(lock, "rw")
    } catch (_: FileNotFoundException) {
        throw SyncPassRefused("Another program holds ${lock.path} open.")
    }
    file.channel.use { channel ->
        // Null from another process; this process's own lock throws instead.
        val held = try {
            channel.tryLock()
        } catch (_: OverlappingFileLockException) {
            null
        } ?: throw SyncPassRefused("Another sync pass is running.")
        held.use {
            val opened = open(files.database)
            try {
                return runBlocking { pass(opened, files, scaler, folder, secrets, wallMillis) }
            } finally {
                opened.database.close()
            }
        }
    }
}

private suspend fun pass(
    opened: DatabaseOpen<FactotumDatabase>,
    files: DeviceFiles,
    scaler: ImageScaler,
    given: String?,
    secrets: SecretStore,
    wallMillis: () -> Long,
): SyncPassReport {
    val db = opened.database
    var device = deviceId(files.deviceId, wallMillis)
    val settings = SettingsRepository(db, LocalWrites(db, db.syncDao().loadClock(device, wallMillis)), secrets)
    val saved = settings.get(Settings.SYNC_FOLDER).ifEmpty { null }
    // Saved whole, and without `..`: a later pass, a scheduled one above all, starts in another folder.
    val path = given?.let { File(it).absoluteFile.normalize().path } ?: saved ?: return SyncPassReport(device, null, 0, false)
    if (!File(path).isDirectory) throw SyncPassRefused("No sync folder at $path.")
    if (path != saved) settings.set(Settings.SYNC_FOLDER, path)

    val folder = DirectorySyncFolder(File(path))
    val blobs = DirectoryBlobStore(files.pictures)
    // A database made anew (a recovery, which also loses `sync_folder`) reads its own files at its
    // first import, whichever pass that is (SPEC:R34): FolderSync keeps that in the database.
    suspend fun build(id: String) = Factotum(
        db, folder, id, db.syncDao().loadClock(id, wallMillis), secrets, blobs, scaler,
        { Ulid.next(wallMillis()) }, wallMillis, ::localNow,
    )

    var app = build(device)
    var renewed = false
    suspend fun renewIfOwed() {
        if (!app.newIdOwed()) return
        device = renewDeviceId(files.deviceId, wallMillis)
        app = build(device)
        renewed = true
    }
    // A debt left by a pass that stopped before its new id is paid before anything is read.
    renewIfOwed()
    val changed = app.import().changed
    renewIfOwed()
    // After a new id this export is a snapshot of everything the device holds (SPEC:R37).
    app.export()
    return SyncPassReport(device, path, changed, renewed)
}
