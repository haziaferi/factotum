package com.factotum.data.sync

/**
 * The folder Syncthing keeps in step between devices, seen through `/`-separated relative paths.
 * Blocking: call it off the main thread.
 */
interface SyncFolder {
    /** The names of the files and directories directly under [dir]; empty when [dir] does not exist. */
    fun list(dir: String): List<String>

    /** The file's length in bytes, or null when it does not exist. */
    fun size(path: String): Long?

    /** The whole file, or null when it does not exist. */
    fun read(path: String): ByteArray?

    /**
     * Replaces the file at [path] with [bytes] in one step (§3.13 requirement 3): readers see the old
     * file or the new one, never a mix. The bytes go first to `TEMP_PREFIX + name` beside it, which a
     * crash can leave behind; the exporter clears those in its own directory.
     */
    fun replace(path: String, bytes: ByteArray)

    fun delete(path: String)
}

internal const val TEMP_PREFIX = ".tmp-"

/** Where each device's files sit (ADR 13): `devices/<device-id>/log-<seq>.jsonl` and `snapshot-<seq>.jsonl`. */
internal object FolderLayout {
    const val DEVICES = "devices"
    private val SEGMENT = Regex("""log-(\d{6,})\.jsonl""")
    private val SNAPSHOT = Regex("""snapshot-(\d{6,})\.jsonl""")

    fun dir(device: String) = "$DEVICES/$device"
    fun segment(device: String, seq: Long) = "${dir(device)}/log-${pad(seq)}.jsonl"
    fun snapshot(device: String, seq: Long) = "${dir(device)}/snapshot-${pad(seq)}.jsonl"

    fun segmentSeq(name: String): Long? = SEGMENT.matchEntire(name)?.groupValues?.get(1)?.toLong()
    fun snapshotSeq(name: String): Long? = SNAPSHOT.matchEntire(name)?.groupValues?.get(1)?.toLong()

    /** Syncthing's name for the losing side of a clash on one file; only possible here if a device id was cloned. */
    fun isConflictCopy(name: String) = ".sync-conflict-" in name

    private fun pad(seq: Long) = seq.toString().padStart(6, '0')
}
