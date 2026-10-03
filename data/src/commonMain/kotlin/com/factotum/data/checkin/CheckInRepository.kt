package com.factotum.data.checkin

import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.Logged
import com.factotum.core.checkin.Stability
import com.factotum.core.checkin.axisValue
import com.factotum.core.habit.dayOf
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.settings.PersonalSettings
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.plus

/** Equipoise's widget values for Low, Some and High (`EnergyWidget.kt:45`). */
private val WIDGET_ENERGY = listOf(0.15, 0.5, 0.85)

/** A check-in as read back; [day] is the personal day it counts for: the day it is about, else the day it was made. */
data class CheckInRecord(
    val id: String,
    val at: LocalDateTime,
    val day: LocalDate,
    val mood: Int?,
    val energy: Double?,
    val pleasantness: Double?,
    val sourceLevels: Int?,
    val stability: Stability?,
    val note: String?,
)

/**
 * Check-ins (ADR 05, own-axis): Tendril's mood taps, its energy taps on Equipoise's energy axis,
 * and Equipoise's two-axis check-ins, several a day. A check-in is made once, and undone rather
 * than changed; its note can change. Nothing here counts or averages for a screen (ADR 05).
 */
internal class CheckInRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val personal: PersonalSettings,
) {
    private val dao = db.checkInDao()
    private val clock = writes.clock

    /**
     * A check-in made at [at], about [day] when given (today or an earlier day, owner 2026-10-03).
     * A value from a scale of steps gives its [sourceLevels].
     */
    suspend fun record(
        at: LocalDateTime,
        mood: Int? = null,
        energy: Double? = null,
        pleasantness: Double? = null,
        sourceLevels: Int? = null,
        stability: Stability? = null,
        note: String? = null,
        day: LocalDate? = null,
    ): String {
        require(mood != null || energy != null || pleasantness != null) { "a check-in says something" }
        require(mood == null || mood in 1..5) { "mood is 1 to 5: $mood" }
        require(energy == null || energy in 0.0..1.0) { "energy is 0 to 1: $energy" }
        require(pleasantness == null || pleasantness in 0.0..1.0) { "pleasantness is 0 to 1: $pleasantness" }
        require(sourceLevels == null || (sourceLevels >= 2 && (energy != null || pleasantness != null))) { "a step scale of two or more, on an axis: $sourceLevels" }
        require(stability != Stability.UNSET) { "an unset stability is none" }
        require(day == null || day <= dayOf(at, personal.dayStart())) { "a check-in is about a day that has happened: $day" }
        val id = newId()
        writes.write(mapOf(CHECK_IN to listOf(id))) { store ->
            val s = clock.tick()
            writes.merger.created(store, Row(CHECK_IN, id, mapOf(
                SAID to Group(s, mapOf(
                    "at" to at.toString(), "day" to day?.toString(), "mood" to mood?.toLong(), "energy" to energy,
                    "pleasantness" to pleasantness, "source_levels" to sourceLevels?.toLong(), "stability" to stability?.name,
                )),
                NOTE to Group(s, mapOf("note" to note?.trim()?.ifEmpty { null })),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    /** Tendril's quick mood tap: one of its five words. */
    suspend fun recordMood(at: LocalDateTime, level: Int, day: LocalDate? = null): String = record(at, mood = level, day = day)

    /** Tendril's quick energy tap: one of its five words, on the shared energy axis at (k − 0.5) / 5 (ADR 05). */
    suspend fun recordEnergy(at: LocalDateTime, level: Int, day: LocalDate? = null): String =
        record(at, energy = axisValue(level, 5), sourceLevels = 5, day = day)

    /** Equipoise's energy widget: Low, Some or High, at the values it has always stored (`EnergyWidget.kt`). */
    suspend fun recordWidgetEnergy(at: LocalDateTime, level: Int): String =
        record(at, energy = WIDGET_ENERGY[level - 1], sourceLevels = WIDGET_ENERGY.size)

    suspend fun setNote(id: String, note: String?) = writes.edit(CHECK_IN, id, NOTE) { mapOf("note" to note?.trim()?.ifEmpty { null }) }

    /** Undoes [id] (Tendril's undo); undoing it again changes nothing. */
    suspend fun undo(id: String) = writes.write(mapOf(CHECK_IN to listOf(id))) { store ->
        val row = requireNotNull(store.row(id)) { "no check-in $id" }
        if (row.groups.getValue(GONE).values["deleted_at"] == null) {
            val s = clock.tick()
            store.put(row.edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        }
    }

    /** The live check-ins that count for the personal [day], in the order they were made. */
    suspend fun onDay(day: LocalDate): List<CheckInRecord> {
        val dayStart = personal.dayStart()
        val next = day.plus(1, DateTimeUnit.DAY)
        return dao.around(LocalDateTime(day, dayStart).toString(), LocalDateTime(next, dayStart).toString(), day.toString(), next.toString())
            .map { it.toRecord(dayStart) }.filter { it.day == day }
    }

    /**
     * Equipoise's engine history for a check-in made at [before]: every live check-in with both
     * axes made earlier (the one judged, and any later, excluded, as Equipoise's `assess` expects),
     * by the personal day it was made on (the engines read the moment, not a day a check-in is
     * about; owner, 2026-10-03). A mood or energy tap alone never reaches it: the loss ADR 05 records.
     */
    suspend fun engineHistory(before: LocalDateTime): List<Logged> {
        val dayStart = personal.dayStart()
        return dao.bothAxes(before.toString()).map { e ->
            Logged(dayOf(LocalDateTime.parse(e.at), dayStart).toEpochDays().toInt(), CheckIn(requireNotNull(e.energy), requireNotNull(e.pleasantness), e.stability?.let(Stability::valueOf) ?: Stability.UNSET))
        }
    }
}

private fun CheckInEntity.toRecord(dayStart: kotlinx.datetime.LocalTime): CheckInRecord {
    val made = LocalDateTime.parse(at)
    return CheckInRecord(
        id, made, day?.let(LocalDate::parse) ?: dayOf(made, dayStart), mood?.toInt(), energy, pleasantness, sourceLevels?.toInt(),
        stability?.let(Stability::valueOf), note,
    )
}
