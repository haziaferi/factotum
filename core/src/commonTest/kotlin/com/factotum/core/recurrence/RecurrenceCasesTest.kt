package com.factotum.core.recurrence

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** ADR 04's cases (`decisions/cases/04-recurrence.jsonl`): the real expander against the owner apps' rules. */
class RecurrenceCasesTest {

    private fun recurrence(t: Truth): Recurrence =
        if (t.kind == "cron") assertNotNull(Cron.toRecurrence(t.form), t.form) else Recurrence.Rule(assertNotNull(RRule.parse(t.form), t.form))

    @Test
    fun theNineFixedRulesGiveTheOwnerAppsOccurrences() {
        for (t in TRUTHS) {
            val got = recurrence(t).occurrences("item", t.start, t.start, t.until)
            assertEquals(t.expected, got, t.id)
            assertTrue(t.expected.isNotEmpty(), t.id)
        }
    }

    @Test
    fun chronicleRandomDays_gapsOfTwoToFourDaysAtTheSameTimeTheSameOnEveryDevice() {
        val start = LocalDateTime(2026, 10, 5, 9, 0)
        val rule = Recurrence.RandomDays(2, 4)
        val series = rule.occurrences("01JB8Z3K4Q7M2N5P6R8S9T0V1W", start, start, LocalDateTime(2027, 1, 5, 0, 0))

        assertTrue(series.size > 5)
        assertEquals(start, series.first())
        for ((a, b) in series.zipWithNext()) {
            assertEquals(a.time, b.time)
            assertTrue(b.date.toEpochDays() - a.date.toEpochDays() in 2..4, "$a -> $b")
        }
        assertEquals(series, rule.occurrences("01JB8Z3K4Q7M2N5P6R8S9T0V1W", start, start, LocalDateTime(2027, 1, 5, 0, 0)))
        // Another item with the same start and range draws its own gaps (Chronicle's seed drew them in lockstep).
        assertTrue(series != rule.occurrences("01JB8Z3K4Q7M2N5P6R8S9T0V1X", start, start, LocalDateTime(2027, 1, 5, 0, 0)))
    }

    @Test
    fun mnemoStochasticWindow_oneTimeInsideTheWindowOnEachWeekday() {
        val start = LocalDateTime(2026, 10, 5, 9, 0)
        val weekdays = setOf(DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY)
        val rule = Recurrence.RandomWindow(weekdays, LocalTime(10, 0), LocalTime(12, 0))
        val to = LocalDateTime(2027, 1, 5, 0, 0)

        val series = rule.occurrences("item", start, start, to)

        val wanted = generateSequence(start.date) { it.plus(1, DateTimeUnit.DAY) }.takeWhile { it < to.date }.filter { it.dayOfWeek in weekdays }.toList()
        assertEquals(wanted, series.map { it.date })
        assertTrue(series.all { it.time >= LocalTime(10, 0) && it.time < LocalTime(12, 0) })
        assertTrue(series.map { it.time }.distinct().size > 10, "the times should vary from day to day")
    }

    @Test
    fun theSeededDrawMatchesTheSpikesSplitMix64() {
        for (d in DRAWS) assertEquals(d.value, SeededDraw.between(d.key, d.from, d.untilExclusive), d.key)
    }

    @Test
    fun aWindowOfOccurrencesLaterInTheSeriesIsTheSameAsTheWholeSeriesCutDown() {
        val start = LocalDateTime(2026, 10, 5, 9, 0)
        for (text in listOf("FREQ=DAILY;INTERVAL=3", "FREQ=MINUTELY;INTERVAL=90", "FREQ=HOURLY;INTERVAL=5;BYMINUTE=15,45", "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,TH",
            "FREQ=MONTHLY;BYDAY=-1FR", "FREQ=YEARLY;BYMONTH=3,10;BYMONTHDAY=5")) {
            val rule = assertNotNull(RRule.parse(text), text)
            val to = LocalDateTime(2028, 1, 1, 0, 0)
            val from = LocalDateTime(2027, 3, 4, 12, 0)
            assertEquals(rule.occurrences(start, start, to).filter { it >= from }, rule.occurrences(start, from, to), text)
        }
    }

    @Test
    fun aYearlyRuleKeepsItsLastYearsEarlierMonths() {
        val rule = assertNotNull(RRule.parse("FREQ=YEARLY;BYMONTH=3,10;BYMONTHDAY=5"))

        val got = rule.occurrences(LocalDateTime(2026, 10, 5, 9, 0), LocalDateTime(2026, 10, 1, 0, 0), LocalDateTime(2028, 4, 1, 0, 0))

        assertEquals(listOf(LocalDateTime(2026, 10, 5, 9, 0), LocalDateTime(2027, 3, 5, 9, 0), LocalDateTime(2027, 10, 5, 9, 0), LocalDateTime(2028, 3, 5, 9, 0)), got)
    }

    @Test
    fun countCountsFromTheStartEvenForALaterWindow() {
        val rule = assertNotNull(RRule.parse("FREQ=DAILY;COUNT=3"))
        val start = LocalDateTime(2026, 10, 5, 9, 0)

        assertEquals(listOf(LocalDateTime(2026, 10, 7, 9, 0)), rule.occurrences(start, LocalDateTime(2026, 10, 7, 0, 0), LocalDateTime(2027, 1, 1, 0, 0)))
    }

    @Test
    fun aStartTheRuleDoesNotMatchIsNotAnOccurrence() {
        val rule = assertNotNull(RRule.parse("FREQ=WEEKLY;BYDAY=MO"))
        val wednesday = LocalDateTime(2026, 10, 7, 9, 0)

        assertEquals(LocalDate(2026, 10, 12), rule.occurrences(wednesday, wednesday, LocalDateTime(2026, 10, 20, 0, 0)).first().date)
    }

    @Test
    fun aRuleWithAPartTheExpanderLacksIsRefusedNotGuessed() {
        for (text in listOf("FREQ=DAILY;BYWEEKNO=3", "FREQ=DAILY;BYSECOND=5", "FREQ=DAILY;X-NAME=1", "FREQ=SECONDLY", "FREQ=DAILY;COUNT=3;UNTIL=20270101",
            "FREQ=WEEKLY;BYDAY=2TU", "FREQ=MONTHLY;BYMONTHDAY=13;BYDAY=1FR", "FREQ=YEARLY;BYDAY=MO", "FREQ=DAILY;INTERVAL=0", "", "FREQ=DAILY;FREQ=WEEKLY")) {
            assertNull(RRule.parse(text), text)
        }
    }

    @Test
    fun aMonthDayAndAWeekdayMeanBoth() {
        val rule = assertNotNull(RRule.parse("FREQ=MONTHLY;BYMONTHDAY=31;BYDAY=MO"))

        val year = rule.occurrences(LocalDateTime(2026, 1, 1, 9, 0), LocalDateTime(2026, 1, 1, 0, 0), LocalDateTime(2027, 1, 1, 0, 0))

        // Only 31 August 2026 is a 31st and a Monday; February, with no 31st, gives nothing.
        assertEquals(listOf(LocalDateTime(2026, 8, 31, 9, 0)), year)
    }

    @Test
    fun bySetPosPicksWithinEachPeriod() {
        val rule = assertNotNull(RRule.parse("FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1"))

        val got = rule.occurrences(LocalDateTime(2026, 10, 1, 17, 0), LocalDateTime(2026, 10, 1, 0, 0), LocalDateTime(2027, 1, 1, 0, 0))

        assertEquals(listOf(LocalDateTime(2026, 10, 30, 17, 0), LocalDateTime(2026, 11, 30, 17, 0), LocalDateTime(2026, 12, 31, 17, 0)), got)
    }

    @Test
    fun aRareMinutelyRuleSkipsTheDaysItExcludes() {
        val rule = assertNotNull(RRule.parse("FREQ=MINUTELY;INTERVAL=30;BYMONTH=2;BYMONTHDAY=29"))

        val got = rule.occurrences(LocalDateTime(2026, 1, 1, 0, 0), LocalDateTime(2026, 1, 1, 0, 0), LocalDateTime(2028, 3, 1, 0, 0))

        assertEquals(48, got.size)
        assertTrue(got.all { it.date == LocalDate(2028, 2, 29) })
    }

    @Test
    fun aRuleThatCouldNeverOccurOrOverflowsIsRefused() {
        for (text in listOf("FREQ=WEEKLY;BYMONTHDAY=13", "FREQ=MONTHLY;BYMONTH=2;BYMONTHDAY=30,31", "FREQ=YEARLY;INTERVAL=2000000000")) {
            assertNull(RRule.parse(text), text)
        }
        assertNotNull(RRule.parse("FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29"))
    }

    @Test
    fun aRuleWrittenOutReadsBackTheSame() {
        for (text in listOf("FREQ=DAILY", "FREQ=MONTHLY;BYMONTHDAY=31,-1;BYSETPOS=1", "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,TH;WKST=SU",
            "FREQ=MONTHLY;BYDAY=2TU,-1FR", "FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20261101T235900", "FREQ=DAILY;COUNT=7;BYHOUR=8,20;BYMINUTE=30",
            "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29")) {
            val rule = assertNotNull(RRule.parse(text), text)
            assertEquals(rule, RRule.parse(rule.format()), text)
        }
    }

    @Test
    fun cronThatIsNotFiveNumericFieldsIsRefused() {
        for (text in listOf("* * * *", "0 9 * * MON", "0 24 * * *", "61 * * * *", "0 9 L * *", "5-1 * * * *", "1-2-3 * * * *")) {
            assertNull(Cron.toRecurrence(text), text)
        }
    }
}
