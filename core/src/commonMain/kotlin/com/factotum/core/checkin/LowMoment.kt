package com.factotum.core.checkin

/**
 * "Lower than usual" (Equipoise SPEC §3.2, decided with the user 2026-09-12): in Equipoise, the trigger for the Mixed ask.
 *
 * A check-in is reduced to one state score, `energy + 1.5 · pleasantness`. The weight is a judgment,
 * not a derivation: a low-energy day in a calm, pleasant setting is rest, while an unpleasant day at
 * any energy — flat or agitated — is what the notes call a low moment, so mood must be able to outweigh
 * energy on its own. One scalar handles both cases the notes distinguish.
 *
 * Three layers, any of which is enough. Each covers a way the others fail:
 *  - fast   — lowest quarter of every check-in on the last [FAST_WINDOW] *logged days* (days need not be
 *             consecutive; several check-ins a day all count), live from [FAST_MIN] such days. Tracks the
 *             person's current range ("lower than usual for me lately").
 *  - slow   — the same quartile over the [SLOW_WINDOW] logged days *before* those, live once it holds
 *             [SLOW_MIN]. The last month never touches it, so a slump cannot become the baseline: the
 *             "lowest good" learned from the person's own better periods.
 *  - floor  — the score of a check-in at the midline of both axes. Always applies; the only rule during
 *             the first check-ins, and the safety net for a record that is low from end to end.
 *
 * Pure: same check-in and history → same verdict. History carries each earlier check-in with its logged
 * day (order irrelevant), excludes the check-in being judged, and anything dated after [today] is
 * ignored. Windows are counted in logged days, not check-ins, by decision (v0.7): three check-ins a day
 * for ten days is ten days of "usual", not thirty. Residual, stated in Equipoise SPEC §8: a slump longer than the
 * fast window starts to enter the slow baseline; only the floor sees days under the midline after that.
 */
object LowMoment {
    const val PLEASANTNESS_WEIGHT = 1.5
    const val FAST_WINDOW = 30
    const val FAST_MIN = 15
    const val SLOW_WINDOW = 120
    const val SLOW_MIN = 15
    /** Both axes at 0.5. */
    val FLOOR: Double = score(CheckIn(0.5, 0.5))

    data class Verdict(
        val score: Double,
        val byFloor: Boolean,
        val byFast: Boolean,
        val bySlow: Boolean,
        val fastCutoff: Double?,
        val slowCutoff: Double?,
    ) {
        val low: Boolean get() = byFloor || byFast || bySlow
    }

    fun score(c: CheckIn): Double = c.energy + PLEASANTNESS_WEIGHT * c.pleasantness

    fun assess(now: CheckIn, today: Int, history: List<Logged>): Verdict {
        val s = score(now)
        val byDay = history.filter { it.day <= today }.groupBy { it.day }
        val days = byDay.keys.sortedDescending()
        val fastDays = days.take(FAST_WINDOW)
        val slowDays = days.drop(FAST_WINDOW).take(SLOW_WINDOW)
        val fast = fastDays.flatMap { d -> byDay.getValue(d).map { score(it.checkIn) } }
        val slow = slowDays.flatMap { d -> byDay.getValue(d).map { score(it.checkIn) } }
        val fastCutoff = if (fastDays.size >= FAST_MIN) lowerQuartile(fast) else null
        val slowCutoff = if (slowDays.size >= SLOW_MIN) lowerQuartile(slow) else null
        return Verdict(
            score = s,
            byFloor = s < FLOOR,
            byFast = fastCutoff != null && s < fastCutoff,
            bySlow = slowCutoff != null && s < slowCutoff,
            fastCutoff = fastCutoff,
            slowCutoff = slowCutoff,
        )
    }

    /** Nearest-rank lower quartile: the value a quarter of the way up the sorted window. */
    private fun lowerQuartile(xs: List<Double>): Double = xs.sorted()[xs.size / 4]
}
