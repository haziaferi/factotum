package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

/**
 * The Mixed answer (Equipoise): "ask when my check-in is lower than usual".
 * Every-time (default) asks at every low moment and never decides that state for the person; auto asks
 * only until the posteriors separate. Learning from outcomes is identical in both modes.
 */
class MixedModeTest {

    private companion object { const val TODAY = 20_000 }

    private val low = CheckIn(0.3, 0.3)          // under the floor on both axes
    private val fine = CheckIn(0.8, 0.8)
    private val goodDays = List(40) { i -> Logged(TODAY - 1 - i, CheckIn(0.8, 0.8)) }

    /** Twenty HELPED taps on UP in the low quadrant — enough for any learner to be sure. */
    private val upHelped = List(20) { RegulationEvent(low, Direction.UP, Outcome.HELPED) }

    @Test
    fun `every-time keeps asking at a low moment however sure the posteriors are`() {
        assertEquals(Recommendation.ASK,
            DirectionEngine.recommend(low, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays))
    }

    @Test
    fun `auto stops asking once the posteriors separate`() {
        assertEquals(Recommendation.UP,
            DirectionEngine.recommend(low, upHelped, OnboardingAnswer.MIXED, MixedMode.AUTO, TODAY, goodDays))
    }

    @Test
    fun `every-time does not ask when the check-in is not low`() {
        val r = DirectionEngine.recommend(fine, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays)
        assertNotEquals(Recommendation.ASK, r)
        assertEquals(DirectionEngine.recommend(fine, upHelped, OnboardingAnswer.MIXED, MixedMode.AUTO, TODAY, goodDays), r)
    }

    @Test
    fun `lower than usual uses the check-in history, not only the floor`() {
        // Above the floor, but in the lowest quarter of forty good days: still asked.
        val mildlyLow = CheckIn(0.6, 0.7)
        assertEquals(Recommendation.ASK,
            DirectionEngine.recommend(mildlyLow, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays))
        // With no history to compare against, only the floor applies and this check-in is not low.
        assertNotEquals(Recommendation.ASK,
            DirectionEngine.recommend(mildlyLow, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, emptyList()))
    }

    @Test
    fun `more and less are untouched by the mixed mode`() {
        for (mode in MixedMode.entries) {
            assertEquals(Recommendation.UP, DirectionEngine.recommend(low, emptyList(), OnboardingAnswer.MORE, mode, TODAY, goodDays))
            assertEquals(Recommendation.DOWN, DirectionEngine.recommend(low, emptyList(), OnboardingAnswer.LESS, mode, TODAY, goodDays))
            assertEquals(Recommendation.UP, DirectionEngine.recommend(low, upHelped, OnboardingAnswer.LESS, mode, TODAY, goodDays))
        }
    }

    @Test
    fun `every-time still learns - switching to auto later has the data`() {
        // Fold the same history under every-time, then read it as auto: the taps were not thrown away.
        val model = DirectionEngine.fold(upHelped, OnboardingAnswer.MIXED)
        assertEquals(Recommendation.UP, model.recommend(low))
    }

    @Test
    fun `defaults are mixed and every-time`() {
        assertEquals(
            DirectionEngine.recommend(low, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays),
            DirectionEngine.recommend(low, upHelped, today = TODAY, checkIns = goodDays),
        )
    }

    @Test
    fun `same inputs give the same recommendation`() {
        val a = DirectionEngine.recommend(low, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays)
        val b = DirectionEngine.recommend(low, upHelped, OnboardingAnswer.MIXED, MixedMode.EVERY_TIME, TODAY, goodDays)
        assertEquals(a, b)
    }
}
