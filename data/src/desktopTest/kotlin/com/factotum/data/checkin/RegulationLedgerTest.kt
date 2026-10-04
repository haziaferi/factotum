package com.factotum.data.checkin

import com.factotum.core.checkin.DemandLevel
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.MaskedLevel
import com.factotum.core.checkin.Outcome
import com.factotum.core.checkin.Recommendation
import com.factotum.core.checkin.RecoveryLevel
import com.factotum.core.settings.Settings
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.openFactotumDatabase
import com.factotum.data.settings.MemorySecretStore
import com.factotum.data.settings.SettingsRepository
import com.factotum.data.sync.World
import com.factotum.data.sync.loadClock
import com.factotum.data.tracker.TrackerRepository
import com.factotum.data.tracker.TrackerType
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.math.exp
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Equipoise's regulation module (§7 step 3), with the owner's answers of 2026-10-03 (decision 14). */
class RegulationLedgerTest {

    @get:Rule val tmp = TemporaryFolder()

    private lateinit var db: FactotumDatabase
    private lateinit var settings: SettingsRepository
    private lateinit var checkIns: CheckInRepository
    private lateinit var regulation: RegulationRepository
    private lateinit var ledger: LedgerRepository
    private lateinit var trackers: TrackerRepository

    @Before fun open() {
        db = openFactotumDatabase(File(tmp.root, "r.db")).database
        var n = 0
        val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
        val newId = { "id-${n++}" }
        settings = SettingsRepository(db, writes, MemorySecretStore())
        checkIns = CheckInRepository(db, writes, newId, settings)
        regulation = RegulationRepository(db, writes, newId, settings)
        ledger = LedgerRepository(db, writes, newId, settings)
        trackers = TrackerRepository(db, writes, newId)
    }

    @After fun close() = db.close()

    private fun <T> go(block: suspend () -> T): T = runBlocking { block() }

    private val noon = LocalDateTime(2026, 10, 5, 12, 0)

    private fun at(hour: Int) = LocalDateTime(2026, 10, 5, hour, 0)

    @Test
    fun theEngineLearnsFromOutcomesAndAnUndoneCheckInStopsTeaching() {
        go { settings.set(Settings.MIXED_MODE, com.factotum.core.checkin.MixedMode.AUTO) }
        // Low energy, pleasant: the prior says up.
        val now = go { checkIns.record(noon, energy = 0.2, pleasantness = 0.8) }
        assertEquals(Recommendation.UP, go { regulation.recommend(now) })

        val taught = (1..4).map { i -> go { checkIns.record(at(8 + i), energy = 0.2, pleasantness = 0.8) } }
        taught.forEach { c ->
            go { regulation.record(c, Direction.UP, "walk", Outcome.NO_CHANGE, noon) }
            go { regulation.record(c, Direction.DOWN, "rest", Outcome.HELPED, noon) }
        }
        assertEquals(Recommendation.DOWN, go { regulation.recommend(now) })

        taught.forEach { go { checkIns.undo(it) } }
        assertEquals(Recommendation.UP, go { regulation.recommend(now) })
    }

    @Test
    fun anOutcomeOwedIsAskedOnceAtTheNextOpenAndLapsesAsNotNow() {
        val c = go { checkIns.record(noon, energy = 0.7, pleasantness = 0.3) }
        go { regulation.startTool(c, Direction.DOWN, "breathe", noon) }
        assertEquals(OwedOutcome(c, Direction.DOWN, "breathe"), go { regulation.onOpen(noon) })
        go { regulation.answer(Outcome.HELPED, noon) }
        assertEquals(listOf(Direction.DOWN to Outcome.HELPED), go { regulation.outcomes(c) })
        assertNull(go { regulation.onOpen(noon) })

        // Asked once, not answered: the next open records "not now" and asks nothing.
        go { regulation.startTool(c, Direction.UP, "music", noon) }
        go { regulation.onOpen(noon) }
        assertNull(go { regulation.onOpen(noon) })
        // A tool chosen while one is owed: the one owed lapses.
        go { regulation.startTool(c, Direction.DOWN, "walk", noon) }
        go { regulation.startTool(c, Direction.DOWN, "bath", noon) }
        assertEquals(
            listOf(Direction.DOWN to Outcome.HELPED, Direction.UP to Outcome.NOT_NOW, Direction.DOWN to Outcome.NOT_NOW),
            go { regulation.outcomes(c) },
        )
    }

    @Test
    fun ledgerScalesTappedOnTwoDevicesBothStandAndATapBringsBackAClearedDay() {
        val w = World(tmp.root, 1)
        try {
            val a = w.Device("A")
            val b = w.Device("B")
            val day = LocalDate(2026, 10, 5)
            w.syncthing.now = 1_000
            go { a.ledger.setMasked(day, MaskedLevel.MOST) }
            w.syncthing.now = 2_000
            go { b.ledger.setDemand(day, DemandLevel.A_LOT) }
            w.settle(listOf(a, b))
            for (d in listOf(a, b)) assertEquals(LedgerDay(MaskedLevel.MOST, DemandLevel.A_LOT, null), go { d.ledger.ledger(day) })

            w.syncthing.now = 3_000
            go { a.ledger.clearLedger(day) }
            w.settle(listOf(a, b))
            assertNull(go { b.ledger.ledger(day) })
            w.syncthing.now = 4_000
            go { b.ledger.setRecovery(day, RecoveryLevel.ENOUGH) }
            w.settle(listOf(a, b))
            for (d in listOf(a, b)) assertEquals(LedgerDay(null, null, RecoveryLevel.ENOUGH), go { d.ledger.ledger(day) })
        } finally {
            w.close()
        }
    }

    @Test
    fun theBurnoutIndexCountsWholeLedgerDaysSleepAndEnergyOverWhatIsPresent() {
        // Only masking: a full day counts, a partly answered one does not.
        go { ledger.setMasked(LocalDate(2026, 10, 4), MaskedLevel.ALL_DAY) }
        go { ledger.setDemand(LocalDate(2026, 10, 4), DemandLevel.SOME) }
        go { ledger.setRecovery(LocalDate(2026, 10, 4), RecoveryLevel.NONE) }
        go { ledger.setMasked(LocalDate(2026, 10, 5), MaskedLevel.NONE) }
        val load = (0.6 * 1.0 + 0.4 * (1 - exp(-3 / 4.0))).coerceIn(0.0, 1.0)
        val masked = go { ledger.burnout(noon) }
        assertEquals(load, masked.maskingLoad, 1e-9)
        assertEquals(load, masked.index, 1e-9)

        // Sleep from the tracker named: two naps on one day add up.
        val sleep = go { trackers.create("Sleep", TrackerType.NUMBER, unit = "HOURS") }
        go { settings.set(Settings.SLEEP_TRACKER, sleep) }
        go { trackers.log(sleep, LocalDateTime(2026, 10, 5, 7, 0), number = 4.0) }
        go { trackers.log(sleep, LocalDateTime(2026, 10, 5, 15, 0), number = 1.0) }
        val withSleep = go { ledger.burnout(at(20)) }
        val sleepTerm = ((7.5 - 5.0) / 3.0).coerceIn(0.0, 1.0)
        assertEquals((0.35 * load + 0.15 * sleepTerm) / 0.5, withSleep.index, 1e-9)

        // Energy: one-axis taps count, and three falling days give a trend.
        listOf(2 to 0.9, 3 to 0.6, 4 to 0.3).forEach { (d, e) -> go { checkIns.recordEnergy(LocalDateTime(2026, 10, d, 9, 0), levelFor(e)) } }
        assertTrue(go { ledger.burnout(at(20)) }.energyTrend < 0)
    }

    @Test
    fun anOutcomeOwedForACheckInUndoneIsDroppedAndOutcomesNeedBothAxes() {
        val c = go { checkIns.record(noon, energy = 0.7, pleasantness = 0.3) }
        go { regulation.startTool(c, Direction.DOWN, "breathe", noon) }
        go { checkIns.undo(c) }
        assertNull(go { regulation.onOpen(noon) })
        go { regulation.answer(Outcome.HELPED, noon) }
        val other = go { checkIns.record(at(13), energy = 0.7, pleasantness = 0.3) }
        go { regulation.startTool(other, Direction.DOWN, "walk", noon) }
        assertEquals(OwedOutcome(other, Direction.DOWN, "walk"), go { regulation.onOpen(noon) })
        assertEquals(emptyList(), go { regulation.outcomes(c) })

        val energyOnly = go { checkIns.recordEnergy(at(14), levelFor(0.4)) }
        assertFailsWith<IllegalArgumentException> { go { regulation.record(energyOnly, Direction.UP, null, Outcome.HELPED, noon) } }
        assertFailsWith<IllegalArgumentException> { go { regulation.startTool(energyOnly, Direction.UP, null, noon) } }
        Unit
    }

    @Test
    fun emptyingAScaleOfAnUntouchedDayWritesNothingAndATrashedSleepTrackerIsNotRead() {
        val day = LocalDate(2026, 10, 5)
        go { ledger.setMasked(day, null) }
        assertNull(go { ledger.ledger(day) })

        val sleep = go { trackers.create("Sleep", TrackerType.NUMBER, unit = "HOURS") }
        go { settings.set(Settings.SLEEP_TRACKER, sleep) }
        go { trackers.log(sleep, at(7), number = 4.0) }
        assertTrue(go { ledger.burnout(noon) }.sleepDeficit > 0)
        go { trackers.delete(sleep) }
        assertEquals(0.0, go { ledger.burnout(noon) }.sleepDeficit)
    }

    @Test
    fun aSensoryLogIsFiveChannelsInZeroToOne() {
        val id = go { ledger.logSensory(noon, 0.2, 0.4, 0.6, 0.8, 1.0) }
        assertEquals(listOf(id), go { ledger.sensoryOn(LocalDate(2026, 10, 5)) }.map { it.id })
        assertFailsWith<IllegalArgumentException> { go { ledger.logSensory(noon, 1.2, 0.0, 0.0, 0.0, 0.0) } }
        val load = go { ledger.burnout(noon) }.sensoryLoad
        assertEquals(0.6, load, 1e-9)
        go { ledger.undoSensory(id) }
        assertEquals(emptyList(), go { ledger.sensoryOn(LocalDate(2026, 10, 5)) })
    }

    /** The energy tap level nearest [value] on Tendril's five steps. */
    private fun levelFor(value: Double) = com.factotum.core.checkin.levelOf(value, 5)
}
