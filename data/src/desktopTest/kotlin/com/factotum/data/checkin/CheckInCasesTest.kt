package com.factotum.data.checkin

import androidx.room.execSQL
import androidx.room.useWriterConnection
import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.Energy
import com.factotum.core.checkin.Mood
import com.factotum.core.checkin.levelOf
import com.factotum.data.FactotumDatabase
import com.factotum.data.FixedSettings
import com.factotum.data.LocalWrites
import com.factotum.data.isConstraintViolation
import com.factotum.data.openFactotumDatabase
import com.factotum.data.search.SearchRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.test.fail

/** ADR 05's cases (`decisions/cases/05-checkin.jsonl`) on the real database, with the owner's 2026-10-03 answers. */
class CheckInCasesTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var checkIns: CheckInRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "checkin.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        checkIns = CheckInRepository(db, writes, { "id-${n++}" }, FixedSettings())
    }

    @After fun close() = db.close()

    private val monday = LocalDate(2026, 10, 5)

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    private fun only(day: LocalDate = monday) = runBlocking { checkIns.onDay(day) }.single()

    @Test
    fun tendrilMoodRoundtrip_aGoodMoodComesBackGoodInItsHue() {
        runBlocking { checkIns.recordMood(at(5, 9), Mood.GOOD.level) }

        assertEquals(Mood.GOOD to "#2E8A76", Mood.fromLevel(only().mood!!)!!.let { it to it.hex })
    }

    @Test
    fun tendrilEnergyRoundtrip_lowIsStoredOnTheSharedAxisAndReadsBackLow() {
        runBlocking { checkIns.recordEnergy(at(5, 9), Energy.LOW.level) }

        val row = only()
        assertEquals(0.3 to 5, row.energy to row.sourceLevels)
        assertEquals(Energy.LOW, Energy.fromLevel(levelOf(row.energy!!, row.sourceLevels!!)))
    }

    @Test
    fun oneScalePerRow_nothingIsInventedOnTheOtherScale() {
        runBlocking { checkIns.recordMood(at(5, 9), 4) }
        runBlocking { checkIns.recordEnergy(at(5, 10), 2) }

        val (mood, energy) = runBlocking { checkIns.onDay(monday) }
        assertEquals(listOf<Any?>(4, null, null), listOf(mood.mood, mood.energy, mood.pleasantness))
        assertEquals(listOf<Any?>(null, 0.3, null), listOf(energy.mood, energy.energy, energy.pleasantness))
    }

    @Test
    fun equipoiseContinuous_twoAxisValuesComeBackExactThroughTheDatabaseAndTheFolder() {
        val w = World(tmp.root, 1)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val id = runBlocking { a.checkIns.record(at(5, 9), energy = 0.81, pleasantness = 0.62) }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) {
                val row = runBlocking { d.checkIns.onDay(monday) }.single()
                assertEquals(Triple(id, 0.81, 0.62), Triple(row.id, row.energy, row.pleasantness))
                assertNull(row.sourceLevels)
            }
        } finally {
            w.close()
        }
    }

    @Test
    fun equipoiseWidgetEnergyOnly_pleasantnessAndMoodStayEmpty() {
        runBlocking { checkIns.recordWidgetEnergy(at(5, 9), 1) }
        runBlocking { checkIns.recordWidgetEnergy(at(5, 10), 2) }

        val (low, some) = runBlocking { checkIns.onDay(monday) }
        assertEquals(listOf<Any?>(null, null, 3, 0.15), listOf(low.mood, low.pleasantness, low.sourceLevels, low.energy))
        assertEquals(0.5 to 2, some.energy to levelOf(some.energy!!, 3))
    }

    @Test
    fun noMidline_theEnginesReadOnlyTwoAxisCheckInsAndAStepValueIsMarked() {
        runBlocking { checkIns.recordEnergy(at(5, 8), 3) }
        runBlocking { checkIns.recordMood(at(5, 9), 2) }
        runBlocking { checkIns.record(at(5, 10), energy = 0.2, pleasantness = 0.3) }

        val history = runBlocking { checkIns.engineHistory(at(9, 0)) }
        assertEquals(listOf(CheckIn(0.2, 0.3)), history.map { it.checkIn })
        // Tendril's middle energy step sits on 0.5, so it carries its scale and never passes as a continuous midline value.
        assertEquals(5, runBlocking { checkIns.onDay(monday) }.first().sourceLevels)
    }

    @Test
    fun sharedOneHistory_aMoodTapNeverReachesTheEnginesAsTheOwnerAccepted() {
        runBlocking { checkIns.recordMood(at(5, 9), 1) }
        runBlocking { checkIns.recordEnergy(at(5, 9, 5), 1) }

        assertEquals(emptyList(), runBlocking { checkIns.engineHistory(at(9, 0)) })
    }

    @Test
    fun aCheckInMayBeAboutAPastDayButNotAFutureOneAndTheEnginesReadTheMoment() {
        runBlocking { checkIns.recordMood(at(6, 9), 3, day = monday) }
        runBlocking { checkIns.record(at(6, 10), energy = 0.4, pleasantness = 0.6, day = monday) }

        assertEquals(2, runBlocking { checkIns.onDay(monday) }.size)
        assertEquals(emptyList(), runBlocking { checkIns.onDay(LocalDate(2026, 10, 6)) })
        assertEquals(listOf(LocalDate(2026, 10, 6).toEpochDays().toInt()), runBlocking { checkIns.engineHistory(at(9, 0)) }.map { it.day })
        assertFailsWith<IllegalArgumentException> { runBlocking { checkIns.recordMood(at(5, 9), 3, day = LocalDate(2026, 10, 6)) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { checkIns.record(at(5, 9), mood = 3, sourceLevels = 5) } }
    }

    @Test
    fun aCheckInAfterMidnightCountsForTheDayBeforeWhenTheDayStartsLater() {
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val owl = CheckInRepository(db, writes, { "owl-${n++}" }, FixedSettings(LocalTime(4, 0)))
        runBlocking { owl.record(at(6, 1), energy = 0.3, pleasantness = 0.3) }
        // Made at 01:00 on the 6th, which is still the 5th: it cannot be about the 6th, which has not begun.
        assertFailsWith<IllegalArgumentException> { runBlocking { owl.recordMood(at(6, 1), 3, day = LocalDate(2026, 10, 6)) } }

        assertEquals(1, runBlocking { owl.onDay(monday) }.size)
        assertEquals(listOf(monday.toEpochDays().toInt()), runBlocking { owl.engineHistory(at(9, 0)) }.map { it.day })
    }

    @Test
    fun theEnginesReadOnlyCheckInsMadeBeforeTheOneJudged() {
        runBlocking { checkIns.record(at(5, 9), energy = 0.2, pleasantness = 0.2) }
        runBlocking { checkIns.record(at(5, 12), energy = 0.8, pleasantness = 0.8) }

        assertEquals(listOf(CheckIn(0.2, 0.2)), runBlocking { checkIns.engineHistory(at(5, 12)) }.map { it.checkIn })
    }

    @Test
    fun aCheckInIsUndoneNotChangedAndItsNoteStaysOutOfSearch() {
        val id = runBlocking { checkIns.record(at(5, 9), energy = 0.4, pleasantness = 0.4, note = "  a quantum of calm  ") }
        assertEquals("a quantum of calm", only().note)
        assertEquals(emptyList(), runBlocking { SearchRepository(db).search("quantum", at(6, 0)) })

        runBlocking { checkIns.undo(id) }
        val undone = runBlocking { db.checkInDao().checkIns(listOf(id)) }.single().goneHlc
        runBlocking { checkIns.undo(id) }
        assertEquals(undone, runBlocking { db.checkInDao().checkIns(listOf(id)) }.single().goneHlc)

        assertEquals(emptyList(), runBlocking { checkIns.onDay(monday) })
        assertEquals(emptyList(), runBlocking { checkIns.engineHistory(at(9, 0)) })
    }

    @Test
    fun aNoteWrittenOnOneDeviceNeverBringsBackACheckInUndoneOnAnother() {
        val w = World(tmp.root, 2)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val id = runBlocking { a.checkIns.recordMood(at(5, 9), 4) }
            w.settle(listOf(a, b))

            runBlocking { a.checkIns.undo(id) }
            runBlocking { b.checkIns.setNote(id, "after the walk") }
            w.settle(listOf(a, b))

            for (d in listOf(a, b)) assertEquals(emptyList(), runBlocking { d.checkIns.onDay(monday) })
        } finally {
            w.close()
        }
    }

    @Test
    fun aCheckInOutsideItsScalesIsRefused() {
        assertFailsWith<IllegalArgumentException> { runBlocking { checkIns.record(at(5, 9)) } }
        assertFailsWith<IllegalArgumentException> { runBlocking { checkIns.recordMood(at(5, 9), 6) } }
        val id = runBlocking { checkIns.record(at(5, 9), energy = 0.5, pleasantness = 0.5) }
        for (bad in listOf("mood = 0", "mood = 3.5", "energy = 1.5", "pleasantness = -0.1", "source_levels = 1", "source_levels = 2.5", "stability = 'UNSET'",
            "day = '2026-10-06'", "day = ''", "at = 'garbage'", "energy = NULL, pleasantness = NULL")) {
            refused("UPDATE check_in SET $bad WHERE id = '$id'")
        }
    }

    private fun refused(sql: String) {
        try {
            runBlocking { db.useWriterConnection { it.execSQL(sql) } }
        } catch (e: Exception) {
            if (isConstraintViolation(e)) return
            throw e
        }
        fail("the database took: $sql")
    }
}
