package com.factotum.core.habit

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/**
 * One Log on a habit's tracker (a tracker reading, ADR 06), at the local wall-clock time it was
 * made. Exactly one value is set, as the tracker's kind allows.
 */
data class Log(
    val at: LocalDateTime,
    val yes: Boolean? = null,
    val rating: Int? = null,
    val number: Double? = null,
    val choiceId: String? = null,
) {
    /**
     * Whether this Log says the habit happened (owner, 2026-10-02): a "yes", any rating, or a
     * number above 0. A "no" is a person saying it did not happen, which is not counted either way.
     */
    val isPresence: Boolean get() = yes == true || rating != null || (number ?: 0.0) > 0.0
}

enum class TimeOfDay { MORNING, AFTERNOON, EVENING, NIGHT }

/** Local-time buckets, where ordinary speech puts them. */
fun timeOfDayOf(hour: Int): TimeOfDay = when (hour) {
    in 5..11 -> TimeOfDay.MORNING
    in 12..16 -> TimeOfDay.AFTERNOON
    in 17..21 -> TimeOfDay.EVENING
    else -> TimeOfDay.NIGHT
}

/**
 * Which day a Log counts for (Chronicle's `DayBoundary`, a personal setting, default midnight):
 * before [dayStart] on the wall clock, it is still yesterday.
 */
fun dayOf(at: LocalDateTime, dayStart: LocalTime = LocalTime(0, 0)): LocalDate =
    if (at.time < dayStart) at.date.plus(-1, DateTimeUnit.DAY) else at.date

/**
 * What a habit's Logs are allowed to say: presence, never absence. There is no streak, no count
 * of misses and nothing a screen could draw a chain from (SPEC §0.1.3). Ported from Chronicle's
 * `HabitPresence` (`domain/stats/HabitPresence.kt`), with the owner's counting rule and
 * Tendril's amounts for number habits.
 */
data class HabitPresence(
    /** Distinct days with a presence this month: "four days this month". */
    val daysThisMonth: Int,
    /** The latest day with a presence, or null while the habit has none. */
    val lastDate: LocalDate?,
    /** When it is usually done, or null until there is enough to say: three presences, more than half in one part of the day. */
    val usualTime: TimeOfDay?,
    /** The sum of today's numbers ("6 of 8 glasses"), or null when today has none. */
    val amountToday: Double?,
    /** The sum of this month's numbers, or null when the month has none. */
    val amountThisMonth: Double?,
)

fun presenceOf(logs: List<Log>, today: LocalDate, dayStart: LocalTime = LocalTime(0, 0)): HabitPresence {
    val live = logs.filter { it.isPresence }
    val days = live.map { dayOf(it.at, dayStart) }
    fun inMonth(d: LocalDate) = d.year == today.year && d.month == today.month
    val usual = live.groupingBy { timeOfDayOf(it.at.hour) }.eachCount().maxByOrNull { it.value }
        ?.takeIf { live.size >= 3 && it.value * 2 > live.size }?.key
    val numbers = live.filter { it.number != null }.map { dayOf(it.at, dayStart) to requireNotNull(it.number) }
    return HabitPresence(
        daysThisMonth = days.filter(::inMonth).toSet().size,
        lastDate = days.maxOrNull(),
        usualTime = usual,
        amountToday = numbers.filter { it.first == today }.takeIf { it.isNotEmpty() }?.sumOf { it.second },
        amountThisMonth = numbers.filter { inMonth(it.first) }.takeIf { it.isNotEmpty() }?.sumOf { it.second },
    )
}
