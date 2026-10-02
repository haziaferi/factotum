package com.factotum.core.time

import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** ADR 07's totals and the owner's answers (2026-10-01, 2026-10-02), on the pure functions. */
class TimeTotalsTest {

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    private fun span(day: Int, from: Int, to: Int?) = Span(at(day, from), to?.let { at(day, it) })

    private val midnight = LocalTime(0, 0)

    @Test
    fun overlappingSpansCountOnceAndApartOnesAddUp() {
        val spans = listOf(span(5, 9, 11), span(5, 10, 12), span(5, 14, 15), span(5, 14, 14))

        assertEquals(4 * 3600L, unionSeconds(spans, at(6, 0)))
        assertEquals(3 * 3600L, unionSeconds(listOf(span(5, 9, 12), span(5, 10, 11)), at(6, 0)))
    }

    @Test
    fun aRunningSpanCountsUpToNowAndNotBeforeItStarts() {
        assertEquals(90 * 60L, unionSeconds(listOf(span(5, 9, null)), at(5, 10, 30)))
        assertEquals(0L, unionSeconds(listOf(span(5, 12, null)), at(5, 10)))
    }

    @Test
    fun aSpanCountsWhollyForTheDayItStarted() {
        val lateNight = Span(at(5, 23), at(6, 1))

        assertEquals(mapOf(LocalDate(2026, 10, 5) to 2 * 3600L), dayTotals(listOf(lateNight), at(7, 0), midnight))
    }

    @Test
    fun theDayStartDecidesWhichDayAnEarlySpanCountsFor() {
        val early = Span(at(6, 2), at(6, 3))

        assertEquals(setOf(LocalDate(2026, 10, 5)), dayTotals(listOf(early), at(7, 0), LocalTime(4, 0)).keys)
    }

    @Test
    fun aWeekIsTheSumOfItsDaysSoTheyAddUp() {
        // Overlapping spans that start on different days count on each day (ADR 07, corrected 2026-10-01).
        val spans = listOf(Span(at(5, 23), at(6, 2)), span(6, 1, 3))
        val week = (5..11).map { LocalDate(2026, 10, it) }

        assertEquals(3 * 3600L + 2 * 3600L, totalOf(week, spans, at(12, 0), midnight))
        assertEquals(dayTotals(spans, at(12, 0), midnight).values.sum(), totalOf(week, spans, at(12, 0), midnight))
    }

    @Test
    fun goalWindowsAreTheDayTheWeekFromMondayTheMonthFromThe1stAndAMilestones400Days() {
        val thursday = LocalDate(2026, 10, 8)

        assertEquals(listOf(thursday), goalDays(GoalPeriod.DAY, false, thursday))
        assertEquals((5..8).map { LocalDate(2026, 10, it) }, goalDays(GoalPeriod.WEEK, false, thursday))
        assertEquals((1..8).map { LocalDate(2026, 10, it) }, goalDays(GoalPeriod.MONTH, false, thursday))
        assertEquals(MILESTONE_DAYS, goalDays(GoalPeriod.WEEK, true, thursday).size)
    }

    @Test
    fun aTimerIsAskedAboutPastTwelveHoursAndAgainTwelveHoursAfterItWasKept() {
        val running = span(5, 8, null)

        assertFalse(runsLong(running, null, at(5, 20), LONG_RUN))
        assertTrue(runsLong(running, null, at(5, 20, 1), LONG_RUN))
        assertFalse(runsLong(running, at(5, 21), at(6, 9), LONG_RUN))
        assertTrue(runsLong(running, at(5, 21), at(6, 9, 1), LONG_RUN))
        assertFalse(runsLong(span(5, 8, 23), null, at(7, 0), LONG_RUN))
    }
}
