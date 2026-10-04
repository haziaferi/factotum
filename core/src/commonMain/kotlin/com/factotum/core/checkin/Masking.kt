package com.factotum.core.checkin

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.min

/** One day of the masking ledger (Equipoise). */
data class MaskingEntry(val day: Int, val maskedMinutes: Int, val demandEvents: Int, val recoveryMinutes: Int)

/**
 * Daily masking load in 0..1 (Equipoise):
 *
 *   m = min(masked / 480, 1)          fraction of an 8-hour day spent masking
 *   d = 1 − exp(−events / 4)          demand events saturate: 4 ≈ 0.63, 12 ≈ 0.95
 *   r = min(recovery / 120, 1)        two hours earn the full credit
 *   load = clamp(0.6 m + 0.4 d − 0.5 r, 0, 1)
 *
 * Recovery is a subtractive credit capped at 0.5, so it can offset but never erase a fully masked day —
 * the allostatic-load framing of Equipoise's notes. Accumulation is the 14-day index's job (BurnoutIndex), not this one.
 * Monotone by construction: non-decreasing in masked minutes and events, non-increasing in recovery.
 */
object MaskingLoad {
    const val FULL_DAY_MINUTES = 480.0
    const val EVENT_SCALE = 4.0
    const val FULL_RECOVERY_MINUTES = 120.0

    fun daily(e: MaskingEntry): Double {
        val m = min(e.maskedMinutes / FULL_DAY_MINUTES, 1.0)
        val d = 1.0 - exp(-e.demandEvents / EVENT_SCALE)
        val r = min(e.recoveryMinutes / FULL_RECOVERY_MINUTES, 1.0)
        return (0.6 * m + 0.4 * d - 0.5 * r).coerceIn(0.0, 1.0)
    }
}

/*
 * The ledger's three felt scales (Equipoise). Each level stands for one number Equipoise's
 * formula was tested with; the numbers are the model's and are never typed. Level *words* live in the UI
 * (a copy review waits for the screens) — these names are only identifiers.
 */

/** How much of today was masking? */
enum class MaskedLevel(val minutes: Int) { NONE(0), SOME(160), MOST(320), ALL_DAY(480) }

/** How demanding was today? */
enum class DemandLevel(val events: Int) { LIGHT(1), SOME(3), A_LOT(6), RELENTLESS(12) }

/** Did you get real recovery? "Enough" is the ceiling by decision — it earns the formula's full credit. */
enum class RecoveryLevel(val minutes: Int) { NONE(0), A_LITTLE(45), ENOUGH(120) }

data class FeltDay(val masked: MaskedLevel, val demand: DemandLevel, val recovery: RecoveryLevel)

object FeltScale {
    fun toEntry(day: Int, felt: FeltDay) =
        MaskingEntry(day, felt.masked.minutes, felt.demand.events, felt.recovery.minutes)

    /**
     * The levels a stored row shows as. Exact for anything written through [toEntry]; rows typed as free
     * numbers before v0.7 snap to the nearest level, ties downward.
     */
    fun fromEntry(e: MaskingEntry) = FeltDay(
        masked = nearest(MaskedLevel.entries, e.maskedMinutes) { it.minutes },
        demand = nearest(DemandLevel.entries, e.demandEvents) { it.events },
        recovery = nearest(RecoveryLevel.entries, e.recoveryMinutes) { it.minutes },
    )

    private inline fun <L> nearest(levels: List<L>, value: Int, of: (L) -> Int): L =
        levels.minBy { abs(of(it) - value) }   // minBy keeps the first (lower) level on a tie
}
