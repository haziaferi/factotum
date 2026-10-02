package com.factotum.data.time

import com.factotum.core.time.GoalPeriod
import com.factotum.core.time.goalDays
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.DETAILS
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemKind
import com.factotum.data.item.MIDNIGHT
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.STATUS
import com.factotum.data.item.WHOLE
import com.factotum.data.item.itemRow
import com.factotum.data.item.schedule
import com.factotum.data.tracker.GOAL
import com.factotum.data.label.resolver
import com.factotum.data.tracker.goalRow
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

/** An activity; [labelId] is its label (Chronicle's category) as it reads now: a merged one's successor, none once deleted. */
data class Activity(val id: String, val name: String, val icon: String?, val color: Long?, val archived: Boolean, val sortOrder: Double?, val labelId: String? = null)

/** A goal on an activity's time against its target, in whole minutes, as Chronicle shows it. */
data class TimeGoalProgress(val minutes: Long, val targetMinutes: Long)

/**
 * Activities (Chronicle's, ADR 07): items of kind ACTIVITY, timed through [TimeRepository], with
 * goals on their time. Deleting one deletes its time and goals with it (Chronicle); none is ever
 * deleted for good (owner, 2026-10-02).
 */
internal class ActivityRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val dayStart: LocalTime = MIDNIGHT,
) {
    private val items = db.itemDao()
    private val times = db.timeDao()
    private val goals = db.trackerDao()
    private val labelDao = db.labelDao()
    private val time = TimeRepository(db, writes, newId, dayStart)
    private val clock = writes.clock

    suspend fun create(name: String, icon: String? = null, color: Long? = null): String {
        val id = newId()
        writes.write(mapOf(ITEM to listOf(id))) { store ->
            val s = clock.tick()
            val row = itemRow(id, s, ItemKind.ACTIVITY, name, null, schedule(null, null, null, null, null), null, 0, null)
                .edit(DETAILS, s, mapOf("icon" to icon, "color" to color))
                .edit(STATUS, s, mapOf("archived" to false))
            writes.merger.created(store, row)
        }
        return id
    }

    /** The live activities in their manual order, archived ones only when asked. */
    suspend fun activities(withArchived: Boolean = false): List<Activity> {
        val label = resolver(labelDao.allLabels())
        return items.liveActivities()
            .filter { withArchived || it.archived != true }
            .map { Activity(it.id, it.title, it.icon, it.color, it.archived == true, it.sortOrder, label(it.labelId)) }
    }

    suspend fun setArchived(id: String, archived: Boolean) {
        activity(id)
        writes.edit(ITEM, id, STATUS) { mapOf("archived" to archived) }
    }

    /**
     * Deletes [id] with its live spans and goals, in one write (Chronicle's `ActivityRepository.delete`).
     * It is never deleted forever (owner, 2026-10-02).
     */
    suspend fun delete(id: String) = writes.write({
        activity(id)
        mapOf(ITEM to listOf(id), TIME_SPAN to times.liveSpansOf(listOf(id)), GOAL to goals.goalsOf(ACTIVITY, id).map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(id)) { "no activity $id" }.edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc)))
        for (span in targets.getValue(TIME_SPAN)) store.put(requireNotNull(store.row(span)).edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        for (goal in targets.getValue(GOAL)) store.put(requireNotNull(store.row(goal)).edit(WHOLE, s, mapOf("deleted_at" to s.hlc)))
    }

    /** A goal on [activityId]'s time: [minutes] a [period], or once within the last 400 days for a [milestone]. */
    suspend fun addGoal(activityId: String, period: GoalPeriod, minutes: Long, milestone: Boolean = false): String {
        activity(activityId)
        val id = newId()
        writes.write(mapOf(GOAL to listOf(id))) { store ->
            writes.merger.created(store, goalRow(id, clock.tick(), ACTIVITY, activityId, period.name, minutes.toDouble(), if (milestone) "MILESTONE" else "RECURRING"))
        }
        return id
    }

    /** [goalId]'s progress on [today] at [now]: the time its window's days hold, overlaps once. */
    suspend fun progress(goalId: String, today: LocalDate, now: LocalDateTime): TimeGoalProgress {
        val goal = requireNotNull(goals.goals(listOf(goalId)).singleOrNull()?.takeIf { it.targetType == ACTIVITY && it.deletedAt == null }) { "no activity goal $goalId" }
        val days = goalDays(GoalPeriod.valueOf(goal.period), goal.kind == "MILESTONE", today)
        return TimeGoalProgress(time.total(days, now, goal.targetId) / 60, goal.value.toLong())
    }

    private suspend fun activity(id: String) =
        requireNotNull(items.items(listOf(id)).singleOrNull()?.takeIf { it.kind == ACTIVITY && it.deletedAt == null }) { "no activity $id" }
}

private val ACTIVITY = ItemKind.ACTIVITY.name
