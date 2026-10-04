package com.factotum.data.image

import com.factotum.core.image.BlobName
import com.factotum.core.image.exifOrientation
import com.factotum.data.page.BlockEntity
import com.factotum.data.page.BlockImage
import com.factotum.data.page.toBlockEntity
import com.factotum.data.page.toRow
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.awt.Color
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import javax.imageio.ImageIO
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Tendril's image blocks (decision 14, answers 24-25 and 31-34). */
class ImagesTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun <T> two(seed: Int, body: World.(World.Device, World.Device) -> T): T {
        val w = World(tmp.root, seed)
        try {
            return w.body(w.Device("A"), w.Device("B"))
        } finally {
            w.close()
        }
    }

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private val day = 24 * 60 * 60 * 1000L

    @Test
    fun aPictureIsScaledToAt2048TurnedUprightAndStrippedOfItsMetadata() {
        val scaler = DesktopImageScaler()
        val big = scaler.scale(encode(picture(4096, 1024, Color.RED), "jpg"))
        assertEquals(listOf(2048, 512, "jpg"), listOf(big.width, big.height, big.format))
        assertEquals(2048 to 512, read(big.bytes).let { it.width to it.height })

        // A phone's photo, stored on its side with EXIF saying "turn 90°": left half red, right half blue.
        val sideways = withExif(encode(halves(40, 20), "jpg"), orientation = 6)
        assertEquals(6, exifOrientation(sideways))
        val upright = scaler.scale(sideways)
        assertEquals(20 to 40, upright.width to upright.height)
        val shown = read(upright.bytes)
        assertTrue(Color(shown.getRGB(10, 5)).red > 200, "top is the red half")
        assertTrue(Color(shown.getRGB(10, 35)).blue > 200, "bottom is the blue half")
        assertEquals(1, exifOrientation(upright.bytes))
        assertFalse(String(upright.bytes, Charsets.ISO_8859_1).contains("Exif"))

        // Transparency stays, as a PNG; an opaque PNG is stored as a JPEG.
        val clear = BufferedImage(10, 10, BufferedImage.TYPE_INT_ARGB)
        assertEquals("png", scaler.scale(encode(clear, "png")).format)
        assertEquals("jpg", scaler.scale(encode(picture(10, 10, Color.GREEN), "png")).format)
        // An RGBA picture with no transparent pixel, as most screenshots are, is stored as a JPEG too.
        val opaque = BufferedImage(10, 10, BufferedImage.TYPE_INT_ARGB).apply { createGraphics().apply { color = Color.GREEN; fillRect(0, 0, 10, 10); dispose() } }
        assertEquals("jpg", scaler.scale(encode(opaque, "png")).format)
        assertFailsWith<IllegalArgumentException> { scaler.scale("not a picture".toByteArray()) }
        Unit
    }

    @Test
    fun aPictureInsertedOnOneDeviceShowsOnTheOtherAndIsStoredOnce() = two(1) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        val bytes = encode(picture(64, 48, Color.ORANGE), "jpg")
        val block = go { a.images.insert(page, bytes, caption = "Roses") }
        go { a.images.insert(page, bytes, after = block) }
        assertEquals(1, a.blobs.files.size)
        settle(listOf(a, b))

        val shown = go { b.pages.outline(page) }.first()
        assertEquals("Roses", shown.content)
        val image = assertNotNull(shown.image)
        assertEquals(64 to 48, image.width to image.height)
        assertContentEquals(a.blobs.read(image.name), b.images.bytes(image))
        assertEquals(setOf("blobs/${image.name}"), syncthing.paths("B").filter { it.startsWith("blobs/") }.toSet())
    }

    @Test
    fun aPictureWhoseBytesHaveNotArrivedReadsAsWaitingAndDamagedBytesAreNotTaken() = two(2) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        go { a.images.insert(page, encode(picture(8, 8, Color.BLUE), "jpg")) }
        // The log goes out before the picture does.
        go { a.sync.export() }
        syncthing.session("A", "B")
        b.import()
        val image = requireNotNull(go { b.pages.outline(page) }.single().image)
        assertNull(go { b.images.bytes(image) })

        // A damaged copy in the folder is never kept.
        syncthing.folder("A").replace("blobs/${image.name}", "garbage".toByteArray())
        syncthing.session("A", "B")
        b.import()
        assertNull(b.images.bytes(image))

        // The device that holds it undamaged puts it back over the damaged copy, and then it arrives.
        settle(listOf(a, b))
        assertNotNull(b.images.bytes(image))
        Unit
    }

    @Test
    fun aPictureReplacedOnTwoDevicesKeepsTheLaterAndTheEarlierGoesToHistoryWithANotice() = two(3) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        val block = go { a.images.insert(page, encode(picture(8, 8, Color.BLUE), "jpg")) }
        settle(listOf(a, b))
        syncthing.now = 2 * day
        go { a.images.replace(block, encode(picture(8, 8, Color.RED), "jpg")) }
        syncthing.now = 2 * day + 1
        go { b.images.replace(block, encode(picture(8, 8, Color.GREEN), "jpg")) }
        settle(listOf(a, b))

        val later = requireNotNull(go { b.pages.outline(page) }.single().image)
        var red: BlockImage? = null
        for (d in listOf(a, b)) {
            assertEquals(later, go { d.pages.outline(page) }.single().image, d.name)
            val notice = go { d.pages.notices(page) }.single()
            val earlier = assertNotNull(notice.lostImage, d.name)
            red = earlier
            assertTrue(Color(read(requireNotNull(d.images.bytes(earlier))).getRGB(4, 4)).red > 200, d.name)
            // History brings the earlier picture back (answer 32).
            val kept = go { d.pages.revisions(page) }.first { it.noticeId == notice.id }
            go { d.pages.restoreRevision(kept.id) }
            assertEquals(earlier, go { d.pages.outline(page) }.single().image, d.name)
        }

        // Replaced again, the red picture is named by History alone: it leaves the folder after 30
        // days, and this device keeps it (answer 32).
        settle(listOf(a, b))
        go { a.pages.notices(page) }.forEach { go { a.pages.dismiss(it.id) } }
        syncthing.now = 3 * day
        go { a.images.replace(block, encode(picture(8, 8, Color.YELLOW), "jpg")) }
        settle(listOf(a, b))
        syncthing.now = 40 * day
        settle(listOf(a, b))
        val kept = requireNotNull(red)
        assertFalse("blobs/${kept.name}" in syncthing.paths("A"))
        assertNotNull(a.images.bytes(kept))
        Unit
    }

    @Test
    fun aDeletedBlocksPictureLeavesTheFolderAfter30DaysButARevivalWithinThemKeepsIt() = two(4) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        val gone = go { a.images.insert(page, encode(picture(8, 8, Color.BLUE), "jpg")) }
        val back = go { a.images.insert(page, encode(picture(8, 8, Color.RED), "jpg"), after = gone) }
        settle(listOf(a, b))
        val goneName = requireNotNull(go { a.pages.outline(page) }.first { it.id == gone }.image).name
        val backName = requireNotNull(go { a.pages.outline(page) }.first { it.id == back }.image).name

        syncthing.now = 2 * day
        go { a.pages.deleteBlock(gone) }
        go { a.pages.deleteBlock(back) }
        settle(listOf(a, b))
        syncthing.now = 20 * day
        settle(listOf(a, b))
        // Within the 30 days both stay in the folder.
        val held = syncthing.paths("A").filter { it.startsWith("blobs/") }.map { it.removePrefix("blobs/") }.toSet()
        assertTrue(goneName in held && backName in held)
        go { b.pages.setText(back, "Revived") }
        settle(listOf(a, b))
        syncthing.now = 33 * day
        settle(listOf(a, b))

        val inFolder = syncthing.paths("A").filter { it.startsWith("blobs/") }.map { it.removePrefix("blobs/") }.toSet()
        assertFalse(goneName in inFolder)
        assertTrue(backName in inFolder)
        // This device keeps the deleted block's picture: History and the block itself still name it.
        assertNotNull(a.images.bytes(BlockImage(goneName, 8, 8)))
        assertTrue(BlobName.isValid(goneName))
    }

    @Test
    fun aDamagedCopyHereIsDroppedAndFetchedAgainAndAConflictCopyIsCollected() = two(5) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        go { a.images.insert(page, encode(picture(8, 8, Color.BLUE), "jpg")) }
        settle(listOf(a, b))
        val image = requireNotNull(go { b.pages.outline(page) }.single().image)
        b.blobs.files[image.name] = "garbage".toByteArray()
        assertNull(b.images.bytes(image))
        syncthing.folder("A").replace("blobs/${image.name.removeSuffix(".jpg")}.sync-conflict-1-B.jpg", "x".toByteArray())
        settle(listOf(a, b))
        assertNotNull(b.images.bytes(image))
        assertEquals(listOf("blobs/${image.name}"), syncthing.paths("A").filter { it.startsWith("blobs/") })
    }

    @Test
    fun aPictureGivenToABlockMadeWithoutOneThenReplacedInTurnLeavesNoNotice() = two(6) { a, b ->
        syncthing.now = day
        val page = go { a.pages.create("Garden") }
        val block = go { a.pages.addBlock(page, type = com.factotum.data.page.BlockType.IMAGE) }
        settle(listOf(a, b))
        // A device that adds the picture, and one that first reads it, both start from it: B replacing
        // it after reading it is no clash for A.
        syncthing.now = 2 * day
        go { a.images.replace(block, encode(picture(8, 8, Color.BLUE), "jpg")) }
        a.export()
        syncthing.session("A", "B")
        b.import()
        syncthing.now = 3 * day
        go { b.images.replace(block, encode(picture(8, 8, Color.RED), "jpg")) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(emptyList(), go { d.pages.notices(page) }, d.name)

        // A picture taken away that loses to one put back offers nothing to bring back.
        syncthing.now = 5 * day
        go { a.pages.setImage(block, null) }
        syncthing.now = 5 * day + 1
        go { b.images.replace(block, encode(picture(8, 8, Color.YELLOW), "jpg")) }
        settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(emptyList(), go { d.pages.notices(page) }, d.name)
    }

    /** C passes A's first picture on after B, who read it from A, has replaced it: that copy is older than B's base, and no clash. */
    @Test
    fun aPictureReadOnceIsTheBaseSoACopyPassedOnLaterIsNoClash() {
        val w = World(tmp.root, 7)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val c = w.Device("C")
            w.syncthing.now = day
            val page = go { a.pages.create("Garden") }
            val block = go { a.pages.addBlock(page, type = com.factotum.data.page.BlockType.IMAGE) }
            w.settle(listOf(a, b, c))
            w.syncthing.now = 2 * day
            go { a.images.replace(block, encode(picture(8, 8, Color.BLUE), "jpg")) }
            a.export()
            w.syncthing.session("A", "B")
            b.import()
            w.syncthing.now = 3 * day
            go { b.images.replace(block, encode(picture(8, 8, Color.RED), "jpg")) }
            w.syncthing.session("A", "C")
            c.import()
            c.export()
            w.syncthing.session("B", "C")
            b.import()
            w.settle(listOf(a, b, c))
            for (d in listOf(a, b, c)) assertEquals(emptyList(), go { d.pages.notices(page) }, d.name)
        } finally {
            w.close()
        }
    }

    @Test
    fun aDatabaseUpgradedFromVersion21TakesPictures() {
        val file = java.io.File(tmp.root, "v21.db")
        com.factotum.data.createAtVersion(file, 21)
        val db = com.factotum.data.openFactotumDatabase(file).database
        try {
            val writes = com.factotum.data.LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
            var n = 0
            val pages = com.factotum.data.page.PageRepository(db, writes, { "id-${n++}" }, { 0 })
            val images = ImageRepository(pages, MemoryBlobStore(), DesktopImageScaler())
            val page = go { pages.create("Garden") }
            go { images.insert(page, encode(picture(8, 8, Color.BLUE), "jpg")) }
            assertEquals(8, go { pages.outline(page) }.single().image?.width)
        } finally {
            db.close()
        }
    }

    @Test
    fun everyExifOrientationShowsThePictureUpright() {
        val palette = listOf(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW, Color.CYAN, Color.MAGENTA)
        // Stored as 2 columns by 3 rows of 16-pixel cells, cell (c, r) coloured palette[r * 2 + c].
        val stored = BufferedImage(32, 48, BufferedImage.TYPE_INT_RGB).apply {
            createGraphics().apply { for (r in 0 until 3) for (c in 0 until 2) { color = palette[r * 2 + c]; fillRect(c * 16, r * 16, 16, 16) }; dispose() }
        }
        for (o in 1..8) {
            val shown = read(DesktopImageScaler().scale(withExif(encode(stored, "jpg"), o)).bytes)
            val (cols, rows) = if (o >= 5) 3 to 2 else 2 to 3
            assertEquals(cols * 16 to rows * 16, shown.width to shown.height, "orientation $o")
            for (y in 0 until rows) for (x in 0 until cols) {
                val (sx, sy) = when (o) {
                    1 -> x to y
                    2 -> 1 - x to y
                    3 -> 1 - x to 2 - y
                    4 -> x to 2 - y
                    5 -> y to x
                    6 -> y to 2 - x
                    7 -> 1 - y to 2 - x
                    else -> 1 - y to x
                }
                val seen = Color(shown.getRGB(x * 16 + 8, y * 16 + 8))
                val nearest = palette.minBy { (it.red - seen.red) * (it.red - seen.red) + (it.green - seen.green) * (it.green - seen.green) + (it.blue - seen.blue) * (it.blue - seen.blue) }
                assertEquals(palette[sy * 2 + sx], nearest, "orientation $o, cell $x,$y")
            }
        }
    }

    @Test
    fun aPictureClaimingMoreThan100MillionPixelsIsRefusedBeforeItsPixelsAreRead() {
        val png = encode(picture(4, 4, Color.BLUE), "png")
        // IHDR's width and height at bytes 16-23, its CRC after them: a 40000 by 40000 picture in a few bytes.
        val bomb = png.copyOf()
        for ((at, v) in listOf(16 to 40_000, 20 to 40_000)) for (i in 0 until 4) bomb[at + i] = (v shr (24 - 8 * i)).toByte()
        val crc = java.util.zip.CRC32().apply { update(bomb, 12, 17) }.value
        for (i in 0 until 4) bomb[29 + i] = (crc shr (24 - 8 * i)).toByte()
        val e = assertFailsWith<IllegalArgumentException> { DesktopImageScaler().scale(bomb) }
        assertTrue(e.message.orEmpty().contains("million pixels"))
    }

    @Test
    fun aLineNamingAPictureWithNoSizeOrABadNameIsRefused() {
        val block = BlockEntity(
            "b", "p", 1, "A", "IMAGE", 1, "A", "", null, 1, "A", null, "k", 1, "A",
            null, null, null, null, null, null, null, 1, "A", null, 1, "A",
            image = "${"a".repeat(64)}.jpg", imageWidth = 8, imageHeight = 8, imageHlc = 1, imageDevice = "A",
        )
        assertEquals(block, block.toRow().toBlockEntity())
        for (bad in listOf(block.copy(imageWidth = 0), block.copy(imageHeight = null), block.copy(image = "../x.jpg"))) {
            assertFailsWith<IllegalArgumentException> { bad.toRow().toBlockEntity() }
        }
        Unit
    }

    private fun picture(w: Int, h: Int, color: Color) = BufferedImage(w, h, BufferedImage.TYPE_INT_RGB).apply {
        createGraphics().apply { this.color = color; fillRect(0, 0, w, h); dispose() }
    }

    private fun halves(w: Int, h: Int) = BufferedImage(w, h, BufferedImage.TYPE_INT_RGB).apply {
        createGraphics().apply { color = Color.RED; fillRect(0, 0, w / 2, h); color = Color.BLUE; fillRect(w / 2, 0, w - w / 2, h); dispose() }
    }

    private fun encode(image: BufferedImage, format: String) = ByteArrayOutputStream().also { ImageIO.write(image, format, it) }.toByteArray()

    private fun read(bytes: ByteArray) = requireNotNull(ImageIO.read(ByteArrayInputStream(bytes)))

    /** [jpeg] with an APP1 EXIF segment saying [orientation] put just after its start. */
    private fun withExif(jpeg: ByteArray, orientation: Int): ByteArray {
        val tiff = listOf(0x4D, 0x4D, 0, 42, 0, 0, 0, 8, 0, 1, 0x01, 0x12, 0, 3, 0, 0, 0, 1, 0, orientation, 0, 0, 0, 0, 0, 0)
        val app1 = "Exif".map { it.code } + listOf(0, 0) + tiff
        val segment = (listOf(0xFF, 0xE1, (app1.size + 2) shr 8, (app1.size + 2) and 0xFF) + app1).map { it.toByte() }
        return jpeg.copyOfRange(0, 2) + segment.toByteArray() + jpeg.copyOfRange(2, jpeg.size)
    }
}
