package com.factotum.core.recurrence

/**
 * The random draws of ADR 04's two random kinds, the same on every device and every app version
 * (SPEC §3.4, measured in `docs/spikes-2026-10-01.md` §9.4). The seed is FNV-1a 64 of the UTF-8
 * key `itemId|occurrenceDate|kind`; the generator is SplitMix64, written here rather than taken
 * from `kotlin.random`, whose algorithm is free to change between Kotlin versions.
 * Ported from the spike's `tools/spikes/seeded_draw/Draw.java`.
 */
object SeededDraw {

    /** A whole number in `[from, untilExclusive)`, drawn for [key]. */
    fun between(key: String, from: Int, untilExclusive: Int): Int {
        require(untilExclusive > from) { "empty range $from until $untilExclusive" }
        val bound = (untilExclusive - from).toULong()
        // The top sliver above the last multiple of bound would favour low results: draw again.
        // The same cut as the spike's Java (`compareUnsigned(r, -1 - limit) <= 0`), so the draws match it.
        val highest = ULong.MAX_VALUE - ULong.MAX_VALUE % bound
        var state = fnv1a64(key)
        while (true) {
            state += GOLDEN
            val r = mix(state)
            if (r <= highest) return from + (r % bound).toInt()
        }
    }

    internal fun fnv1a64(key: String): ULong {
        var h = 0xcbf29ce484222325uL
        for (b in key.encodeToByteArray()) {
            h = h xor (b.toULong() and 0xffuL)
            h *= 0x100000001b3uL
        }
        return h
    }

    private fun mix(state: ULong): ULong {
        var z = state
        z = (z xor (z shr 30)) * 0xBF58476D1CE4E5B9uL
        z = (z xor (z shr 27)) * 0x94D049BB133111EBuL
        return z xor (z shr 31)
    }

    private const val GOLDEN = 0x9E3779B97F4A7C15uL
}
