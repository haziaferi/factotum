package com.factotum.core.checkin.sim

import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.Outcome
import com.factotum.core.checkin.Recommendation
import com.factotum.core.checkin.RegulationEvent
import com.factotum.core.checkin.Stability
import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.max

/**
 * The shared online logistic SPEC v0.2 §3.2 originally assumed — kept test-only as the baseline the spike
 * falsified, so the comparison in LearnabilitySpikeTest stays reproducible. Not production code.
 */
class ParamLogistic(
    private val lr: Double,
    private val holdBelow: Double,
    private val askWithin: Double,
    private val noHoldWhenLowEnergy: Boolean,
    private val up: DoubleArray = doubleArrayOf(0.0, -2.0, 0.0, 0.0),
    private val down: DoubleArray = doubleArrayOf(0.0, 2.0, -2.0, 0.8),
) : DirectionPolicy {

    private fun x(c: CheckIn) = doubleArrayOf(1.0, c.energy - 0.5, c.pleasantness - 0.5, if (c.stability == Stability.FLAT) 1.0 else 0.0)
    private fun sig(z: Double) = 1.0 / (1.0 + exp(-z))
    private fun p(w: DoubleArray, c: CheckIn) = sig(w.indices.sumOf { w[it] * x(c)[it] })

    override fun recommend(c: CheckIn): Recommendation {
        val pUp = p(up, c); val pDown = p(down, c)
        val mayHold = !(noHoldWhenLowEnergy && c.energy < 0.5)
        return when {
            mayHold && max(pUp, pDown) < holdBelow -> Recommendation.HOLD
            abs(pUp - pDown) < askWithin -> Recommendation.ASK
            pUp > pDown -> Recommendation.UP
            else -> Recommendation.DOWN
        }
    }

    override fun update(e: RegulationEvent): DirectionPolicy {
        val y = when (e.outcome) { Outcome.HELPED -> 1.0; Outcome.NO_CHANGE -> 0.0; Outcome.NOT_NOW -> return this }
        val w = if (e.direction == Direction.UP) up else down
        val xs = x(e.checkIn)
        val err = y - sig(w.indices.sumOf { w[it] * xs[it] })
        val next = DoubleArray(w.size) { w[it] + lr * err * xs[it] }
        return if (e.direction == Direction.UP) ParamLogistic(lr, holdBelow, askWithin, noHoldWhenLowEnergy, next, down)
        else ParamLogistic(lr, holdBelow, askWithin, noHoldWhenLowEnergy, up, next)
    }
}
