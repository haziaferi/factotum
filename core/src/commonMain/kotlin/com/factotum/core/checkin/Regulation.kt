package com.factotum.core.checkin

import kotlin.math.abs
import kotlin.math.max

/** A direction the user can actually act on. */
enum class Direction { UP, DOWN }

/** What the engine says (Equipoise). */
enum class Recommendation { UP, DOWN, HOLD, ASK }

/** One-tap outcome after a regulation action. */
enum class Outcome { HELPED, NO_CHANGE, NOT_NOW }

/** History row the engine learns from. Carries the check-in it answered, which replay needs (Equipoise). */
data class RegulationEvent(val checkIn: CheckIn, val direction: Direction, val outcome: Outcome)

/**
 * The one onboarding question (Equipoise): "When you experience a low moment, what is it that usually helps?"
 * More / Less seed the uncertain low-energy/unpleasant quadrant with a soft prior — a wrong answer is
 * recoverable from a few taps. Mixed leaves it flat and turns on the lower-than-usual ask ([MixedMode]).
 */
enum class OnboardingAnswer { MORE, LESS, MIXED }

/**
 * What Mixed means (Equipoise). EVERY_TIME — the default — asks at every check-in that is
 * lower than usual ([LowMoment]) and never decides that state for the person; AUTO asks only until the
 * posteriors separate, then suggests. Outcomes are learned identically in both.
 */
enum class MixedMode { EVERY_TIME, AUTO }

/**
 * Per-quadrant Beta posteriors over "this direction helped" (Equipoise).
 *
 * The arousal grid is split into four quadrants (energy < 0.5, pleasantness < 0.5); each quadrant holds an
 * independent (α, β) pair per direction. Stability does not split the data — it is too rare a signal to
 * afford halving the sample. Immutable: every update returns a new model, so the same history always folds
 * to the same posterior (replayable). No randomness anywhere.
 *
 * Why not the shared logistic the spec first assumed: the spike showed its shared bias lets successes in
 * one quadrant prop up the same direction in another, and a HOLD in a low-energy state produces no outcome
 * and so can never be learned out of. Both are structural, not tuning.
 */
class DirectionModel private constructor(private val table: Map<Key, Posterior>) {

    private data class Key(val lowEnergy: Boolean, val unpleasant: Boolean, val direction: Direction)
    private data class Posterior(val alpha: Double, val beta: Double) {
        val mean get() = alpha / (alpha + beta)
    }

    private fun key(c: CheckIn, d: Direction) = Key(c.energy < 0.5, c.pleasantness < 0.5, d)

    /** Posterior mean probability that [direction] helps in [checkIn]'s quadrant. */
    fun probability(direction: Direction, checkIn: CheckIn): Double = table.getValue(key(checkIn, direction)).mean

    fun recommend(checkIn: CheckIn): Recommendation {
        val pUp = probability(Direction.UP, checkIn)
        val pDown = probability(Direction.DOWN, checkIn)
        // Low energy always needs *something* (Equipoise's notes): HOLD is only available when energy is high.
        val mayHold = checkIn.energy >= 0.5
        return when {
            mayHold && max(pUp, pDown) < HOLD_BELOW -> Recommendation.HOLD
            abs(pUp - pDown) < ASK_WITHIN -> Recommendation.ASK
            pUp > pDown -> Recommendation.UP
            else -> Recommendation.DOWN
        }
    }

    /** HELPED → α+1, NO_CHANGE → β+1, NOT_NOW → unchanged (the user did not try it). */
    fun update(event: RegulationEvent): DirectionModel {
        val k = key(event.checkIn, event.direction)
        val p = table.getValue(k)
        val next = when (event.outcome) {
            Outcome.HELPED -> p.copy(alpha = p.alpha + 1)
            Outcome.NO_CHANGE -> p.copy(beta = p.beta + 1)
            Outcome.NOT_NOW -> return this
        }
        return DirectionModel(table + (k to next))
    }

    companion object {
        const val HOLD_BELOW = 0.55
        const val ASK_WITHIN = 0.10
        const val SEED_FOR = 2.6
        const val SEED_AGAINST = 2.0

        /**
         * Priors (Equipoise's acceptance at zero history):
         *  low energy + pleasant   → UP   (ADHD default)
         *  high energy + unpleasant → DOWN (depression default)
         *  high energy + pleasant   → HOLD
         *  low energy + unpleasant  → ASK — genuinely uncertain, because depression can invert the ADHD default
         *                              (Equipoise's notes) and a wrong prior cannot be overturned in time.
         */
        val PRIOR: DirectionModel = prior(OnboardingAnswer.MIXED)

        /** The prior with the low-energy/unpleasant quadrant seeded by the onboarding answer. */
        fun prior(answer: OnboardingAnswer): DirectionModel = DirectionModel(buildMap {
            for (low in listOf(true, false)) for (unpleasant in listOf(true, false)) {
                val (up, down) = when {
                    low && unpleasant -> when (answer) {
                        // Softer than the defaulted quadrants on purpose: steers the first attempt, and one failure
                        // on the seeded direction already reopens ASK — a wrong self-report must not become a trap.
                        OnboardingAnswer.MORE -> Posterior(SEED_FOR, SEED_AGAINST) to Posterior(SEED_AGAINST, SEED_FOR)
                        OnboardingAnswer.LESS -> Posterior(SEED_AGAINST, SEED_FOR) to Posterior(SEED_FOR, SEED_AGAINST)
                        OnboardingAnswer.MIXED -> Posterior(2.0, 2.0) to Posterior(2.0, 2.0)
                    }
                    low -> Posterior(3.0, 1.5) to Posterior(1.5, 3.0)
                    unpleasant -> Posterior(1.5, 3.0) to Posterior(3.0, 1.5)
                    else -> Posterior(1.5, 3.0) to Posterior(1.5, 3.0)
                }
                put(Key(low, unpleasant, Direction.UP), up)
                put(Key(low, unpleasant, Direction.DOWN), down)
            }
        })
    }
}

/**
 * Pure entry point: same (answer, mode, history, check-ins) → same recommendation (Equipoise).
 *
 * The learner ([DirectionModel]) is untouched by the Mixed answer; what changes is who gets the last
 * word. With Mixed + EVERY_TIME the engine asks at every check-in that is lower than usual
 * ([LowMoment]) instead of deciding from the posteriors — the person asked to be asked. Outcomes still
 * fold into the model, so switching to AUTO later has the data.
 *
 * [checkIns] is the person's earlier check-ins with their logged days, without [checkIn] itself; [today] is the
 * day [checkIn] is being made (epoch day).
 */
object DirectionEngine {
    fun fold(history: List<RegulationEvent>, answer: OnboardingAnswer = OnboardingAnswer.MIXED): DirectionModel =
        history.fold(DirectionModel.prior(answer)) { model, event -> model.update(event) }

    fun recommend(
        checkIn: CheckIn,
        history: List<RegulationEvent>,
        answer: OnboardingAnswer = OnboardingAnswer.MIXED,
        mixedMode: MixedMode = MixedMode.EVERY_TIME,
        today: Int = Int.MAX_VALUE,
        checkIns: List<Logged> = emptyList(),
    ): Recommendation {
        if (answer == OnboardingAnswer.MIXED && mixedMode == MixedMode.EVERY_TIME && LowMoment.assess(checkIn, today, checkIns).low) {
            return Recommendation.ASK
        }
        return fold(history, answer).recommend(checkIn)
    }
}

/**
 * The outcome tap is asked when the answer exists (Equipoise). A tool done in the app
 * ends with the tap; anything done away from the phone is asked in one line at the next open; an
 * unanswered ask lapses as NOT_NOW — never a second prompt. Three events over one optional pending:
 * [start] (a tool was chosen), [open] (the app came to the foreground), [answer] (the tap).
 *
 * A lapse is a real row, not a deletion: DirectionModel ignores NOT_NOW, so it is neutral for the
 * learner, but the replay stays honest about what was suggested. Ids and clocks are the repository's.
 */
data class PendingOutcome(val direction: Direction, val tool: String, val asked: Boolean = false)

data class Resolved(val pending: PendingOutcome, val outcome: Outcome)

/** What one event changed: the pending afterwards, the row to write if any, and whether to ask now. */
data class Step(val pending: PendingOutcome? = null, val resolved: Resolved? = null, val ask: PendingOutcome? = null)

object OutcomeAtNextOpen {
    fun start(current: PendingOutcome?, direction: Direction, tool: String) = Step(
        pending = PendingOutcome(direction, tool),
        resolved = current?.let { Resolved(it, Outcome.NOT_NOW) },
    )

    fun open(current: PendingOutcome?): Step = when {
        current == null -> Step()
        current.asked -> Step(resolved = Resolved(current, Outcome.NOT_NOW))
        else -> current.copy(asked = true).let { Step(pending = it, ask = it) }
    }

    fun answer(current: PendingOutcome?, outcome: Outcome): Step =
        if (current == null) Step() else Step(resolved = Resolved(current, outcome))
}
