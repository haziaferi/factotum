package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The ledger asks for perception, not measurement (Equipoise): three felt scales, each
 * level standing for one number the §9.2 formula was tested with. The numbers are the model's, never
 * typed, so the mapping is a table in `domain/` and the rows in Room are only ever its outputs.
 */
class FeltScaleTest {

    @Test
    fun `masking levels are the four fractions of an eight-hour day`() {
        assertEquals(listOf(0, 160, 320, 480), MaskedLevel.entries.map { it.minutes })
        assertEquals(MaskingLoad.FULL_DAY_MINUTES.toInt(), MaskedLevel.ALL_DAY.minutes)
    }

    @Test
    fun `demand levels are one, three, six and twelve events`() {
        assertEquals(listOf(1, 3, 6, 12), DemandLevel.entries.map { it.events })
    }

    @Test
    fun `recovery levels stop at enough, which is the full credit`() {
        assertEquals(listOf(0, 45, 120), RecoveryLevel.entries.map { it.minutes })
        assertEquals(MaskingLoad.FULL_RECOVERY_MINUTES.toInt(), RecoveryLevel.ENOUGH.minutes)
    }

    @Test
    fun `a felt day becomes the entry the formula expects`() {
        val entry = FeltScale.toEntry(day = 20_000, felt = FeltDay(MaskedLevel.MOST, DemandLevel.A_LOT, RecoveryLevel.A_LITTLE))
        assertEquals(MaskingEntry(day = 20_000, maskedMinutes = 320, demandEvents = 6, recoveryMinutes = 45), entry)
    }

    @Test
    fun `every combination round-trips exactly`() {
        for (m in MaskedLevel.entries) for (d in DemandLevel.entries) for (r in RecoveryLevel.entries) {
            val felt = FeltDay(m, d, r)
            assertEquals(felt, FeltScale.fromEntry(FeltScale.toEntry(1, felt)))
        }
    }

    @Test
    fun `numbers that were typed before v0_7 snap to the nearest level, ties downward`() {
        // 100 min is nearer "some" (160) than "none" (0); 400 is exactly between "most" and "all day".
        assertEquals(
            FeltDay(MaskedLevel.SOME, DemandLevel.LIGHT, RecoveryLevel.ENOUGH),
            FeltScale.fromEntry(MaskingEntry(1, maskedMinutes = 100, demandEvents = 2, recoveryMinutes = 100)),
        )
        assertEquals(MaskedLevel.MOST, FeltScale.fromEntry(MaskingEntry(1, 400, 0, 0)).masked)
        assertEquals(RecoveryLevel.ENOUGH, FeltScale.fromEntry(MaskingEntry(1, 0, 0, 600)).recovery)
    }

    @Test
    fun `each step on each scale moves the load - no level is dead`() {
        fun load(m: MaskedLevel, d: DemandLevel, r: RecoveryLevel) = MaskingLoad.daily(FeltScale.toEntry(1, FeltDay(m, d, r)))
        // Masking and demand raise the load, recovery lowers it, strictly at every step, from a mid baseline.
        val masked = MaskedLevel.entries.map { load(it, DemandLevel.SOME, RecoveryLevel.NONE) }
        val demand = DemandLevel.entries.map { load(MaskedLevel.SOME, it, RecoveryLevel.NONE) }
        val recovery = RecoveryLevel.entries.map { load(MaskedLevel.MOST, DemandLevel.SOME, it) }
        assertTrue("$masked", masked.zipWithNext().all { (a, b) -> b > a + 1e-9 })
        assertTrue("$demand", demand.zipWithNext().all { (a, b) -> b > a + 1e-9 })
        assertTrue("$recovery", recovery.zipWithNext().all { (a, b) -> b < a - 1e-9 })
    }

    @Test
    fun `enough recovery offsets but never erases an all-day mask`() {
        val worst = FeltScale.toEntry(1, FeltDay(MaskedLevel.ALL_DAY, DemandLevel.RELENTLESS, RecoveryLevel.ENOUGH))
        assertTrue(MaskingLoad.daily(worst) > 0.4)
        val best = FeltScale.toEntry(1, FeltDay(MaskedLevel.NONE, DemandLevel.LIGHT, RecoveryLevel.ENOUGH))
        assertEquals(0.0, MaskingLoad.daily(best), 1e-12)
    }
}
