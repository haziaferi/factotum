package com.factotum.core.chart

import com.factotum.core.time.GoalPeriod
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

/** Chronicle's chart helpers (`MovingAverage.kt`, `GoalProgressRepository.recurringLineFor`, `ChartDataRepository` values). */
class ChartsTest {

    @Test
    fun aMovingAverageStartsOnDayOneAndSlidesItsWindow() {
        assertEquals(listOf(2.0, 3.0, 4.0, 6.0), movingAverageByDays(listOf(2.0, 4.0, 6.0, 8.0), 3))
        assertEquals(emptyList(), movingAverageByDays(emptyList(), 7))
        assertEquals(emptyList(), movingAverageByDays(listOf(1.0), 0))
    }

    @Test
    fun aGoalIsADailyLine() {
        assertEquals(10.0, dailyGoalLine(GoalPeriod.DAY, 10.0))
        assertEquals(2.0, dailyGoalLine(GoalPeriod.WEEK, 14.0))
        assertEquals(1.5, dailyGoalLine(GoalPeriod.MONTH, 45.0))
    }

    @Test
    fun aReadingIsANumberUnlessItIsAChoice() {
        assertEquals(3.5, readingValue(3.5, null, null))
        assertEquals(4.0, readingValue(null, null, 4))
        assertEquals(1.0 to 0.0, readingValue(null, true, null) to readingValue(null, false, null))
        assertNull(readingValue(null, null, null))
    }
}
