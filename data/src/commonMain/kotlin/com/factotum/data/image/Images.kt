package com.factotum.data.image

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.image.BlobName
import com.factotum.data.FactotumDatabase
import com.factotum.data.page.BlockImage
import com.factotum.data.page.BlockType
import com.factotum.data.page.PageRepository
import com.factotum.data.page.revisionImages
import com.factotum.data.sync.FolderLayout
import com.factotum.data.sync.SyncFolder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** A picture's bytes as this device keeps them, by blob name ([BlobName]); apart from the sync folder, which is only how they travel. */
interface BlobStore {
    fun read(name: String): ByteArray?
    fun write(name: String, bytes: ByteArray)
    fun delete(name: String)
    fun list(): List<String>
}

/** A picture as stored (answers 24, 33 and 34): its bytes in [format] (`jpg` or `png`) and its size. */
class ScaledImage(val bytes: ByteArray, val format: String, val width: Int, val height: Int)

/**
 * Turns a picture as picked into one as stored (decision 14, answers 24, 33 and 34): turned as its
 * EXIF says, its longest edge at most 2048 pixels, re-encoded with no metadata (a JPEG at about
 * quality 85, or a PNG when it has transparency; an animation's first frame). Platform code: each
 * platform decodes with what it has. Throws [IllegalArgumentException] for bytes it cannot read.
 */
interface ImageScaler {
    fun scale(bytes: ByteArray): ScaledImage
}

/** The SHA-256 of [bytes] in lower-case hex. */
internal expect fun sha256Hex(bytes: ByteArray): String

/** The largest picture taken in, before it is scaled: a phone's photo is well under it, and it keeps a decode within memory. */
const val MAX_PICKED_BYTES = 64 * 1024 * 1024

/**
 * Pictures in pages (Tendril's image blocks, decision 14 answers 24-25 and 31-34). A picture is
 * scaled and stored once by the hash of its bytes, kept on this device in [blobs], and named by
 * its block's picture group; [BlobSync] carries the bytes through the folder.
 */
internal class ImageRepository(
    private val pages: PageRepository,
    private val blobs: BlobStore,
    private val scaler: ImageScaler,
) {
    /** A new image block on [pageId] after [after] (first when null), under [parent], with [caption] as its text. */
    suspend fun insert(pageId: String, picked: ByteArray, after: String? = null, parent: String? = null, caption: String = ""): String =
        pages.addBlock(pageId, after, parent, BlockType.IMAGE, caption, image = store(picked))

    /** Replaces image block [blockId]'s picture; the one replaced stays in History. */
    suspend fun replace(blockId: String, picked: ByteArray) = pages.setImage(blockId, store(picked))

    /**
     * [image]'s bytes, or null while they have not arrived from the device that stored them (the
     * screen shows a placeholder of its size). A copy damaged here is dropped, so the next sync
     * fetches it again.
     */
    fun bytes(image: BlockImage): ByteArray? = verified(blobs, image.name)

    /** Scaling is work for the processor, kept off the caller's thread. */
    private suspend fun store(picked: ByteArray): BlockImage = withContext(Dispatchers.Default) {
        require(picked.size <= MAX_PICKED_BYTES) { "a picture is at most ${MAX_PICKED_BYTES / (1024 * 1024)} MB" }
        val scaled = scaler.scale(picked)
        val name = BlobName.of(sha256Hex(scaled.bytes), scaled.format)
        if (verified(blobs, name) == null) blobs.write(name, scaled.bytes)
        BlockImage(name, scaled.width, scaled.height)
    }
}

/** [name]'s bytes in [blobs] when they match their name; a damaged copy is deleted. */
private fun verified(blobs: BlobStore, name: String): ByteArray? {
    val bytes = blobs.read(name) ?: return null
    if (sha256Hex(bytes) == BlobName.hashOf(name)) return bytes
    blobs.delete(name)
    return null
}

/**
 * When this device last saw a picture unreferenced, apart from the folder's copy and its own: what
 * the 30 days of answer 31 count from. Local, never synced.
 */
@Entity(tableName = "blob_seen")
internal data class BlobSeenEntity(
    @PrimaryKey val name: String,
    @ColumnInfo(name = "folder_since") val folderSince: Long?,
    @ColumnInfo(name = "local_since") val localSince: Long?,
)

@Dao
internal interface BlobDao {
    @Query("SELECT * FROM blob_seen") suspend fun seen(): List<BlobSeenEntity>
    @Upsert suspend fun putSeen(rows: List<BlobSeenEntity>)
    @Query("DELETE FROM blob_seen WHERE name IN (:names)") suspend fun clearSeen(names: List<String>)
}

/**
 * Carries pictures through the sync folder, as `blobs/<name>` beside `devices/` (decision 14):
 * the folder only carries them, and each device keeps its own copy.
 *
 * - **Publish**, before the logs are exported: every picture a live block or an open notice names,
 *   held here undamaged and missing from the folder (or there with other bytes), is written
 *   there; so a live picture's copy collected or damaged comes back from any device holding it.
 * - **Fetch**, after an import: every picture this device names and lacks is read from the folder,
 *   and kept only when its bytes match its name.
 * - **Collect**: the folder's copy goes once this device has named it nowhere live for 30 days (a
 *   block deleted, a notice dismissed; answer 31), so a block revived within them keeps its
 *   picture, and a picture that arrives up to 30 days before the line naming it is not taken. This
 *   device's copy goes once nothing here names it, History and deleted blocks included (answer
 *   32), for as long. Syncthing's conflict copies of a picture go at once: a picture's bytes are
 *   its name, so the copy is the same picture or a damaged one.
 *
 * A known limit: a picture only History or a deleted block names travels no more once its folder
 * copy is collected, so a device that was away longer than 30 days restores that version without
 * it until a device holding it names it live again.
 */
internal class BlobSync(
    db: FactotumDatabase,
    private val folder: SyncFolder,
    private val blobs: BlobStore,
    private val wallMillis: () -> Long,
) {
    private val pageDao = db.pageDao()
    private val dao = db.blobDao()

    suspend fun exchange() {
        val pictured = pageDao.pictured()
        val shared = (pictured.filter { it.deletedAt == null }.mapNotNull { it.image } + pageDao.lostImages()).toSet()
        val kept = shared + pictured.mapNotNull { it.image } + pageDao.revisionBlocks().flatMap(::revisionImages)
        val listed = folder.list(BLOBS)
        listed.filter(FolderLayout::isConflictCopy).forEach { folder.delete("$BLOBS/$it") }
        val inFolder = listed.filter(BlobName::isValid).toSet()
        val held = blobs.list().filter(BlobName::isValid).toMutableSet()
        for (name in kept - held) {
            if (name !in inFolder) continue
            val bytes = folder.read("$BLOBS/$name")?.takeIf { sha256Hex(it) == BlobName.hashOf(name) } ?: continue
            blobs.write(name, bytes)
            held += name
        }
        for (name in shared intersect held) {
            val bytes = blobs.read(name) ?: continue
            if (name in inFolder && folder.size("$BLOBS/$name") == bytes.size.toLong()) continue
            val good = verified(blobs, name)
            if (good == null) held -= name else folder.replace("$BLOBS/$name", good)
        }

        val now = wallMillis()
        val seen = dao.seen().associateBy { it.name }
        val next = mutableListOf<BlobSeenEntity>()
        val cleared = mutableListOf<String>()
        for (name in inFolder + held) {
            val was = seen[name]
            val folderSince = if (name in shared || name !in inFolder) null else was?.folderSince ?: now
            val localSince = if (name in kept || name !in held) null else was?.localSince ?: now
            if (folderSince != null && now - folderSince >= GRACE_MS) folder.delete("$BLOBS/$name")
            if (localSince != null && now - localSince >= GRACE_MS) blobs.delete(name)
            if (folderSince == null && localSince == null) cleared += name else next += BlobSeenEntity(name, folderSince, localSince)
        }
        dao.putSeen(next)
        dao.clearSeen(cleared + (seen.keys - inFolder - held))
    }

    private companion object {
        const val BLOBS = "blobs"
        const val GRACE_MS = 30L * 24 * 60 * 60 * 1000
    }
}
