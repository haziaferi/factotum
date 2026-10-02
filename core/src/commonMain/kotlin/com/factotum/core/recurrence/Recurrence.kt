package com.factotum.core.recurrence

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/**
 * How an item repeats (ADR 04, rrule+ext). Each kind expands from the item's start (DTSTART) into
 * local, floating date-times. PLANNED, the habit planner's kind, comes with habits (ADR 06).
 */
sealed interface Recurrence {

    /** One RFC 5545 rule. */
    data class Rule(val rule: RRule) : Recurrence

    /** A union of rules: several set times a day, or cron's "day of month OR day of week". */
    data class RuleSet(val rules: List<RRule>) : Recurrence {
        init {
            require(rules.size >= 2) { "a rule set holds two rules or more" }
        }
    }

    /** Chronicle's RandomDays: the next occurrence comes a drawn [minDays]..[maxDays] whole days later, at the same time. */
    data class RandomDays(val minDays: Int, val maxDays: Int) : Recurrence {
        init {
            require(minDays in 1..maxDays) { "need 1 <= minDays <= maxDays: $minDays..$maxDays" }
        }
    }

    /** Mnemo's stochastic window: on each of [days], one drawn minute in `[start, end)`. */
    data class RandomWindow(val days: Set<DayOfWeek>, val start: LocalTime, val end: LocalTime) : Recurrence {
        init {
            require(days.isNotEmpty()) { "a window needs a day" }
            require(end.toSecondOfDay() - start.toSecondOfDay() >= 60) { "the window must be a minute or more: $start..$end" }
        }
    }
}

/**
 * The occurrences of [this] for the item [itemId] starting at [dtstart], within `[from, to)`. The
 * random kinds draw from [itemId] and the occurrence's date, so every device computes the same
 * times and nothing drawn is stored (SPEC §3.4).
 */
fun Recurrence.occurrences(itemId: String, dtstart: LocalDateTime, from: LocalDateTime, to: LocalDateTime): List<LocalDateTime> =
    when (this) {
        is Recurrence.Rule -> rule.occurrences(dtstart, from, to)
        is Recurrence.RuleSet -> rules.flatMap { it.occurrences(dtstart, from, to) }.distinct().sorted()
        is Recurrence.RandomDays -> buildList {
            // Each gap is drawn from the occurrence before it, so the walk starts at dtstart.
            var at = dtstart
            while (at < to) {
                if (at >= from) add(at)
                val gap = SeededDraw.between(key(itemId, at.date, "RANDOM_DAYS"), minDays, maxDays + 1)
                at = LocalDateTime(at.date.plus(gap, DateTimeUnit.DAY), at.time)
            }
        }
        is Recurrence.RandomWindow -> buildList {
            val minutes = (end.toSecondOfDay() - start.toSecondOfDay()) / 60
            var day = maxOf(from.date, dtstart.date)
            while (LocalDateTime(day, MIDNIGHT) < to) {
                if (day.dayOfWeek in days) {
                    val minute = SeededDraw.between(key(itemId, day, "RANDOM_WINDOW"), 0, minutes)
                    val at = LocalDateTime(day, LocalTime.fromSecondOfDay(start.toSecondOfDay() + 60 * minute))
                    if (at >= dtstart && at >= from && at < to) add(at)
                }
                day = day.plus(1, DateTimeUnit.DAY)
            }
        }
    }

/** Whether the recurrence gives each occurrence its own time of day, rather than the start's. */
val Recurrence.setsTimes: Boolean
    get() = when (this) {
        is Recurrence.Rule -> rule.setsTimes
        is Recurrence.RuleSet -> rules.any { it.setsTimes }
        is Recurrence.RandomDays -> false
        is Recurrence.RandomWindow -> true
    }

private fun key(itemId: String, date: LocalDate, kind: String) = "$itemId|$date|$kind"
