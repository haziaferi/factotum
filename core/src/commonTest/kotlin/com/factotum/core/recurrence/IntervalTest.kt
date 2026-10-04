package com.factotum.core.recurrence

import kotlinx.datetime.DayOfWeek
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull

class IntervalTest {
    @Test
    fun anIntervalIsStoredAsTendrilStoredItAndRepeatsAsAPlainRule() {
        val fortnight = Interval(2, IntervalUnit.WEEK)
        assertEquals("2:WEEK", fortnight.stored())
        assertEquals(fortnight, Interval.parse("2:WEEK"))
        assertEquals(Recurrence.Rule(RRule(Frequency.WEEKLY, 2)), fortnight.recurrence())
        assertEquals(fortnight, Interval.of(fortnight.recurrence()))
    }

    @Test
    fun aZeroOrNegativeCountOrAnUnknownUnitIsNoInterval() {
        listOf("0:DAY", "-1:WEEK", "2:YEAR", "2", "two:DAY", "", "1:DAY:3").forEach { assertNull(Interval.parse(it), it) }
        assertNull(Interval.parse(null))
        assertFailsWith<IllegalArgumentException> { Interval(0, IntervalUnit.DAY) }
        Unit
    }

    @Test
    fun aRicherRuleIsNoInterval() {
        assertNull(Interval.of(Recurrence.Rule(RRule(Frequency.WEEKLY, byDay = listOf(WeekdayNum(null, DayOfWeek.MONDAY))))))
        assertNull(Interval.of(Recurrence.Rule(RRule(Frequency.DAILY, count = 3))))
        assertNull(Interval.of(Recurrence.Rule(RRule(Frequency.YEARLY))))
        assertNull(Interval.of(Recurrence.RandomDays(1, 3)))
        assertNull(Interval.of(null))
    }
}
