package com.factotum.data.item

import com.factotum.core.recurrence.Recurrence
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime

/** The kinds of item built so far (ADR 02, 03, 06); ACTIVITY comes with slice 07. */
enum class ItemKind { TASK, EVENT, REMINDER, HABIT }

enum class TaskStatus { PENDING, DONE, SKIPPED }

/** How one occurrence of a recurring task was resolved; PENDING is not an outcome. */
enum class Outcome { DONE, SKIPPED }

/**
 * A task, an event (ADR 02) or a standalone reminder (ADR 03). A task's [start] and [at] are
 * when it is planned, and [due] is a separate deadline. With no [at] the item takes the whole day.
 * Only a task has [due], [capacityRank] and [parentId]; an event has no [status].
 */
data class Item(
    val id: String,
    val kind: ItemKind,
    val title: String,
    val parentId: String?,
    val start: LocalDate?,
    val at: LocalTime?,
    val endDate: LocalDate?,
    val endTime: LocalTime?,
    val due: LocalDate?,
    val deleted: Boolean,
    val status: TaskStatus?,
    val importance: Long,
    val capacityRank: Long?,
    /** How the item repeats from its start (ADR 04), or null for a one-off. */
    val recurrence: Recurrence?,
    /** A habit's tracker (ADR 06). */
    val trackerId: String? = null,
    /** A habit's pause; no end means until resumed. */
    val pauseFrom: LocalDate? = null,
    val pauseUntil: LocalDate? = null,
    /** A habit's default time block and length (ADR 06, amended). */
    val blockId: String? = null,
    val durationMin: Long? = null,
)

/** A person's answer to a clash on an item's schedule (ADR 01). */
enum class Answer { KEEP_MINE, TAKE_THEIRS, KEEP_BOTH }

/** A clash waiting for a person: the item, and the group both sides changed. */
data class Question(val itemId: String, val group: String)
