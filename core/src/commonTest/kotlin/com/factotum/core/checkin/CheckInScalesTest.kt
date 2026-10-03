package com.factotum.core.checkin

import kotlinx.datetime.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class CheckInScalesTest {

    @Test
    fun aStepSitsInTheMiddleOfItsBandAndReadsBackAsItself() {
        assertEquals(0.3, axisValue(2, 5))
        assertEquals(listOf(1, 2, 3, 4, 5), (1..5).map { levelOf(axisValue(it, 5), 5) })
        assertEquals(listOf(1, 2, 3), (1..3).map { levelOf(axisValue(it, 3), 3) })
        assertEquals(5, levelOf(1.0, 5))
        assertEquals(1, levelOf(0.0, 5))
    }

    @Test
    fun anEvenScaleHasNoStepOnTheMidline() {
        for (levels in listOf(4, 6)) assertFalse((1..levels).any { axisValue(it, levels) == 0.5 })
        assertFailsWith<IllegalArgumentException> { axisValue(6, 5) }
    }

    @Test
    fun tendrilsWordsAndACheckInOnlyForADayThatHasHappened() {
        assertEquals("Good", Mood.fromLevel(4)?.label)
        assertEquals("High", Energy.fromLevel(4)?.label)
        assertTrue(checkInOffered(LocalDate(2026, 10, 2), LocalDate(2026, 10, 3)))
        assertFalse(checkInOffered(LocalDate(2026, 10, 4), LocalDate(2026, 10, 3)))
    }
}
