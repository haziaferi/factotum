package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import com.factotum.core.checkin.sim.HiddenUser
import com.factotum.core.checkin.sim.ModelPolicy
import com.factotum.core.checkin.sim.Region
import com.factotum.core.checkin.sim.Simulator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Equipoise's cold-start mitigation: one onboarding question — "When you are low and miserable, does
 * stimulation or quiet help?" — seeds the uncertain low-energy/unpleasant quadrant. It is an input to the
 * engine like history is, so replay stays exact; and it is a soft prior, so a wrong answer is recoverable.
 */
class OnboardingTest {

    private val low = CheckIn(0.2, 0.2, Stability.STEADY)

    @Test
    fun `answering LESS makes the low unpleasant quadrant start at DOWN`() {
        assertEquals(Recommendation.DOWN, auto(low, emptyList(), OnboardingAnswer.LESS))
    }

    @Test
    fun `answering MORE makes the low unpleasant quadrant start at UP`() {
        assertEquals(Recommendation.UP, auto(low, emptyList(), OnboardingAnswer.MORE))
    }

    @Test
    fun `answering MIXED keeps the quadrant at ASK`() {
        assertEquals(Recommendation.ASK, auto(low, emptyList(), OnboardingAnswer.MIXED))
    }

    @Test
    fun `the default with no answer is MIXED`() {
        assertEquals(auto(low, emptyList(), OnboardingAnswer.MIXED), auto(low, emptyList()))
    }

    @Test
    fun `the answer touches no other quadrant`() {
        for (answer in OnboardingAnswer.values()) {
            assertEquals(Recommendation.UP, auto(CheckIn(0.2, 0.8), emptyList(), answer))
            assertEquals(Recommendation.DOWN, auto(CheckIn(0.8, 0.2), emptyList(), answer))
            assertEquals(Recommendation.HOLD, auto(CheckIn(0.8, 0.8), emptyList(), answer))
        }
    }

    @Test
    fun `a wrong answer is recoverable from a handful of taps`() {
        // Answered LESS, but in practice quiet does nothing and stimulation helps.
        val history = List(4) { RegulationEvent(low, Direction.DOWN, Outcome.NO_CHANGE) } +
            List(3) { RegulationEvent(low, Direction.UP, Outcome.HELPED) }
        assertEquals(Recommendation.UP, auto(low, history, OnboardingAnswer.LESS))
    }

    @Test
    fun `a correct answer lifts day 21 agreement for both users`() {
        val seeds = 1..20
        fun pass21(user: HiddenUser, answer: OnboardingAnswer) =
            seeds.count { Simulator.run(user, ModelPolicy(DirectionModel.prior(answer)), it).rollingAgreement(21) >= 0.70 }
        val consistent = pass21(HiddenUser.CONSISTENT, OnboardingAnswer.MORE)
        val inverted = pass21(HiddenUser.INVERTED, OnboardingAnswer.LESS)
        println("SPIKE-9.1 onboarding correct: consistent pass@21=$consistent/20 inverted pass@21=$inverted/20")
        assertTrue("consistent $consistent", consistent >= 15)
        assertTrue("inverted $inverted", inverted >= 15)
    }

    @Test
    fun `a wrong answer still recovers by day 49`() {
        val seeds = 1..20
        fun stats(user: HiddenUser, answer: OnboardingAnswer): Pair<Int, Double> {
            var p49 = 0; var t = 0.0
            for (s in seeds) {
                val sim = Simulator.run(user, ModelPolicy(DirectionModel.prior(answer)), s)
                if (sim.rollingAgreement(49) >= 0.70) p49++
                t += sim.agreementIn(Region.TARGET, 30, 60)
            }
            return p49 to t / seeds.count()
        }
        val (cP, cT) = stats(HiddenUser.CONSISTENT, OnboardingAnswer.LESS)      // wrong
        val (iP, iT) = stats(HiddenUser.INVERTED, OnboardingAnswer.MORE)  // wrong
        println("SPIKE-9.1 onboarding wrong: consistent pass@49=$cP/20 target=${"%.2f".format(cT)} inverted pass@49=$iP/20 target=${"%.2f".format(iT)}")
        assertTrue("consistent wrong-answer pass@49=$cP", cP >= 14)
        assertTrue("inverted wrong-answer pass@49=$iP", iP >= 14)
    }
}

/** The learner on its own: these tests are about what the model learns, so Mixed runs in AUTO. */
private fun auto(c: CheckIn, history: List<RegulationEvent>, answer: OnboardingAnswer = OnboardingAnswer.MIXED) =
    DirectionEngine.recommend(c, history, answer, MixedMode.AUTO)
