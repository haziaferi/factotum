package com.factotum.data.page

import com.factotum.core.habit.dayOf
import com.factotum.core.recurrence.Interval
import com.factotum.core.recurrence.IntervalUnit
import com.factotum.core.recurrence.Occurrence
import com.factotum.core.recurrence.occurrencesWithEdits
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.DETAILS
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemEntity
import com.factotum.data.item.ItemKind
import com.factotum.data.item.ItemRepository
import com.factotum.data.item.OccurrenceRepository
import com.factotum.data.item.Outcome
import com.factotum.data.item.SCHEDULE
import com.factotum.data.item.STATUS
import com.factotum.data.item.TaskStatus
import com.factotum.data.item.dtstart
import com.factotum.data.item.itemRow
import com.factotum.data.item.recurrence
import com.factotum.data.item.recurrenceValues
import com.factotum.data.item.schedule
import com.factotum.data.item.toEdit
import com.factotum.data.settings.PersonalSettings
import com.factotum.data.sync.readChunked
import com.factotum.data.time.localNow
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.plus

/** The task field a column shows while a database's rows are tasks (Tendril's binding roles), and the column type it needs. */
enum class TaskRole(val type: PropertyType) { DONE(PropertyType.CHECKBOX), DATE(PropertyType.DATE), DUE(PropertyType.DATE), RECURRENCE(PropertyType.INTERVAL) }

/** What editing a repeating row's Date cell moves: asked every time (owner, 2026-10-04, decision 14 answer 26). */
enum class DateScope { SERIES, NEXT }

/** The prefix of a row's task id; `ItemDao.rowTasks` spells it out, as a query must. */
private const val ROW_TASK = "rowtask:"

/** A row's task: one per page, whichever databases it is a row of, so two devices seeding it make one. */
internal fun rowTaskId(pageId: String) = ROW_TASK + pageId

internal fun pageOfRowTask(itemId: String): String? = itemId.takeIf { it.startsWith(ROW_TASK) }?.removePrefix(ROW_TASK)

/**
 * A seeded task's stamp: the lowest there is, and the app's, as the journal's days are, so two
 * devices seeding one row write one row and any edit outranks the seed.
 */
private val SEED = Stamp(0, "rowtask~")

/**
 * Tendril's database rows as tasks (decision 14, answers 15-30). While a database has rows as tasks
 * on, every row is a task: one item, `rowtask:<page>`, whose title is the page's title (a rename of
 * either renames both, in one write), whose life follows the page's (trashed, restored and purged
 * with it, and a task edit made after the page was trashed brings it back), and whose done, date,
 * due date and repeat show in the columns bound to them. A bound column's stored cells are ignored
 * while bound and get the task's value when unbound.
 *
 * [settle] makes the tasks match the rows. It runs after every import, and the composition root
 * runs it after a local write that changes which pages are rows (a page made, moved, trashed or
 * restored, a label, a doorway); a row's own edits here seed its task first if it has none yet.
 */
internal class RowTaskRepository(
    private val db: FactotumDatabase,
    private val writes: LocalWrites,
    private val items: ItemRepository,
    private val occurrences: OccurrenceRepository,
    private val databases: DatabaseRepository,
    private val personal: PersonalSettings,
    private val now: () -> LocalDateTime = ::localNow,
) {
    private val dao = db.databaseDao()
    private val itemDao = db.itemDao()
    private val pageDao = db.pageDao()
    private val sync = db.syncDao()
    private val clock = writes.clock

    /**
     * Turns rows as tasks on or off. On, every row becomes a task; off, each bound column keeps its
     * tasks' last values, every column lets go of its task field (one a sync left bound too), and the
     * tasks are trashed unless another database still makes their pages tasks (answer 19).
     */
    suspend fun setRowsAsTasks(databaseId: String, on: Boolean) {
        var frozen = emptyMap<Pair<String, String>, String?>()
        writes.write({
            shell(databaseId)
            val roles = if (on) emptyList() else dao.propertiesOf(databaseId).filter { it.taskRole != null }.map { it.id }
            frozen = if (on) emptyMap() else freeze(databaseId, bindingsOf(databaseId).values.toList())
            mapOf(PAGE_DATABASE to listOf(shellId(databaseId)), PROPERTY to roles, PROPERTY_VALUE to frozen.keys.map { valueId(it.first, it.second) })
        }) { store, targets ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(shellId(databaseId))).set(TASKS, s, mapOf("tasks_on" to on)))
            targets.getValue(PROPERTY).forEach { store.put(requireNotNull(store.row(it)).edit(TASK_ROLE, s, mapOf("task_role" to null))) }
            for ((cell, v) in frozen) putCell(store, cell.first, cell.second, v, automatic(s))
        }
        settle()
    }

    /**
     * Shows [role] in the column [propertyId]: a column bound before to the same role is unbound
     * (keeping its tasks' values), and each row's value in this column, where it has one, becomes its
     * task's. Setting an interval on a task with no date starts it today (answer 28). What this writes
     * into tasks and cells is the app's, so it never brings back a row trashed elsewhere.
     */
    suspend fun bind(propertyId: String, role: TaskRole) {
        settle()
        val today = today()
        var frozen = emptyMap<Pair<String, String>, String?>()
        var pushed = emptyMap<String, String>()
        var before = emptyList<String>()
        writes.write({
            val p = requireNotNull(dao.properties(listOf(propertyId)).singleOrNull()) { "no property $propertyId" }
            require(p.type == role.type.name) { "${p.name} is a ${p.type}, and $role shows in a ${role.type}" }
            require(shell(p.databaseId).tasksOn == true) { "the rows of ${p.databaseId} are not tasks" }
            val previous = bindingsOf(p.databaseId)[role]?.takeIf { it.id != propertyId }
            before = listOfNotNull(previous?.id)
            frozen = previous?.let { freeze(p.databaseId, listOf(it)) }.orEmpty()
            val rows = databases.members(p.databaseId).toSet()
            val live = readChunked(rows.map(::rowTaskId)) { itemDao.items(it) }.filter { it.deletedAt == null }.map { it.id }.toSet()
            pushed = dao.valuesOf(propertyId).filter { it.pageId in rows && it.value != null }.associate { rowTaskId(it.pageId) to requireNotNull(it.value) }.filterKeys { it in live }
            mapOf(PROPERTY to listOf(propertyId) + before, PROPERTY_VALUE to frozen.keys.map { valueId(it.first, it.second) }, ITEM to pushed.keys.toList())
        }) { store, _ ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(propertyId)).set(TASK_ROLE, s, mapOf("task_role" to role.name)))
            before.forEach { store.put(requireNotNull(store.row(it)).edit(TASK_ROLE, s, mapOf("task_role" to null))) }
            for ((cell, v) in frozen) putCell(store, cell.first, cell.second, v, automatic(s))
            for ((taskId, value) in pushed) {
                val row = requireNotNull(store.row(taskId))
                val (group, changes) = when (role) {
                    TaskRole.DONE -> STATUS to if (row.repeats()) emptyMap() else mapOf("status" to (if (value == "true") TaskStatus.DONE else TaskStatus.PENDING).name)
                    TaskRole.DATE -> SCHEDULE to dateOf(value)?.let { mapOf("start_date" to it.toString()) }.orEmpty()
                    TaskRole.DUE -> SCHEDULE to dateOf(value)?.let { mapOf("due_date" to it.toString()) }.orEmpty()
                    TaskRole.RECURRENCE -> SCHEDULE to Interval.parse(value)?.let { row.intervalValues(it, today) }.orEmpty()
                }
                if (changes.any { (k, v) -> row.groups.getValue(group).values[k] != v }) store.put(row.edit(group, automatic(s), changes))
            }
        }
    }

    /** Takes [propertyId] off its task field: each row's cell keeps its task's value now (answer 20; a richer repeat than an interval leaves it empty, answer 27). */
    suspend fun unbind(propertyId: String) {
        var frozen = emptyMap<Pair<String, String>, String?>()
        writes.write({
            val p = requireNotNull(dao.properties(listOf(propertyId)).singleOrNull()?.takeIf { it.taskRole != null }) { "$propertyId shows no task field" }
            frozen = if (bindingsOf(p.databaseId).values.any { it.id == propertyId }) freeze(p.databaseId, listOf(p)) else emptyMap()
            mapOf(PROPERTY to listOf(propertyId), PROPERTY_VALUE to frozen.keys.map { valueId(it.first, it.second) })
        }) { store, _ ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(propertyId)).edit(TASK_ROLE, s, mapOf("task_role" to null)))
            for ((cell, v) in frozen) putCell(store, cell.first, cell.second, v, automatic(s))
        }
    }

    /** Each task field's column in [databaseId]; none while its rows are not tasks. */
    suspend fun bindings(databaseId: String): Map<TaskRole, String> = bindingsOf(databaseId).mapValues { it.value.id }

    /** The live task of row [pageId], or null. */
    suspend fun taskOf(pageId: String): String? = liveTask(pageId)?.id

    /**
     * Ticks or unticks row [pageId]. A repeating row is ticked only: its next open occurrence is
     * resolved, and the row shows the one after (answer 22).
     */
    suspend fun setDone(pageId: String, done: Boolean) {
        val id = ensure(pageId)
        if (task(pageId).recurrence() == null) return items.setStatus(id, if (done) TaskStatus.DONE else TaskStatus.PENDING)
        require(done) { "a repeating row is ticked, one occurrence at a time" }
        items.resolve(id, Outcome.DONE) {
            val next = requireNotNull(nextOpen(db, task(pageId))) { "row $pageId has no open occurrence" }
            next.original ?: next.at
        }
    }

    /**
     * Sets row [pageId]'s date. On a repeating row, [scope] says whether the series starts on [date]
     * or only its next open occurrence moves there (answer 26: the screen asks every time).
     */
    suspend fun setDate(pageId: String, date: LocalDate?, scope: DateScope) {
        val id = ensure(pageId)
        val task = task(pageId)
        if (task.recurrence() != null && scope == DateScope.NEXT) {
            val next = requireNotNull(nextOpen(db, task)) { "row $pageId has no open occurrence" }
            occurrences.move(id, next.original ?: next.at, requireNotNull(date) { "an occurrence moves to a day" })
            return
        }
        writes.edit(ITEM, id, SCHEDULE, {
            val now = task(pageId)
            require(date != null || now.recurrence() == null) { "a repeating row keeps a date to repeat from" }
            require(date != null || db.reminderDao().remindersOf(id).isEmpty()) { "row $pageId has reminders, so it keeps a date" }
        }) { mapOf("start_date" to date?.toString()) }
    }

    suspend fun setDue(pageId: String, date: LocalDate?) = writes.edit(ITEM, ensure(pageId), SCHEDULE, { task(pageId) }) { mapOf("due_date" to date?.toString()) }

    /** Sets how row [pageId] repeats, or that it does not; a row with no date starts today (answer 28). */
    suspend fun setInterval(pageId: String, interval: Interval?) {
        val id = ensure(pageId)
        val today = today()
        writes.write({ task(pageId); mapOf(ITEM to listOf(id)) }) { store, _ ->
            val row = requireNotNull(store.row(id))
            store.put(row.edit(SCHEDULE, clock.tick(), if (interval == null) recurrenceValues(null) else row.intervalValues(interval, today)))
        }
    }

    /**
     * Before revive, after every import: a clash on a row task's schedule that the app's own write
     * took part in (a trash or restore following its page) is no person's question. The person's
     * fields stand, and whether the task is deleted comes from the later of the two, so a task
     * edited after its row was trashed elsewhere stands and brings the row back (answer 18), and
     * one edited before keeps its edit in the trash. A clash between two people's edits stays a
     * question, with no "keep both" (answer 21).
     */
    suspend fun settleClashes() = writes.write({
        mapOf(ITEM to sync.allAsks().filter { it.grp == SCHEDULE && pageOfRowTask(it.id) != null }.map { it.id })
    }) { store, targets ->
        for (id in targets.getValue(ITEM)) {
            val mine = requireNotNull(store.row(id)).groups.getValue(SCHEDULE)
            val theirs = store.asked(id, SCHEDULE) ?: continue
            if (mine.stamp.byHand && theirs.stamp.byHand) continue
            writes.merger.settle(store, id, SCHEDULE) { a, b ->
                val later = maxOf(a, b, compareBy { it.stamp })
                val values = (listOf(a, b).singleOrNull { it.stamp.byHand } ?: later).values + ("deleted_at" to later.values["deleted_at"])
                // The later version as it is, or the two joined under a stamp just above it, so a device holding only the later one takes the join.
                if (values == later.values) later else Group(automatic(later.stamp), values)
            }
        }
    }

    /**
     * After every import, and after a local write that changes which pages are rows: each row of a
     * database with rows as tasks has a live task, seeded with its title when it has none; a task
     * whose page is no such row any more is trashed (answer 30); a task whose page was deleted for
     * good goes on this device alone, so a page a later edit brings back finds its task again; a
     * task's title follows its page's. Every write here is the app's own.
     */
    suspend fun settle() {
        var seed = emptyMap<String, String>()
        var back = emptyList<String>()
        var retired = emptyList<String>()
        var gone = emptyList<String>()
        var retitled = emptyMap<String, String>()
        writes.write({
            val wanted = rows()
            val tasks = itemDao.rowTasks().associateBy { requireNotNull(pageOfRowTask(it.id)) }
            val states = pageStates(db, tasks.keys.toList())
            val titles = readChunked((wanted + tasks.keys).toList()) { pageDao.pages(it) }.associate { it.id to it.title }
            seed = (wanted - tasks.keys).associate { rowTaskId(it) to titles.getValue(it) }
            back = tasks.filter { (page, t) -> page in wanted && t.deletedAt != null }.map { it.value.id }
            gone = tasks.filter { (page, _) -> states[page] == PageState.DELETED }.map { it.value.id }
            retired = tasks.filter { (page, t) -> page !in wanted && t.deletedAt == null && states[page] != PageState.DELETED }.map { it.value.id }
            retitled = tasks.filter { (page, t) -> page in wanted && titles[page] != t.title }.map { (page, t) -> t.id to titles.getValue(page) }.toMap()
            mapOf(ITEM to (seed.keys + back + retired + gone + retitled.keys).toList())
        }) { store, _ ->
            val s = automatic(clock.tick())
            for ((id, title) in seed) writes.merger.created(store, itemRow(id, SEED, ItemKind.TASK, title, null, schedule(null, null, null, null, null), TaskStatus.PENDING, 0, null))
            back.forEach { store.put(requireNotNull(store.row(it)).edit(SCHEDULE, s, mapOf("deleted_at" to null))) }
            retired.forEach { store.put(requireNotNull(store.row(it)).edit(SCHEDULE, s, mapOf("deleted_at" to s.hlc))) }
            gone.forEach(store::remove)
            for ((id, title) in retitled) store.put(requireNotNull(store.row(id)).edit(DETAILS, s, mapOf("title" to title)))
        }
    }

    /** Every page that is a row of a live database with rows as tasks. */
    private suspend fun rows(): Set<String> = dao.allDatabases().filter { it.tasksOn == true }.map { it.pageId }
        .filter { pageDao.pages(listOf(it)).singleOrNull()?.deletedAt == null }
        .flatMap { databases.members(it) }.toSet()

    private suspend fun bindingsOf(databaseId: String): Map<TaskRole, PropertyEntity> = bindingsOf(db, databaseId)

    /**
     * The cells [bound]'s columns keep when they stop showing their tasks: each row's task value now,
     * as stored text, by page and property. A row with no live task keeps its cell as it is.
     */
    private suspend fun freeze(databaseId: String, bound: List<PropertyEntity>): Map<Pair<String, String>, String?> {
        if (bound.isEmpty()) return emptyMap()
        val rows = databases.members(databaseId).filter { liveTask(it) != null }
        val cells = boundCells(db, databaseId, rows)
        return rows.flatMap { page ->
            bound.map { p ->
                val cell = cells[page]?.get(p.id)
                (page to p.id) to when (TaskRole.valueOf(requireNotNull(p.taskRole))) {
                    TaskRole.DONE -> cell?.checked?.toString()
                    TaskRole.DATE, TaskRole.DUE -> cell?.date?.toString()
                    TaskRole.RECURRENCE -> cell?.text?.takeIf { !cell.fixed }
                }
            }
        }.toMap()
    }

    /** Row [pageId]'s task id, seeding it first when the row has none yet ([settle] not run since the row was made). */
    private suspend fun ensure(pageId: String): String {
        if (liveTask(pageId) == null) settle()
        return task(pageId).id
    }

    private suspend fun liveTask(pageId: String) = itemDao.items(listOf(rowTaskId(pageId))).singleOrNull()?.takeIf { it.deletedAt == null }

    private suspend fun task(pageId: String) = requireNotNull(liveTask(pageId)) { "row $pageId is not a task" }

    private suspend fun shell(databaseId: String) =
        requireNotNull(dao.databases(listOf(shellId(databaseId))).singleOrNull()?.takeIf { pageDao.pages(listOf(databaseId)).singleOrNull()?.deletedAt == null }) { "no database $databaseId" }

    private suspend fun today() = dayOf(now(), personal.dayStart())
}

private fun dateOf(text: String) = runCatching { LocalDate.parse(text) }.getOrNull()

/** [interval]'s schedule values on a task row, starting it [today] when it has no date. */
private fun Row.intervalValues(interval: Interval, today: LocalDate): Map<String, Any?> =
    recurrenceValues(interval.recurrence()) + ("start_date" to (groups.getValue(SCHEDULE).values["start_date"] ?: today.toString()))

private fun Row.repeats() = groups.getValue(SCHEDULE).values["recurrence_kind"] != null

/** [group] set to [values]: edited when the row has it, added when a version before it wrote none. */
private fun Row.set(group: String, s: Stamp, values: Map<String, Any?>): Row =
    if (group in groups) edit(group, s, values) else copy(groups = groups + (group to Group(s, values)))

internal suspend fun bindingsOf(db: FactotumDatabase, databaseId: String): Map<TaskRole, PropertyEntity> {
    val dao = db.databaseDao()
    if (dao.databases(listOf(shellId(databaseId))).singleOrNull()?.tasksOn != true) return emptyMap()
    return dao.propertiesOf(databaseId).mapNotNull { p -> p.taskRole?.let(TaskRole::valueOf)?.takeIf { it.type.name == p.type }?.let { it to p } }
        .groupBy({ it.first }, { it.second }).mapValues { (_, ps) -> ps.maxWith(compareBy({ Stamp(requireNotNull(it.roleHlc), requireNotNull(it.roleDevice)) }, { it.id })) }
}

/**
 * The bound columns' cells of [pageIds] in [databaseId], by page then property: what each row's
 * task holds now, empty for a row with no live task. A repeating task shows its next open
 * occurrence (answer 22): its date there, and unticked until none is left. A repeat richer than an
 * interval shows read-only ([Cell.fixed], answer 23), with its rule's text when it has one.
 */
internal suspend fun boundCells(db: FactotumDatabase, databaseId: String, pageIds: List<String>): Map<String, Map<String, Cell>> {
    val bound = bindingsOf(db, databaseId)
    if (bound.isEmpty()) return emptyMap()
    val tasks = readChunked(pageIds.map(::rowTaskId)) { db.itemDao().items(it) }.filter { it.deletedAt == null }.associateBy { requireNotNull(pageOfRowTask(it.id)) }
    val empty = Cell(null, null, null, false, emptyList())
    return pageIds.associateWith { page ->
        val task = tasks[page]
        val repeat = task?.let { runCatching { it.recurrence() }.getOrNull() }
        val next = if (task != null && repeat != null) nextOpen(db, task) else null
        bound.entries.associate { (role, p) ->
            p.id to if (task == null) empty else when (role) {
                TaskRole.DONE -> empty.copy(checked = if (repeat == null) task.status == TaskStatus.DONE.name else next == null)
                TaskRole.DATE -> (next?.at?.date ?: task.startDate?.let(LocalDate::parse)).let { empty.copy(text = it?.toString(), date = it) }
                TaskRole.DUE -> task.dueDate?.let(LocalDate::parse).let { empty.copy(text = it?.toString(), date = it) }
                TaskRole.RECURRENCE -> when (val interval = Interval.of(repeat)) {
                    null -> if (repeat == null) empty else empty.copy(text = task.repeat.rrule, fixed = true)
                    else -> empty.copy(text = interval.stored())
                }
            }
        }
    }
}

/**
 * [task]'s earliest occurrence not yet resolved, its occurrence edits applied, or null when every
 * one is; searched in widening windows from its start, or from an occurrence an edit put earlier.
 */
internal suspend fun nextOpen(db: FactotumDatabase, task: ItemEntity): Occurrence? {
    val repeat = runCatching { task.recurrence() }.getOrNull() ?: return null
    val start = task.dtstart() ?: return null
    val dao = db.itemDao()
    val edits = dao.liveEditsOf(task.id).map { it.toEdit() }
    val resolved = dao.completionsOf(task.id).map { LocalDateTime.parse(it.occurrence) }.toSet()
    val from = (listOf(start) + edits.mapNotNull { it.at } + edits.mapNotNull { e -> e.changes.movedTo?.let { LocalDateTime(it, LocalTime(0, 0)) } }).min()
    for (days in SEARCH_DAYS) {
        val to = LocalDateTime(start.date.plus(days, DateTimeUnit.DAY), start.time)
        repeat.occurrencesWithEdits(task.id, start, task.title, task.durationMin, edits, from, to)
            .filter { (it.original ?: it.at) !in resolved }.minByOrNull { it.at }?.let { return it }
    }
    return null
}

/** As a reminder's search: a day, then a week, a year, and eight years for a 29 February rule. */
private val SEARCH_DAYS = listOf(2, 9, 367, 8 * 366 + 2)

/** An interval's rough length in days, for sorting a column of them. */
internal fun Interval.days(): Int = every * when (unit) { IntervalUnit.DAY -> 1; IntervalUnit.WEEK -> 7; IntervalUnit.MONTH -> 30 }
