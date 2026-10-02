package com.factotum.data.item

import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.format
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalTime
import kotlinx.datetime.isoDayNumber

/**
 * ADR 04's columns on `item`, all in its schedule group: `recurrence_kind`, `rrule` (one rule, or
 * a rule set one rule per line), `rand_min_days` and `rand_max_days`, and `window_days` (Monday is
 * bit 0), `window_start` and `window_end`. Triggers tie each kind to its columns.
 */
internal fun recurrenceValues(r: Recurrence?): Map<String, Any?> {
    val none = mapOf<String, Any?>(
        "recurrence_kind" to null, "rrule" to null, "rand_min_days" to null, "rand_max_days" to null,
        "window_days" to null, "window_start" to null, "window_end" to null,
    )
    return none + when (r) {
        null -> emptyMap()
        is Recurrence.Rule -> mapOf("recurrence_kind" to "RRULE", "rrule" to r.rule.format())
        is Recurrence.RuleSet -> mapOf("recurrence_kind" to "RULE_SET", "rrule" to r.rules.joinToString("\n") { it.format() })
        is Recurrence.RandomDays -> mapOf("recurrence_kind" to "RANDOM_DAYS", "rand_min_days" to r.minDays.toLong(), "rand_max_days" to r.maxDays.toLong())
        is Recurrence.RandomWindow -> mapOf(
            "recurrence_kind" to "RANDOM_WINDOW",
            "window_days" to r.days.sumOf { 1L shl (it.isoDayNumber - 1) },
            "window_start" to r.start.toString(),
            "window_end" to r.end.toString(),
        )
    }
}

/** The recurrence these columns hold. Throws when they hold one this version cannot read. */
internal fun recurrenceOf(
    kind: String?,
    rrule: String?,
    randMinDays: Long?,
    randMaxDays: Long?,
    windowDays: Long?,
    windowStart: String?,
    windowEnd: String?,
): Recurrence? = when (kind) {
    null -> null
    "RRULE" -> Recurrence.Rule(parse(rrule))
    "RULE_SET" -> Recurrence.RuleSet(requireNotNull(rrule).lines().map(::parse))
    "RANDOM_DAYS" -> Recurrence.RandomDays(requireNotNull(randMinDays).toInt(), requireNotNull(randMaxDays).toInt())
    "RANDOM_WINDOW" -> Recurrence.RandomWindow(
        DayOfWeek.entries.filter { requireNotNull(windowDays) and (1L shl (it.isoDayNumber - 1)) != 0L }.toSet(),
        LocalTime.parse(requireNotNull(windowStart)),
        LocalTime.parse(requireNotNull(windowEnd)),
    )
    else -> throw IllegalArgumentException("unknown recurrence kind $kind")
}

internal fun ItemEntity.recurrence() = recurrenceOf(recurrenceKind, rrule, randMinDays, randMaxDays, windowDays, windowStart, windowEnd)

private fun parse(text: String?) = requireNotNull(RRule.parse(requireNotNull(text))) { "not a rule this version reads: $text" }
