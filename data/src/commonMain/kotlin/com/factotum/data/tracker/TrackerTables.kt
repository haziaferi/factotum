package com.factotum.data.tracker

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable
import com.factotum.data.item.WHOLE
import com.factotum.data.label.LABELLED

internal const val TRACKER = "tracker"
internal const val TRACKER_CHOICE = "tracker_choice"
internal const val TRACKER_READING = "tracker_reading"
internal const val GOAL = "goal"

internal fun trackerTable(dao: TrackerDao) =
    EntityTable(dao::trackers, dao::allTrackers, dao::putTrackers, dao::deleteTrackers, TrackerEntity::toRow, Row::toTrackerEntity) { emptyList() }

internal fun choiceTable(dao: TrackerDao) =
    EntityTable(dao::choices, dao::allChoices, dao::putChoices, dao::deleteChoices, TrackerChoiceEntity::toRow, Row::toChoiceEntity) {
        listOf(TRACKER to it.trackerId)
    }

internal fun readingTable(dao: TrackerDao) =
    EntityTable(dao::readings, dao::allReadings, dao::putReadings, dao::deleteReadings, TrackerReadingEntity::toRow, Row::toReadingEntity) {
        listOf(TRACKER to it.trackerId)
    }

/** A goal's target is polymorphic and has no foreign key (Chronicle), so it waits on nothing. */
internal fun goalTable(dao: TrackerDao) =
    EntityTable(dao::goals, dao::allGoals, dao::putGoals, dao::deleteGoals, GoalEntity::toRow, Row::toGoalEntity) { emptyList() }

private fun whole(table: String, id: String, hlc: Long, device: String, values: Map<String, Any?>) =
    Row(table, id, mapOf(WHOLE to Group(Stamp(hlc, device), values)))

/** The one group of a single-group row, read with casts that throw on a value of the wrong type. */
private class Values(row: Row) {
    val group = row.groups.getValue(WHOLE)
    val v = group.values
    fun s(k: String) = v[k] as String
    fun sOrNull(k: String) = v[k] as String?
    fun l(k: String) = v[k] as Long
    fun lOrNull(k: String) = v[k] as Long?
    fun dOrNull(k: String) = v[k] as Double?
    fun d(k: String) = v[k] as Double
    fun b(k: String) = v[k] as Boolean
    fun bOrNull(k: String) = v[k] as Boolean?
}

internal fun TrackerEntity.toRow() = Row(TRACKER, id, mapOf(
    WHOLE to Group(Stamp(hlc, device), mapOf(
        "name" to name, "type" to type, "unit" to unit, "unit_label" to unitLabel, "default_number" to defaultNumber,
        "default_bool" to defaultBool, "default_rating" to defaultRating, "polarity" to polarity, "archived" to archived,
        "sort_order" to sortOrder, "deleted_at" to deletedAt,
    )),
    LABELLED to Group(Stamp(labelHlc, labelDevice), mapOf("label_id" to labelId)),
))

internal fun Row.toTrackerEntity() = Values(this).run {
    val label = groups.getValue(LABELLED)
    TrackerEntity(
        id, s("name"), s("type"), sOrNull("unit"), sOrNull("unit_label"), dOrNull("default_number"), bOrNull("default_bool"),
        lOrNull("default_rating"), s("polarity"), b("archived"), l("sort_order"), lOrNull("deleted_at"), group.stamp.hlc, group.stamp.device,
        label.values["label_id"] as String?, label.stamp.hlc, label.stamp.device,
    )
}

internal fun TrackerChoiceEntity.toRow() = whole(TRACKER_CHOICE, id, hlc, device, mapOf(
    "tracker_id" to trackerId, "label" to label, "color_argb" to colorArgb, "sort_order" to sortOrder, "deleted_at" to deletedAt,
))

internal fun Row.toChoiceEntity() = Values(this).run {
    TrackerChoiceEntity(id, s("tracker_id"), s("label"), lOrNull("color_argb"), l("sort_order"), lOrNull("deleted_at"), group.stamp.hlc, group.stamp.device)
}

internal fun TrackerReadingEntity.toRow() = whole(TRACKER_READING, id, hlc, device, mapOf(
    "tracker_id" to trackerId, "at" to at, "number_value" to numberValue, "bool_value" to boolValue, "rating_value" to ratingValue,
    "choice_id" to choiceId, "label" to label, "note" to note, "occurrence" to occurrence, "deleted_at" to deletedAt,
))

internal fun Row.toReadingEntity() = Values(this).run {
    TrackerReadingEntity(
        id, s("tracker_id"), s("at"), dOrNull("number_value"), bOrNull("bool_value"), lOrNull("rating_value"), sOrNull("choice_id"),
        sOrNull("label"), sOrNull("note"), sOrNull("occurrence"), lOrNull("deleted_at"), group.stamp.hlc, group.stamp.device,
    )
}

internal fun GoalEntity.toRow() = whole(GOAL, id, hlc, device, mapOf(
    "target_type" to targetType, "target_id" to targetId, "period" to period, "value" to value, "kind" to kind,
    "completion_mode" to completionMode, "achieved_at" to achievedAt, "deleted_at" to deletedAt,
))

internal fun Row.toGoalEntity() = Values(this).run {
    GoalEntity(
        id, s("target_type"), s("target_id"), s("period"), d("value"), s("kind"), s("completion_mode"), sOrNull("achieved_at"),
        lOrNull("deleted_at"), group.stamp.hlc, group.stamp.device,
    )
}
