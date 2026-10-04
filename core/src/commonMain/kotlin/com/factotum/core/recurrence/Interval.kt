package com.factotum.core.recurrence

/** Tendril's `IntervalUnit`: what an interval column counts in. */
enum class IntervalUnit(internal val frequency: Frequency) { DAY(Frequency.DAILY), WEEK(Frequency.WEEKLY), MONTH(Frequency.MONTHLY) }

/**
 * A Recurrence column's value (decision 14, answer 23): "every [every] days, weeks or months",
 * stored as `n:UNIT` as Tendril stored it, and repeating as the plain rule `FREQ=…;INTERVAL=n`
 * from the task's start. A month is a calendar month on the start's day, as RFC 5545 counts it, so
 * a series begun on the 31st skips the months without one (Tendril added months one at a time, so
 * 31 January went to 28 February and stayed on the 28th).
 */
data class Interval(val every: Int, val unit: IntervalUnit) {
    init {
        // Tendril took 0 and negative counts, and the task then never moved on.
        require(every in 1..MAX_EVERY) { "an interval is every 1 to $MAX_EVERY units: $every" }
    }

    fun stored(): String = "$every:${unit.name}"

    fun recurrence(): Recurrence = Recurrence.Rule(RRule(unit.frequency, every))

    companion object {
        private const val MAX_EVERY = 10_000

        /** The interval [text] stores, or null when it stores none. */
        fun parse(text: String?): Interval? {
            val (n, u) = text?.split(':')?.takeIf { it.size == 2 } ?: return null
            val every = n.toIntOrNull()?.takeIf { it in 1..MAX_EVERY } ?: return null
            return IntervalUnit.entries.firstOrNull { it.name == u }?.let { Interval(every, it) }
        }

        /** The interval [recurrence] is, or null when it is anything richer: a rule with any other part, or another kind. */
        fun of(recurrence: Recurrence?): Interval? {
            val rule = (recurrence as? Recurrence.Rule)?.rule ?: return null
            val unit = IntervalUnit.entries.firstOrNull { it.frequency == rule.frequency } ?: return null
            return Interval(rule.interval, unit).takeIf { RRule(rule.frequency, rule.interval) == rule }
        }
    }
}
