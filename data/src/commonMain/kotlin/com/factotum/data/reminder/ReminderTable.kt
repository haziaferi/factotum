package com.factotum.data.reminder

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable
import com.factotum.data.item.ITEM
import com.factotum.data.item.STATUS

internal const val REMINDER = "reminder"
internal const val ALERT = "alert"

internal fun reminderTable(dao: ReminderDao) =
    EntityTable(dao::reminders, dao::allReminders, dao::putReminders, dao::deleteReminders, ReminderEntity::toRow, Row::toReminderEntity) {
        listOf(ITEM to it.itemId)
    }

internal fun ReminderEntity.toRow() = Row(REMINDER, id, mapOf(
    ALERT to Group(Stamp(alertHlc, alertDevice), mapOf(
        "item_id" to itemId, "offset_min" to offsetMin, "anchor_time" to anchorTime, "alert_kind" to alertKind,
        "nag_repeats" to nagRepeats, "nag_minutes" to nagMinutes, "sound" to sound, "vibration" to vibration,
        "mode" to mode, "skin" to skin, "exact" to exact, "deleted_at" to deletedAt,
    )),
    STATUS to Group(Stamp(statusHlc, statusDevice), mapOf("snoozed_until" to snoozedUntil, "snoozed_from" to snoozedFrom)),
))

/** Throws when [this] lacks a reminder's groups or holds a value of the wrong type. */
internal fun Row.toReminderEntity(): ReminderEntity {
    val a = groups.getValue(ALERT)
    val s = groups.getValue(STATUS)
    return ReminderEntity(
        id = id,
        itemId = a.values["item_id"] as String,
        offsetMin = a.values["offset_min"] as Long,
        anchorTime = a.values["anchor_time"] as String?,
        alertKind = a.values["alert_kind"] as String,
        nagRepeats = a.values["nag_repeats"] as Long,
        nagMinutes = a.values["nag_minutes"] as Long?,
        sound = a.values["sound"] as String?,
        vibration = a.values["vibration"] as String?,
        mode = a.values["mode"] as String,
        skin = a.values["skin"] as String?,
        exact = a.values["exact"] as Boolean,
        deletedAt = a.values["deleted_at"] as Long?,
        alertHlc = a.stamp.hlc,
        alertDevice = a.stamp.device,
        snoozedUntil = s.values["snoozed_until"] as String?,
        snoozedFrom = s.values["snoozed_from"] as String?,
        statusHlc = s.stamp.hlc,
        statusDevice = s.stamp.device,
    )
}
