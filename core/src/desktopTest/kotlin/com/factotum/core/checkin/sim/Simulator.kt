package com.factotum.core.checkin.sim

import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.Outcome
import com.factotum.core.checkin.Recommendation
import com.factotum.core.checkin.RegulationEvent
import com.factotum.core.checkin.Stability
import kotlin.random.Random

/** One simulated check-in day: what the engine said, what was true, and the tap (if any). */
data class DayTrace(val day: Int, val checkIn: CheckIn, val recommendation: Recommendation, val best: Recommendation, val event: RegulationEvent?)

class Simulation(val traces: List<DayTrace>, val history: List<RegulationEvent>) {
    /** Agreement = recommendation == hidden best; ASK counts as disagreement. Over the last [window] check-in days up to [day]. */
    fun rollingAgreement(day: Int, window: Int = 14): Double {
        val recent = traces.filter { it.day <= day }.takeLast(window)
        if (recent.isEmpty()) return 0.0
        return recent.count { it.recommendation == it.best }.toDouble() / recent.size
    }

    fun agreementIn(region: Region, fromDay: Int, toDay: Int): Double {
        val rows = traces.filter { it.day in fromDay..toDay && regionOf(it.checkIn) == region }
        if (rows.isEmpty()) return 0.0
        return rows.count { it.recommendation == it.best }.toDouble() / rows.size
    }

    fun askRateIn(region: Region, fromDay: Int, toDay: Int): Double {
        val rows = traces.filter { it.day in fromDay..toDay && regionOf(it.checkIn) == region }
        if (rows.isEmpty()) return 0.0
        return rows.count { it.recommendation == Recommendation.ASK }.toDouble() / rows.size
    }

    /** First day on which rolling agreement reaches [target]; null if never. */
    fun firstDayReaching(target: Double, window: Int = 14): Int? =
        traces.map { it.day }.firstOrNull { rollingAgreement(it, window) >= target }
}

/**
 * 60 days, one check-in per non-skipped day. State mixture 40/20/20/20 over the four regions; FLAT with
 * p = 0.5 in the target region. Taps: recommended direction is tried; HELPED with the hidden probability,
 * else NO_CHANGE; 10 % of taps become NOT_NOW; ASK → user picks a direction uniformly; HOLD → no event.
 */
object Simulator {
    const val DAYS = 60

    fun run(user: HiddenUser, policy0: DirectionPolicy, seed: Int): Simulation {
        val rnd = Random(seed)
        var policy = policy0
        val traces = ArrayList<DayTrace>()
        val history = ArrayList<RegulationEvent>()
        for (day in 1..DAYS) {
            if (rnd.nextDouble() < 0.10) continue
            val c = sampleCheckIn(rnd)
            val rec = policy.recommend(c)
            val best = user.hiddenBest(c)
            val tried: Direction? = when (rec) {
                Recommendation.UP -> Direction.UP
                Recommendation.DOWN -> Direction.DOWN
                Recommendation.ASK -> if (rnd.nextBoolean()) Direction.UP else Direction.DOWN
                Recommendation.HOLD -> null
            }
            val event = tried?.let { d ->
                val outcome = when {
                    rnd.nextDouble() < 0.10 -> Outcome.NOT_NOW
                    rnd.nextDouble() < user.pHelped(c, d) -> Outcome.HELPED
                    else -> Outcome.NO_CHANGE
                }
                RegulationEvent(c, d, outcome)
            }
            if (event != null) {
                history += event
                policy = policy.update(event)
            }
            traces += DayTrace(day, c, rec, best, event)
        }
        return Simulation(traces, history)
    }

    private fun sampleCheckIn(rnd: Random): CheckIn {
        val u = rnd.nextDouble()
        fun lo() = 0.05 + rnd.nextDouble() * 0.30
        fun hi() = 0.65 + rnd.nextDouble() * 0.30
        return when {
            u < 0.40 -> CheckIn(lo(), lo(), if (rnd.nextBoolean()) Stability.FLAT else Stability.STEADY)
            u < 0.60 -> CheckIn(lo(), hi(), Stability.STEADY)
            u < 0.80 -> CheckIn(hi(), lo(), Stability.STEADY)
            else -> CheckIn(hi(), hi(), Stability.STEADY)
        }
    }
}
