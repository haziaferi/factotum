package com.factotum.core.sync

import kotlin.random.Random

/** Row identity (ADR 01): 26 Crockford base32 characters, a 48-bit millisecond time then 80 random bits. */
object Ulid {
    private const val ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    private const val MAX_TIME = (1L shl 48) - 1

    fun next(nowMillis: Long, random: Random = Random.Default): String {
        require(nowMillis in 0..MAX_TIME) { "time out of ULID range: $nowMillis" }
        val out = CharArray(26)
        var time = nowMillis
        for (i in 9 downTo 0) {
            out[i] = ALPHABET[(time and 31).toInt()]
            time = time shr 5
        }
        var buffer = 0
        var bits = 0
        var i = 10
        for (byte in random.nextBytes(10)) {
            buffer = (buffer shl 8) or (byte.toInt() and 0xFF)
            bits += 8
            while (bits >= 5) {
                bits -= 5
                out[i++] = ALPHABET[(buffer shr bits) and 31]
            }
            buffer = buffer and ((1 shl bits) - 1)
        }
        return out.concatToString()
    }

    fun isValid(id: String): Boolean =
        id.length == 26 && id[0] <= '7' && id.all { it in ALPHABET }

    fun timeOf(id: String): Long {
        require(isValid(id)) { "not a ULID: $id" }
        return id.take(10).fold(0L) { acc, c -> (acc shl 5) or ALPHABET.indexOf(c).toLong() }
    }
}
