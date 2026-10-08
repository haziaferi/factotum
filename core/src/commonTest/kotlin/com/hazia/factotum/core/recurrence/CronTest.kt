package com.hazia.factotum.core.recurrence

import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull

/** The owner's cron extensions (decision 17, 2026-10-08): names, `L`, `#`, several lines. Dates checked against a calendar. */
class CronTest {

    private val start = LocalDateTime(2026, 10, 1, 0, 0)

    private fun next(expression: String, until: LocalDateTime = LocalDateTime(2027, 3, 1, 0, 0)): List<LocalDateTime> =
        assertNotNull(Cron.toRecurrence(expression), expression).occurrences("item", start, start, until)

    private fun days(vararg d: Triple<Int, Int, Int>, hour: Int = 9) = d.map { (y, m, day) -> LocalDateTime(y, m, day, hour, 0) }

    @Test
    fun namesReadAsTheirNumbersInAnyCase() {
        assertEquals(next("0 9 * * 1-5"), next("0 9 * * MON-FRI"))
        assertEquals(next("0 9 * * 1-5"), next("0 9 * * mon-fri"))
        assertEquals(next("0 9 1 1,7 *"), next("0 9 1 JAN,JUL *"))
        assertEquals(next("0 9 * * 0,6"), next("0 9 * * SUN,SAT"))
    }

    @Test
    fun lInTheDayOfMonthIsTheLastDay() {
        val got = next("0 9 L * *")
        assertEquals(days(Triple(2026, 10, 31), Triple(2026, 11, 30), Triple(2026, 12, 31), Triple(2027, 1, 31), Triple(2027, 2, 28)), got)
    }

    @Test
    fun aHashIsTheNthWeekdayOfTheMonth() {
        // the second Tuesdays from October 2026: 13 Oct, 10 Nov, 8 Dec, 12 Jan, 9 Feb
        val expected = days(Triple(2026, 10, 13), Triple(2026, 11, 10), Triple(2026, 12, 8), Triple(2027, 1, 12), Triple(2027, 2, 9))
        assertEquals(expected, next("0 9 * * TUE#2"))
        assertEquals(expected, next("0 9 * * 2#2"))
    }

    @Test
    fun aWeekdayEndingInLIsTheLastOneOfTheMonth() {
        // the last Fridays: 30 Oct, 27 Nov, 25 Dec, 29 Jan, 26 Feb
        val expected = days(Triple(2026, 10, 30), Triple(2026, 11, 27), Triple(2026, 12, 25), Triple(2027, 1, 29), Triple(2027, 2, 26))
        assertEquals(expected, next("0 9 * * FRIL"))
        assertEquals(expected, next("0 9 * * 5L"))
    }

    @Test
    fun severalLinesAreOneRuleTheirUnion() {
        // every 90 minutes from 09:00 to 16:30, which one line cannot say
        val rule = assertNotNull(Cron.toRecurrence("0 9,12,15 * * *\n30 10,13,16 * * *"))
        assertIs<Recurrence.RuleSet>(rule)
        val day = rule.occurrences("item", start, start, LocalDateTime(2026, 10, 2, 0, 0)).map { it.hour * 60 + it.minute }
        assertEquals(listOf(540, 630, 720, 810, 900, 990), day)
        // blank lines and surrounding spaces do not count
        assertEquals(rule, Cron.toRecurrence("\n  0 9,12,15 * * *  \n\n30 10,13,16 * * *\n"))
    }

    @Test
    fun theOrRuleHoldsWithAnOrdinalWeekday() {
        // the 1st of the month, or its first Monday: 1 Oct, 5 Oct, 1 Nov, 2 Nov, 1 Dec, 7 Dec
        val got = next("0 9 1 * MON#1", LocalDateTime(2027, 1, 1, 0, 0))
        assertEquals(days(Triple(2026, 10, 1), Triple(2026, 10, 5), Triple(2026, 11, 1), Triple(2026, 11, 2), Triple(2026, 12, 1), Triple(2026, 12, 7)), got)
    }

    @Test
    fun plainAndOrdinalWeekdaysTogetherAreBoth() {
        // every Monday, and the second Friday: October 2026 has Mondays 5, 12, 19, 26 and its second Friday on the 9th
        val got = next("0 9 * * MON,FRI#2", LocalDateTime(2026, 11, 1, 0, 0)).map { it.date }
        assertEquals(listOf(5, 9, 12, 19, 26).map { LocalDate(2026, 10, it) }, got)
    }

    @Test
    fun whatTheExtensionsDoNotCoverIsStillRefused() {
        for (text in listOf("0 9 LW * *", "0 9 * * MON#6", "0 9 * * MON#0", "0 9 * * L", "0 9 ? * *", "0 9 * FOO *", "0 JAN * * *",
            "0 9 31 FEB *", "0 9 30,31 FEB *", "0 9 L,L * *", "", "\n \n", "0 9 * * *\n0 25 * * *", "0 9 * * TUE#2#3", "0 9 * * 8#1")) {
            assertNull(Cron.toRecurrence(text), "<$text>")
        }
        // a last day is in every month, February included
        assertNotNull(Cron.toRecurrence("0 9 L FEB *"))
    }

    @Test
    fun aSingleLineStaysASingleRule() {
        assertIs<Recurrence.Rule>(Cron.toRecurrence("30 8,20 * * *"))
        assertIs<Recurrence.Rule>(Cron.toRecurrence("0 9 * * TUE#2"))
    }
}
