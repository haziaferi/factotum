package com.factotum.core.checkin

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * "Lower than usual" (Equipoise SPEC §3.2, decided 2026-09-12): a weighted state score compared against three
 * layers — a fast personal baseline, a slow "lowest good" baseline, and an absolute floor. Any layer
 * saying low is enough. History carries each check-in with its logged day and excludes the check-in being judged; order is irrelevant.
 */
class LowMomentTest {

    private fun c(e: Double, p: Double) = CheckIn(e, p)

    /** [n] consecutive logged days, [perDay] check-ins each, ending yesterday relative to [TODAY]. */
    private fun days(n: Int, e: Double, p: Double, perDay: Int = 1, endDay: Int = TODAY - 1): List<Logged> =
        (0 until n).flatMap { i -> List(perDay) { Logged(endDay - (n - 1) + i, c(e, p)) } }

    private fun assess(now: CheckIn, history: List<Logged>) = LowMoment.assess(now, TODAY, history)

    companion object { const val TODAY = 20_000 }

    @Test
    fun `score weighs pleasantness one and a half times energy`() {
        assertEquals(0.2 + 1.5 * 0.8, LowMoment.score(c(0.2, 0.8)), 1e-9)
        // Agitation (high energy, unpleasant) scores lower than rest (low energy, pleasant).
        assertTrue(LowMoment.score(c(0.9, 0.1)) < LowMoment.score(c(0.2, 0.8)))
    }

    @Test
    fun `before fifteen logged days only the floor applies`() {
        val history = days(10, 0.6, 0.7)
        assertTrue(assess(c(0.4, 0.4), history).low)      // under the midline on both axes
        assertTrue(assess(c(0.9, 0.1), history).low)      // agitation is under the floor too
        val v = assess(c(0.55, 0.55), history)              // the lowest of this history, but not low
        assertFalse(v.low)
        assertEquals(null, v.fastCutoff)
        assertEquals(null, v.slowCutoff)
    }

    @Test
    fun `rest is above the floor, agitation is under it`() {
        val rest = assess(c(0.2, 0.8), days(10, 0.6, 0.7))
        assertFalse(rest.byFloor)
        assertFalse(rest.low)                                          // before the 15th only the floor applies
        assertTrue(assess(c(0.9, 0.1), days(10, 0.6, 0.7)).byFloor)
    }

    @Test
    fun `rest can still be lower than usual when the energy drop outweighs the mood gain`() {
        // Weight 1.5 lets mood outweigh energy, it does not make rest immune: for someone usually at
        // (0.6, 0.7) = 1.65, a content-but-drained (0.2, 0.8) = 1.40 is lower than usual by the score.
        val v = assess(c(0.2, 0.8), days(40, 0.6, 0.7))
        assertFalse(v.byFloor)
        assertTrue(v.byFast)
        // ...whereas for someone whose usual is (0.4, 0.6) = 1.30 it is not.
        assertFalse(assess(c(0.2, 0.8), days(40, 0.4, 0.6)).low)
    }

    @Test
    fun `fast baseline - the lowest quarter of the last thirty`() {
        // 20 check-ins with scores 1.6, 1.8, 2.0, 2.2 (five each): the lower quartile is 1.8.
        val history = days(5, 0.4, 0.8, endDay = TODAY - 16) + days(5, 0.6, 0.8, endDay = TODAY - 11) +
            days(5, 0.8, 0.8, endDay = TODAY - 6) + days(5, 1.0, 0.8)
        val below = assess(c(0.5, 0.8), history)   // 1.7 — above the floor, below the person's usual
        assertTrue(below.low)
        assertTrue(below.byFast)
        assertFalse(below.byFloor)
        assertEquals(1.8, below.fastCutoff!!, 1e-9)
        assertFalse(assess(c(0.7, 0.8), history).low)   // 1.9 — inside the usual range
        assertFalse(assess(c(0.6, 0.8), history).low)   // 1.8 — at the cutoff is not below it
    }

    @Test
    fun `fast baseline only looks at the last thirty`() {
        // 30 bad days long ago, then 30 good days: the bad days have left the fast window.
        val history = days(30, 0.3, 0.6, endDay = TODAY - 31) + days(30, 0.8, 0.8)
        val v = assess(c(0.7, 0.75), history)              // 1.825 vs a usual of 2.0
        assertTrue(v.byFast)
        assertEquals(2.0, v.fastCutoff!!, 1e-9)
    }

    @Test
    fun `a slump cannot hide itself - the slow baseline remembers the good months`() {
        // Ninety good days, then twenty bad ones (all above the floor). On day 111 another bad day:
        // the fast window is two-thirds slump, so its quartile has sunk into the slump and says "usual";
        // the slow baseline, which the last thirty never touch, still says low.
        val history = days(90, 0.8, 0.8, endDay = TODAY - 21) + days(20, 0.5, 0.6)
        val v = assess(c(0.5, 0.62), history)              // 1.43 — above the floor (1.25)
        assertFalse(v.byFloor)
        assertFalse(v.byFast)
        assertTrue(v.bySlow)
        assertTrue(v.low)
    }

    @Test
    fun `a bad first fortnight does not become the definition of usual`() {
        // Five bad days inside the first fifteen (the floor catches those at the time), then twenty-five
        // good ones. A mildly low day afterwards is still lower than usual, because the bad days are
        // less than a quarter of the fast window.
        val history = days(5, 0.3, 0.3, endDay = TODAY - 26) + days(25, 0.8, 0.8)
        val v = assess(c(0.6, 0.7), history)               // 1.65
        assertTrue(v.byFast)
    }

    @Test
    fun `no variation means nothing is lower than usual`() {
        assertFalse(assess(c(0.7, 0.7), days(40, 0.7, 0.7)).low)
    }

    @Test
    fun `someone who lives under the midline is asked every time`() {
        val history = days(60, 0.3, 0.3)
        val v = assess(c(0.3, 0.3), history)
        assertTrue(v.byFloor)
        assertFalse(v.byFast)   // not lower than their usual — the floor is what fires
        assertTrue(v.low)
    }

    @Test
    fun `slow baseline needs fifteen logged days older than the fast window`() {
        val history = days(44, 0.8, 0.8)                              // 30 days in the fast window, 14 before it
        assertEquals(null, assess(c(0.8, 0.8), history).slowCutoff)
        val more = days(45, 0.8, 0.8)                                 // 15 before it
        assertEquals(2.0, assess(c(0.8, 0.8), more).slowCutoff!!, 1e-9)
    }

    @Test
    fun `windows count logged days, not check-ins`() {
        // Three check-ins a day for ten days is thirty check-ins but ten days: the fast baseline is not live.
        val dense = days(10, 0.8, 0.8, perDay = 3)
        assertEquals(null, assess(c(0.5, 0.5), dense).fastCutoff)
        // Fifteen days with three check-ins each: live, and all forty-five check-ins are in the window.
        val fifteen = days(15, 0.8, 0.8, perDay = 3)
        assertEquals(2.0, assess(c(0.5, 0.5), fifteen).fastCutoff!!, 1e-9)
    }

    @Test
    fun `days need not be consecutive`() {
        // Fifteen logged days spread over three months still make a fast baseline.
        val sparse = (0 until 15).map { i -> Logged(TODAY - 1 - i * 6, c(0.8, 0.8)) }
        assertEquals(2.0, assess(c(0.5, 0.5), sparse).fastCutoff!!, 1e-9)
    }

    @Test
    fun `the fast window is the last thirty logged days, all their check-ins included`() {
        // 40 logged days: the ten oldest (bad) fall outside the fast window even though they are "recent"
        // in calendar terms if the person logs daily.
        val history = days(10, 0.3, 0.6, endDay = TODAY - 31) + days(30, 0.8, 0.8)
        val v = assess(c(0.7, 0.75), history)
        assertEquals(2.0, v.fastCutoff!!, 1e-9)
        // and today's own earlier check-ins count as part of today
        val withToday = history + listOf(Logged(TODAY, c(0.1, 0.1)))
        assertTrue(assess(c(0.7, 0.75), withToday).fastCutoff!! <= 2.0)
    }

    @Test
    fun `history order does not matter`() {
        val history = days(20, 0.8, 0.8) + days(5, 0.3, 0.3, endDay = TODAY - 21)
        assertEquals(assess(c(0.6, 0.7), history), assess(c(0.6, 0.7), history.shuffled(kotlin.random.Random(3))))
    }

    @Test
    fun `pure and deterministic`() {
        val history = days(50, 0.6, 0.7, endDay = TODAY - 11) + days(10, 0.4, 0.5)
        assertEquals(assess(c(0.5, 0.5), history), assess(c(0.5, 0.5), history))
    }
}
