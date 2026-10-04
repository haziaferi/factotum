package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

/** Equipoise's spec — direction-engine priors at zero history (Equipoise's acceptance, as amended by the spike). */
class DirectionEngineSpikeTest {

    private fun rec(e: Double, p: Double, s: Stability = Stability.STEADY) =
        auto(CheckIn(e, p, s), emptyList())

    @Test
    fun `low energy and pleasant recommends UP at zero history`() {
        assertEquals(Recommendation.UP, rec(0.2, 0.8))
    }

    @Test
    fun `high energy and unpleasant recommends DOWN at zero history`() {
        assertEquals(Recommendation.DOWN, rec(0.8, 0.2))
    }

    @Test
    fun `low energy and unpleasant asks whatever the stability`() {
        // Spike finding: the ADHD default (UP) must not be assumed here — depression can invert it (Equipoise's notes)
        // and a wrong prior cannot be overturned in time from one noisy tap a day.
        for (s in Stability.values()) assertEquals("stability=$s", Recommendation.ASK, rec(0.2, 0.2, s))
    }

    @Test
    fun `high energy and pleasant holds`() {
        assertEquals(Recommendation.HOLD, rec(0.8, 0.8))
    }
}

class DirectionEngineLearningTest {

    private val target = CheckIn(0.2, 0.2, Stability.FLAT)   // the ASK quadrant at zero history

    private fun events(n: Int, direction: Direction, outcome: Outcome, at: CheckIn = target) =
        List(n) { RegulationEvent(at, direction, outcome) }

    @Test
    fun `repeated HELPED taps for DOWN turn the ASK quadrant into DOWN`() {
        assertEquals(Recommendation.DOWN, auto(target, events(4, Direction.DOWN, Outcome.HELPED)))
    }

    @Test
    fun `repeated HELPED taps for UP turn the ASK quadrant into UP`() {
        assertEquals(Recommendation.UP, auto(target, events(4, Direction.UP, Outcome.HELPED)))
    }

    @Test
    fun `NOT_NOW taps do not move the model`() {
        assertEquals(Recommendation.ASK, auto(target, events(20, Direction.DOWN, Outcome.NOT_NOW)))
    }

    @Test
    fun `low energy never holds even when both directions have failed`() {
        // Spike finding: HOLD produces no outcome, so a HOLD in a low-energy state is a trap the engine cannot learn out of.
        val history = events(8, Direction.UP, Outcome.NO_CHANGE) + events(8, Direction.DOWN, Outcome.NO_CHANGE)
        assertNotEquals(Recommendation.HOLD, auto(target, history))
    }

    @Test
    fun `learning in one quadrant does not leak into another`() {
        // Spike finding: shared weights let UP's successes when pleasant prop up UP when unpleasant.
        val pleasant = CheckIn(0.2, 0.8, Stability.STEADY)
        val history = events(10, Direction.UP, Outcome.HELPED, at = pleasant)
        assertEquals(Recommendation.ASK, auto(target, history))
    }

    @Test
    fun `stability does not split the data`() {
        val steady = CheckIn(0.2, 0.2, Stability.STEADY)
        val history = events(4, Direction.DOWN, Outcome.HELPED, at = steady)
        assertEquals(Recommendation.DOWN, auto(target, history))
    }

    @Test
    fun `folding history equals incremental updates`() {
        val history = events(3, Direction.DOWN, Outcome.HELPED) + events(2, Direction.UP, Outcome.NO_CHANGE)
        var model = DirectionModel.PRIOR
        for (e in history) model = model.update(e)
        assertEquals(model.recommend(target), auto(target, history))
        assertEquals(model.probability(Direction.DOWN, target),
            DirectionEngine.fold(history).probability(Direction.DOWN, target), 1e-12)
    }
}

/** The learner on its own: these tests are about what the model learns, so Mixed runs in AUTO. */
private fun auto(c: CheckIn, history: List<RegulationEvent>, answer: OnboardingAnswer = OnboardingAnswer.MIXED) =
    DirectionEngine.recommend(c, history, answer, MixedMode.AUTO)
