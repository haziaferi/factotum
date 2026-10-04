package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

/**
 * Equipoise's spec — the 14-day burnout early-warning index must separate a "sustainable" fortnight from a
 * "sliding" one, tolerate missing days and null sleep, and never move the wrong way.
 */
class BurnoutIndexSpikeTest {

    /** Moderate masking, adequate recovery, flat energy, decent sleep. */
    private val sustainable: List<DayRecord> = (1..14).map { d ->
        DayRecord(
            day = d,
            energy = 0.55 + 0.10 * ((d % 3) / 2.0),
            maskingLoad = MaskingLoad.daily(MaskingEntry(d, maskedMinutes = 210 + 20 * (d % 4), demandEvents = 2 + d % 3, recoveryMinutes = 90)),
            sensoryLoad = 0.30,
            sleepHours = 7.5,
        )
    }

    /** Masking rising, recovery shrinking, energy declining, sensory load climbing, sleep eroding. */
    private val sliding: List<DayRecord> = (1..14).map { d ->
        val t = (d - 1) / 13.0
        DayRecord(
            day = d,
            energy = 0.70 - 0.45 * t,
            maskingLoad = MaskingLoad.daily(MaskingEntry(d, maskedMinutes = (300 + 240 * t).toInt(), demandEvents = (3 + 7 * t).toInt(), recoveryMinutes = (90 - 80 * t).toInt())),
            sensoryLoad = 0.35 + 0.25 * t,
            sleepHours = 7.5 - 2.0 * t,
        )
    }

    @Test
    fun `sliding scores at least a quarter higher than sustainable`() {
        val s = BurnoutIndex.compute(sustainable)
        val g = BurnoutIndex.compute(sliding)
        println("SPIKE-9.2 sustainable index=${"%.3f".format(s.index)} sliding index=${"%.3f".format(g.index)} " +
            "(mask ${"%.2f".format(s.maskingLoad)}/${"%.2f".format(g.maskingLoad)} trend ${"%.2f".format(s.energyTrend)}/${"%.2f".format(g.energyTrend)})")
        assertTrue("sustainable=${s.index} sliding=${g.index}", g.index - s.index >= 0.25)
    }

    @Test
    fun `only the sliding fortnight crosses the default threshold`() {
        assertFalse(BurnoutIndex.compute(sustainable).thresholdCrossed)
        assertTrue(BurnoutIndex.compute(sliding).thresholdCrossed)
    }

    @Test
    fun `index stays within zero and one on random windows`() {
        val rnd = Random(5)
        repeat(300) {
            val window = (1..14).filter { rnd.nextDouble() < 0.85 }.map { d ->
                DayRecord(d, rnd.nextDouble(), rnd.nextDouble(), rnd.nextDouble(), if (rnd.nextBoolean()) rnd.nextDouble() * 10 else null)
            }
            val v = BurnoutIndex.compute(window).index
            assertTrue("$v", v in 0.0..1.0)
        }
    }

    @Test
    fun `raising any single day's masking or sensory load never lowers the index`() {
        val rnd = Random(9)
        repeat(200) {
            val base = sliding.map { it.copy(maskingLoad = rnd.nextDouble() * 0.8, sensoryLoad = rnd.nextDouble() * 0.8) }
            val i = rnd.nextInt(base.size)
            val before = BurnoutIndex.compute(base).index
            val moreMask = base.toMutableList().also { it[i] = it[i].copy(maskingLoad = (it[i].maskingLoad!! + 0.2).coerceAtMost(1.0)) }
            val moreSensory = base.toMutableList().also { it[i] = it[i].copy(sensoryLoad = (it[i].sensoryLoad!! + 0.2).coerceAtMost(1.0)) }
            assertTrue(BurnoutIndex.compute(moreMask).index >= before - 1e-12)
            assertTrue(BurnoutIndex.compute(moreSensory).index >= before - 1e-12)
        }
    }

    @Test
    fun `dropping two days changes verdicts by nothing and the index by little`() {
        val gaps = setOf(4, 9)
        val s = BurnoutIndex.compute(sustainable); val s2 = BurnoutIndex.compute(sustainable.filter { it.day !in gaps })
        val g = BurnoutIndex.compute(sliding); val g2 = BurnoutIndex.compute(sliding.filter { it.day !in gaps })
        assertEquals(s.thresholdCrossed, s2.thresholdCrossed)
        assertEquals(g.thresholdCrossed, g2.thresholdCrossed)
        assertTrue(kotlin.math.abs(s.index - s2.index) <= 0.05)
        assertTrue(kotlin.math.abs(g.index - g2.index) <= 0.05)
    }

    @Test
    fun `null sleep everywhere reweighs the other terms and produces no NaN`() {
        // Factotum's rule (decision 14): a term with no data is left out and the weights spread over the rest.
        val noSleep = sliding.map { it.copy(sleepHours = null) }
        val v = BurnoutIndex.compute(noSleep)
        val with = BurnoutIndex.compute(sliding)
        assertFalse(v.index.isNaN())
        val trend = (-with.energyTrend / BurnoutIndex.TREND_SATURATION).coerceIn(0.0, 1.0)
        assertEquals((0.35 * with.maskingLoad + 0.30 * trend + 0.20 * with.sensoryLoad) / 0.85, v.index, 1e-9)
    }

    @Test
    fun `a person who tracks nothing but masking can still reach the top`() {
        val maskedOnly = (1..14).map { DayRecord(day = it, maskingLoad = 1.0) }
        assertEquals(1.0, BurnoutIndex.compute(maskedOnly).index, 1e-9)
        assertEquals(0.0, BurnoutIndex.compute(emptyList()).index, 1e-9)
    }

    @Test
    fun `an empty window scores zero and does not cross`() {
        val r = BurnoutIndex.compute(emptyList())
        assertEquals(0.0, r.index, 0.0)
        assertFalse(r.thresholdCrossed)
    }

    @Test
    fun `energy trend is the per-fortnight slope and is negative when energy declines`() {
        assertTrue(BurnoutIndex.compute(sliding).energyTrend < -0.3)
        assertTrue(kotlin.math.abs(BurnoutIndex.compute(sustainable).energyTrend) < 0.1)
    }

    @Test
    fun `same window always scores the same`() {
        assertEquals(BurnoutIndex.compute(sliding), BurnoutIndex.compute(sliding.map { it.copy() }))
    }
}
