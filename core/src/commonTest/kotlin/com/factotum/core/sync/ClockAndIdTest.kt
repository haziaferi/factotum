package com.factotum.core.sync

import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ClockAndIdTest {

    @Test
    fun ulidIsValidSortsByTimeAndKeepsItsTime() {
        val random = Random(1)
        val early = Ulid.next(1_000, random)
        val late = Ulid.next(2_000, random)

        assertTrue(Ulid.isValid(early) && Ulid.isValid(late))
        assertTrue(early < late)
        assertEquals(1_000, Ulid.timeOf(early))
        assertEquals("01ARYZ6S41", Ulid.next(1_469_918_176_385).take(10)) // the ULID spec's example
        assertEquals(1_469_922_850_259, Ulid.timeOf("01ARZ3NDEKTSV4RRFFQ69G5FAV"))
    }

    @Test
    fun ulidRandomPartUsesAllEightyBits() {
        val all = Ulid.next(0, Random(0)).drop(10)
        val ones = Ulid.next(0, object : Random() { override fun nextBits(bitCount: Int) = -1 }).drop(10)

        assertEquals(16, all.length)
        assertEquals("ZZZZZZZZZZZZZZZZ", ones)
        assertFalse(Ulid.isValid("8" + "0".repeat(25)), "the first character holds only 3 bits")
    }

    @Test
    fun clockNeverGoesBackwardsAndOutranksWhatItHasSeen() {
        var wall = 100L
        val clock = HybridClock("A", { wall })

        val first = clock.tick()
        wall = 50
        val second = clock.tick()
        clock.observe(Stamp(1_000, "B"))
        val third = clock.tick()

        assertEquals(100, first.hlc)
        assertEquals(101, second.hlc)
        assertEquals(1_001, third.hlc)
    }

    @Test
    fun aSeededClockCannotIssueAnOlderStamp() {
        val clock = HybridClock("A", { 10 }, last = 500)

        assertEquals(501, clock.tick().hlc)
    }

    @Test
    fun aGroupRefusesAValueTypeThatWouldCompareUnequalToItsTwin() {
        assertFailsWith<IllegalArgumentException> { Group(Stamp(1, "A"), mapOf("minutes" to 5)) }
        Group(Stamp(1, "A"), mapOf("minutes" to 5L, "note" to null))
    }

    @Test
    fun stampsOrderByClockThenDevice() {
        assertTrue(Stamp(1, "B") > Stamp(1, "A"))
        assertTrue(Stamp(2, "A") > Stamp(1, "B"))
    }
}
