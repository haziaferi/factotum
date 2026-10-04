package com.factotum.core.image

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ImagesTest {
    @Test
    fun anImageIsStoredWithItsLongestEdgeAt2048AndNeverEnlarged() {
        assertEquals(2048 to 1536, storedSize(4032, 3024))
        assertEquals(1536 to 2048, storedSize(3024, 4032))
        assertEquals(800 to 600, storedSize(800, 600))
        assertEquals(2048 to 2048, storedSize(2048, 2048))
        assertEquals(2048 to 1, storedSize(40_000, 2))
        assertFailsWith<IllegalArgumentException> { storedSize(0, 10) }
        Unit
    }

    @Test
    fun aBlobIsNamedByTheHashOfItsBytesAndItsFormat() {
        val hash = "a".repeat(64)
        assertEquals("$hash.jpg", BlobName.of(hash, "jpg"))
        assertEquals(hash, BlobName.hashOf("$hash.png"))
        listOf("$hash.gif", "${"A".repeat(64)}.jpg", "../$hash.jpg", "$hash.jpg.tmp", "abc.jpg", ".tmp-$hash.jpg").forEach { assertFalse(BlobName.isValid(it), it) }
        assertTrue(BlobName.isValid("$hash.png"))
        assertFailsWith<IllegalArgumentException> { BlobName.of(hash, "webp") }
        Unit
    }

    @Test
    fun theExifOrientationIsReadFromEitherByteOrder() {
        for (o in 1..8) {
            assertEquals(o, exifOrientation(jpegWithOrientation(o, bigEndian = true)))
            assertEquals(o, exifOrientation(jpegWithOrientation(o, bigEndian = false)))
        }
        assertEquals(1, exifOrientation(byteArrayOf(0xFF.toByte(), 0xD8.toByte(), 0xFF.toByte(), 0xDA.toByte(), 0, 2)))
        assertEquals(1, exifOrientation(byteArrayOf(0x89.toByte(), 'P'.code.toByte(), 'N'.code.toByte(), 'G'.code.toByte())))
        assertEquals(1, exifOrientation(jpegWithOrientation(6, bigEndian = true).copyOf(20)))
        assertEquals(1, exifOrientation(ByteArray(0)))
    }
}

/** A JPEG's first bytes: SOI, then an APP1 EXIF segment whose IFD0 holds one Orientation entry, then SOS. */
internal fun jpegWithOrientation(orientation: Int, bigEndian: Boolean): ByteArray {
    fun u16(v: Int) = if (bigEndian) listOf(v shr 8, v and 0xFF) else listOf(v and 0xFF, v shr 8)
    fun u32(v: Int) = if (bigEndian) u16(v shr 16) + u16(v and 0xFFFF) else u16(v and 0xFFFF) + u16(v shr 16)
    val tiff = (if (bigEndian) listOf(0x4D, 0x4D) else listOf(0x49, 0x49)) + u16(42) + u32(8) +
        u16(1) + u16(0x0112) + u16(3) + u32(1) + u16(orientation) + u16(0) + u32(0)
    val app1 = "Exif".map { it.code } + listOf(0, 0) + tiff
    val segment = listOf(0xFF, 0xE1, (app1.size + 2) shr 8, (app1.size + 2) and 0xFF) + app1
    return (listOf(0xFF, 0xD8) + segment + listOf(0xFF, 0xDA, 0, 2)).map { it.toByte() }.toByteArray()
}
