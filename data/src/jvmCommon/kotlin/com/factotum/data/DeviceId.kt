package com.factotum.data

import com.factotum.core.sync.Ulid
import java.io.File
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files

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
