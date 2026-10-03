package com.factotum.core.checkin

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.random.Random

/**
 * Stability is measured, not asked (Equipoise SPEC §3.1, decided 2026-09-12): the spread of a day's check-ins.
 * A day with one check-in counts as stable at half weight — the user's reading: one log and no return
 * means no swing worth reporting. Weighted mean over the last 30 logged days, live from 15.
 */
class StabilityTrendTest {

    private fun c(e: Double, p: Double) = CheckIn(e, p)
    private fun day(d: Int, vararg cs: CheckIn) = cs.map { Logged(d, it) }

    companion object { const val TODAY = 20_000 }

    @Test
    fun `a single check-in day is stable at half weight`() {
        assertEquals(StabilityTrend.DayValue(1.0, 0.5), StabilityTrend.dayValue(listOf(c(0.3, 0.3))))
    }

    @Test
    fun `two identical check-ins are fully stable at full weight`() {
        assertEquals(StabilityTrend.DayValue(1.0, 1.0), StabilityTrend.dayValue(listOf(c(0.6, 0.7), c(0.6, 0.7))))
    }

    @Test
    fun `the full swing of the scale is zero stability`() {
        assertEquals(StabilityTrend.DayValue(0.0, 1.0), StabilityTrend.dayValue(listOf(c(0.0, 0.0), c(1.0, 1.0), c(0.5, 0.5))))
    }

    @Test
    fun `spread is the range of the weighted score, not of either axis`() {
        // (0.2, 0.8) = 1.4 and (0.6, 0.7) = 1.65: spread 0.25 -> 1 - 0.25/2.5 = 0.9
        assertEquals(0.9, StabilityTrend.dayValue(listOf(c(0.2, 0.8), c(0.6, 0.7))).value, 1e-9)
    }

    @Test
    fun `no index before fifteen logged days`() {
        val fourteen = (1..14).flatMap { day(TODAY - it, c(0.6, 0.7)) }
        assertNull(StabilityTrend.index(TODAY, fourteen))
        val fifteen = fourteen + day(TODAY - 15, c(0.6, 0.7))
        assertEquals(1.0, StabilityTrend.index(TODAY, fifteen)!!, 1e-9)
    }

    @Test
    fun `weighted mean - single days at half weight, swing days at full`() {
        // Ten single-check-in days (value 1, weight 0.5) and five days with a 1.25 swing (value 0.5, weight 1):
        // (10 * 0.5 * 1 + 5 * 1 * 0.5) / (5 + 5) = 0.75
        val singles = (1..10).flatMap { day(TODAY - it, c(0.6, 0.7)) }
        val swings = (11..15).flatMap { day(TODAY - it, c(0.2, 0.2), c(0.7, 0.7)) }   // 0.5 vs 1.75
        assertEquals(0.75, StabilityTrend.index(TODAY, singles + swings)!!, 1e-9)
    }

    @Test
    fun `only the last thirty logged days count`() {
        val jumpyLongAgo = (31..45).flatMap { day(TODAY - it, c(0.0, 0.0), c(1.0, 1.0)) }
        val calmRecent = (1..30).flatMap { day(TODAY - it, c(0.6, 0.7)) }
        assertEquals(1.0, StabilityTrend.index(TODAY, jumpyLongAgo + calmRecent)!!, 1e-9)
    }

    @Test
    fun `days need not be consecutive and order does not matter`() {
        val sparse = (0 until 20).flatMap { i -> day(TODAY - 1 - i * 4, c(0.5, 0.5), c(0.5, 0.6)) }
        val a = StabilityTrend.index(TODAY, sparse)!!
        val b = StabilityTrend.index(TODAY, sparse.shuffled(Random(5)))!!
        assertEquals(a, b, 0.0)
        assertTrue(a in 0.9..1.0)
    }

    @Test
    fun `days after today are ignored`() {
        val history = (1..15).flatMap { day(TODAY - it, c(0.6, 0.7)) } + day(TODAY + 1, c(0.0, 0.0), c(1.0, 1.0))
        assertEquals(1.0, StabilityTrend.index(TODAY, history)!!, 1e-9)
    }

    @Test
    fun `always within zero and one`() {
        val rng = Random(11)
        repeat(300) {
            val history = (1..rng.nextInt(15, 60)).flatMap { d ->
                day(TODAY - d, *Array(rng.nextInt(1, 4)) { c(rng.nextDouble(), rng.nextDouble()) })
            }
            val v = StabilityTrend.index(TODAY, history)!!
            assertTrue("$v", v in 0.0..1.0)
        }
    }
}
