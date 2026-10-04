package com.factotum.data.image

import com.factotum.core.image.BlobName
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption.ATOMIC_MOVE
import java.nio.file.StandardCopyOption.REPLACE_EXISTING
import java.security.MessageDigest

internal actual fun sha256Hex(bytes: ByteArray): String =
    MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }

/** A [BlobStore] in a directory of the app's own storage; a picture is written whole or not at all. */
class DirectoryBlobStore(private val dir: File) : BlobStore {

    override fun read(name: String): ByteArray? = file(name).takeIf { it.isFile }?.readBytes()

    override fun write(name: String, bytes: ByteArray) {
        val target = file(name)
        dir.mkdirs()
        val tmp = File(dir, ".tmp-$name")
        tmp.writeBytes(bytes)
        Files.move(tmp.toPath(), target.toPath(), ATOMIC_MOVE, REPLACE_EXISTING)
    }

    override fun delete(name: String) {
        Files.deleteIfExists(file(name).toPath())
    }

    override fun list(): List<String> = dir.list()?.filter(BlobName::isValid).orEmpty()

    /** Only a name this app writes reaches the disk, so no name walks out of [dir]. */
    private fun file(name: String) = File(dir, name.also { require(BlobName.isValid(it)) { "not a blob name: $it" } })
}
