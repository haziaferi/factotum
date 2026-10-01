package com.factotum.core.sync

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** A person's answer to a schedule clash settles it on every device: nobody is asked again. */
class ResolutionTest {

    /** A and B both changed x's time before syncing; both are asked. */
    private fun clash(): Pair<Device, Device> {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "dA"); b.edit("x", 11, SCHEDULE, "due" to "dB"); sync(listOf(a, b), 12)
        check(a.asked("x") && b.asked("x"))
        return a to b
    }

    @Test
    fun keepMineWinsEverywhere() {
        val (a, b) = clash()
        a.merger.keepMine(a.store, "x", SCHEDULE)
        sync(listOf(a, b), 20)

        assertEquals(listOf("dA", "dA"), listOf(a.due(), b.due()))
        assertFalse(a.asked("x") || b.asked("x"))
    }

    @Test
    fun takeTheirsWinsEverywhere() {
        val (a, b) = clash()
        a.merger.takeTheirs(a.store, "x", SCHEDULE)
        sync(listOf(a, b), 20)

        assertEquals(listOf("dB", "dB"), listOf(a.due(), b.due()))
        assertFalse(a.asked("x") || b.asked("x"))
    }

    @Test
    fun keepBothLeavesTwoRowsEverywhere() {
        val (a, b) = clash()
        a.merger.keepBoth(a.store, "x", SCHEDULE, newId = "x2")
        sync(listOf(a, b), 20)

        assertEquals(listOf("dA", "dA"), listOf(a.due(), b.due()))
        assertEquals(listOf("dB", "dB"), listOf(a.due("x2"), b.due("x2")))
        assertFalse(a.asked("x") || b.asked("x"))
    }

    /** ADR 01 asks whenever both sides changed the schedule since their base; two different answers did. */
    @Test
    fun twoDevicesAnsweringDifferentlyAreAskedAgainAndLoseNothing() {
        val (a, b) = clash()
        a.merger.keepMine(a.store, "x", SCHEDULE)
        b.merger.keepMine(b.store, "x", SCHEDULE)
        sync(listOf(a, b), 20)

        assertTrue(a.asked("x") && b.asked("x"))
        assertEquals(listOf("dA", "dB"), listOf(a.due(), b.due()))
        assertEquals("dB", a.store.asked("x", SCHEDULE)?.values?.get("due"))
    }

    @Test
    fun twoDevicesGivingTheSameAnswerConvergeSilently() {
        val (a, b) = clash()
        a.merger.keepMine(a.store, "x", SCHEDULE)
        b.merger.takeTheirs(b.store, "x", SCHEDULE)
        sync(listOf(a, b), 20)

        assertEquals(listOf("dA", "dA"), listOf(a.due(), b.due()))
        assertFalse(a.asked("x") || b.asked("x"))
    }

    @Test
    fun aNewEditAfterAnAnswerIsAskedAgain() {
        val (a, b) = clash()
        a.merger.keepMine(a.store, "x", SCHEDULE)
        b.edit("x", 15, SCHEDULE, "due" to "dB2")
        sync(listOf(a, b), 20)

        assertTrue(a.asked("x") || b.asked("x"))
    }
}
