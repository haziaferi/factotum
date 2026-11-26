package com.hazia.factotum.data

import com.hazia.factotum.core.sync.Ulid
import java.io.File
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/**
 * The device-id file's name (SPEC:R204): beside the database on Windows, in the app's files on
 * Android, where the backup rules keep it out of Auto Backup and device transfer (SPEC:R32).
 */
const val DEVICE_ID_FILE = "device-id"

/**
 * This device's sync identity (ADR 01), kept in its own [file] (ADR 09): not a setting and not
 * in the database, so neither a settings reset nor a recovered database gives the device a new one.
 *
 * Created once: the new id is written to a temporary file and moved into place only if no other
 * process got there first, in which case that process's id is used. An unreadable file is set
 * aside and a new identity made; peers then see a new device, which costs only a stale name.
 */
fun deviceId(file: File, now: () -> Long = System::currentTimeMillis): String {
    if (file.exists()) {
        val id = file.readText().trim()
        if (Ulid.isValid(id)) return id
        setAside(file, now())
    }
    val dir = requireNotNull(file.absoluteFile.parentFile) { "no directory for ${file.path}" }.apply { mkdirs() }
    val tmp = Files.createTempFile(dir.toPath(), file.name, ".tmp")
    Files.writeString(tmp, Ulid.next(now()))
    try {
        Files.move(tmp, file.toPath())
    } catch (_: FileAlreadyExistsException) {
        Files.delete(tmp)
    }
    return file.readText().trim()
}

/**
 * A new identity for this device in place of [file]'s (SPEC:R37), once `Factotum.newIdOwed` says
 * another device writes under the old one. Written to a temporary file and moved over the old one in
 * one step, so a stop part way leaves one whole id, the old or the new.
 */
fun renewDeviceId(file: File, now: () -> Long = System::currentTimeMillis): String {
    val dir = requireNotNull(file.absoluteFile.parentFile) { "no directory for ${file.path}" }.apply { mkdirs() }
    val tmp = Files.createTempFile(dir.toPath(), file.name, ".tmp")
    val id = Ulid.next(now())
    Files.writeString(tmp, id)
    Files.move(tmp, file.toPath(), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)
    return id
}
