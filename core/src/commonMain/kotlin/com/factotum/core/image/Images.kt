package com.factotum.core.image

import kotlin.math.roundToInt

/** The longest edge an inserted image keeps (owner, 2026-10-04, decision 14 answers 24 and 33). */
const val MAX_EDGE = 2048

/**
 * The size an image of [width] by [height] is stored at: its longest edge at most [max], its shape
 * kept, never enlarged, and neither edge below one pixel.
 */
fun storedSize(width: Int, height: Int, max: Int = MAX_EDGE): Pair<Int, Int> {
    require(width > 0 && height > 0) { "an image has a size: ${width}x$height" }
    val longest = maxOf(width, height)
    if (longest <= max) return width to height
    val scale = max.toDouble() / longest
    return maxOf(1, (width * scale).roundToInt()) to maxOf(1, (height * scale).roundToInt())
}

/**
 * A stored image's name in the sync folder and on each device: the SHA-256 of its bytes as stored,
 * in lower-case hex, and its format, so two devices storing the same picture store one file, and
 * bytes that do not match their name are known for damaged.
 */
object BlobName {
    /** The formats an image is stored in (answer 33): a photo as JPEG, one with transparency as PNG. */
    val FORMATS = setOf("jpg", "png")
    private val NAME = Regex("""^([0-9a-f]{64})\.(jpg|png)$""")

    fun of(sha256: String, format: String): String = "$sha256.$format".also { require(isValid(it)) { "not a blob name: $it" } }

    /** Whether [name] is one this app writes; anything else in the folder is left alone. */
    fun isValid(name: String) = NAME.matches(name)

    /** The hash [name] promises. */
    fun hashOf(name: String): String = requireNotNull(NAME.matchEntire(name)) { "not a blob name: $name" }.groupValues[1]
}

/**
 * The EXIF orientation of a JPEG (1 to 8, as EXIF numbers them), or 1 when it has none, is not a
 * JPEG, or its EXIF cannot be read: a phone's photo is stored as the sensor saw it, with this
 * saying how to turn it, and the turn is applied to the pixels on insert (answer 34).
 */
fun exifOrientation(jpeg: ByteArray): Int {
    fun u8(i: Int) = jpeg[i].toInt() and 0xFF
    fun u16(i: Int, big: Boolean) = if (big) (u8(i) shl 8) or u8(i + 1) else (u8(i + 1) shl 8) or u8(i)
    fun u32(i: Int, big: Boolean) = if (big) (u16(i, true) shl 16) or u16(i + 2, true) else (u16(i + 2, false) shl 16) or u16(i, false)
    return runCatching {
        if (u16(0, true) != 0xFFD8) return 1
        var at = 2
        while (at + 4 <= jpeg.size && u8(at) == 0xFF) {
            val marker = u8(at + 1)
            val length = u16(at + 2, true)
            // Start of scan: the image data begins, and EXIF comes before it.
            if (marker == 0xDA) return 1
            if (marker == 0xE1 && CharArray(6) { u8(at + 4 + it).toChar() }.concatToString() == "Exif\u0000\u0000") {
                val tiff = at + 10
                val big = u16(tiff, true) == 0x4D4D
                val ifd = tiff + u32(tiff + 4, big)
                for (e in 0 until u16(ifd, big)) {
                    val entry = ifd + 2 + 12 * e
                    if (u16(entry, big) == 0x0112) return u16(entry + 8, big).takeIf { it in 1..8 } ?: 1
                }
                return 1
            }
            at += 2 + length
        }
        1
    }.getOrDefault(1)
}
