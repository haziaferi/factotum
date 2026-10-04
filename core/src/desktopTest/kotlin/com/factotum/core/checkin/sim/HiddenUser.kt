package com.factotum.core.checkin.sim

import com.factotum.core.checkin.CheckIn
import com.factotum.core.checkin.Direction
import com.factotum.core.checkin.Recommendation

/** Which region of the arousal grid a check-in falls in (test vocabulary only). */
enum class Region { TARGET, LOW_PLEASANT, HIGH_UNPLEASANT, HIGH_PLEASANT }

fun regionOf(c: CheckIn): Region = when {
    c.energy < 0.5 && c.pleasantness < 0.5 -> Region.TARGET
    c.energy < 0.5 -> Region.LOW_PLEASANT
    c.pleasantness < 0.5 -> Region.HIGH_UNPLEASANT
    else -> Region.HIGH_PLEASANT
}

/**
 * A simulated person with a hidden truth about what helps. Outside the target region everyone follows the
 * notes' defaults (up when low, down when high-and-unpleasant, nothing when high-and-pleasant).
 * In the target region (low energy + unpleasant) the two users disagree — that is what the engine must learn.
 */
class HiddenUser(val name: String, private val targetUpHelps: Double, private val targetDownHelps: Double) {

    fun pHelped(c: CheckIn, d: Direction): Double = when (regionOf(c)) {
        Region.TARGET -> if (d == Direction.UP) targetUpHelps else targetDownHelps
        Region.LOW_PLEASANT -> if (d == Direction.UP) 0.75 else 0.35
        Region.HIGH_UNPLEASANT -> if (d == Direction.DOWN) 0.75 else 0.35
        Region.HIGH_PLEASANT -> 0.35
    }

    fun hiddenBest(c: CheckIn): Recommendation = when (regionOf(c)) {
        Region.TARGET -> if (targetUpHelps >= targetDownHelps) Recommendation.UP else Recommendation.DOWN
        Region.LOW_PLEASANT -> Recommendation.UP
        Region.HIGH_UNPLEASANT -> Recommendation.DOWN
        Region.HIGH_PLEASANT -> Recommendation.HOLD
    }

    companion object {
        /** ADHD default holds even when unpleasant. */
        val CONSISTENT = HiddenUser("consistent", targetUpHelps = 0.75, targetDownHelps = 0.35)
        /** Depression overrides the ADHD signature (Equipoise's notes): quiet helps, stimulation does not. */
        val INVERTED = HiddenUser("inverted", targetUpHelps = 0.35, targetDownHelps = 0.75)
    }
}
