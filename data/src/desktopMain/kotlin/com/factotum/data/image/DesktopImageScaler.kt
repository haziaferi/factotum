package com.factotum.data.image

import com.factotum.core.image.MAX_EDGE
import com.factotum.core.image.exifOrientation
import com.factotum.core.image.storedSize
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import javax.imageio.IIOImage
import javax.imageio.ImageIO
import javax.imageio.ImageWriteParam

/**
 * The desktop's [ImageScaler], on the JDK's ImageIO: JPEG, PNG, GIF (its first frame) and BMP. It
 * writes no metadata, so a photo's camera details and location stay behind (answer 34). What the
 * JDK cannot read (WebP, HEIC, a CMYK JPEG) is refused as not a picture this device can read.
 */
class DesktopImageScaler : ImageScaler {

    override fun scale(bytes: ByteArray): ScaledImage {
        val source = try {
            decode(bytes)
        } catch (e: IOException) {
            throw IllegalArgumentException("not a picture this device can read", e)
        }
        val orientation = exifOrientation(bytes)
        // Scaled first, then turned: the turn walks every pixel, and there are fewer once scaled.
        val turns = orientation >= 5
        val (w, h) = storedSize(source.width, source.height)
        val alpha = source.colorModel.hasAlpha() && transparent(source)
        val scaled = turn(resize(source, w, h, alpha), orientation, alpha)
        val out = ByteArrayOutputStream()
        if (alpha) {
            ImageIO.write(scaled, "png", out)
        } else {
            val writer = ImageIO.getImageWritersByFormatName("jpg").next()
            try {
                val param = writer.defaultWriteParam.apply { compressionMode = ImageWriteParam.MODE_EXPLICIT; compressionQuality = JPEG_QUALITY }
                ImageIO.createImageOutputStream(out).use { stream ->
                    writer.output = stream
                    writer.write(null, IIOImage(scaled, null, null), param)
                }
            } finally {
                writer.dispose()
            }
        }
        return ScaledImage(out.toByteArray(), if (alpha) "png" else "jpg", if (turns) h else w, if (turns) w else h)
    }

    /**
     * [bytes]' first frame, its size read before its pixels: one past [MAX_PIXELS] is refused, as a
     * few megabytes can claim a size whose pixels fill no memory, and a large one is read every
     * n-th pixel, still at least twice the stored size, so a photo never fills memory either.
     */
    private fun decode(bytes: ByteArray): BufferedImage {
        val input = ImageIO.createImageInputStream(ByteArrayInputStream(bytes)) ?: throw IOException("no input")
        input.use {
            val reader = ImageIO.getImageReaders(input).asSequence().firstOrNull() ?: throw IOException("no reader")
            try {
                reader.input = input
                val width = reader.getWidth(0)
                val height = reader.getHeight(0)
                require(width.toLong() * height <= MAX_PIXELS) { "a picture is at most ${MAX_PIXELS / 1_000_000} million pixels" }
                val step = maxOf(1, maxOf(width, height) / (2 * MAX_EDGE))
                val param = reader.defaultReadParam.apply { setSourceSubsampling(step, step, 0, 0) }
                return reader.read(0, param)
            } finally {
                reader.dispose()
            }
        }
    }

    /** Whether any pixel lets what is behind it show: an RGBA picture with none, a screenshot most often, is stored as a JPEG. */
    private fun transparent(image: BufferedImage): Boolean {
        val raster = image.alphaRaster ?: return image.colorModel.hasAlpha()
        val row = IntArray(raster.width)
        return (0 until raster.height).any { y -> raster.getPixels(0, y, raster.width, 1, row).any { it < 255 } }
    }

    /** [image] at [w] by [h], halved step by step first so a large reduction keeps its detail. */
    private fun resize(image: BufferedImage, w: Int, h: Int, alpha: Boolean): BufferedImage {
        var current = image
        do {
            val stepW = maxOf(w, current.width / 2)
            val stepH = maxOf(h, current.height / 2)
            val next = BufferedImage(stepW, stepH, if (alpha) BufferedImage.TYPE_INT_ARGB else BufferedImage.TYPE_INT_RGB)
            next.createGraphics().apply {
                setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC)
                setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY)
                drawImage(current, 0, 0, stepW, stepH, null)
                dispose()
            }
            current = next
        } while (current.width != w || current.height != h)
        return current
    }

    /** [image] turned as EXIF [orientation] says, its pixels moved so it shows upright with no metadata. */
    private fun turn(image: BufferedImage, orientation: Int, alpha: Boolean): BufferedImage {
        if (orientation == 1) return image
        val w = image.width
        val h = image.height
        val (outW, outH) = if (orientation >= 5) h to w else w to h
        val from = image.getRGB(0, 0, w, h, null, 0, w)
        val to = IntArray(outW * outH)
        for (y in 0 until outH) for (x in 0 until outW) {
            val (sx, sy) = when (orientation) {
                2 -> w - 1 - x to y
                3 -> w - 1 - x to h - 1 - y
                4 -> x to h - 1 - y
                5 -> y to x
                6 -> y to h - 1 - x
                7 -> w - 1 - y to h - 1 - x
                else -> w - 1 - y to x
            }
            to[y * outW + x] = from[sy * w + sx]
        }
        return BufferedImage(outW, outH, if (alpha) BufferedImage.TYPE_INT_ARGB else BufferedImage.TYPE_INT_RGB).apply { setRGB(0, 0, outW, outH, to, 0, outW) }
    }

    private companion object {
        const val JPEG_QUALITY = 0.85f
        const val MAX_PIXELS = 100_000_000L
    }
}
