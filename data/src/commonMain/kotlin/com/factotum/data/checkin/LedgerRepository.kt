package com.factotum.data.checkin

import com.factotum.core.checkin.BurnoutIndex
import com.factotum.core.checkin.DailyIndex
import com.factotum.core.checkin.DayRecord
import com.factotum.core.checkin.DemandLevel
import com.factotum.core.checkin.FeltDay
import com.factotum.core.checkin.FeltScale
import com.factotum.core.checkin.MaskedLevel
import com.factotum.core.checkin.MaskingLoad
import com.factotum.core.checkin.RecoveryLevel
import com.factotum.core.habit.dayOf
import com.factotum.core.settings.Settings
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.page.automatic
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.SettingsRepository
import kotlinx.datetime.DatePeriod
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.minus
import kotlinx.datetime.plus

/** A ledger day's three felt scales, each empty until tapped. */
data class LedgerDay(val masked: MaskedLevel?, val demand: DemandLevel?, val recovery: RecoveryLevel?)

data class SensoryLog(val id: String, val at: LocalDateTime, val sound: Double, val light: Double, val crowd: Double, val temperature: Double, val touch: Double)

/**
 * Equipoise's masking ledger and sensory log, and its burnout index worked out from them on demand,
 * never stored or synced (owner, 2026-10-03, decision 14). Days are personal days.
 */
internal class LedgerRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val settings: SettingsRepository,
) {
    private val dao = db.regulationDao()
    private val checkIns = db.checkInDao()
    private val trackers = db.trackerDao()
    private val clock = writes.clock

    /** A sensory snapshot at [at], each channel in 0..1. */
    suspend fun logSensory(at: LocalDateTime, sound: Double, light: Double, crowd: Double, temperature: Double, touch: Double): String {
        listOf(sound, light, crowd, temperature, touch).forEach { require(it in 0.0..1.0) { "a channel is in 0..1" } }
        val id = newId()
        writes.write(mapOf(SENSORY_LOG to listOf(id))) { store ->
            val s = clock.tick()
            writes.merger.created(store, Row(SENSORY_LOG, id, mapOf(
                SAID to Group(s, mapOf("at" to at.toString(), "sound" to sound, "light" to light, "crowd" to crowd, "temperature" to temperature, "touch" to touch)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun undoSensory(id: String) = writes.edit(SENSORY_LOG, id, GONE, {
        requireNotNull(dao.sensory(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no sensory log $id" }
    }) { s -> mapOf("deleted_at" to s.hlc) }

    /** The live sensory logs of the personal day [day]. */
    suspend fun sensoryOn(day: LocalDate): List<SensoryLog> {
        val (from, to) = bounds(day, day)
        return dao.sensoryBetween(from, to).map { SensoryLog(it.id, LocalDateTime.parse(it.at), it.sound, it.light, it.crowd, it.temperature, it.touch) }
    }

    suspend fun setMasked(day: LocalDate, level: MaskedLevel?) = setScale(day, MASKED, "masked", level?.name)

    suspend fun setDemand(day: LocalDate, level: DemandLevel?) = setScale(day, DEMAND, "demand", level?.name)

    suspend fun setRecovery(day: LocalDate, level: RecoveryLevel?) = setScale(day, RECOVERY, "recovery", level?.name)

    /** The ledger of [day], or null when nothing was tapped (or it was cleared). */
    suspend fun ledger(day: LocalDate): LedgerDay? = dao.masking(listOf(maskingId(day))).singleOrNull()?.takeIf { it.deletedAt == null }?.toLedger()

    /** Clears [day]'s ledger: its scales are emptied with it, so a tap that brings the day back starts it afresh. */
    suspend fun clearLedger(day: LocalDate) {
        val id = maskingId(day)
        writes.write({
            requireNotNull(dao.masking(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no ledger on $day" }
            mapOf(MASKING_ENTRY to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(id)).edit(MASKED, s, mapOf("masked" to null)).edit(DEMAND, s, mapOf("demand" to null))
                .edit(RECOVERY, s, mapOf("recovery" to null)).edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        }
    }

    /**
     * The burnout index at [now] (Equipoise's, reweighed over what is present, decision 14): the
     * fourteen personal days up to the one [now] is in. A day's energy is the mean of every energy
     * value that day, one-axis taps included; its masking load is its ledger's when all three scales
     * are set (a day partly answered adds nothing, so nothing is invented); its sensory load is the
     * mean of its logs, each the mean of its channels; its sleep is the sum of the readings of the
     * tracker named in [Settings.SLEEP_TRACKER] that day.
     */
    suspend fun burnout(now: LocalDateTime): DailyIndex {
        val dayStart = settings.dayStart()
        val today = dayOf(now, dayStart)
        val first = today.minus(DatePeriod(days = WINDOW - 1))
        val (from, to) = bounds(first, today)
        fun dayIn(at: String) = dayOf(LocalDateTime.parse(at), dayStart)
        val energy = checkIns.madeBetween(from, to).filter { it.energy != null }
            .groupBy({ dayIn(it.at) }, { requireNotNull(it.energy) })
        val masking = dao.maskingBetween(first.toString(), today.toString()).mapNotNull { e ->
            val felt = e.toLedger().takeIf { it.masked != null && it.demand != null && it.recovery != null } ?: return@mapNotNull null
            val day = LocalDate.parse(e.day)
            day to MaskingLoad.daily(FeltScale.toEntry(day.toEpochDays().toInt(), FeltDay(requireNotNull(felt.masked), requireNotNull(felt.demand), requireNotNull(felt.recovery))))
        }.toMap()
        val sensory = dao.sensoryBetween(from, to).groupBy({ dayIn(it.at) }, { listOf(it.sound, it.light, it.crowd, it.temperature, it.touch).average() })
        val sleepTracker = settings.get(Settings.SLEEP_TRACKER).ifBlank { null }?.takeIf { t -> trackers.trackers(listOf(t)).singleOrNull()?.let { it.deletedAt == null } == true }
        val sleep = sleepTracker?.let { t -> trackers.liveReadingsBetween(listOf(t), from, to).mapNotNull { r -> r.numberValue?.let { dayIn(r.at) to it } } }
            ?.groupBy({ it.first }, { it.second })?.mapValues { (_, hours) -> hours.sum() }.orEmpty()
        val days = (0 until WINDOW).map { first.plus(DatePeriod(days = it)) }
        val window = days.map { d ->
            DayRecord(d.toEpochDays().toInt(), energy[d]?.average(), masking[d], sensory[d]?.average(), sleep[d])
        }
        return BurnoutIndex.compute(window, settings.get(Settings.BURNOUT_THRESHOLD))
    }

    /**
     * Sets one scale of [day]'s ledger. The day's row is made with one fixed stamp, the app's and the
     * lowest, so two devices write one row and making it never undoes a clearing made elsewhere; a
     * tap on a cleared day brings it back, and emptying a scale of a day with no ledger writes nothing.
     */
    private suspend fun setScale(day: LocalDate, group: String, field: String, level: String?) = writes.write(mapOf(MASKING_ENTRY to listOf(maskingId(day)))) { store ->
        val id = maskingId(day)
        val existing = store.row(id)
        if (level == null && (existing == null || existing.groups.getValue(GONE).values["deleted_at"] != null)) return@write
        if (existing == null) {
            writes.merger.created(store, Row(MASKING_ENTRY, id, mapOf(
                MADE to Group(LEDGER_STAMP, mapOf("day" to day.toString())),
                MASKED to Group(LEDGER_STAMP, mapOf("masked" to null)),
                DEMAND to Group(LEDGER_STAMP, mapOf("demand" to null)),
                RECOVERY to Group(LEDGER_STAMP, mapOf("recovery" to null)),
                GONE to Group(LEDGER_STAMP, mapOf("deleted_at" to null)),
            )))
        }
        val s = clock.tick()
        var row = requireNotNull(store.row(id)).edit(group, s, mapOf(field to level))
        if (row.groups.getValue(GONE).values["deleted_at"] != null) row = row.edit(GONE, automatic(s), mapOf("deleted_at" to null))
        store.put(row)
    }

    /** The personal days [first]..[last] as `at` bounds. */
    private suspend fun bounds(first: LocalDate, last: LocalDate): Pair<String, String> {
        val dayStart = settings.dayStart()
        return LocalDateTime(first, dayStart).toString() to LocalDateTime(last.plus(DatePeriod(days = 1)), dayStart).toString()
    }
}

private const val WINDOW = 14

/** A ledger day's rows are made with this stamp: the lowest there is, and the app's (`~`). */
private val LEDGER_STAMP = Stamp(0, "ledger~")

private fun MaskingEntryEntity.toLedger() = LedgerDay(masked?.let(MaskedLevel::valueOf), demand?.let(DemandLevel::valueOf), recovery?.let(RecoveryLevel::valueOf))
