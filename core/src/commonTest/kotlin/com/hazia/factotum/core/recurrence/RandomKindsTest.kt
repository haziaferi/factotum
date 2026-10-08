package com.hazia.factotum.core.recurrence

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** The When sheet's random kinds and ends (decision 17, owner 2026-10-08), built on Chronicle's and Mnemo's. */
class RandomKindsTest {

    private val id = "01JB8Z3K4Q7M2N5P6R8S9T0V1W"
    private val start = LocalDateTime(2026, 10, 5, 9, 0)
    private val to = LocalDateTime(2027, 1, 5, 0, 0)
    private val everyDay = DayOfWeek.entries.toSet()

    // ---- the old forms draw exactly as before: items stored before this change keep their times ----------------------

    @Test
    fun mnemosOneTimeAWindowDrawsAsBefore() {
        val rule = Recurrence.RandomWindow(setOf(DayOfWeek.MONDAY, DayOfWeek.THURSDAY), LocalTime(10, 0), LocalTime(12, 0))
        // the previous expansion, verbatim
        val before = buildList {
            val minutes = 120
            var day = start.date
            while (LocalDateTime(day, LocalTime(0, 0)) < to) {
                if (day.dayOfWeek in rule.days) {
                    val minute = SeededDraw.between("$id|$day|RANDOM_WINDOW", 0, minutes)
                    add(LocalDateTime(day, LocalTime.fromSecondOfDay(10 * 3600 + 60 * minute)))
                }
                day = day.plus(1, DateTimeUnit.DAY)
            }
        }
        assertEquals(before, rule.occurrences(id, start, start, to))
        assertTrue(rule.plain)
    }

    @Test
    fun chroniclesRandomDaysDrawAsBefore() {
        val rule = Recurrence.RandomDays(2, 4)
        val before = buildList {
            var at = start
            while (at < to) {
                add(at)
                at = LocalDateTime(at.date.plus(SeededDraw.between("$id|${at.date}|RANDOM_DAYS", 2, 5), DateTimeUnit.DAY), at.time)
            }
        }
        assertEquals(before, rule.occurrences(id, start, start, to))
        assertTrue(rule.plain)
    }

    // ---- several random times a day -------------------------------------------------------------------------------------

    @Test
    fun threeRandomTimesADaySpreadOverTheWindow() {
        val rule = Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 3)
        val got = rule.occurrences(id, start, start, LocalDateTime(2026, 11, 5, 0, 0))
        val byDay = got.groupBy { it.date }
        assertEquals(31, byDay.size)
        for ((day, times) in byDay) {
            assertEquals(3, times.size, "$day")
            // one in each third of 09:00-17:00: [09:00, 11:40), [11:40, 14:20), [14:20, 17:00)
            val minutes = times.map { it.hour * 60 + it.minute - 540 }
            assertTrue(minutes[0] in 0 until 160 && minutes[1] in 160 until 320 && minutes[2] in 320 until 480, "$day $minutes")
        }
        assertEquals(got, got.sorted())
        assertTrue(got.map { it.time }.distinct().size > 30, "the times should vary")
        assertEquals(got, rule.occurrences(id, start, start, LocalDateTime(2026, 11, 5, 0, 0)))
        assertTrue(!rule.plain)
    }

    @Test
    fun aWindowPastMidnightEndsTheNextDay() {
        // opens on Fridays only, 22:00 to 02:00
        val rule = Recurrence.RandomWindow(setOf(DayOfWeek.FRIDAY), LocalTime(22, 0), LocalTime(2, 0), count = 2)
        val got = rule.occurrences(id, start, start, LocalDateTime(2026, 12, 1, 0, 0))
        assertTrue(got.isNotEmpty())
        for (at in got) {
            val friday = if (at.hour >= 22) at.date else at.date.plus(-1, DateTimeUnit.DAY)
            assertEquals(DayOfWeek.FRIDAY, friday.dayOfWeek, "$at")
            assertTrue(at.hour >= 22 || at.hour < 2, "$at")
        }
        // the part after midnight is found from a window that starts on that Saturday too
        val saturday = LocalDateTime(2026, 10, 10, 0, 0)
        assertEquals(got.filter { it >= saturday && it < LocalDateTime(2026, 10, 10, 12, 0) },
            rule.occurrences(id, start, saturday, LocalDateTime(2026, 10, 10, 12, 0)))
    }

    @Test
    fun moreTimesThanTheWindowHasMinutesIsRefused() {
        assertFailsWith<IllegalArgumentException> { Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(9, 2), count = 3) }
        assertFailsWith<IllegalArgumentException> { Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 49) }
    }

    // ---- random gaps bounded by a window -------------------------------------------------------------------------------

    @Test
    fun gapsOfMinutesStayInsideEachDaysWindow() {
        val rule = Recurrence.RandomDays(20, 40, GapUnit.MINUTE, TimeWindow(LocalTime(9, 0), LocalTime(17, 0)))
        val got = rule.occurrences(id, start, start, LocalDateTime(2026, 10, 12, 0, 0))
        for ((day, times) in got.groupBy { it.date }) {
            assertEquals(LocalTime(9, 0), times.first().time, "$day starts at the window's start")
            assertTrue(times.all { it.time <= LocalTime(17, 0) }, "$day")
            for ((a, b) in times.zipWithNext()) assertTrue((b.hour * 60 + b.minute) - (a.hour * 60 + a.minute) in 20..40, "$a -> $b")
        }
        assertEquals(7, got.groupBy { it.date }.size)
    }

    @Test
    fun gapsOfDaysDrawTheirTimeInTheWindow() {
        val rule = Recurrence.RandomDays(2, 4, GapUnit.DAY, TimeWindow(LocalTime(9, 0), LocalTime(12, 0)))
        val got = rule.occurrences(id, start, start, to)
        assertTrue(got.size > 15)
        for ((a, b) in got.zipWithNext()) assertTrue(b.date.toEpochDays() - a.date.toEpochDays() in 2..4, "$a -> $b")
        assertTrue(got.all { it.time >= LocalTime(9, 0) && it.time < LocalTime(12, 0) })
        assertTrue(got.map { it.time }.distinct().size > 5)
    }

    @Test
    fun gapsOfWeeksAreWholeWeeks() {
        val rule = Recurrence.RandomDays(1, 3, GapUnit.WEEK)
        val got = rule.occurrences(id, start, start, LocalDateTime(2027, 6, 1, 0, 0))
        for ((a, b) in got.zipWithNext()) assertTrue((b.date.toEpochDays() - a.date.toEpochDays()).let { it % 7 == 0L && it / 7 in 1..3 }, "$a -> $b")
        assertTrue(got.all { it.time == start.time })
    }

    @Test
    fun gapsWithinADayNeedAWindow() {
        assertFailsWith<IllegalArgumentException> { Recurrence.RandomDays(20, 40, GapUnit.MINUTE) }
    }

    // ---- ends ------------------------------------------------------------------------------------------------------------

    @Test
    fun aCountCountsFromTheStartWhateverTheWindowAsked() {
        val rule = Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(17, 0), count = 3, total = 7)
        val all = rule.occurrences(id, start, start, to)
        assertEquals(7, all.size)
        val later = LocalDateTime(2026, 10, 6, 12, 0)
        assertEquals(all.filter { it >= later }, rule.occurrences(id, start, later, to))
    }

    @Test
    fun anUntilIsInclusive() {
        val until = LocalDateTime(2026, 10, 20, 9, 0)
        val rule = Recurrence.RandomDays(2, 4, until = until)
        val got = rule.occurrences(id, start, start, to)
        assertTrue(got.isNotEmpty() && got.all { it <= until })
        assertEquals(Recurrence.RandomDays(2, 4).occurrences(id, start, start, to).filter { it <= until }, got)
    }

    @Test
    fun forSixDaysEndsAtTheLastMomentOfTheSixthDay() {
        assertEquals(LocalDateTime(2026, 10, 21, 23, 59, 59), untilForDays(LocalDate(2026, 10, 16), 6))
        // an RRULE ends the same way: every hour from 09:00 to 17:00, for 3 days
        val rule = RRule.parse("FREQ=HOURLY;BYHOUR=9,10,11,12,13,14,15,16,17;UNTIL=20261018T235959")!!
        val got = rule.occurrences(LocalDateTime(2026, 10, 16, 0, 0), LocalDateTime(2026, 10, 16, 0, 0), to)
        assertEquals(27, got.size)
        assertEquals(LocalDateTime(2026, 10, 18, 17, 0), got.last())
        assertEquals(untilForDays(LocalDate(2026, 10, 16), 3), LocalDateTime(2026, 10, 18, 23, 59, 59))
    }

    @Test
    fun anEndIsADateOrACountNotBoth() {
        assertFailsWith<IllegalArgumentException> { Recurrence.RandomDays(2, 4, until = start, total = 3) }
        assertFailsWith<IllegalArgumentException> { Recurrence.RandomWindow(everyDay, LocalTime(9, 0), LocalTime(10, 0), until = start, total = 3) }
        assertFailsWith<IllegalArgumentException> { untilForDays(LocalDate(2026, 10, 16), 0) }
    }
}
