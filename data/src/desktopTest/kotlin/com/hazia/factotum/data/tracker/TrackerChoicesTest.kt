package com.hazia.factotum.data.tracker

import com.hazia.factotum.data.sync.World
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

/** A CHOICE tracker's choices, kept as a database's Select options are (SPEC:R203; owner, 2026-11-25). */
class TrackerChoicesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var w: World

    @Before fun open() {
        w = World(tmp.root, 7)
    }

    @After fun close() = w.close()

    private val noon = LocalDateTime(2026, 10, 5, 12, 0)

    private fun World.Device.labels(tracker: String) = runBlocking { trackers.choices(tracker) }.map { it.label }

    private fun World.Device.picked(tracker: String) = runBlocking { trackers.logs(tracker) }.map { it.choiceId }

    // SPEC:R203
    @Test
    fun choicesAreAddedRenamedRecolouredAndMovedAndANameIsTakenOnce() {
        val a = w.Device("A")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm", color = 0xFF00FF00) }
        val tense = runBlocking { a.trackers.addChoice(mood, " tense ") }
        val glad = runBlocking { a.trackers.addChoice(mood, "glad") }
        assertEquals(listOf("calm", "tense", "glad"), a.labels(mood))
        assertEquals(0xFF00FF00, runBlocking { a.trackers.choices(mood) }.first().color)

        runBlocking { a.trackers.moveChoice(glad, after = null) }
        runBlocking { a.trackers.moveChoice(calm, after = tense) }
        assertEquals(listOf("glad", "tense", "calm"), a.labels(mood))
        runBlocking { a.trackers.moveChoice(calm, after = glad) }
        assertEquals(listOf("glad", "calm", "tense"), a.labels(mood))

        runBlocking { a.trackers.renameChoice(tense, "Uneasy") }
        runBlocking { a.trackers.recolorChoice(calm, null) }
        assertEquals(listOf("glad", "calm", "Uneasy"), a.labels(mood))
        assertEquals(null, runBlocking { a.trackers.choices(mood) }[1].color)

        val water = runBlocking { a.trackers.create("Water", TrackerType.NUMBER) }
        for (attempt in listOf<suspend () -> Unit>(
            { a.trackers.addChoice(mood, "CALM") },
            { a.trackers.addChoice(mood, "  ") },
            { a.trackers.renameChoice(glad, "uneasy") },
            { a.trackers.addChoice(water, "lots") },
            { a.trackers.moveChoice(calm, after = "no-such-choice") },
        )) assertFailsWith<IllegalArgumentException> { runBlocking { attempt() } }
        assertEquals(listOf("glad", "calm", "Uneasy"), a.labels(mood))
    }

    // SPEC:R203
    @Test
    fun aLogPicksALiveChoiceOfItsOwnTracker() {
        val a = w.Device("A")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val weather = runBlocking { a.trackers.create("Weather", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        val sunny = runBlocking { a.trackers.addChoice(weather, "sunny") }
        val gone = runBlocking { a.trackers.addChoice(mood, "gone") }
        runBlocking { a.trackers.deleteChoice(gone) }

        runBlocking { a.trackers.log(mood, noon, choiceId = calm) }
        for (choice in listOf(sunny, gone, "no-such-choice")) {
            assertFailsWith<IllegalArgumentException>(choice) { runBlocking { a.trackers.log(mood, noon, choiceId = choice) } }
        }
        assertEquals(listOf(calm), a.picked(mood))
    }

    // SPEC:R203
    @Test
    fun aDeletedChoiceWaitsInTheTrashItsLogsKeepItAndItIsRestoredOrDeletedForever() {
        val a = w.Device("A")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        runBlocking { a.trackers.log(mood, noon, choiceId = calm) }

        assertFailsWith<IllegalArgumentException> { runBlocking { a.trackers.purgeChoice(calm) } }
        runBlocking { a.trackers.deleteChoice(calm) }
        assertEquals(emptyList(), a.labels(mood))
        assertEquals(listOf("calm"), runBlocking { a.trackers.trashedChoices(mood) }.map { it.label })
        assertEquals(listOf(calm), a.picked(mood))

        val other = runBlocking { a.trackers.addChoice(mood, "Calm") }
        assertFailsWith<IllegalArgumentException> { runBlocking { a.trackers.restoreChoice(calm) } }
        runBlocking { a.trackers.deleteChoice(other) }
        runBlocking { a.trackers.restoreChoice(calm) }
        assertEquals(listOf("calm"), a.labels(mood))

        runBlocking { a.trackers.deleteChoice(calm) }
        runBlocking { a.trackers.purgeChoice(calm) }
        assertEquals(listOf("Calm"), runBlocking { a.trackers.trashedChoices(mood) }.map { it.label })
        assertEquals(listOf(calm), a.picked(mood))

        val b = w.Device("B")
        w.settle(listOf(a, b))
        assertEquals(listOf(other), runBlocking { b.db.trackerDao().choicesOf(mood) }.map { it.id })
    }

    // SPEC:R203
    @Test
    fun twoChoicesOfOneNameMadeOnTwoDevicesMergeIntoTheFirstEverywhere() {
        val a = w.Device("A")
        val b = w.Device("B")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        w.settle(listOf(a, b))

        val first = runBlocking { a.trackers.addChoice(mood, "calm") }
        runBlocking { a.trackers.log(mood, noon, choiceId = first) }
        val second = runBlocking { b.trackers.addChoice(mood, "Calm") }
        runBlocking { b.trackers.log(mood, noon, choiceId = second) }
        val survivor = minOf(first, second)
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(listOf(survivor), runBlocking { d.trackers.choices(mood) }.map { it.id }, d.name)
            assertEquals(listOf(survivor, survivor), d.picked(mood), d.name)
            assertEquals(emptyList(), runBlocking { d.trackers.trashedChoices(mood) }, d.name)
        }
        assertEquals(runBlocking { a.db.trackerDao().choicesOf(mood) }, runBlocking { b.db.trackerDao().choicesOf(mood) })
    }

    // SPEC:R203
    @Test
    fun aChoiceLoggedAfterItsDeleteOnADeviceThatHadNotSeenItComesBack() {
        val a = w.Device("A")
        val b = w.Device("B")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        val tense = runBlocking { a.trackers.addChoice(mood, "tense") }
        w.settle(listOf(a, b))

        runBlocking { a.trackers.deleteChoice(calm) }
        runBlocking { b.trackers.log(mood, noon, choiceId = tense) }
        w.syncthing.now += 1_000
        runBlocking { b.trackers.log(mood, noon, choiceId = calm) }
        w.settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(listOf("calm", "tense"), d.labels(mood), d.name)

        w.syncthing.now += 1_000
        runBlocking { b.trackers.deleteChoice(tense) }
        w.syncthing.now += 1_000
        runBlocking { a.trackers.log(mood, noon, choiceId = tense) }
        runBlocking { a.trackers.undoLast(mood, noon.date, LocalTime(0, 0)) }
        w.settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(listOf("calm"), d.labels(mood), d.name)
    }

    // SPEC:R203
    @Test
    fun aLogMadeBeforeTheDeleteLeavesTheChoiceInTheTrash() {
        val a = w.Device("A")
        val b = w.Device("B")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        w.settle(listOf(a, b))

        runBlocking { b.trackers.log(mood, noon, choiceId = calm) }
        w.syncthing.now += 1_000
        runBlocking { a.trackers.deleteChoice(calm) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) {
            assertEquals(emptyList(), d.labels(mood), d.name)
            assertEquals(listOf(calm), d.picked(mood), d.name)
        }
    }

    // SPEC:R203
    @Test
    fun aMoveWritesOnlyTheMovedChoiceSoARenameElsewhereStands() {
        val a = w.Device("A")
        val b = w.Device("B")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        val tense = runBlocking { a.trackers.addChoice(mood, "tense") }
        runBlocking { a.trackers.addChoice(mood, "glad") }
        w.settle(listOf(a, b))

        runBlocking { b.trackers.renameChoice(tense, "uneasy") }
        w.syncthing.now += 1_000
        runBlocking { a.trackers.moveChoice(calm, after = tense) }
        w.settle(listOf(a, b))

        for (d in listOf(a, b)) assertEquals(listOf("uneasy", "calm", "glad"), d.labels(mood), d.name)
    }

    // SPEC:R203
    @Test
    fun twoChoicesAddedAtOnceOnTwoDevicesTieAndAMoveBetweenThemRenumbers() {
        val a = w.Device("A")
        val b = w.Device("B")
        val mood = runBlocking { a.trackers.create("Mood", TrackerType.CHOICE) }
        val calm = runBlocking { a.trackers.addChoice(mood, "calm") }
        w.settle(listOf(a, b))

        val tense = runBlocking { a.trackers.addChoice(mood, "tense") }
        val glad = runBlocking { b.trackers.addChoice(mood, "glad") }
        w.settle(listOf(a, b))
        val (low, high) = listOf(tense to "tense", glad to "glad").sortedBy { it.first }
        assertEquals(listOf("calm", low.second, high.second), a.labels(mood))

        runBlocking { a.trackers.moveChoice(calm, after = low.first) }
        w.settle(listOf(a, b))
        for (d in listOf(a, b)) assertEquals(listOf(low.second, "calm", high.second), d.labels(mood), d.name)
    }
}
