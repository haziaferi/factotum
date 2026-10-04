package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

/** Equipoise's spec — daily masking-load formula: masked minutes, demand events, recovery minutes → 0..1. */
class MaskingLoadSpikeTest {

    private fun entry(masked: Int, events: Int, recovery: Int) = MaskingEntry(day = 1, maskedMinutes = masked, demandEvents = events, recoveryMinutes = recovery)

    @Test
    fun `an unmasked day with no demands and no recovery scores zero`() {
        assertEquals(0.0, MaskingLoad.daily(entry(0, 0, 0)), 1e-9)
    }

    @Test
    fun `a fully masked demanding day with no recovery scores near one`() {
        assertTrue(MaskingLoad.daily(entry(480, 12, 0)) >= 0.95)
    }

    @Test
    fun `two hours of recovery cannot erase a fully masked day`() {
        // Allostatic framing (Equipoise's notes): recovery offsets, it does not reset.
        assertTrue(MaskingLoad.daily(entry(480, 12, 120)) >= 0.45)
    }

    @Test
    fun `load is within zero and one for random entries`() {
        val rnd = Random(7)
        repeat(1000) {
            val v = MaskingLoad.daily(entry(rnd.nextInt(0, 1441), rnd.nextInt(0, 40), rnd.nextInt(0, 1441)))
            assertTrue("$v", v in 0.0..1.0)
        }
    }

    @Test
    fun `more recovery never raises the load`() {
        val rnd = Random(11)
        repeat(1000) {
            val e = entry(rnd.nextInt(0, 800), rnd.nextInt(0, 20), rnd.nextInt(0, 300))
            assertTrue(MaskingLoad.daily(e.copy(recoveryMinutes = e.recoveryMinutes + rnd.nextInt(1, 120))) <= MaskingLoad.daily(e) + 1e-12)
        }
    }

    @Test
    fun `more masked minutes or more demand events never lower the load`() {
        val rnd = Random(13)
        repeat(1000) {
            val e = entry(rnd.nextInt(0, 800), rnd.nextInt(0, 20), rnd.nextInt(0, 300))
            assertTrue(MaskingLoad.daily(e.copy(maskedMinutes = e.maskedMinutes + rnd.nextInt(1, 200))) >= MaskingLoad.daily(e) - 1e-12)
            assertTrue(MaskingLoad.daily(e.copy(demandEvents = e.demandEvents + rnd.nextInt(1, 5))) >= MaskingLoad.daily(e) - 1e-12)
        }
    }

    @Test
    fun `same entry always scores the same`() {
        val e = entry(300, 5, 45)
        assertEquals(MaskingLoad.daily(e), MaskingLoad.daily(e.copy()), 0.0)
    }
}
