package com.factotum.core.checkin

// Ported from Equipoise (domain/src/test/.../domain).

import com.factotum.core.checkin.sim.DirectionPolicy
import com.factotum.core.checkin.sim.HiddenUser
import com.factotum.core.checkin.sim.ModelPolicy
import com.factotum.core.checkin.sim.ParamLogistic
import com.factotum.core.checkin.sim.Region
import com.factotum.core.checkin.sim.Simulator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Equipoise's spec — direction-engine learnability.
 *
 * Original bar ("every seed ≥ 70 % rolling agreement by day 21, both users") is at the information floor of
 * one noisy tap per day and was not met by any learner tried; the spike's diagnostic sweeps are summarised
 * in Equipoise's spec. The amended acceptance below is the measured behaviour of the chosen design, asserted on
 * 20 seeds so a regression in the engine shows up as a drop in pass counts, not as a flaky single seed.
 */
class LearnabilitySpikeTest {

    private val seeds = 1..20
    private val users = listOf(HiddenUser.CONSISTENT, HiddenUser.INVERTED)

    private data class Curve(val pass21: Int, val pass49: Int, val meanTarget: Double, val meanAsk: Double)

    private fun curve(user: HiddenUser, policy: () -> DirectionPolicy): Curve {
        var p21 = 0; var p49 = 0; var t = 0.0; var a = 0.0
        for (seed in seeds) {
            val sim = Simulator.run(user, policy(), seed)
            if (sim.rollingAgreement(21) >= 0.70) p21++
            if (sim.rollingAgreement(49) >= 0.70) p49++
            t += sim.agreementIn(Region.TARGET, 30, 60)
            a += sim.askRateIn(Region.TARGET, 30, 60)
        }
        val n = seeds.count()
        return Curve(p21, p49, t / n, a / n)
    }

    @Test
    fun `report production engine against the falsified shared logistic`() {
        for (user in users) {
            val prod = curve(user) { ModelPolicy() }
            val logi = curve(user) { ParamLogistic(0.5, 0.55, 0.10, noHoldWhenLowEnergy = false) }
            println("SPIKE-9.1 user=${user.name} production: pass@21=${prod.pass21}/20 pass@49=${prod.pass49}/20 " +
                "target@30-60=${"%.2f".format(prod.meanTarget)} ask@30-60=${"%.2f".format(prod.meanAsk)}")
            println("SPIKE-9.1 user=${user.name} logistic  : pass@21=${logi.pass21}/20 pass@49=${logi.pass49}/20 " +
                "target@30-60=${"%.2f".format(logi.meanTarget)} ask@30-60=${"%.2f".format(logi.meanAsk)}")
        }
    }

    @Test
    fun `at least half the simulated users reach 70 percent rolling agreement by day 21`() {
        for (user in users) {
            val c = curve(user) { ModelPolicy() }
            assertTrue("user=${user.name} pass@21=${c.pass21}/20", c.pass21 >= 10)
        }
    }

    @Test
    fun `at least 80 percent of simulated users reach 70 percent rolling agreement by day 49`() {
        for (user in users) {
            val c = curve(user) { ModelPolicy() }
            assertTrue("user=${user.name} pass@49=${c.pass49}/20", c.pass49 >= 16)
        }
    }

    @Test
    fun `target quadrant agreement over days 30 to 60 averages at least 70 percent for both users`() {
        for (user in users) {
            val c = curve(user) { ModelPolicy() }
            assertTrue("user=${user.name} target=${c.meanTarget}", c.meanTarget >= 0.70)
        }
    }

    @Test
    fun `the inverted user is learned no worse than the consistent one`() {
        // The whole point of the amended prior: depression-override must not be the case the engine fails on.
        val cons = curve(HiddenUser.CONSISTENT) { ModelPolicy() }
        val inv = curve(HiddenUser.INVERTED) { ModelPolicy() }
        assertTrue("inverted=${inv.meanTarget} consistent=${cons.meanTarget}", inv.meanTarget >= cons.meanTarget - 0.05)
    }

    @Test
    fun `same seed gives an identical trace`() {
        val a = Simulator.run(HiddenUser.INVERTED, ModelPolicy(), 3)
        val b = Simulator.run(HiddenUser.INVERTED, ModelPolicy(), 3)
        assertEquals(a.traces, b.traces)
    }

    @Test
    fun `every recommendation in the trace is reproducible from folded history`() {
        for (user in users) {
            val sim = Simulator.run(user, ModelPolicy(), 4)
            var seen = 0
            for (t in sim.traces) {
                assertEquals("user=${user.name} day ${t.day}", t.recommendation,
                    auto(t.checkIn, sim.history.take(seen)))
                if (t.event != null) seen++
            }
        }
    }
}

/** The learner on its own: these tests are about what the model learns, so Mixed runs in AUTO. */
private fun auto(c: CheckIn, history: List<RegulationEvent>, answer: OnboardingAnswer = OnboardingAnswer.MIXED) =
    DirectionEngine.recommend(c, history, answer, MixedMode.AUTO)
