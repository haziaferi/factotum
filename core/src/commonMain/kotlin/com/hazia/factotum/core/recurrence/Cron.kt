package com.hazia.factotum.core.recurrence

import kotlinx.datetime.DayOfWeek

/**
 * Raw cron, accepted as input and converted, never stored (ADR 04). Mnemo's five fields (minute,
 * hour, day of month, month, day of week) with lists, ranges and steps, 0 and 7 being Sunday, and
 * the owner's extensions (decision 17, 2026-10-08):
 *
 * - **names**: `JAN`–`DEC` in the month field and `SUN`–`SAT` in the weekday field, any case, in
 *   lists and ranges (`MON-FRI`);
 * - **`L`** in the day of month: the last day (`BYMONTHDAY=-1`); `FRIL` or `5L` in the weekday
 *   field: the month's last Friday (`BYDAY=-1FR`);
 * - **`#`** in the weekday field: `TUE#2` or `2#2`, the month's second Tuesday (`BYDAY=2TU`), 1 to 5;
 * - **several lines**: one rule, the union of every line's (a [Recurrence.RuleSet]), for what one
 *   line cannot say, such as every 90 minutes.
 *
 * Still refused: `W`, `?`, seconds and years, and a line or day that could never occur.
 *
 * When both day fields are restricted, a day matches either one: the crontab OR rule, so a union.
 * A weekday field mixing plain days with an ordinal (`MON,FRI#2`) is a union too. The rules expand
 * from midnight of the start day, which [occurrences] never emits unless the rule matches it.
 */
object Cron {

    /** Null when [expression] (one line, or several separated by line breaks) has a line that is not valid cron. */
    fun toRecurrence(expression: String): Recurrence? {
        val lines = expression.lines().map { it.trim() }.filter { it.isNotEmpty() }
        if (lines.isEmpty()) return null
        val rules = lines.flatMap { line(it) ?: return null }.distinct()
        return if (rules.size == 1) Recurrence.Rule(rules.single()) else Recurrence.RuleSet(rules)
    }

    private fun line(expression: String): List<RRule>? {
        val fields = expression.split(Regex("""\s+"""))
        if (fields.size != 5) return null
        val minutes = field(fields[0], 0, 59) ?: return null
        val hours = field(fields[1], 0, 23) ?: return null
        val monthDays = monthDays(fields[2]) ?: return null
        val months = field(names(fields[3], MONTHS), 1, 12) ?: return null
        val (plain, ordinals) = weekdays(fields[4]) ?: return null

        val byMonth = months.takeIf { fields[3] != "*" }.orEmpty()
        // A day no listed month has (31 FEB) would never occur, and the expander would walk forever looking.
        if (byMonth.isNotEmpty() && fields[2] != "*" && monthDays.none { d -> d == -1 || byMonth.any { m -> d <= LONGEST[m - 1] } }) return null

        val base = RRule(Frequency.DAILY, byHour = hours, byMinute = minutes, byMonth = byMonth)
        val byMonthDay = base.copy(byMonthDay = monthDays)
        val byWeekday = buildList {
            if (plain.isNotEmpty()) add(base.copy(byDay = plain.map { WeekdayNum(null, it) }))
            // An ordinal weekday only expands within a month (RRule's rule), so this one is MONTHLY.
            if (ordinals.isNotEmpty()) add(RRule(Frequency.MONTHLY, byDay = ordinals, byHour = hours, byMinute = minutes, byMonth = byMonth))
        }
        return when {
            fields[2] != "*" && fields[4] != "*" -> listOf(byMonthDay) + byWeekday
            fields[2] != "*" -> listOf(byMonthDay)
            fields[4] != "*" -> byWeekday
            else -> listOf(base)
        }
    }

    /** The day-of-month field: numbers, ranges and steps as [field], and `L` for the last day (-1). */
    private fun monthDays(spec: String): List<Int>? {
        val terms = spec.split(',')
        val last = terms.count { it.equals("L", ignoreCase = true) }
        val rest = terms.filterNot { it.equals("L", ignoreCase = true) }
        if (last > 1) return null
        val numbers = if (rest.isEmpty()) emptyList() else field(rest.joinToString(","), 1, 31) ?: return null
        return (numbers + List(last) { -1 })
    }

    /** The weekday field: plain days (names, numbers, ranges, steps) and ordinal ones (`TUE#2`, `FRIL`), apart. */
    private fun weekdays(spec: String): Pair<List<DayOfWeek>, List<WeekdayNum>>? {
        val plain = mutableListOf<String>()
        val ordinals = mutableListOf<WeekdayNum>()
        for (term in spec.split(',')) {
            val t = names(term, WEEKDAY_NAMES)
            when {
                '#' in t -> {
                    val (day, n) = t.split('#').let { if (it.size != 2) return null else it[0] to it[1] }
                    val ordinal = n.toIntOrNull()?.takeIf { it in 1..5 } ?: return null
                    ordinals += WeekdayNum(ordinal, WEEKDAYS[day.toIntOrNull()?.takeIf { it in 0..7 }?.rem(7) ?: return null])
                }
                t.length > 1 && t.endsWith('L', ignoreCase = true) -> {
                    val day = t.dropLast(1).toIntOrNull()?.takeIf { it in 0..7 } ?: return null
                    ordinals += WeekdayNum(-1, WEEKDAYS[day % 7])
                }
                else -> plain += t
            }
        }
        val days = if (plain.isEmpty()) emptyList() else field(plain.joinToString(","), 0, 7)?.map { WEEKDAYS[it % 7] }?.distinct() ?: return null
        return days to ordinals.distinct()
    }

    /** [spec] with its names replaced by their numbers (`MON-FRI` is `1-5`); a name in the wrong field stays and fails. */
    private fun names(spec: String, table: Map<String, Int>): String =
        Regex("[A-Za-z]{3}").replace(spec) { m -> table[m.value.uppercase()]?.toString() ?: m.value }

    /** One field's values: a star, `n` or `a-b`, each optionally stepped (`a/s` runs from a to the top), in lists. */
    private fun field(spec: String, lo: Int, hi: Int): List<Int>? {
        val values = mutableSetOf<Int>()
        for (part in spec.split(',')) {
            val (range, step) = part.split('/').let { if (it.size > 2) return null else it[0] to it.getOrNull(1) }
            val by = step?.let { it.toIntOrNull()?.takeIf { s -> s >= 1 } ?: return null } ?: 1
            val (a, b) = when {
                range == "*" -> lo to hi
                '-' in range -> range.split('-').let { r -> if (r.size != 2) return null else (r[0].toIntOrNull() ?: return null) to (r[1].toIntOrNull() ?: return null) }
                else -> (range.toIntOrNull() ?: return null).let { it to if (step == null) it else hi }
            }
            if (a < lo || b > hi || a > b) return null
            values += (a..b step by)
        }
        return values.sorted()
    }

    private val WEEKDAYS = listOf(
        DayOfWeek.SUNDAY, DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY,
    )
    private val WEEKDAY_NAMES = listOf("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT").withIndex().associate { (i, n) -> n to i }
    private val MONTHS = listOf("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC").withIndex().associate { (i, n) -> n to i + 1 }

    /** The longest each month can be, February in a leap year. */
    private val LONGEST = listOf(31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
}
