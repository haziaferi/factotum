package com.factotum.core.chart

import com.factotum.core.time.GoalPeriod

/**
 * A trailing moving average over a daily series, oldest first (Chronicle's `movingAverageByDays`):
 * point i is the mean of the last [windowDays] days ending at it, the first days averaging over what
 * there is, so there is one point per day. Every day counts, so a series with days of no reading
 * needs a value for them first: an activity's empty day is truly 0; how a tracker's is filled waits
 * for the screens (decision 14).
 */
fun movingAverageByDays(values: List<Double>, windowDays: Int): List<Double> {
    if (values.isEmpty() || windowDays <= 0) return emptyList()
    var sum = 0.0
    return values.mapIndexed { i, v ->
        sum += v
        if (i >= windowDays) sum -= values[i - windowDays]
        sum / minOf(i + 1, windowDays)
    }
}

/** A recurring goal as a daily line on a chart (Chronicle's `recurringLineFor`): a day's value, a week's over 7, a month's over 30. */
fun dailyGoalLine(period: GoalPeriod, value: Double): Double = when (period) {
    GoalPeriod.DAY -> value
    GoalPeriod.WEEK -> value / 7.0
    GoalPeriod.MONTH -> value / 30.0
}

/**
 * One tracker reading as a number to chart (Chronicle's): a number as it is, a rating as its
 * stars, a yes as 1 and a no as 0; a choice has none.
 */
fun readingValue(number: Double?, yes: Boolean?, rating: Long?): Double? = number ?: rating?.toDouble() ?: yes?.let { if (it) 1.0 else 0.0 }
