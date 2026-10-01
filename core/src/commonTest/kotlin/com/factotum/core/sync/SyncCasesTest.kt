package com.factotum.core.sync

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * ADR 01's acceptance: the ten cases of `decisions/cases/01-sync.jsonl`, each replaying its
 * `tools/sync_sim.py` scenario, and each expecting hybrid+'s scored outcome
 * (`decisions/options/01-sync.sim.json`): 1 = the guarantee holds, 0.5 = a person is asked.
 */
class SyncCasesTest {

    @Test // 1
    fun chronicleGroupMerge() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "d1"); b.edit("x", 11, STATUS, "done" to true); sync(listOf(a, b), 12)

        for (d in listOf(a, b)) assertEquals(View("d1", false, true), d.view("x"))
    }

    @Test // 0.5: a same-millisecond change to the schedule on both sides is asked, never dropped
    fun chronicleTieConverges() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "dA"); b.edit("x", 10, SCHEDULE, "due" to "dB"); sync(listOf(a, b), 11)

        assertTrue(a.asked("x") && b.asked("x"))
        assertEquals(listOf("dA", "dB"), listOf(a.due(), b.due()))
    }

    @Test // 1
    fun sharedLaterEditBeatsFastClock() {
        val (a, b) = Device("A") to Device("B", skew = 2 * DAY)
        a.create("x", 0); sync(listOf(a, b), 1)
        b.edit("x", 10, SCHEDULE, "due" to "dB"); sync(listOf(a, b), 11)
        a.edit("x", 20, SCHEDULE, "due" to "dA"); sync(listOf(a, b), 21)

        assertEquals(listOf("dA", "dA"), listOf(a.due(), b.due()))
    }

    @Test // 1
    fun chronicleDeleteBeatsStatus() {
        val (a, b) = pairWithX()
        a.delete("x", 10); b.edit("x", 11, STATUS, "done" to true); sync(listOf(a, b), 12)

        assertTrue(a.gone("x") && b.gone("x"))
    }

    @Test // 1
    fun tendrilPurgeHolds() {
        val (a, b) = pairWithX()
        a.delete("x", 10); a.purge("x", 10 + 100 * DAY)
        sync(listOf(a, b), 11 + 100 * DAY)

        assertTrue(a.gone("x") && b.gone("x"))
    }

    @Test // 1
    fun tendrilLateJoin() {
        val a = Device("A")
        a.create("x", 0); a.create("y", 0); a.delete("y", 5)
        val c = Device("C"); sync(listOf(a, c), 7)

        assertEquals(View("d0", false, false), c.view("x"))
        assertTrue(c.gone("y"))
    }

    @Test // 1
    fun tendrilRemoteEditSilent() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "d1"); sync(listOf(a, b), 11)

        assertEquals(listOf("d1", "d1"), listOf(a.due(), b.due()))
        assertFalse(a.asked("x") || b.asked("x"))
    }

    @Test // 1
    fun mnemoSameTimeShown() {
        val (a, b) = pairWithX()
        a.edit("x", 10, SCHEDULE, "due" to "dA"); b.edit("x", 11, SCHEDULE, "due" to "dB"); sync(listOf(a, b), 12)

        assertTrue(a.asked("x") || b.asked("x"))
    }

    @Test // 1
    fun mnemoDeleteVsEditShown() {
        val (a, b) = pairWithX()
        a.delete("x", 10); b.edit("x", 11, SCHEDULE, "due" to "dB"); sync(listOf(a, b), 12)

        assertTrue(a.asked("x") || b.asked("x"))
    }

    @Test // 0.5: the schedule clash on y is asked; x has no clash and converges
    fun sharedConverges() {
        val (a, b, c) = Triple(Device("A"), Device("B", skew = 3), Device("C"))
        a.create("x", 0); b.create("y", 0); sync(listOf(a, b, c), 1)
        a.edit("x", 10, STATUS, "done" to true); b.edit("x", 10, SCHEDULE, "due" to "dB"); c.delete("y", 10)
        b.edit("y", 12, SCHEDULE, "due" to "dy"); sync(listOf(a, b, c), 13)

        assertTrue(listOf(a, b, c).any { it.asked("y") })
        assertEquals(1, listOf(a, b, c).map { it.view("x") }.toSet().size)
    }
}
