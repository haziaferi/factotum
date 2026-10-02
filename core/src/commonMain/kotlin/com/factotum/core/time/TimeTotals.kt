package com.factotum.core.time

import com.factotum.core.habit.dayOf
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.TimeZone
import kotlinx.datetime.isoDayNumber
import kotlinx.datetime.plus
import kotlinx.datetime.toInstant
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours

/*
 * Tracked time (ADR 07). A span counts wholly for the day it started (owner, 2026-10-01); a day's
 * total is the union of the spans that started that day, so two timers running at once count
 * once, and a week's or a goal period's total is the sum of its days. A running span counts up to
 * now. Times are floating local date-times, as every Factotum time is, so a span across a clock
 * change is measured on the wall clock.
 */

/** One span of tracked time; [end] is null while it runs. */
data class Span(val start: LocalDateTime, val end: LocalDateTime?)

/** Seconds from [a] to [b] on the wall clock. */
fun secondsBetween(a: LocalDateTime, b: LocalDateTime): Long = (b.toInstant(TimeZone.UTC) - a.toInstant(TimeZone.UTC)).inWholeSeconds

/** The seconds [spans] cover together, a running one up to [now]: overlaps count once. */
fun unionSeconds(spans: List<Span>, now: LocalDateTime): Long {
    var total = 0L
    var reached: LocalDateTime? = null
    // In start order, each span adds only what lies past the furthest end so far.
    for ((start, end) in spans.map { it.start to (it.end ?: maxOf(now, it.start)) }.sortedBy { it.first }) {
        val from = reached?.let { maxOf(it, start) } ?: start
        if (end > from) {
            total += secondsBetween(from, end)
            reached = end
        }
    }
    return total
}

/** Each day's total in seconds, by the personal day ([dayStart]) each span started on. */
fun dayTotals(spans: List<Span>, now: LocalDateTime, dayStart: LocalTime): Map<LocalDate, Long> =
    spans.groupBy { dayOf(it.start, dayStart) }.mapValues { (_, day) -> unionSeconds(day, now) }

/** The total of [days], in seconds: the sum of their day totals, so the days add up to it. */
fun totalOf(days: Iterable<LocalDate>, spans: List<Span>, now: LocalDateTime, dayStart: LocalTime): Long {
    val totals = dayTotals(spans, now, dayStart)
    return days.sumOf { totals[it] ?: 0L }
}

enum class GoalPeriod { DAY, WEEK, MONTH }

/**
 * The days a goal on tracked time counts, up to [today] (Chronicle's windows): a recurring goal
 * its day, its week from Monday or its month from the 1st; a milestone the last [MILESTONE_DAYS].
 */
fun goalDays(period: GoalPeriod, milestone: Boolean, today: LocalDate): List<LocalDate> {
    val first = when {
        milestone -> today.plus(1 - MILESTONE_DAYS, DateTimeUnit.DAY)
        period == GoalPeriod.DAY -> today
        period == GoalPeriod.WEEK -> today.plus(1 - today.dayOfWeek.isoDayNumber, DateTimeUnit.DAY)
        else -> LocalDate(today.year, today.month, 1)
    }
    return generateSequence(first) { it.plus(1, DateTimeUnit.DAY) }.takeWhile { it <= today }.toList()
}

/** How far back a milestone counts (Chronicle's `MILESTONE_DAYS`). */
const val MILESTONE_DAYS = 400

/** How long a timer runs before the person is asked about it, until they set otherwise (owner, 2026-10-02: a personal setting). */
val LONG_RUN: Duration = 12.hours

/**
 * Whether a running span has run past [limit] since it started, or since the person last said to
 * keep it ([keptAt]): then they are asked to keep it, end it at a time they pick, or end it at the
 * limit. A finished span never is.
 */
fun runsLong(span: Span, keptAt: LocalDateTime?, now: LocalDateTime, limit: Duration): Boolean =
    span.end == null && secondsBetween(maxOf(span.start, keptAt ?: span.start), now) > limit.inWholeSeconds
