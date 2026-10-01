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

    /**
     * A imports B before B has seen A's change: B's copy is still the base, so it brings nothing
     * new. B's later change is then a clash with A's, and must be asked, not taken silently.
     */
    @Test
    fun anImportThatBringsNothingNewDoesNotHideALaterClash() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "dA")
        a.importFrom(b, 11)
        b.edit("x", 12, SCHEDULE, "due" to "dB")
        a.importFrom(b, 13)

        assertTrue(a.asked("x"))
        assertEquals("dA", a.due())
    }

    /** A version both sides already had, arriving again (a log replays old versions), is not a clash. */
    @Test
    fun aReplayedOldVersionIsNotAskedAbout() {
        val (a, b) = pairWithX()
        val old = b.store.rows.getValue("x")
        a.edit("x", 10, SCHEDULE, "due" to "dA")
        b.importFrom(a, 11)
        a.merger.import(a.store, listOf(old), emptyMap())

        assertFalse(a.asked("x"))
        assertEquals("dA", a.due())
    }

    /** B changes x twice; A, which also changed it, is asked about B's latest, and a replay of B's first stays out. */
    @Test
    fun aPendingQuestionIsNotReplacedByAnOlderReplay() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "dA")
        b.edit("x", 11, SCHEDULE, "due" to "dB1")
        val first = b.store.rows.getValue("x")
        b.edit("x", 12, SCHEDULE, "due" to "dB2")
        a.importFrom(b, 13)
        a.merger.import(a.store, listOf(first), emptyMap())

        assertEquals("dB2", a.store.asked("x", SCHEDULE)?.values?.get("due"))
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
