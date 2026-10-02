package com.factotum.core.recurrence

import com.factotum.core.sync.Stamp
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.isoDayNumber
import kotlinx.datetime.plus

/** What an occurrence edit covers (ADR 11). */
enum class EditScope {
    /** One occurrence, named by the date-time the series gave it. */
    OCCURRENCE,

    /** Every occurrence now on one date. */
    DAY,

    /** Every occurrence now in one week, from its Monday, optionally only some weekdays; with `week_days`, that week's days. */
    WEEK,

    /** Every occurrence now on or after a date, optionally only some weekdays; with `week_days` or a rule, a new pattern from then. */
    FROM,

    /** An added occurrence. */
    EXTRA,
}

/**
 * The fields one edit sets, and only those (ADR 11). [movedTo] (OCCURRENCE only) keeps the
 * occurrence's time unless [time] sets one. [rule] (FROM only) repeats the item differently from
 * the edit's date, and [weekDays] on a FROM edit is the weekly pattern from then; on a WEEK edit it
 * is that week's days. [others] holds the habit fields (block, sort_order, rule_patch, pause) as raw
 * JSON until habits apply them (ADR 06), so nothing a peer wrote is lost.
 */
data class EditChanges(
    val skip: Boolean = false,
    val movedTo: LocalDate? = null,
    val time: LocalTime? = null,
    val durationMin: Long? = null,
    val title: String? = null,
    val rule: Recurrence? = null,
    val weekDays: Set<DayOfWeek>? = null,
    val others: Map<String, String> = emptyMap(),
) {
    /** The fields that decide when an occurrence happens (ADR 11), with their values: what a clash is about. */
    val schedule: Map<String, Any>
        get() = buildMap {
            movedTo?.let { put("moved_to", it) }
            time?.let { put("time", it) }
            durationMin?.let { put("duration", it) }
            rule?.let { put("rule", it) }
            weekDays?.let { put("week_days", it) }
        }
}

/** Where an edit applies: its scope and what the scope names. Two edits clash only on the same place. */
data class EditPlace(val scope: EditScope, val at: LocalDateTime?, val date: LocalDate?, val days: Set<DayOfWeek>)

/**
 * One row of the insert-once occurrence-edit log. [created] is its ADR 01 stamp, which orders the
 * edits. [seen] are the ids of the edits on the same place its author had seen, which tells a clash
 * from a correction exactly. [at] is the occurrence (OCCURRENCE) or the added time (EXTRA); [date] is
 * the day (DAY), the week's Monday (WEEK) or the first day (FROM); [days] narrow WEEK and FROM.
 */
data class OccurrenceEdit(
    val id: String,
    val scope: EditScope,
    val at: LocalDateTime? = null,
    val date: LocalDate? = null,
    val days: Set<DayOfWeek> = emptySet(),
    val changes: EditChanges,
    val created: Stamp,
    val seen: Set<String> = emptySet(),
) {
    init {
        when (scope) {
            EditScope.OCCURRENCE, EditScope.EXTRA -> require(at != null && date == null) { "$scope edits name a date-time" }
            EditScope.DAY, EditScope.WEEK, EditScope.FROM -> require(date != null && at == null) { "$scope edits name a date" }
        }
        require(scope == EditScope.WEEK || scope == EditScope.FROM || days.isEmpty()) { "only WEEK and FROM edits narrow to days" }
        require(scope == EditScope.WEEK || scope == EditScope.FROM || changes.weekDays == null) { "only WEEK and FROM edits set week_days" }
        require(scope == EditScope.OCCURRENCE || changes.movedTo == null) { "only one occurrence is moved: a moved day or week is a new pattern" }
        require(scope == EditScope.FROM || changes.rule == null) { "only a FROM edit sets a rule" }
        require(changes.rule == null || (changes.weekDays == null && days.isEmpty())) { "a new rule is the whole pattern" }
        require(scope != EditScope.WEEK || date?.dayOfWeek == DayOfWeek.MONDAY) { "a WEEK edit names its Monday" }
    }

    val place: EditPlace get() = EditPlace(scope, at, date, days)

    /** Whether this DAY, WEEK or FROM edit reaches an occurrence now at [now]. */
    fun reaches(now: LocalDateTime): Boolean {
        val d = now.date
        val onDays = days.isEmpty() || now.dayOfWeek in days
        return when (scope) {
            EditScope.DAY -> d == date
            EditScope.WEEK -> date != null && d >= date && d < date.plus(7, DateTimeUnit.DAY) && onDays
            EditScope.FROM -> date != null && d >= date && onDays
            EditScope.OCCURRENCE, EditScope.EXTRA -> false
        }
    }
}

/** One occurrence as shown: [original] is where the series put it (null for an added one). */
data class Occurrence(val original: LocalDateTime?, val at: LocalDateTime, val title: String, val durationMin: Long?)

/**
 * The occurrences of a series in `[from, to)` with its live [edits] applied in stamp order, field by
 * field (ADR 11). DAY, WEEK and FROM edits reach occurrences where they are at that point, added
 * ones too, as `tools/occurrence_sim.py` applies them. Each occurrence shows the series' current
 * [title] and [durationMin] except where an edit sets them, so renaming a series renames its moved
 * occurrences. A moved occurrence is one occurrence, so two concurrent moves still leave one.
 */
fun Recurrence?.occurrencesWithEdits(
    itemId: String,
    dtstart: LocalDateTime,
    title: String,
    durationMin: Long?,
    edits: List<OccurrenceEdit>,
    from: LocalDateTime,
    to: LocalDateTime,
    lastDone: LocalDate? = null,
): List<Occurrence> {
    val ordered = edits.sortedBy { it.created }
    // A FROM edit with a rule or week_days repeats the item differently from its date. Each day
    // follows the latest-created pattern dated on or before it; a new pattern starts afresh there.
    val patterns = ordered.mapNotNull { e ->
        val weekly = e.changes.weekDays?.takeIf { e.scope == EditScope.FROM }
            ?.let { days -> Recurrence.Rule(RRule(Frequency.WEEKLY, byDay = days.sorted().map { WeekdayNum(null, it) })) }
        (e.changes.rule ?: weekly)?.let { e.date to it }
    }
    fun series(a: LocalDateTime, b: LocalDateTime): List<LocalDateTime> {
        val segments = listOf<Pair<LocalDate?, Recurrence?>>(null to this) + patterns
        return segments.flatMapIndexed { i, (start, rule) ->
            val begin = start?.let { LocalDateTime(it, dtstart.time) } ?: dtstart
            val end = segments.drop(i + 1).mapNotNull { it.first }.minOrNull()?.let { LocalDateTime(it, MIDNIGHT) }
            val lo = maxOf(a, begin)
            val hi = minOf(b, end ?: b)
            if (lo >= hi) emptyList()
            else rule?.occurrences(itemId, begin, lo, hi, lastDone) ?: listOf(begin).filter { it >= lo && it < hi }
        }.distinct().sorted()
    }

    // An occurrence moved or retimed into the window from outside it must be found too.
    val named = ordered.filter { it.scope == EditScope.OCCURRENCE && (it.changes.movedTo != null || it.changes.time != null) }
        .mapNotNull { it.at }.filter { it < from || it >= to }
        .filter { at -> series(at, LocalDateTime(at.date.plus(1, DateTimeUnit.DAY), at.time)).firstOrNull() == at }
    // Keyed by the series' date-time; an added occurrence is keyed by its edit, so it never replaces one.
    val shown: MutableMap<Any, Occurrence?> = (series(from, to) + named).distinct()
        .associateWith<LocalDateTime, Occurrence?> { Occurrence(it, it, title, durationMin) }.toMutableMap()

    fun change(o: Occurrence, c: EditChanges): Occurrence? = if (c.skip) null else o.copy(
        at = LocalDateTime(c.movedTo ?: o.at.date, c.time ?: o.at.time),
        title = c.title ?: o.title,
        durationMin = c.durationMin ?: o.durationMin,
    )

    for (edit in ordered) {
        val c = edit.changes
        val at = edit.at
        val monday = edit.date
        when {
            edit.scope == EditScope.OCCURRENCE && at != null -> shown[at]?.let { shown[at] = change(it, c) }
            edit.scope == EditScope.EXTRA && at != null -> shown[edit.id] = if (c.skip) null else Occurrence(null, at, c.title ?: title, c.durationMin ?: durationMin)
            edit.scope == EditScope.WEEK && monday != null && c.weekDays != null -> {
                // A confirmed week: exactly these days that week, at the series' time, whatever was there.
                shown.entries.filter { (_, o) -> o != null && edit.reaches(o.at) }.forEach { shown.remove(it.key) }
                for (day in c.weekDays) {
                    val confirmed = LocalDateTime(monday.plus(day.isoDayNumber - 1, DateTimeUnit.DAY), dtstart.time)
                    shown[confirmed] = Occurrence(confirmed, confirmed, title, durationMin)
                }
            }
            // A new pattern from a date was laid out by series(); its other fields apply like any FROM edit.
            else -> for ((key, o) in shown.entries.toList()) {
                if (o != null && edit.reaches(o.at)) shown[key] = change(o, c)
            }
        }
    }
    return shown.values.filterNotNull().filter { it.at >= from && it.at < to }.sortedWith(compareBy({ it.at }, { it.title }))
}

/**
 * Pairs of live edits that clash (ADR 11): OCCURRENCE or FROM edits on the same place, made on
 * different devices, neither having seen the other, that set a same schedule field to different
 * values, and not yet settled by a later edit that has seen both. A person is asked; until then
 * the later stamp applies.
 */
fun clashes(edits: List<OccurrenceEdit>): List<Pair<OccurrenceEdit, OccurrenceEdit>> =
    edits.filter { it.scope == EditScope.OCCURRENCE || it.scope == EditScope.FROM }.groupBy { it.place }.values.flatMap { here ->
        here.flatMapIndexed { i, a ->
            here.drop(i + 1).filter { b ->
                val shared = a.changes.schedule.keys intersect b.changes.schedule.keys
                a.created.device != b.created.device && b.id !in a.seen && a.id !in b.seen &&
                    shared.any { a.changes.schedule[it] != b.changes.schedule[it] } &&
                    here.none { c -> a.id in c.seen && b.id in c.seen }
            }.map { b -> if (a.created < b.created) a to b else b to a }
        }
    }
