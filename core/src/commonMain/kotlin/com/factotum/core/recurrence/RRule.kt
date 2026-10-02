package com.factotum.core.recurrence

import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.isoDayNumber
import kotlinx.datetime.number
import kotlinx.datetime.plus

/** The `FREQ` values the expander handles. */
enum class Frequency { MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY }

/** One `BYDAY` term: `MO` (no ordinal), `2TU` (the second Tuesday), `-1FR` (the last Friday). */
data class WeekdayNum(val ordinal: Int?, val day: DayOfWeek)

/**
 * A parsed RFC 5545 `RRULE` (ADR 04). Ported from Tendril's `RecurrenceSpec` (commit 163c9a7),
 * which handled whole days only, and extended to the times of day ADR 04 requires: `MINUTELY`,
 * `HOURLY`, `BYHOUR`, `BYMINUTE` and `BYSETPOS`, with `UNTIL` to the second.
 *
 * Times are local and floating: a rule rings at the same wall-clock time in any time zone (SPEC
 * §3.4). **Strict on purpose**, as Tendril's was: a rule with a part this does not implement parses
 * to null, because ignoring a limiter adds occurrences that do not exist, and a phantom occurrence
 * is believed where a missing one is noticed.
 */
data class RRule(
    val frequency: Frequency,
    val interval: Int = 1,
    val count: Int? = null,
    /** Inclusive. A date-only `UNTIL` covers that whole day. */
    val until: LocalDateTime? = null,
    val byDay: List<WeekdayNum> = emptyList(),
    val byMonthDay: List<Int> = emptyList(),
    val byMonth: List<Int> = emptyList(),
    val byHour: List<Int> = emptyList(),
    val byMinute: List<Int> = emptyList(),
    val bySetPos: List<Int> = emptyList(),
    val weekStart: DayOfWeek = DayOfWeek.MONDAY,
) {
    companion object {
        private val KNOWN = setOf("FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "BYHOUR", "BYMINUTE", "BYSETPOS", "WKST")

        private val WEEKDAYS = mapOf(
            "MO" to DayOfWeek.MONDAY, "TU" to DayOfWeek.TUESDAY, "WE" to DayOfWeek.WEDNESDAY, "TH" to DayOfWeek.THURSDAY,
            "FR" to DayOfWeek.FRIDAY, "SA" to DayOfWeek.SATURDAY, "SU" to DayOfWeek.SUNDAY,
        )

        private val BYDAY_TERM = Regex("""^([+-]?\d{1,2})?(MO|TU|WE|TH|FR|SA|SU)$""")
        /** An interval past this is a typo: a rule that repeats every 10,001 years has no use, and its arithmetic overflows. */
        private const val MAX_INTERVAL = 10_000

        /** The longest each month can be, February in a leap year. */
        private val LONGEST = listOf(31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

        private val UNTIL = Regex("""^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})Z?)?$""")

        /** Null when [text] is empty, malformed, or uses a part outside the supported subset. */
        fun parse(text: String): RRule? {
            val body = text.trim().removePrefix("RRULE:").trim()
            if (body.isEmpty()) return null
            val parts = mutableMapOf<String, String>()
            for (chunk in body.split(';')) {
                if (chunk.isBlank()) continue
                val eq = chunk.indexOf('=')
                if (eq <= 0) return null
                val name = chunk.substring(0, eq).trim().uppercase()
                // BYWEEKNO, BYYEARDAY, BYSECOND and anything unknown: unsupported, never ignored.
                if (name !in KNOWN || name in parts) return null
                parts[name] = chunk.substring(eq + 1).trim()
            }
            val frequency = Frequency.entries.firstOrNull { it.name == parts["FREQ"]?.uppercase() } ?: return null
            val interval = parts["INTERVAL"]?.let { it.toIntOrNull()?.takeIf { n -> n in 1..MAX_INTERVAL } ?: return null } ?: 1
            val count = parts["COUNT"]?.let { it.toIntOrNull()?.takeIf { n -> n >= 1 } ?: return null }
            val until = parts["UNTIL"]?.let { parseUntil(it) ?: return null }
            // RFC 5545 forbids both.
            if (count != null && until != null) return null

            val byDay = parts["BYDAY"]?.split(',')?.map { term ->
                val match = BYDAY_TERM.find(term.trim().uppercase()) ?: return null
                val ordinal = match.groupValues[1].takeIf { it.isNotEmpty() }?.removePrefix("+")?.toIntOrNull()
                if (match.groupValues[1].isNotEmpty() && (ordinal == null || ordinal == 0 || ordinal !in -5..5)) return null
                WeekdayNum(ordinal, WEEKDAYS.getValue(match.groupValues[2]))
            } ?: emptyList()
            val byMonthDay = numbers(parts["BYMONTHDAY"]) { it in 1..31 || it in -31..-1 } ?: return null
            val byMonth = numbers(parts["BYMONTH"]) { it in 1..12 } ?: return null
            val byHour = numbers(parts["BYHOUR"]) { it in 0..23 } ?: return null
            val byMinute = numbers(parts["BYMINUTE"]) { it in 0..59 } ?: return null
            val bySetPos = numbers(parts["BYSETPOS"]) { it != 0 && it in -366..366 } ?: return null
            val weekStart = parts["WKST"]?.let { WEEKDAYS[it.trim().uppercase()] ?: return null } ?: DayOfWeek.MONDAY

            // An ordinal BYDAY ("the first Friday") only expands within a month here: under
            // MONTHLY, or YEARLY with BYMONTH, and never beside BYMONTHDAY, where it would have to
            // limit instead (Tendril: BYMONTHDAY=13;BYDAY=1FR emitted every 13th).
            val ordinals = byDay.any { it.ordinal != null }
            if (ordinals && (byMonthDay.isNotEmpty() || frequency !in setOf(Frequency.MONTHLY, Frequency.YEARLY))) return null
            // YEARLY day selection without BYMONTH ranges over the whole year (every Monday, the
            // 13th of every month); the expander works month by month, so it refuses these.
            if (frequency == Frequency.YEARLY && byMonth.isEmpty() && (byDay.isNotEmpty() || byMonthDay.isNotEmpty())) return null
            // RFC 5545 forbids BYMONTHDAY under WEEKLY; reading it as nothing would add occurrences.
            if (frequency == Frequency.WEEKLY && byMonthDay.isNotEmpty()) return null
            // A day no listed month has (the 30th of February) would never occur, and a fine rule would walk forever looking.
            if (byMonth.isNotEmpty() && byMonthDay.isNotEmpty() && byMonth.none { m -> byMonthDay.any { kotlin.math.abs(it) <= LONGEST[m - 1] } }) return null

            return RRule(frequency, interval, count, until, byDay, byMonthDay, byMonth, byHour, byMinute, bySetPos, weekStart)
        }

        private fun numbers(raw: String?, valid: (Int) -> Boolean): List<Int>? =
            raw?.split(',')?.map { it.trim().toIntOrNull()?.takeIf(valid) ?: return null } ?: emptyList()

        /** `20261101` (the whole day) or `20261101T235900`, with or without `Z`: times are floating local (§3.4). */
        private fun parseUntil(raw: String): LocalDateTime? {
            val m = UNTIL.matchEntire(raw.trim()) ?: return null
            val (y, mo, d, h, mi, s) = m.destructured
            return runCatching {
                val date = LocalDate(y.toInt(), mo.toInt(), d.toInt())
                if (h.isEmpty()) LocalDateTime(date, LocalTime(23, 59, 59)) else LocalDateTime(date, LocalTime(h.toInt(), mi.toInt(), s.toInt()))
            }.getOrNull()
        }
    }
}

/** Whether the rule gives each occurrence its own time of day, rather than the start's. */
val RRule.setsTimes: Boolean
    get() = frequency <= Frequency.HOURLY || byHour.isNotEmpty() || byMinute.isNotEmpty()

/** The rule as RFC 5545 text, in a fixed part order, that [RRule.parse] reads back to this rule. */
fun RRule.format(): String = buildList {
    add("FREQ=${frequency.name}")
    if (interval != 1) add("INTERVAL=$interval")
    count?.let { add("COUNT=$it") }
    until?.let { u -> add("UNTIL=" + pad(u.year, 4) + pad(u.month.number) + pad(u.day) + "T" + pad(u.hour) + pad(u.minute) + pad(u.second)) }
    if (byMonth.isNotEmpty()) add("BYMONTH=${byMonth.joinToString(",")}")
    if (byMonthDay.isNotEmpty()) add("BYMONTHDAY=${byMonthDay.joinToString(",")}")
    if (byDay.isNotEmpty()) add("BYDAY=${byDay.joinToString(",") { (it.ordinal?.toString() ?: "") + it.day.name.take(2) }}")
    if (byHour.isNotEmpty()) add("BYHOUR=${byHour.joinToString(",")}")
    if (byMinute.isNotEmpty()) add("BYMINUTE=${byMinute.joinToString(",")}")
    if (bySetPos.isNotEmpty()) add("BYSETPOS=${bySetPos.joinToString(",")}")
    if (weekStart != DayOfWeek.MONDAY) add("WKST=${weekStart.name.take(2)}")
}.joinToString(";")

/**
 * The occurrences of this rule starting at [start] (DTSTART) that fall in `[from, to)`.
 *
 * Unlike RFC 5545, [start] is an occurrence only when it matches the rule: Factotum aligns it to
 * the rule (SPEC §3.4), and a converted cron rule starts at midnight, which must not ring.
 *
 * Without `COUNT` the walk starts at the period holding [from]; with it, at [start], because
 * `COUNT` counts the whole series.
 */
fun RRule.occurrences(start: LocalDateTime, from: LocalDateTime, to: LocalDateTime): List<LocalDateTime> {
    val out = mutableListOf<LocalDateTime>()
    if (to <= from) return out
    var emitted = 0
    var period = if (count == null) firstPeriodNear(start, from) else 0L
    // Stop on where a period begins, not on its candidates: a period may produce none.
    while (periodStart(start, period) < to) {
        val begin = periodStart(start, period)
        if (frequency <= Frequency.HOURLY && !dayAllowed(begin.date)) {
            // A minute or hour on a day the rule excludes yields nothing: jump to the next day.
            // Such a period counts nothing, so this is safe with COUNT too.
            period = maxOf(period + 1, firstPeriodNear(start, LocalDateTime(begin.date.plus(1, DateTimeUnit.DAY), MIDNIGHT)))
            continue
        }
        for (c in candidates(start, period)) {
            if (c < start) continue
            if (until != null && c > until) return out
            if (count != null && emitted >= count) return out
            if (c >= to) return out
            emitted++
            if (c >= from) out += c
        }
        period++
    }
    return out
}

/** The first moment of the [period]-th interval after [start]'s own: a loop bound, never an occurrence. */
private fun RRule.periodStart(start: LocalDateTime, period: Long): LocalDateTime {
    val step = period * interval
    return when (frequency) {
        Frequency.MINUTELY -> minuteAt(epochMinute(start) + step)
        Frequency.HOURLY -> minuteAt((epochMinute(start).floorDiv(60) + step) * 60)
        Frequency.DAILY -> LocalDateTime(start.date.plus(step, DateTimeUnit.DAY), MIDNIGHT)
        Frequency.WEEKLY -> LocalDateTime(weekOf(start.date).plus(step * 7, DateTimeUnit.DAY), MIDNIGHT)
        Frequency.MONTHLY -> LocalDateTime(firstOfMonth(start.date).plus(step, DateTimeUnit.MONTH), MIDNIGHT)
        // 1 January, not the start's month: BYMONTH can pick months before it (Tendril began the
        // year at the start's month, and so stopped before a final year's earlier months).
        Frequency.YEARLY -> LocalDateTime(LocalDate(start.date.year, 1, 1).plus(step, DateTimeUnit.YEAR), MIDNIGHT)
    }
}

/** The last period, counted in intervals, that begins on or before [from]; 0 when [from] is before [start]. */
private fun RRule.firstPeriodNear(start: LocalDateTime, from: LocalDateTime): Long {
    val units = when (frequency) {
        Frequency.MINUTELY -> epochMinute(from) - epochMinute(start)
        Frequency.HOURLY -> epochMinute(from).floorDiv(60) - epochMinute(start).floorDiv(60)
        Frequency.DAILY -> from.date.toEpochDays() - start.date.toEpochDays()
        Frequency.WEEKLY -> (weekOf(from.date).toEpochDays() - weekOf(start.date).toEpochDays()) / 7
        Frequency.MONTHLY -> monthIndex(from.date) - monthIndex(start.date)
        Frequency.YEARLY -> (from.date.year - start.date.year).toLong()
    }
    return if (units <= 0) 0 else units / interval
}

/** The [period]-th interval's candidates, ordered, with the limiting parts and BYSETPOS applied. */
private fun RRule.candidates(start: LocalDateTime, period: Long): List<LocalDateTime> {
    val begin = periodStart(start, period)
    val days: List<LocalDate> = when (frequency) {
        Frequency.MINUTELY, Frequency.HOURLY, Frequency.DAILY -> listOf(begin.date).filter(::dayAllowed)
        Frequency.WEEKLY -> byDay.map { it.day }.ifEmpty { listOf(start.dayOfWeek) }.map { day ->
            begin.date.plus((day.isoDayNumber - weekStart.isoDayNumber + 7) % 7, DateTimeUnit.DAY)
        }
        Frequency.MONTHLY -> datesInMonth(begin.date, start.date.day)
        Frequency.YEARLY -> byMonth.ifEmpty { listOf(start.date.month.number) }.sorted().flatMap { m ->
            datesInMonth(LocalDate(begin.date.year, m, 1), start.date.day)
        }
    }.filter { frequency == Frequency.YEARLY || byMonth.isEmpty() || it.month.number in byMonth }


    val times: List<LocalDateTime> = days.flatMap { day ->
        val hours = when (frequency) {
            Frequency.MINUTELY, Frequency.HOURLY -> listOf(begin.hour).filter { byHour.isEmpty() || it in byHour }
            else -> byHour.ifEmpty { listOf(start.hour) }
        }
        val minutes = when (frequency) {
            Frequency.MINUTELY -> listOf(begin.minute).filter { byMinute.isEmpty() || it in byMinute }
            else -> byMinute.ifEmpty { listOf(start.minute) }
        }
        hours.flatMap { h -> minutes.map { m -> LocalDateTime(day, LocalTime(h, m, start.second)) } }
    }.distinct().sorted()

    if (bySetPos.isEmpty()) return times
    return bySetPos.mapNotNull { p -> times.getOrNull(if (p > 0) p - 1 else times.size + p) }.distinct().sorted()
}

/**
 * MONTHLY and YEARLY day selection: BYMONTHDAY and an ordinal BYDAY expand, a plain BYDAY beside
 * BYMONTHDAY limits it, and with neither the start's own day is used. A day the month lacks (the
 * 31st of February) is skipped, never moved: BYSETPOS is how a rule says "or the last day".
 */
private fun RRule.datesInMonth(anyDayOfMonth: LocalDate, defaultDay: Int): List<LocalDate> {
    val first = firstOfMonth(anyDayOfMonth)
    val length = lengthOfMonth(first)
    val all = (1..length).map { LocalDate(first.year, first.month, it) }
    val fromMonthDay = byMonthDay.mapNotNull { d -> (if (d > 0) d else length + d + 1).takeIf { it in 1..length } }.map { all[it - 1] }
    val fromOrdinals = byDay.filter { it.ordinal != null }.mapNotNull { term ->
        val matching = all.filter { it.dayOfWeek == term.day }
        val ordinal = requireNotNull(term.ordinal)
        matching.getOrNull(if (ordinal > 0) ordinal - 1 else matching.size + ordinal)
    }
    val plainDays = byDay.filter { it.ordinal == null }.map { it.day }
    // On BYMONTHDAY, not on what it found: a 31st February is no day at all, not "fall back to BYDAY".
    return when {
        byMonthDay.isNotEmpty() && plainDays.isNotEmpty() -> fromMonthDay.filter { it.dayOfWeek in plainDays }
        byMonthDay.isNotEmpty() -> fromMonthDay
        fromOrdinals.isNotEmpty() || plainDays.isNotEmpty() -> fromOrdinals + all.filter { it.dayOfWeek in plainDays }
        // A selector that matched nothing this month means nothing this month, not the start's day.
        byMonthDay.isNotEmpty() || byDay.isNotEmpty() -> emptyList()
        else -> listOfNotNull(all.getOrNull(defaultDay - 1))
    }.distinct().sorted()
}

/** Whether a MINUTELY, HOURLY or DAILY rule's day limits (BYMONTH, BYDAY, BYMONTHDAY) let [date] through. */
private fun RRule.dayAllowed(date: LocalDate): Boolean =
    (byMonth.isEmpty() || date.month.number in byMonth) &&
        (byDay.isEmpty() || byDay.any { it.day == date.dayOfWeek }) &&
        (byMonthDay.isEmpty() || matchesMonthDay(date))

private fun RRule.matchesMonthDay(date: LocalDate): Boolean {
    val length = lengthOfMonth(date)
    return byMonthDay.any { d -> date.day == if (d > 0) d else length + d + 1 }
}

private fun RRule.weekOf(date: LocalDate): LocalDate =
    date.plus(-((date.dayOfWeek.isoDayNumber - weekStart.isoDayNumber + 7) % 7), DateTimeUnit.DAY)

internal val MIDNIGHT = LocalTime(0, 0)

private fun pad(n: Int, width: Int = 2) = n.toString().padStart(width, '0')

private fun firstOfMonth(date: LocalDate) = LocalDate(date.year, date.month, 1)

private fun lengthOfMonth(date: LocalDate): Int = firstOfMonth(date).plus(1, DateTimeUnit.MONTH).plus(-1, DateTimeUnit.DAY).day

private fun monthIndex(date: LocalDate): Long = date.year * 12L + date.month.number

private fun epochMinute(t: LocalDateTime): Long = t.date.toEpochDays() * MINUTES_PER_DAY + t.hour * 60 + t.minute

private fun minuteAt(epochMinute: Long): LocalDateTime {
    val minute = epochMinute.mod(MINUTES_PER_DAY).toInt()
    return LocalDateTime(LocalDate.fromEpochDays(epochMinute.floorDiv(MINUTES_PER_DAY)), LocalTime(minute / 60, minute % 60))
}

private const val MINUTES_PER_DAY = 24 * 60L
