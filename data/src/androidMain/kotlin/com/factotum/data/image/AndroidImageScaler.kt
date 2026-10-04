package com.factotum.data.image

import android.graphics.Bitmap
import android.graphics.ColorSpace
import android.graphics.ImageDecoder
import com.factotum.core.image.storedSize
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.nio.ByteBuffer

/**
 * Android's [ImageScaler], on [ImageDecoder] (API 28): it reads JPEG, PNG, WebP, HEIF and GIF (an
 * animation's first frame), turns a photo as its EXIF says, and decodes straight to the stored size.
 * [Bitmap.compress] writes no metadata, so camera details and location stay behind (answer 34).
 */
class AndroidImageScaler : ImageScaler {

    override fun scale(bytes: ByteArray): ScaledImage {
        val bitmap = try {
            ImageDecoder.decodeBitmap(ImageDecoder.createSource(ByteBuffer.wrap(bytes))) { decoder, info, _ ->
                val (w, h) = storedSize(info.size.width, info.size.height)
                decoder.setTargetSize(w, h)
                decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                // sRGB, as the desktop stores: a wide-gamut photo's own profile would not travel with no metadata.
                decoder.setTargetColorSpace(ColorSpace.get(ColorSpace.Named.SRGB))
            }
        } catch (e: IOException) {
            throw IllegalArgumentException("not a picture this device can read", e)
        }
        val alpha = bitmap.hasAlpha()
        val out = ByteArrayOutputStream()
        bitmap.compress(if (alpha) Bitmap.CompressFormat.PNG else Bitmap.CompressFormat.JPEG, if (alpha) 100 else JPEG_QUALITY, out)
        return ScaledImage(out.toByteArray(), if (alpha) "png" else "jpg", bitmap.width, bitmap.height).also { bitmap.recycle() }
    }

    private companion object {
        const val JPEG_QUALITY = 85
    }
}
