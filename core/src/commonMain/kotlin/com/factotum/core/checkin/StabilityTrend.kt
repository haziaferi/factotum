package com.factotum.core.checkin

/**
 * Arousal stability, measured rather than asked (Equipoise SPEC §3.1, decided 2026-09-12).
 *
 * The notes' Hegerl–Hensch frame cares about how arousal *behaves* — labile and jumpy, or rigid and
 * flat — as much as where it sits. The v0.3 design asked for it as a chip ("jumpy / steady / flat");
 * the engine never learned from it, and several check-ins a day measure it directly: the spread of a
 * day's weighted scores ([LowMoment.score]) is the day's jumpiness.
 *
 * Per logged day: ≥ 2 check-ins → `1 − spread / SCALE` at weight 1; exactly one → 1 at weight 0.5.
 * The half weight is the user's reading — one log and no return means no swing worth reporting —
 * halved because it can also mean the day was too hard to open the app (Equipoise SPEC §8). Weighted mean over
 * the last [WINDOW_DAYS] logged days, available from [MIN_DAYS]. Never an input to anything and never a
 * verdict; in Factotum it may be said in words, never drawn or shown as a number (owner, 2026-10-03).
 */
object StabilityTrend {
    /** Full range of the weighted score: (1, 1) − (0, 0) = 1 + 1.5. */
    const val SCALE = 1.0 + LowMoment.PLEASANTNESS_WEIGHT
    const val SINGLE_WEIGHT = 0.5
    const val WINDOW_DAYS = 30
    const val MIN_DAYS = 15

    data class DayValue(val value: Double, val weight: Double)

    fun dayValue(checkIns: List<CheckIn>): DayValue {
        require(checkIns.isNotEmpty()) { "a logged day has at least one check-in" }
        if (checkIns.size == 1) return DayValue(1.0, SINGLE_WEIGHT)
        val scores = checkIns.map(LowMoment::score)
        val spread = scores.max() - scores.min()
        return DayValue((1.0 - spread / SCALE).coerceIn(0.0, 1.0), 1.0)
    }

    /** Null until [MIN_DAYS] logged days exist on or before [today]. */
    fun index(today: Int, history: List<Logged>): Double? {
        val byDay = history.filter { it.day <= today }.groupBy { it.day }
        val days = byDay.keys.sortedDescending().take(WINDOW_DAYS)
        if (days.size < MIN_DAYS) return null
        val values = days.map { d -> dayValue(byDay.getValue(d).map { it.checkIn }) }
        return values.sumOf { it.value * it.weight } / values.sumOf { it.weight }
    }
}
