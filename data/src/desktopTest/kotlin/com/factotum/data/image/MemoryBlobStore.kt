package com.factotum.data.image

/** A device's pictures in memory, as a test's devices keep them. */
internal class MemoryBlobStore : BlobStore {
    val files = mutableMapOf<String, ByteArray>()

    override fun read(name: String) = files[name]?.copyOf()
    override fun write(name: String, bytes: ByteArray) { files[name] = bytes.copyOf() }
    override fun delete(name: String) { files.remove(name) }
    override fun list() = files.keys.toList()
}
