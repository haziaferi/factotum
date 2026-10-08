package com.hazia.factotum.core.recurrence

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

    /**
     * Random gaps. Chronicle's RandomDays as it was: the next occurrence comes a drawn [minDays]..[maxDays] whole days
     * later, at the same time. The When sheet's (decision 17, owner 2026-10-08) generalise it: the gap counts [unit]s,
     * so [minDays] and [maxDays] are in that unit; a [window] draws each occurrence's time inside it ("every 2-4 days at
     * random between 9:00 and 12:00"); minutes and hours need one ("every 20-40 minutes at random between 9:00 and
     * 17:00", restarting at the window's start each day). [until] (inclusive) or [total] (occurrences in all) ends it.
     */
    data class RandomDays(
        val minDays: Int,
        val maxDays: Int,
        val unit: GapUnit = GapUnit.DAY,
        val window: TimeWindow? = null,
        val until: LocalDateTime? = null,
        val total: Int? = null,
    ) : Recurrence {
        init {
            require(minDays in 1..maxDays) { "need 1 <= minDays <= maxDays: $minDays..$maxDays" }
            require(window != null || !unit.withinDay) { "gaps of ${unit.name.lowercase()}s need a window (the owner's bound)" }
            require(until == null || total == null) { "an end is a date or a count, not both" }
            require(total == null || total >= 1) { "a count of occurrences is 1 or more: $total" }
        }

        /** Whether this is Chronicle's form, which the RANDOM_DAYS columns hold (older versions read it). */
        val plain: Boolean get() = unit == GapUnit.DAY && window == null && until == null && total == null
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

    /**
     * Mnemo's stochastic window: on each of [days], one drawn minute in `[start, end)`. The When sheet's (decision 17,
     * owner 2026-10-08) generalise it: [count] times a day, one drawn in each of [count] equal parts of the window, so
     * they spread and never coincide; an [end] at or before [start] runs past midnight (22:00-02:00); [until]
     * (inclusive) or [total] (occurrences in all) ends it.
     */
    data class RandomWindow(
        val days: Set<DayOfWeek>,
        val start: LocalTime,
        val end: LocalTime,
        val count: Int = 1,
        val until: LocalDateTime? = null,
        val total: Int? = null,
    ) : Recurrence {
        init {
            require(days.isNotEmpty()) { "a window needs a day" }
            require(start != end) { "the window must be a minute or more: $start..$end" }
            require(count in 1..MAX_PER_DAY) { "1 to $MAX_PER_DAY times a day: $count" }
            require(TimeWindow(start, end).minutes >= count) { "$count times need a window of $count minutes or more: $start..$end" }
            require(until == null || total == null) { "an end is a date or a count, not both" }
            require(total == null || total >= 1) { "a count of occurrences is 1 or more: $total" }
        }

        /** Whether this is Mnemo's form, which the RANDOM_WINDOW columns hold (older versions read it). */
        val plain: Boolean get() = count == 1 && end > start && until == null && total == null
    }
}

enum class RollUnit { DAY, WEEK, MONTH }

/** The unit of a random gap; minutes and hours fall within a day's window. */
enum class GapUnit(val withinDay: Boolean) { MINUTE(true), HOUR(true), DAY(false), WEEK(false), MONTH(false) }

/** A time of day from [start] to [end]; an [end] at or before [start] is on the next day. */
data class TimeWindow(val start: LocalTime, val end: LocalTime) {
    init {
        require(start != end) { "the window must be a minute or more: $start..$end" }
    }

    /** Its length in whole minutes. */
    val minutes: Int get() = ((end.toSecondOfDay() - start.toSecondOfDay()) / 60).let { if (it > 0) it else it + 24 * 60 }

    /** [minute] minutes into the window that opens on [day]. */
    fun at(day: LocalDate, minute: Int): LocalDateTime {
        val m = start.toSecondOfDay() / 60 + minute
        return LocalDateTime(day.plus(m / (24 * 60), DateTimeUnit.DAY), LocalTime.fromSecondOfDay((m % (24 * 60)) * 60))
    }
}

/** "For [days] days" (the When sheet's end, decision 17) as an inclusive end: the last moment of the [days]-th day from [start]. */
fun untilForDays(start: LocalDate, days: Int): LocalDateTime {
    require(days >= 1) { "for 1 day or more: $days" }
    return LocalDateTime(start.plus(days - 1, DateTimeUnit.DAY), LocalTime(23, 59, 59))
}

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
        is Recurrence.RandomDays -> {
            val ends = Ends(until, total)
            if (unit.withinDay) buildList {
                // Within each day's window: from its start, a drawn gap after each occurrence, until the window closes.
                val w = requireNotNull(window)
                val step = if (unit == GapUnit.HOUR) 60 else 1
                var day = if (total == null) maxOf(from.date.plus(-1, DateTimeUnit.DAY), dtstart.date) else dtstart.date
                walk@ while (LocalDateTime(day, MIDNIGHT) < to) {
                    var minute = 0
                    var i = 0
                    while (minute <= w.minutes) {
                        val at = w.at(day, minute)
                        if (at >= dtstart) {
                            if (!ends.allow(at) || at >= to) break@walk
                            if (at >= from) add(at)
                        }
                        minute += step * SeededDraw.between(key(itemId, day, "RANDOM_GAPS#$i"), minDays, maxDays + 1)
                        i++
                    }
                    day = day.plus(1, DateTimeUnit.DAY)
                }
            } else buildList {
                // Each gap is drawn from the occurrence before it, so the walk starts at dtstart.
                val step = when (unit) {
                    GapUnit.WEEK -> DateTimeUnit.WEEK
                    GapUnit.MONTH -> DateTimeUnit.MONTH
                    else -> DateTimeUnit.DAY
                }
                var date = dtstart.date
                while (true) {
                    val at = window?.let { it.at(date, SeededDraw.between(key(itemId, date, "RANDOM_GAP_TIME"), 0, it.minutes)) } ?: LocalDateTime(date, dtstart.time)
                    if (at >= to || !ends.allow(at)) break
                    if (at >= from && at >= dtstart) add(at)
                    // the same key as Chronicle's form, so its gaps do not move
                    date = date.plus(SeededDraw.between(key(itemId, date, "RANDOM_DAYS"), minDays, maxDays + 1), step)
                }
            }
        }
        is Recurrence.RandomWindow -> buildList {
            val w = TimeWindow(start, end)
            val ends = Ends(until, total)
            // A window past midnight can reach into the day after it opened; a count counts from the start.
            var day = if (total == null) maxOf(from.date.plus(-1, DateTimeUnit.DAY), dtstart.date) else dtstart.date
            walk@ while (LocalDateTime(day, MIDNIGHT) < to) {
                if (day.dayOfWeek in days) {
                    for (j in 0 until count) {
                        // one in each of count equal parts; the single draw keeps Mnemo's key, so its times do not move
                        val lo = j * w.minutes / count
                        val hi = (j + 1) * w.minutes / count
                        val at = w.at(day, lo + SeededDraw.between(key(itemId, day, if (count == 1) "RANDOM_WINDOW" else "RANDOM_WINDOW#$j"), 0, hi - lo))
                        if (at < dtstart) continue
                        if (!ends.allow(at) || at >= to) break@walk
                        if (at >= from) add(at)
                    }
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
        is Recurrence.RandomDays -> window != null
        is Recurrence.Rolling, is Recurrence.Planned -> false
        is Recurrence.RandomWindow -> true
    }

private fun key(itemId: String, date: LocalDate, kind: String) = "$itemId|$date|$kind"

/** A random kind's end: [allow] counts every occurrence from the start, so call it on each one in order. */
private class Ends(private val until: LocalDateTime?, private val total: Int?) {
    private var seen = 0

    fun allow(at: LocalDateTime): Boolean {
        if (until != null && at > until) return false
        if (total != null && seen >= total) return false
        seen++
        return true
    }
}
