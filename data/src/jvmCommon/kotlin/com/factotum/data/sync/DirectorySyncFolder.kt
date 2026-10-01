package com.factotum.data.sync

import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption.ATOMIC_MOVE
import java.nio.file.StandardCopyOption.REPLACE_EXISTING

/** A [SyncFolder] on a directory the app can open as a [File]: Windows, and Android's own storage. */
class DirectorySyncFolder(private val root: File) : SyncFolder {

    override fun list(dir: String): List<String> = File(root, dir).list()?.toList().orEmpty()

    override fun size(path: String): Long? = File(root, path).takeIf { it.isFile }?.length()

    override fun read(path: String): ByteArray? = File(root, path).takeIf { it.isFile }?.readBytes()

    override fun replace(path: String, bytes: ByteArray) {
        val target = File(root, path)
        val dir = requireNotNull(target.parentFile) { "no directory for $path" }.apply { mkdirs() }
        val tmp = File(dir, TEMP_PREFIX + target.name)
        tmp.writeBytes(bytes)
        Files.move(tmp.toPath(), target.toPath(), ATOMIC_MOVE, REPLACE_EXISTING)
    }

    override fun delete(path: String) {
        Files.deleteIfExists(File(root, path).toPath())
    }
}
