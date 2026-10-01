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
import com.factotum.data.item.schedule
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

    /** A standalone reminder: an item of kind REMINDER, firing at [date] [at]. Returns the item's id. */
    suspend fun createStandalone(text: String, date: LocalDate, at: LocalTime, alert: Alert = Alert()): String {
        val itemId = newId()
        val reminderId = newId()
        writes.write(mapOf(ITEM to listOf(itemId), REMINDER to listOf(reminderId))) { store ->
            val s = clock.tick()
            writes.merger.created(store, itemRow(itemId, s, ItemKind.REMINDER, text, null, schedule(date, at, null, null, null), TaskStatus.PENDING, 0, null))
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
     * Snoozes [id] until [until]. The snooze syncs, leaves the item's schedule as it is (ADR 03),
     * and holds only for the firing it snoozed: once the item or the reminder is retimed, the
     * reminder fires at its new time.
     */
    suspend fun snooze(id: String, until: LocalDateTime) {
        val source = requireNotNull(dao.firingSources().singleOrNull { it.reminderId == id }) { "reminder $id has no firing to snooze" }
        writes.edit(REMINDER, id, STATUS) { mapOf("snoozed_until" to until.toString(), "snoozed_from" to source.due().toString()) }
    }

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
     * When each live reminder fires next, after [after] if given: the item's start date and time (or
     * the reminder's anchor when the item has none, else midnight), moved by the offset in
     * wall-clock minutes; a snooze of that firing takes its place. A reminder is quiet once its
     * item is done, skipped or deleted. Nothing here writes (§3.13 requirement 1).
     */
    suspend fun firings(after: LocalDateTime? = null): List<Firing> = dao.firingSources().map { s ->
        val due = s.due()
        val snoozed = s.snoozedUntil?.takeIf { s.snoozedFrom == due.toString() }?.let(LocalDateTime::parse)
        Firing(s.reminderId, s.itemId, snoozed ?: due)
    }.filter { after == null || it.at > after }.sortedWith(compareBy({ it.at }, { it.reminderId }))

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

/** The unsnoozed firing: start date at start time (else anchor, else midnight), moved by the offset on the wall clock. */
private fun FiringSource.due(): LocalDateTime {
    val time = (startTime ?: anchorTime)?.let(LocalTime::parse) ?: LocalTime(0, 0)
    // "5 minutes before 14:00" is 13:55 on any day, whatever the time zone does.
    val total = time.toSecondOfDay() + offsetMin * 60
    val day = total.floorDiv(SECONDS_PER_DAY)
    return LocalDateTime(LocalDate.parse(startDate).plus(day, DateTimeUnit.DAY), LocalTime.fromSecondOfDay(total.mod(SECONDS_PER_DAY).toInt()))
}

private const val SECONDS_PER_DAY = 24 * 60 * 60L
