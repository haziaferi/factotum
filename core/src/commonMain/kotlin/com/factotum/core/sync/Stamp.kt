package com.factotum.core.sync

/** When a field group was last written, and by which device. Ordered by [hlc], then [device]. */
data class Stamp(val hlc: Long, val device: String) : Comparable<Stamp> {
    override fun compareTo(other: Stamp): Int = compareValuesBy(this, other, Stamp::hlc, Stamp::device)
}

/**
 * A hybrid logical clock: never behind the wall clock, never behind any stamp it has seen, and
 * strictly increasing. A device whose clock runs fast therefore wins only until its stamp has been
 * seen; the next edit anywhere outranks it (ADR 01, `shared-later-edit-beats-fast-clock`).
 *
 * Not thread-safe: the repository calls it inside its write transaction. Seed [last] from storage
 * so a wall clock set backwards across a restart cannot issue an older stamp.
 */
class HybridClock(
    private val device: String,
    private val wallMillis: () -> Long,
    last: Long = 0,
) {
    var last: Long = last
        private set

    fun tick(): Stamp {
        last = maxOf(last + 1, wallMillis())
        return Stamp(last, device)
    }

    fun observe(stamp: Stamp) {
        if (stamp.hlc > last) last = stamp.hlc
    }
}
