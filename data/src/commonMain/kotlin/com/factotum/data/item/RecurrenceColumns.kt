package com.factotum.data.item

import androidx.room.ColumnInfo
import com.factotum.core.recurrence.RRule
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.RollUnit
import com.factotum.core.recurrence.format
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalTime
import kotlinx.datetime.isoDayNumber

/**
 * ADR 04's columns on `item`, all in its schedule group: `recurrence_kind`, `rrule` (one rule, or
 * a rule set one rule per line), `rand_min_days` and `rand_max_days`, `window_days` (Monday is
 * bit 0), `window_start` and `window_end`, `roll_every` and `roll_unit` (ROLLING), and `plan_n`,
 * `plan_per`, `plan_days` (a mask, as `window_days`) and `plan_blocks` (block ids, comma-separated;
 * PLANNED). Triggers tie each kind to its columns. Embedded wherever a row's recurrence is read.
 */
internal data class RecurrenceColumns(
    @ColumnInfo(name = "recurrence_kind") val kind: String? = null,
    val rrule: String? = null,
    @ColumnInfo(name = "rand_min_days") val randMinDays: Long? = null,
    @ColumnInfo(name = "rand_max_days") val randMaxDays: Long? = null,
    @ColumnInfo(name = "window_days") val windowDays: Long? = null,
    @ColumnInfo(name = "window_start") val windowStart: String? = null,
    @ColumnInfo(name = "window_end") val windowEnd: String? = null,
    @ColumnInfo(name = "roll_every") val rollEvery: Long? = null,
    @ColumnInfo(name = "roll_unit") val rollUnit: String? = null,
    @ColumnInfo(name = "plan_n") val planN: Long? = null,
    @ColumnInfo(name = "plan_per") val planPer: String? = null,
    @ColumnInfo(name = "plan_days") val planDays: Long? = null,
    @ColumnInfo(name = "plan_blocks") val planBlocks: String? = null,
) {
    /** The columns by name, as a row's schedule group holds them. */
    val values: Map<String, Any?>
        get() = mapOf(
            "recurrence_kind" to kind, "rrule" to rrule, "rand_min_days" to randMinDays, "rand_max_days" to randMaxDays,
            "window_days" to windowDays, "window_start" to windowStart, "window_end" to windowEnd, "roll_every" to rollEvery,
            "roll_unit" to rollUnit, "plan_n" to planN, "plan_per" to planPer, "plan_days" to planDays, "plan_blocks" to planBlocks,
        )

    /** The recurrence these columns hold. Throws when they hold one this version cannot read. */
    fun recurrence(): Recurrence? = when (kind) {
        null -> null
        "RRULE" -> Recurrence.Rule(parse(rrule))
        "RULE_SET" -> Recurrence.RuleSet(requireNotNull(rrule).lines().map(::parse))
        "RANDOM_DAYS" -> Recurrence.RandomDays(requireNotNull(randMinDays).toInt(), requireNotNull(randMaxDays).toInt())
        "RANDOM_WINDOW" -> Recurrence.RandomWindow(daysOf(requireNotNull(windowDays)), LocalTime.parse(requireNotNull(windowStart)), LocalTime.parse(requireNotNull(windowEnd)))
        "ROLLING" -> Recurrence.Rolling(requireNotNull(rollEvery).toInt(), RollUnit.valueOf(requireNotNull(rollUnit)))
        "PLANNED" -> Recurrence.Planned(
            requireNotNull(planN).toInt(),
            Recurrence.Planned.Per.valueOf(requireNotNull(planPer)),
            daysOf(requireNotNull(planDays)),
            planBlocks?.split(',').orEmpty(),
        )
        else -> throw IllegalArgumentException("unknown recurrence kind $kind")
    }

    companion object {
        fun of(r: Recurrence?): RecurrenceColumns = when (r) {
            null -> RecurrenceColumns()
            is Recurrence.Rule -> RecurrenceColumns("RRULE", rrule = r.rule.format())
            is Recurrence.RuleSet -> RecurrenceColumns("RULE_SET", rrule = r.rules.joinToString("\n") { it.format() })
            is Recurrence.RandomDays -> RecurrenceColumns("RANDOM_DAYS", randMinDays = r.minDays.toLong(), randMaxDays = r.maxDays.toLong())
            is Recurrence.RandomWindow -> RecurrenceColumns("RANDOM_WINDOW", windowDays = maskOf(r.days), windowStart = r.start.toString(), windowEnd = r.end.toString())
            is Recurrence.Rolling -> RecurrenceColumns("ROLLING", rollEvery = r.every.toLong(), rollUnit = r.unit.name)
            is Recurrence.Planned -> RecurrenceColumns(
                "PLANNED", planN = r.n.toLong(), planPer = r.per.name, planDays = maskOf(r.days),
                planBlocks = r.blocks.takeIf { it.isNotEmpty() }?.joinToString(","),
            )
        }

        /** The columns from their values by name: text through [text], whole numbers through [number]. */
        fun read(text: (String) -> String?, number: (String) -> Long?) = RecurrenceColumns(
            text("recurrence_kind"), text("rrule"), number("rand_min_days"), number("rand_max_days"), number("window_days"),
            text("window_start"), text("window_end"), number("roll_every"), text("roll_unit"), number("plan_n"), text("plan_per"),
            number("plan_days"), text("plan_blocks"),
        )
    }
}

/** A recurrence as the schedule group's values; none clears every recurrence column. */
internal fun recurrenceValues(r: Recurrence?): Map<String, Any?> = RecurrenceColumns.of(r).values

internal fun ItemEntity.recurrence() = repeat.recurrence()

internal fun daysOf(mask: Long): Set<DayOfWeek> = DayOfWeek.entries.filter { mask and (1L shl (it.isoDayNumber - 1)) != 0L }.toSet()

internal fun maskOf(days: Set<DayOfWeek>): Long = days.sumOf { 1L shl (it.isoDayNumber - 1) }

private fun parse(text: String?) = requireNotNull(RRule.parse(requireNotNull(text))) { "not a rule this version reads: $text" }
