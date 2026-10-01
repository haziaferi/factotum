package com.factotum.data.sync

import kotlin.random.Random

/**
 * Syncthing as ADR 13's simulator (`tools/folder_sim.py`) models it, one folder copy per device:
 * - every write replaces a whole file, and carries a version vector and a modification time;
 * - a session moves whole files with no order between them, and a cut session moves only some;
 * - two concurrent versions of one file: the older modification time loses and is kept beside it
 *   as a `.sync-conflict-` copy, which then syncs like any file; a change beats a concurrent delete.
 */
class SyncthingDouble(private val random: Random) {
    var now = 0L
    var conflictCopies = 0
        private set
    var bytesRead = 0L
        private set

    private val folders = mutableMapOf<String, Copy>()

    fun folder(device: String): SyncFolder = folders.getOrPut(device) { Copy(device) }

    /** The device and its copy of the folder are gone, as after a wipe. */
    fun forget(device: String) {
        folders.remove(device)
    }

    fun paths(device: String): Set<String> = folders.getValue(device).live()

    fun session(a: String, b: String, cut: Boolean = false) {
        val x = folders.getValue(a)
        val y = folders.getValue(b)
        var paths = (x.files.keys + y.files.keys).shuffled(random)
        if (cut) paths = paths.take(random.nextInt(paths.size + 1))
        for (path in paths) exchange(path, x, y)
    }

    private fun exchange(path: String, x: Copy, y: Copy) {
        val vx = x.files[path]
        val vy = y.files[path]
        when {
            vy == null || (vx != null && vx.vector covers vy.vector) -> y.files[path] = vx!!
            vx == null || vy.vector covers vx.vector -> x.files[path] = vy
            else -> {
                val merged = (vx.vector.keys + vy.vector.keys).associateWith { maxOf(vx.vector[it] ?: 0, vy.vector[it] ?: 0) }
                val winner = when {
                    vx.bytes == null -> vy
                    vy.bytes == null -> vx
                    vx.mtime != vy.mtime -> if (vx.mtime > vy.mtime) vx else vy
                    else -> if (vx.by > vy.by) vx else vy
                }
                val loser = if (winner === vx) vy else vx
                if (loser.bytes != null) {
                    val copy = conflictName(path, loser)
                    val kept = Version(loser.bytes, mapOf("$copy@${loser.by}" to 1), loser.mtime, loser.by)
                    x.files[copy] = kept
                    y.files[copy] = kept
                    conflictCopies++
                }
                val settled = winner.copy(vector = merged)
                x.files[path] = settled
                y.files[path] = settled
            }
        }
    }

    private fun conflictName(path: String, loser: Version): String {
        val dot = path.lastIndexOf('.')
        return path.substring(0, dot) + ".sync-conflict-${loser.mtime}-${loser.by}" + path.substring(dot)
    }

    private data class Version(val bytes: ByteArray?, val vector: Map<String, Int>, val mtime: Long, val by: String)

    private infix fun Map<String, Int>.covers(other: Map<String, Int>) = other.all { (k, n) -> (this[k] ?: 0) >= n }

    private inner class Copy(private val device: String) : SyncFolder {
        val files = mutableMapOf<String, Version>()

        fun live() = files.filterValues { it.bytes != null }.keys

        override fun list(dir: String): List<String> =
            live().filter { it.startsWith("$dir/") }.map { it.removePrefix("$dir/").substringBefore('/') }.distinct()

        override fun size(path: String): Long? = files[path]?.bytes?.size?.toLong()

        override fun read(path: String): ByteArray? = files[path]?.bytes?.copyOf()?.also { bytesRead += it.size }

        override fun replace(path: String, bytes: ByteArray) = write(path, bytes.copyOf())

        override fun delete(path: String) {
            if (files[path]?.bytes != null) write(path, null)
        }

        private fun write(path: String, bytes: ByteArray?) {
            val vector = files[path]?.vector.orEmpty()
            files[path] = Version(bytes, vector + (device to (vector[device] ?: 0) + 1), now, device)
        }
    }
}
