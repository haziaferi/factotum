package com.factotum.core.recurrence

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/**
 * How an item repeats (ADR 04, rrule+ext). Each kind expands from the item's start (DTSTART) into
 * local, floating date-times. ROLLING is Tendril's rolling habit (ADR 06, owner 2026-10-02), and
 * PLANNED its habit planner's two rules (ADR 04, amended).
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

    /**
     * Tendril's rolling habit (owner, 2026-10-02): it falls due [every] [unit]s after the last Log,
     * or at the start before any Log, and stays due every day from then until a Log moves it, as
     * Tendril's does (`isIntervalHabitDueOn`). A month is a calendar month (Tendril counted 30 days).
     */
    data class Rolling(val every: Int, val unit: RollUnit) : Recurrence {
        init {
            require(every in 1..10_000) { "roll every 1 to 10,000 units: $every" }
        }
    }

    /**
     * Tendril's planner rules, which no fixed schedule expresses (ADR 04, amended). [Per.DAY]: [n]
     * a day on [days], each in a time block: [blocks] in order when given (one each, so [n] is their
     * count), else spread evenly over all of them. Its occurrences have no time of their own: the
     * i-th of a day is at [slotTime] (i), which tells them apart. [Per.WEEK]: [n] days a week among
     * [days]; the planner only suggests them, and a week's days are the person's WEEK edit (ADR 11),
     * so the rule alone gives no occurrence.
     */
    data class Planned(val n: Int, val per: Per, val days: Set<DayOfWeek> = DayOfWeek.entries.toSet(), val blocks: List<String> = emptyList()) : Recurrence {
        enum class Per { DAY, WEEK }

        init {
            require(days.isNotEmpty()) { "a planned habit needs a day" }
            require(n in 1..(if (per == Per.DAY) MAX_PER_DAY else 7)) { "$n a ${per.name.lowercase()} is out of range" }
            require(blocks.isEmpty() || (per == Per.DAY && blocks.size == n)) { "blocks name each of a day's occurrences" }
            require(blocks.none { it.isEmpty() || ',' in it }) { "not block ids: $blocks" }
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

enum class RollUnit { DAY, WEEK, MONTH }

/** At most one occurrence every half hour (Tendril's `MAX_TIMES_PER_DAY`). */
const val MAX_PER_DAY = 48

/** The time that tells the [i]-th of a planned day's occurrences apart: [i] seconds past midnight, which no set time uses. */
fun slotTime(i: Int): LocalTime = LocalTime.fromSecondOfDay(i)

/**
 * The occurrences of [this] for the item [itemId] starting at [dtstart], within `[from, to)`. The
 * random kinds draw from [itemId] and the occurrence's date, so every device computes the same
 * times and nothing drawn is stored (SPEC §3.4). A ROLLING item rolls from [lastDone], the day of
 * its last Log.
 */
fun Recurrence.occurrences(
    itemId: String,
    dtstart: LocalDateTime,
    from: LocalDateTime,
    to: LocalDateTime,
    lastDone: LocalDate? = null,
): List<LocalDateTime> =
    when (this) {
        is Recurrence.Rolling -> buildList {
            val unit = when (unit) {
                RollUnit.DAY -> DateTimeUnit.DAY
                RollUnit.WEEK -> DateTimeUnit.WEEK
                RollUnit.MONTH -> DateTimeUnit.MONTH
            }
            val due = maxOf(lastDone?.plus(every, unit) ?: dtstart.date, dtstart.date)
            var day = maxOf(due, from.date)
            while (true) {
                val at = LocalDateTime(day, dtstart.time)
                if (at >= to) break
                if (at >= from) add(at)
                day = day.plus(1, DateTimeUnit.DAY)
            }
        }
        is Recurrence.Planned -> buildList {
            if (per == Recurrence.Planned.Per.WEEK) return@buildList
            var day = maxOf(from.date, dtstart.date)
            while (LocalDateTime(day, MIDNIGHT) < to) {
                if (day.dayOfWeek in days) {
                    for (i in 0 until n) LocalDateTime(day, slotTime(i)).takeIf { it >= from && it < to }?.let(::add)
                }
                day = day.plus(1, DateTimeUnit.DAY)
            }
        }
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
        is Recurrence.RandomDays, is Recurrence.Rolling, is Recurrence.Planned -> false
        is Recurrence.RandomWindow -> true
    }

private fun key(itemId: String, date: LocalDate, kind: String) = "$itemId|$date|$kind"
