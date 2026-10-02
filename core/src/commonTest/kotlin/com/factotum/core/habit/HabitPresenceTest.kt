package com.factotum.core.habit

import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.RollUnit
import com.factotum.core.recurrence.occurrences
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

/** ADR 06 with the owner's 2026-10-02 answers: what a habit's Logs say, and rolling habits. */
class HabitPresenceTest {

    private val today = LocalDate(2026, 10, 14)

    private fun at(day: Int, hour: Int, minute: Int = 0) = LocalDateTime(2026, 10, day, hour, minute)

    @Test
    fun chronicleTrackerPresence_threeMorningsOfYesAreThreePresences() {
        val logs = listOf(Log(at(5, 7), yes = true), Log(at(6, 8), yes = true), Log(at(7, 7, 30), yes = true))

        val p = presenceOf(logs, today)

        assertEquals(3, p.daysThisMonth)
        assertEquals(LocalDate(2026, 10, 7), p.lastDate)
        assertEquals(TimeOfDay.MORNING, p.usualTime)
    }

    @Test
    fun aYesAnyRatingAndANumberAboveZeroCountAndANoDoesNot() {
        val logs = listOf(Log(at(1, 9), yes = false), Log(at(2, 9), rating = 1), Log(at(3, 9), number = 0.0), Log(at(4, 9), number = 2.0), Log(at(5, 9), yes = true))

        assertEquals(3, presenceOf(logs, today).daysThisMonth)
    }

    @Test
    fun aNumberHabitShowsTodaysAndThisMonthsAmounts() {
        val glasses = (0 until 6).map { Log(at(14, 8 + it), number = 1.0) } + Log(at(13, 9), number = 2.0) + Log(LocalDateTime(2026, 9, 30, 9, 0), number = 5.0)

        val p = presenceOf(glasses, today)

        assertEquals(6.0, p.amountToday)
        assertEquals(8.0, p.amountThisMonth)
    }

    @Test
    fun aHabitWithNoNumbersHasNoAmounts() {
        val p = presenceOf(listOf(Log(at(14, 9), yes = true)), today)

        assertNull(p.amountToday)
        assertNull(p.amountThisMonth)
    }

    @Test
    fun usualTimeNeedsThreeAndMoreThanHalfInOnePart() {
        assertNull(presenceOf(listOf(Log(at(1, 7), yes = true), Log(at(2, 7), yes = true)), today).usualTime)
        assertNull(presenceOf(listOf(Log(at(1, 7), yes = true), Log(at(2, 13), yes = true), Log(at(3, 19), yes = true), Log(at(4, 7), yes = true)), today).usualTime)
    }

    @Test
    fun aLogAfterMidnightCountsForYesterdayWhenTheDayStartsLater() {
        val late = Log(at(14, 1, 30), yes = true)

        assertEquals(LocalDate(2026, 10, 14), presenceOf(listOf(late), today).lastDate)
        assertEquals(LocalDate(2026, 10, 13), presenceOf(listOf(late), today, dayStart = LocalTime(4, 0)).lastDate)
    }

    @Test
    fun aRollingHabitIsDueAPeriodAfterItsLastLog() {
        val water = Recurrence.Rolling(2, RollUnit.DAY)
        val start = at(5, 8)

        // Never logged: due from the start, and every day until a Log.
        assertEquals(listOf(at(5, 8), at(6, 8), at(7, 8)), water.occurrences("w", start, at(5, 0), at(8, 0)))
        // Logged a day late, on the 8th: due again on the 10th, and every day from then until a Log.
        assertEquals(listOf(at(10, 8), at(11, 8), at(12, 8)), water.occurrences("w", start, at(8, 0), at(13, 0), lastDone = LocalDate(2026, 10, 8)))
    }

    @Test
    fun aRollingMonthIsACalendarMonth() {
        val haircut = Recurrence.Rolling(1, RollUnit.MONTH)

        val next = haircut.occurrences("h", at(1, 10), at(1, 0), LocalDateTime(2026, 12, 1, 0, 0), lastDone = LocalDate(2026, 10, 31))

        assertEquals(LocalDateTime(2026, 11, 30, 10, 0), next.first())
    }

    @Test
    fun anOverdueRollingHabitIsDueToday() {
        val weekly = Recurrence.Rolling(7, RollUnit.DAY)

        val got = weekly.occurrences("w", LocalDateTime(2026, 8, 1, 9, 0), LocalDateTime(2026, 10, 2, 0, 0), LocalDateTime(2026, 10, 4, 0, 0), lastDone = LocalDate(2026, 9, 1))

        assertEquals(listOf(LocalDateTime(2026, 10, 2, 9, 0), LocalDateTime(2026, 10, 3, 9, 0)), got)
    }
}
