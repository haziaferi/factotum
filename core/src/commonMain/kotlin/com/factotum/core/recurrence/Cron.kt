package com.factotum.core.recurrence

import kotlinx.datetime.DayOfWeek

/**
 * Mnemo's raw cron, accepted as input and converted, never stored (ADR 04). Five numeric fields
 * (minute, hour, day of month, month, day of week) with lists, ranges and steps; 0 and 7 are
 * Sunday; no names and no `L W # ?`, as Mnemo's `ScheduleCalculator` reads them.
 *
 * When both day fields are restricted, a day matches either one: the crontab OR rule. That is two
 * rules, so it becomes a [Recurrence.RuleSet]; anything else is one [Recurrence.Rule]. The rules
 * expand from midnight of the start day, which [occurrences] never emits unless the rule matches it.
 */
object Cron {

    /** Null when [expression] is not five valid numeric fields. */
    fun toRecurrence(expression: String): Recurrence? {
        val fields = expression.trim().split(Regex("""\s+"""))
        if (fields.size != 5) return null
        val minutes = field(fields[0], 0, 59) ?: return null
        val hours = field(fields[1], 0, 23) ?: return null
        val monthDays = field(fields[2], 1, 31) ?: return null
        val months = field(fields[3], 1, 12) ?: return null
        val weekdays = field(fields[4], 0, 7)?.map { WEEKDAYS[it % 7] }?.distinct() ?: return null

        val base = RRule(Frequency.DAILY, byHour = hours, byMinute = minutes, byMonth = months.takeIf { fields[3] != "*" }.orEmpty())
        val byMonthDay = base.copy(byMonthDay = monthDays)
        val byWeekday = base.copy(byDay = weekdays.map { WeekdayNum(null, it) })
        return when {
            fields[2] != "*" && fields[4] != "*" -> Recurrence.RuleSet(listOf(byMonthDay, byWeekday))
            fields[2] != "*" -> Recurrence.Rule(byMonthDay)
            fields[4] != "*" -> Recurrence.Rule(byWeekday)
            else -> Recurrence.Rule(base)
        }
    }

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
}
