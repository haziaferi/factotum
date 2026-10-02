package com.factotum.data.reminder

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemKind
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.STATUS
import com.factotum.data.item.TaskStatus
import com.factotum.data.item.itemRow
import com.factotum.data.item.dtstartOf
import com.factotum.data.item.OccurrenceEditEntity
import com.factotum.data.item.toEdit
import com.factotum.data.item.recurrenceOf
import com.factotum.data.item.recurrenceValues
import com.factotum.data.item.schedule
import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.OccurrenceEdit
import com.factotum.core.recurrence.Recurrence
import com.factotum.core.recurrence.occurrencesWithEdits
import com.factotum.core.recurrence.setsTimes
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/**
 * Reminders (ADR 03): rows hung off an item, at an offset from its start. A standalone reminder
 * ("take pills at 08:00") is an item of kind REMINDER with one reminder at offset 0. Writes go
 * through [writes]; [newId] makes row ids (ULIDs).
 */
internal class ReminderRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val dao = db.reminderDao()
    private val items = db.itemDao()
    private val clock = writes.clock

    /** A standalone reminder: an item of kind REMINDER, firing at [date] [at] and as [recurrence] repeats. Returns the item's id. */
    suspend fun createStandalone(text: String, date: LocalDate, at: LocalTime, alert: Alert = Alert(), recurrence: Recurrence? = null): String {
        val itemId = newId()
        val reminderId = newId()
        writes.write(mapOf(ITEM to listOf(itemId), REMINDER to listOf(reminderId))) { store ->
            val s = clock.tick()
            writes.merger.created(store, itemRow(itemId, s, ItemKind.REMINDER, text, null, schedule(date, at, null, null, null) + recurrenceValues(recurrence), TaskStatus.PENDING, 0, null))
            writes.merger.created(store, reminderRow(reminderId, itemId, 0, null, alert))
        }
        return itemId
    }

    /**
     * A reminder [offsetMinutes] from [itemId]'s start (negative is before). [anchor] is the time of
     * day used when the item has no start time. An item with no start date, or a deleted one, is
     * refused: its reminder could never fire.
     */
    suspend fun add(itemId: String, offsetMinutes: Long, anchor: LocalTime? = null, alert: Alert = Alert()): String {
        val id = newId()
        writes.write({
            val item = requireNotNull(items.items(listOf(itemId)).singleOrNull()) { "no item $itemId" }
            require(item.startDate != null && item.deletedAt == null) { "item $itemId has no start date or is deleted, so a reminder on it could never fire" }
            mapOf(REMINDER to listOf(id))
        }) { store, _ ->
            writes.merger.created(store, reminderRow(id, itemId, offsetMinutes, anchor, alert))
        }
        return id
    }

    suspend fun retime(id: String, offsetMinutes: Long, anchor: LocalTime? = null) =
        writes.edit(REMINDER, id, ALERT) { mapOf("offset_min" to offsetMinutes, "anchor_time" to anchor?.toString()) }

    suspend fun setAlert(id: String, alert: Alert) = writes.edit(REMINDER, id, ALERT) { alertValues(alert) }

    /**
     * Snoozes the [firing] of [id] that just rang until [until]. The snooze syncs, leaves the item's
     * schedule as it is (ADR 03), and holds only for that firing: once the item or the reminder is
     * retimed, the reminder fires at its new time.
     */
    suspend fun snooze(id: String, firing: LocalDateTime, until: LocalDateTime) =
        writes.edit(REMINDER, id, STATUS) { mapOf("snoozed_until" to until.toString(), "snoozed_from" to firing.toString()) }

    /** Deletes [id]; a standalone reminder's item goes with its last reminder, or it would sit unseen, never firing. */
    suspend fun delete(id: String) = writes.write({
        val itemId = requireNotNull(dao.reminders(listOf(id)).singleOrNull()) { "no reminder $id" }.itemId
        val standalone = items.items(listOf(itemId)).single().kind == ItemKind.REMINDER.name
        val last = dao.remindersOf(itemId).map { it.id } == listOf(id)
        mapOf(REMINDER to listOf(id), ITEM to if (standalone && last) listOf(itemId) else emptyList())
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(id)).edit(ALERT, s, mapOf("deleted_at" to s.hlc)))
        for (itemId in targets.getValue(ITEM)) store.put(requireNotNull(store.row(itemId)).edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
    }

    suspend fun alertOf(id: String): Alert? = dao.reminders(listOf(id)).singleOrNull()?.toAlert()

    suspend fun remindersOf(itemId: String): List<String> = dao.remindersOf(itemId).map { it.id }

    /**
     * When each live reminder fires next, after [after] if given. A firing is an occurrence of the
     * item (its start, or each time its recurrence gives, ADR 04) at the occurrence's time (or the
     * reminder's anchor for a whole-day item, else midnight), moved by the offset in wall-clock
     * minutes. An occurrence resolved in the completion log does not fire, nor does any once the
     * item is done, skipped or deleted. A snooze replaces the one firing it snoozed. Nothing here
     * writes (§3.13 requirement 1).
     */
    suspend fun firings(after: LocalDateTime? = null): List<Firing> {
        val editsByItem = items.liveEdits().groupBy { it.itemId }
        return dao.firingSources().mapNotNull { s -> firing(s, editsByItem[s.itemId].orEmpty(), after) }
            .sortedWith(compareBy({ it.at }, { it.reminderId }))
    }

    private suspend fun firing(s: FiringSource, editRows: List<OccurrenceEditEntity>, after: LocalDateTime?): Firing? {
        // A row this version cannot read (a rule from a newer peer) silences its own reminder, not all of them.
        val recurrence = try {
            recurrenceOf(s.recurrenceKind, s.rrule, s.randMinDays, s.randMaxDays, s.windowDays, s.windowStart, s.windowEnd)
        } catch (_: IllegalArgumentException) {
            return null
        }
        val resolved = if (recurrence == null) emptySet() else items.completionsOf(s.itemId).map { LocalDateTime.parse(it.occurrence) }.toSet()
        return Firings(s, recurrence, editRows.map { it.toEdit() }, resolved).next(after)?.let { Firing(s.reminderId, s.itemId, it) }
    }

    /** One reminder's firings, from its item's start, [recurrence] and occurrence [edits] (ADR 11), less the [resolved] occurrence dates. */
    private class Firings(
        private val s: FiringSource,
        private val recurrence: Recurrence?,
        private val edits: List<OccurrenceEdit>,
        private val resolved: Set<LocalDateTime>,
    ) {
        private val dtstart = dtstartOf(s.startDate, s.startTime)
        private val anchor = s.anchorTime?.let(LocalTime::parse) ?: MIDNIGHT

        /** The first firing after [after] (from the start when null) other than [skip], searched in widening windows. */
        fun first(after: LocalDateTime?, skip: LocalDateTime? = null): LocalDateTime? {
            // An occurrence can fire days either side of itself: start the search the offset earlier, less a day.
            val from = after?.let { LocalDateTime(it.date.plus(-(s.offsetMin.floorDiv(MINUTES_PER_DAY) + 1), DateTimeUnit.DAY), it.time) } ?: dtstart
            for (days in SEARCH_DAYS) {
                val to = LocalDateTime(from.date.plus(days, DateTimeUnit.DAY), from.time)
                recurrence.occurrencesWithEdits(s.itemId, dtstart, "", null, edits, from, to).asSequence()
                    .filter { (it.original ?: it.at) !in resolved }.map(::fire)
                    .firstOrNull { (after == null || it > after) && it != skip }
                    ?.let { return it }
            }
            return null
        }

        fun next(after: LocalDateTime?): LocalDateTime? {
            val snoozedFrom = s.snoozedFrom?.let(LocalDateTime::parse)
            val snoozed = s.snoozedUntil?.let(LocalDateTime::parse)?.takeIf { until ->
                (after == null || until > after) && snoozedFrom != null && isDue(snoozedFrom)
            }
            return listOfNotNull(snoozed, first(after, skip = snoozedFrom)).minOrNull()
        }

        /** Whether [at] is still one of this reminder's firings: a reschedule or a retime makes an old snooze stale. */
        private fun isDue(at: LocalDateTime): Boolean = first(after = secondBefore(at)) == at

        /**
         * A timed item fires at each occurrence's time, and so does a whole-day one whose rule sets
         * times, or whose edit gave this occurrence a time of its own; others at the anchor.
         */
        private fun fire(o: Occurrence): LocalDateTime {
            val original = o.original
            val ownTime = if (original == null) o.at.time != MIDNIGHT else o.at.time != original.time
            val timed = s.startTime != null || recurrence?.setsTimes == true || ownTime
            return shift(o.at.date, if (timed) o.at.time else anchor, s.offsetMin)
        }
    }

    private fun reminderRow(id: String, itemId: String, offset: Long, anchor: LocalTime?, alert: Alert): Row {
        val s = clock.tick()
        return Row(REMINDER, id, mapOf(
            ALERT to Group(s, mapOf("item_id" to itemId, "offset_min" to offset, "anchor_time" to anchor?.toString(), "deleted_at" to null) + alertValues(alert)),
            STATUS to Group(s, mapOf("snoozed_until" to null, "snoozed_from" to null)),
        ))
    }

    private fun alertValues(a: Alert) = mapOf(
        "alert_kind" to a.kind.name, "nag_repeats" to a.nagRepeats, "nag_minutes" to a.nagMinutes, "sound" to a.sound,
        "vibration" to a.vibration, "mode" to a.mode.name, "skin" to a.skin, "exact" to a.exact,
    )
}

internal fun ReminderEntity.toAlert() = Alert(
    kind = AlertKind.valueOf(alertKind),
    nagRepeats = nagRepeats,
    nagMinutes = nagMinutes,
    sound = sound,
    vibration = vibration,
    mode = AlertMode.valueOf(mode),
    skin = skin,
    exact = exact,
)

/** [date] at [time], moved by [offsetMin] on the wall clock: "5 minutes before 14:00" is 13:55 on any day, whatever the time zone does. */
private fun shift(date: LocalDate, time: LocalTime, offsetMin: Long): LocalDateTime {
    val total = time.toSecondOfDay() + offsetMin * 60
    val day = total.floorDiv(SECONDS_PER_DAY)
    return LocalDateTime(date.plus(day, DateTimeUnit.DAY), LocalTime.fromSecondOfDay(total.mod(SECONDS_PER_DAY).toInt()))
}

private fun secondBefore(t: LocalDateTime): LocalDateTime =
    if (t.time.toSecondOfDay() > 0) LocalDateTime(t.date, LocalTime.fromSecondOfDay(t.time.toSecondOfDay() - 1))
    else LocalDateTime(t.date.plus(-1, DateTimeUnit.DAY), LocalTime(23, 59, 59))

private val MIDNIGHT = LocalTime(0, 0)

private const val SECONDS_PER_DAY = 24 * 60 * 60L
private const val MINUTES_PER_DAY = 24 * 60L

/** A minutely rule finds its next firing within a day; a 29 February one needs years. */
private val SEARCH_DAYS = listOf(2, 9, 367, 8 * 366 + 2)
