package com.factotum.core.checkin

/** One day's inputs to the index (Equipoise). Missing days are simply absent; fields may be null. */
data class DayRecord(
    val day: Int,
    val energy: Double? = null,
    val maskingLoad: Double? = null,
    val sensoryLoad: Double? = null,
    val sleepHours: Double? = null,
)

/** The index at one moment, worked out on demand and never stored (decision 14). `energyTrend` is the fortnight slope: negative = declining. */
data class DailyIndex(
    val energyTrend: Double,
    val maskingLoad: Double,
    val sensoryLoad: Double,
    val sleepDeficit: Double,
    val index: Double,
    val thresholdCrossed: Boolean,
)

/**
 * Equipoise's rolling early-warning index (its §9.2). Not a diagnosis.
 *
 *   slope14 = OLS slope of energy against day × 14   (from 3 energy points)
 *   trend   = clamp(−slope14 / 0.5, 0, 1)             a 0.5 drop over the fortnight saturates
 *   mask    = mean(maskingLoad)   over present days
 *   sensory = mean(sensoryLoad)   over present days
 *   sleep   = mean(clamp((7.5 − h) / 3, 0, 1)) over days with a value
 *   index   = Σ wᵢ termᵢ / Σ wᵢ over the terms present, weights 0.35 mask, 0.30 trend, 0.20 sensory,
 *             0.15 sleep; 0 when none is
 *   crossed = index ≥ threshold                        default 0.50, personal
 *
 * Changed from Equipoise, which counted a missing term as 0 (so without a sleep source the index
 * could never pass 0.85): the weights are spread over the terms present (owner, 2026-10-03,
 * decision 14), so not tracking something never makes the threshold harder to reach.
 */
object BurnoutIndex {
    const val DEFAULT_THRESHOLD = 0.50
    const val WINDOW_DAYS = 14.0
    const val TREND_SATURATION = 0.5
    const val SLEEP_TARGET_HOURS = 7.5
    const val SLEEP_SATURATION_HOURS = 3.0

    fun compute(window: List<DayRecord>, threshold: Double = DEFAULT_THRESHOLD): DailyIndex {
        val energies = window.count { it.energy != null }
        val slope14 = energySlope(window) * WINDOW_DAYS
        val trend = (-slope14 / TREND_SATURATION).coerceIn(0.0, 1.0)
        val mask = window.mapNotNull { it.maskingLoad }.takeIf { it.isNotEmpty() }?.average()
        val sensory = window.mapNotNull { it.sensoryLoad }.takeIf { it.isNotEmpty() }?.average()
        val sleep = window.mapNotNull { it.sleepHours }.takeIf { it.isNotEmpty() }
            ?.map { ((SLEEP_TARGET_HOURS - it) / SLEEP_SATURATION_HOURS).coerceIn(0.0, 1.0) }?.average()
        val terms = listOfNotNull(mask?.let { 0.35 to it }, trend.takeIf { energies >= 3 }?.let { 0.30 to it }, sensory?.let { 0.20 to it }, sleep?.let { 0.15 to it })
        val weight = terms.sumOf { it.first }
        val index = if (weight == 0.0) 0.0 else (terms.sumOf { it.first * it.second } / weight).coerceIn(0.0, 1.0)
        return DailyIndex(slope14, mask ?: 0.0, sensory ?: 0.0, sleep ?: 0.0, index, index >= threshold)
    }

    /** Ordinary least squares slope of energy per day; 0 with fewer than three points. */
    private fun energySlope(window: List<DayRecord>): Double {
        val pts = window.filter { it.energy != null }.map { it.day.toDouble() to it.energy!! }
        if (pts.size < 3) return 0.0
        val mx = pts.map { it.first }.average()
        val my = pts.map { it.second }.average()
        val sxx = pts.sumOf { (it.first - mx) * (it.first - mx) }
        if (sxx == 0.0) return 0.0
        return pts.sumOf { (it.first - mx) * (it.second - my) } / sxx
    }
}
