package com.factotum.core.plan

import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.ownTime
import com.factotum.core.recurrence.setsTimes
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.isoDayNumber
import kotlinx.datetime.plus

/*
 * Tendril's habit planner (`CalendarSchedule.kt`) for ADR 04's PLANNED kind and ADR 06's time
 * blocks. It receives each habit's week already expanded and edited (`occurrencesWithEdits`), and
 * places it in the day's blocks, suggesting days for "n a week" habits not yet confirmed.
 */

/** A time block's own start and end, in minutes from midnight, on some weekdays. */
data class BlockOverride(val days: Set<DayOfWeek>, val start: Int, val end: Int)

/**
 * A time block of the day, in minutes from midnight; [end] is not part of it (09:00 belongs to the
 * block starting at 09:00). [position] orders the blocks and the spread of a several-a-day habit.
 */
data class TimeBlock(val id: String, val start: Int, val end: Int, val position: Int, val overrides: List<BlockOverride> = emptyList()) {
    /** The block's times on [day]: a later override wins over an earlier one, as in Tendril. */
    fun on(day: DayOfWeek): TimeBlock = overrides.lastOrNull { day in it.days }?.let { copy(start = it.start, end = it.end) } ?: this
}

/** Tendril's text for a block's weekday times, `SAT,SUN@480-630;MON@420-540`, so its rows import as they are. */
object Overrides {
    private val codes = listOf("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
    private val part = Regex("([A-Z,]+)@(\\d{1,4})-(\\d{1,4})")

    fun format(overrides: List<BlockOverride>): String? =
        overrides.takeIf { it.isNotEmpty() }?.joinToString(";") { o -> o.days.sorted().joinToString(",") { codes[it.isoDayNumber - 1] } + "@${o.start}-${o.end}" }

    /** Throws on text this version cannot read, as every row reader here does. */
    fun parse(text: String?): List<BlockOverride> = text.orEmpty().split(';').filter { it.isNotEmpty() }.map { p ->
        val (days, start, end) = requireNotNull(part.matchEntire(p)) { "not a block override: $p" }.destructured
        val set = days.split(',').map { code -> DayOfWeek.entries[codes.indexOf(code).also { require(it >= 0) { "not a day: $code" } }] }.toSet()
        BlockOverride(set, start.toInt(), end.toInt()).also { require(it.start in 0 until it.end && it.end <= 1440) { "not a block's times: $p" } }
    }
}

/**
 * A habit as the planner reads it: [occurrences] are this week's, edits applied and paused days
 * gone; [rules], the rule each day of the week follows (its own, or one a FROM edit set). An
 * occurrence keeps its time when the habit has a [setTime], its day's rule sets times, or an edit
 * gave it one; the others sit in a block. [pool] and [confirmed] matter to "n a week" alone: the
 * days it may fall on this week, and whether the person has confirmed this week's days.
 */
data class PlanHabit(
    val itemId: String,
    val rules: Map<LocalDate, Recurrence?>,
    val blockId: String?,
    val durationMin: Int,
    val setTime: Boolean,
    val occurrences: List<Occurrence>,
    val pool: List<LocalDate> = emptyList(),
    val confirmed: Boolean = false,
)

/** One occurrence as placed: at [minute] when timed, else in [blockId]. */
data class Placed(val itemId: String, val occurrence: Occurrence, val minute: Int?, val blockId: String?, val durationMin: Int)

data class PlacedBlock(val block: TimeBlock, val timed: List<Placed>, val flexible: List<Placed>)

data class PlanDay(
    val date: LocalDate,
    val blocks: List<PlacedBlock>,
    /** Occurrences with a set time outside every block: kept and shown, not dropped. */
    val outside: List<Placed>,
    /** Occurrences with no time and no block, or a block that is gone. */
    val anyTime: List<Placed>,
    /** Pairs of blocks that overlap this day, earlier first. */
    val overlaps: List<Pair<String, String>>,
)

/** The days suggested for an "n a week" habit whose week is not confirmed; nothing is placed until it is. */
data class WeekSuggestion(val itemId: String, val days: List<LocalDate>)

data class PlanWeek(val monday: LocalDate, val days: List<PlanDay>, val suggestions: List<WeekSuggestion>)

fun mondayOf(d: LocalDate): LocalDate = d.plus(1 - d.dayOfWeek.isoDayNumber, DateTimeUnit.DAY)

/** Tendril's `spread`: [n] places evenly over [k], by index. */
fun spread(k: Int, n: Int): List<Int> = (0 until n).map { i -> minOf(k - 1, ((i + 0.5) * k / n).toInt()) }

/**
 * The plan of the week from [monday]: every habit's occurrences placed in the day's [blocks], the
 * overlapping blocks, and the suggestions for unconfirmed "n a week" habits. A suggestion is the
 * evenly spaced pick of the pool, rotated to the offset that keeps the busiest day lightest, then
 * the spread of load lowest, then the first offset (Tendril). Habits are suggested in id order,
 * each on the load the earlier ones left.
 */
fun planWeek(monday: LocalDate, blocks: List<TimeBlock>, habits: List<PlanHabit>): PlanWeek {
    val days = (0 until 7).map { monday.plus(it, DateTimeUnit.DAY) }
    val order = blockOrder(blocks)
    val placed = habits.associate { h -> h.itemId to h.occurrences.map { o -> placed(h, o, order) } }

    // The days a habit follows an "n a week" rule are its weekly part; the rest is fixed load.
    fun weeklyOn(h: PlanHabit, d: LocalDate) = (h.rules[d] as? Recurrence.Planned)?.per == Recurrence.Planned.Per.WEEK
    val load = days.associateWith { 0L }.toMutableMap()
    fun addLoad(h: PlanHabit, weekly: Boolean) = placed.getValue(h.itemId).forEach { p ->
        val d = p.occurrence.at.date
        load[d]?.let { if (weeklyOn(h, p.occurrence.original?.date ?: d) == weekly) load[d] = it + p.durationMin }
    }
    habits.forEach { addLoad(it, weekly = false) }
    val suggestions = mutableListOf<WeekSuggestion>()
    for (h in habits.filter { h -> days.any { weeklyOn(h, it) } }.sortedBy { it.itemId }) {
        val pool = h.pool.sorted()
        val n = minOf((pool.firstOrNull()?.let(h.rules::get) as? Recurrence.Planned)?.n ?: 0, pool.size)
        if (h.confirmed || n == 0) {
            if (h.confirmed) addLoad(h, weekly = true)
            continue
        }
        val base = spread(pool.size, n)
        val pick = pool.indices.map { off -> base.map { pool[(it + off) % pool.size] }.distinct().sorted() }.minWith(
            compareBy<List<LocalDate>>({ p -> days.maxOf { load.getValue(it) + if (it in p) h.durationMin else 0 } }, { p ->
                days.sumOf { (load.getValue(it) + if (it in p) h.durationMin else 0).let { l -> l * l } }
            }),
        )
        pick.forEach { load[it] = load.getValue(it) + h.durationMin }
        suggestions += WeekSuggestion(h.itemId, pick)
    }

    val byDay = placed.values.flatten().groupBy { it.occurrence.at.date }
    return PlanWeek(monday, days.map { d -> placeDay(d, blocks.map { it.on(d.dayOfWeek) }, byDay[d].orEmpty()) }, suggestions)
}

/** The order blocks are listed in and an "n a day" habit is spread over: by position, then id. */
fun blockOrder(blocks: List<TimeBlock>): List<String> = blocks.sortedWith(compareBy({ it.position }, { it.id })).map { it.id }

/**
 * The block an untimed [o] sits in: the one an edit gave it, even none ("any time"); else, under
 * an "n a day" [rule] (its day's), its slot's block by its place in the day, those the rule names
 * or the blocks in [order] spread evenly; else [habitBlock]. With no block left, an "n a day"
 * habit's occurrences are at any time, where Tendril placed none.
 */
fun blockOf(o: Occurrence, rule: Recurrence?, habitBlock: String?, order: List<String>): String? {
    o.block?.let { return it.value }
    val r = (rule as? Recurrence.Planned)?.takeIf { it.per == Recurrence.Planned.Per.DAY }
    val slots = r?.blocks?.ifEmpty { if (order.isEmpty()) emptyList() else spread(order.size, r.n).map(order::get) }
    return o.original?.let { slots?.getOrNull(it.time.second) } ?: habitBlock
}

/** Where [o] goes: at its time when timed, else in its block ([blockOf]). */
private fun placed(h: PlanHabit, o: Occurrence, order: List<String>): Placed {
    val rule = h.rules[o.original?.date ?: o.at.date]
    val minute = if (h.setTime || rule?.setsTimes == true || o.ownTime) o.at.time.hour * 60 + o.at.time.minute else null
    return Placed(h.itemId, o, minute, blockOf(o, rule, h.blockId, order), (o.durationMin ?: h.durationMin.toLong()).toInt())
}

private fun placeDay(d: LocalDate, blocks: List<TimeBlock>, entries: List<Placed>): PlanDay {
    val timed = blocks.associate { it.id to mutableListOf<Placed>() }
    val flexible = blocks.associate { it.id to mutableListOf<Placed>() }
    val outside = mutableListOf<Placed>()
    val anyTime = mutableListOf<Placed>()
    for (p in entries) {
        val t = p.minute
        if (t != null) {
            val home = blocks.firstOrNull { t >= it.start && t < it.end }
            if (home == null) outside += p else timed.getValue(home.id) += p
        } else {
            flexible[p.blockId]?.add(p) ?: anyTime.add(p)
        }
    }
    // A habit's own occurrences in their order; an added one after them.
    val byOrder = compareBy<Placed>({ it.itemId }, { it.occurrence.original == null }, { it.occurrence.original }, { it.occurrence.at })
    val byTime = compareBy<Placed> { it.minute }.then(byOrder)
    val ordered = blocks.sortedBy { it.start }
    return PlanDay(
        date = d,
        blocks = blocks.map { b -> PlacedBlock(b, timed.getValue(b.id).sortedWith(byTime), flexible.getValue(b.id).sortedWith(byOrder)) },
        outside = outside.sortedWith(byTime),
        anyTime = anyTime.sortedWith(byOrder),
        overlaps = ordered.zipWithNext().filter { (a, b) -> b.start < a.end }.map { (a, b) -> a.id to b.id },
    )
}
