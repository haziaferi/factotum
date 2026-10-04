package com.factotum.data

import androidx.room.RoomDatabase
import com.factotum.data.item.COMPLETION
import com.factotum.data.item.HABIT_BLOCK
import com.factotum.data.label.LABEL
import com.factotum.data.checkin.CHECK_IN
import com.factotum.data.search.rebuildSearchIfStale
import com.factotum.data.search.searchTriggers
import com.factotum.data.item.seedBlocks
import com.factotum.data.item.ITEM
import com.factotum.data.item.OCCURRENCE_EDIT
import com.factotum.data.reminder.REMINDER
import com.factotum.data.tracker.GOAL
import com.factotum.data.tracker.TRACKER
import com.factotum.data.tracker.TRACKER_READING
import com.factotum.data.time.TIME_SPAN
import com.factotum.data.page.BLOCK
import com.factotum.data.page.PAGE_LABEL
import com.factotum.data.page.CANVAS_EDGE
import com.factotum.data.page.CANVAS_NODE
import com.factotum.data.page.PAGE_CANVAS
import com.factotum.data.chart.CHART_SOURCE
import com.factotum.data.chart.SAVED_CHART
import com.factotum.data.checklist.CHECKLIST_ITEM
import com.factotum.data.checkin.MASKING_ENTRY
import com.factotum.data.checkin.REGULATION_EVENT
import com.factotum.data.checkin.SENSORY_LOG
import com.factotum.data.page.PAGE_DATABASE
import com.factotum.data.page.PAGE_RELATION
import com.factotum.data.page.RELATION_LINK
import com.factotum.data.page.PAGE_NOTICE
import com.factotum.data.page.PAGE_VIEW
import com.factotum.data.page.PROPERTY
import com.factotum.data.page.PROPERTY_OPTION
import com.factotum.data.page.PROPERTY_VALUE
import com.factotum.data.page.VALUE_PICK
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL

/**
 * The triggers Room's annotations cannot declare, dropped and created again on every open so an
 * upgrade never keeps an old body:
 * - each table's rules on `item`, `completion` and `reminder`, standing in for CHECK constraints
 *   (ADR 02, ADR 03);
 * - the sync outbox: every write to a synced table, and every purge, queues the row for export
 *   (ADR 13), so no write path can forget to; a deleted row's base and pending questions go too.
 *
 * A new database also gets the default time blocks, before the triggers exist ([seedBlocks]).
 * The search index's triggers are made with the rest, and the index is rebuilt when it does not
 * hold what it should ([rebuildSearchIfStale], ADR 10).
 */
internal object SchemaTriggers : RoomDatabase.Callback() {

    /**
     * ADR 04: each recurrence kind has all of its own columns and none of another's, and repeats
     * from a start date. Wrapped in COALESCE, since a NULL inside would make WHEN NOT(...) let the
     * row through.
     */
    private val recurrenceRules = """
        COALESCE(
            (NEW.recurrence_kind IS NULL OR NEW.start_date IS NOT NULL)
            AND (NEW.recurrence_kind IS NULL OR NEW.recurrence_kind IN ('RRULE', 'RULE_SET', 'RANDOM_DAYS', 'RANDOM_WINDOW', 'ROLLING', 'PLANNED'))
            AND (NEW.rrule IS NOT NULL) = (NEW.recurrence_kind IS 'RRULE' OR NEW.recurrence_kind IS 'RULE_SET')
            AND (NEW.recurrence_kind IS NOT 'RULE_SET' OR instr(NEW.rrule, char(10)) > 0)
            AND (NEW.rand_min_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_DAYS')
            AND (NEW.rand_max_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_DAYS')
            AND (NEW.rand_min_days IS NULL OR (NEW.rand_min_days >= 1 AND NEW.rand_max_days >= NEW.rand_min_days))
            AND (NEW.window_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_start IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_end IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_days IS NULL OR (NEW.window_days BETWEEN 1 AND 127 AND NEW.window_end > NEW.window_start))
            AND (NEW.roll_every IS NOT NULL) = (NEW.recurrence_kind IS 'ROLLING')
            AND (NEW.roll_unit IS NOT NULL) = (NEW.recurrence_kind IS 'ROLLING')
            AND (NEW.roll_every IS NULL OR (NEW.roll_every BETWEEN 1 AND 10000 AND NEW.roll_unit IN ('DAY', 'WEEK', 'MONTH')))
            AND (NEW.plan_n IS NOT NULL) = (NEW.recurrence_kind IS 'PLANNED')
            AND (NEW.plan_per IS NOT NULL) = (NEW.recurrence_kind IS 'PLANNED')
            AND (NEW.plan_days IS NOT NULL) = (NEW.recurrence_kind IS 'PLANNED')
            AND (NEW.plan_blocks IS NULL OR NEW.plan_per IS 'DAY')
            AND (NEW.plan_per IS NULL OR (NEW.plan_days BETWEEN 1 AND 127 AND (
                (NEW.plan_per = 'DAY' AND NEW.plan_n BETWEEN 1 AND 48 AND NEW.start_time IS NULL
                    AND (NEW.plan_blocks IS NULL OR (length(NEW.plan_blocks) - length(replace(NEW.plan_blocks, ',', '')) + 1 = NEW.plan_n
                        AND instr(',' || NEW.plan_blocks || ',', ',,') = 0)))
                OR (NEW.plan_per = 'WEEK' AND NEW.plan_n BETWEEN 1 AND 7)))),
        0)
    """.trimIndent()

    /**
     * ADR 02's kind rules; ADR 03's (a standalone reminder has a status and always a date and time);
     * ADR 06's (a habit has a tracker, which nothing else has, and only a habit pauses, has a block
     * or a length, rolls, or is planned); ADR 07's (only an activity has an icon, a colour or an
     * archived flag, and it has no dates; an activity or a habit has a manual order); ADR 08's (an
     * activity or a habit carries a label). In COALESCE, as a NULL inside would let the row through.
     */
    private val itemRules = """
        COALESCE(
            NEW.kind IN ('TASK', 'EVENT', 'REMINDER', 'HABIT', 'ACTIVITY')
            AND (NEW.kind = 'TASK' OR (NEW.due_date IS NULL AND NEW.capacity_rank IS NULL AND NEW.parent_id IS NULL))
            AND (NEW.kind = 'EVENT' OR (NEW.end_date IS NULL AND NEW.end_time IS NULL))
            AND (NEW.status IS NULL) = (NEW.kind IN ('EVENT', 'HABIT', 'ACTIVITY'))
            AND (NEW.status IS NULL OR NEW.status IN ('PENDING', 'DONE', 'SKIPPED'))
            AND (NEW.kind <> 'REMINDER' OR (NEW.start_date IS NOT NULL AND NEW.start_time IS NOT NULL))
            AND (NEW.tracker_id IS NOT NULL) = (NEW.kind = 'HABIT')
            AND (NEW.kind = 'HABIT' OR (NEW.pause_from IS NULL AND NEW.pause_until IS NULL AND NEW.block_id IS NULL AND NEW.duration_min IS NULL))
            AND (NEW.kind = 'HABIT' OR NEW.recurrence_kind IS NULL OR NEW.recurrence_kind NOT IN ('ROLLING', 'PLANNED'))
            AND (NEW.pause_until IS NULL OR (NEW.pause_from IS NOT NULL AND NEW.pause_until >= NEW.pause_from))
            AND (NEW.duration_min IS NULL OR NEW.duration_min > 0)
            AND (NEW.kind = 'ACTIVITY' OR (NEW.icon IS NULL AND NEW.color IS NULL))
            AND (NEW.archived IS NOT NULL) = (NEW.kind = 'ACTIVITY')
            AND (NEW.sort_order IS NULL OR NEW.kind IN ('ACTIVITY', 'HABIT'))
            AND (NEW.label_id IS NULL OR NEW.kind IN ('ACTIVITY', 'HABIT'))
            AND (NEW.kind <> 'ACTIVITY' OR (NEW.start_date IS NULL AND NEW.start_time IS NULL AND NEW.due_date IS NULL AND NEW.recurrence_kind IS NULL)),
        0)
        AND $recurrenceRules
    """.trimIndent()

    /** Chronicle's tracker rules, which its domain layer kept and the database here keeps instead. */
    private val trackerRules = """
        COALESCE(
            NEW.type IN ('NUMBER', 'BOOLEAN', 'RATING', 'CHOICE')
            AND NEW.polarity IN ('HIGHER_IS_BETTER', 'LOWER_IS_BETTER', 'NEUTRAL')
            AND (NEW.unit IS NULL OR (NEW.type = 'NUMBER' AND NEW.unit IN ('HOURS', 'KM', 'TIMES', 'PAGES', 'REPS', 'STEPS', 'CALORIES', 'CUSTOM')))
            AND (NEW.unit_label IS NOT NULL) = (NEW.unit IS 'CUSTOM')
            AND (NEW.default_number IS NULL OR NEW.type = 'NUMBER')
            AND (NEW.default_bool IS NULL OR NEW.type = 'BOOLEAN')
            AND (NEW.default_rating IS NULL OR (NEW.type = 'RATING' AND NEW.default_rating BETWEEN 1 AND 5)),
        0)
    """.trimIndent()

    /** A reading holds exactly one value, a rating from 1 to 5 (Chronicle `Entry.kt`). */
    private val readingRules = """
        COALESCE(
            (NEW.number_value IS NOT NULL) + (NEW.bool_value IS NOT NULL) + (NEW.rating_value IS NOT NULL) + (NEW.choice_id IS NOT NULL) = 1
            AND (NEW.rating_value IS NULL OR NEW.rating_value BETWEEN 1 AND 5),
        0)
    """.trimIndent()

    private val goalRules = """
        COALESCE(
            NEW.target_type IN ('ACTIVITY', 'TRACKER') AND NEW.period IN ('DAY', 'WEEK', 'MONTH')
            AND NEW.kind IN ('RECURRING', 'MILESTONE') AND NEW.completion_mode IN ('AUTO', 'MANUAL'),
        0)
    """.trimIndent()

    /**
     * ADR 07: a span is on a task, habit or activity (an owner not yet arrived passes, as foreign
     * keys are deferred, and readers check the kind too). That it ends no earlier than it starts is
     * checked where it is written, not here: its start and end merge apart, and a merged row the
     * database refused would stop every import after it.
     */
    private val spanRules = "COALESCE((SELECT kind FROM item WHERE id = NEW.item_id) IN ('TASK', 'HABIT', 'ACTIVITY'), 1)"

    /**
     * ADR 08: a label's scope is one of three. That names are unique is not a database rule: two
     * devices make the same name apart, and the sync merges them (owner, 2026-10-02).
     */
    private val labelRules = "COALESCE(NEW.applies_to IN ('ALL', 'ACTIVITY', 'TRACKER'), 0)"

    /**
     * ADR 05: a check-in says something, on its scales: a whole mood 1 to 5, energy and
     * pleasantness 0 to 1, a whole step count of two or more on an axis, a known stability, a
     * well-formed moment, and a day it is about no later than the date it was made (the repository
     * holds it to the personal day). All in the group written once, so no rule spans two groups.
     */
    private val checkInRules = """
        COALESCE(
            (NEW.mood IS NOT NULL OR NEW.energy IS NOT NULL OR NEW.pleasantness IS NOT NULL)
            AND (NEW.mood IS NULL OR (typeof(NEW.mood) = 'integer' AND NEW.mood BETWEEN 1 AND 5))
            AND (NEW.energy IS NULL OR NEW.energy BETWEEN 0 AND 1)
            AND (NEW.pleasantness IS NULL OR NEW.pleasantness BETWEEN 0 AND 1)
            AND (NEW.source_levels IS NULL OR (typeof(NEW.source_levels) = 'integer' AND NEW.source_levels >= 2
                AND (NEW.energy IS NOT NULL OR NEW.pleasantness IS NOT NULL)))
            AND (NEW.stability IS NULL OR NEW.stability IN ('JUMPY', 'STEADY', 'FLAT'))
            AND NEW.at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]*'
            AND (NEW.day IS NULL OR (NEW.day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND NEW.day <= substr(NEW.at, 1, 10))),
        0)
    """.trimIndent()

    /** A block is a stretch of one day (Tendril's planner); its weekday times are checked where they are read. */
    private val blockRules = "COALESCE(NEW.start_minute >= 0 AND NEW.end_minute > NEW.start_minute AND NEW.end_minute <= 1440 AND NEW.position >= 0, 0)"

    /** ADR 11: each scope names what it covers, a date-time or a date, and nothing else. */
    private val editRules = """
        COALESCE(
            NEW.scope IN ('OCCURRENCE', 'DAY', 'WEEK', 'FROM', 'EXTRA')
            AND (NEW.at IS NOT NULL) = (NEW.scope IN ('OCCURRENCE', 'EXTRA'))
            AND (NEW.date IS NOT NULL) = (NEW.scope IN ('DAY', 'WEEK', 'FROM'))
            AND NEW.days BETWEEN 0 AND 127 AND (NEW.days = 0 OR NEW.scope IN ('WEEK', 'FROM')),
        0)
    """.trimIndent()

    /** ADR 03's alert settings: unknown values are refused. */
    private val reminderRules = """
        NEW.alert_kind IN ('NOTIFICATION', 'ALARM') AND NEW.mode IN ('EASE', 'SCHEDULE', 'ALERT')
        AND NEW.nag_repeats >= 0 AND (NEW.nag_minutes IS NULL OR NEW.nag_minutes > 0)
    """.trimIndent()

    private val rules = mapOf(
        ITEM to itemRules,
        COMPLETION to "NEW.status IN ('DONE', 'SKIPPED')",
        REMINDER to reminderRules,
        OCCURRENCE_EDIT to editRules,
        TRACKER to trackerRules,
        TRACKER_READING to readingRules,
        GOAL to goalRules,
        HABIT_BLOCK to blockRules,
        TIME_SPAN to spanRules,
        LABEL to labelRules,
        CHECK_IN to checkInRules,
        SAVED_CHART to "NEW.chart_type IN ('LINE', 'BAR', 'PIE') AND NEW.range_days > 0",
        CHART_SOURCE to "NEW.source_kind IN ('ACTIVITY', 'TRACKER')",
        SENSORY_LOG to "COALESCE(NEW.sound BETWEEN 0 AND 1 AND NEW.light BETWEEN 0 AND 1 AND NEW.crowd BETWEEN 0 AND 1 AND NEW.temperature BETWEEN 0 AND 1 AND NEW.touch BETWEEN 0 AND 1 " +
            "AND NEW.at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]*', 0)",
        MASKING_ENTRY to "NEW.day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND (NEW.masked IS NULL OR NEW.masked IN ('NONE', 'SOME', 'MOST', 'ALL_DAY')) " +
            "AND (NEW.demand IS NULL OR NEW.demand IN ('LIGHT', 'SOME', 'A_LOT', 'RELENTLESS')) AND (NEW.recovery IS NULL OR NEW.recovery IN ('NONE', 'A_LITTLE', 'ENOUGH'))",
        REGULATION_EVENT to "NEW.direction IN ('UP', 'DOWN') AND NEW.outcome IN ('HELPED', 'NO_CHANGE', 'NOT_NOW')",
    )

    private val statements: List<String> = buildList {
        for ((table, rule) in rules) for (event in listOf("INSERT", "UPDATE")) {
            val name = "${table}_rules_${event.lowercase()}"
            add("DROP TRIGGER IF EXISTS $name")
            add("CREATE TRIGGER $name BEFORE $event ON $table WHEN NOT ($rule) BEGIN SELECT RAISE(ABORT, '$table: a row breaks its rules'); END")
        }
        // ADR 11: an edit is written once and undone once; nothing else about it changes.
        add("DROP TRIGGER IF EXISTS occurrence_edit_once")
        add(
            "CREATE TRIGGER occurrence_edit_once BEFORE UPDATE ON occurrence_edit WHEN " +
                "NEW.item_id IS NOT OLD.item_id OR NEW.scope IS NOT OLD.scope OR NEW.at IS NOT OLD.at OR NEW.date IS NOT OLD.date " +
                "OR NEW.days IS NOT OLD.days OR NEW.changes IS NOT OLD.changes OR NEW.created_hlc IS NOT OLD.created_hlc " +
                "OR NEW.created_device IS NOT OLD.created_device OR NEW.seen IS NOT OLD.seen " +
                "OR (OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NOT OLD.deleted_at) " +
                "BEGIN SELECT RAISE(ABORT, 'occurrence_edit: an edit is written once and undone once'); END",
        )
        // ADR 07: a span stays on its owner; an activity is never deleted for good (owner, 2026-10-02).
        add("DROP TRIGGER IF EXISTS time_span_owner_fixed")
        add(
            "CREATE TRIGGER time_span_owner_fixed BEFORE UPDATE ON time_span WHEN NEW.item_id IS NOT OLD.item_id " +
                "BEGIN SELECT RAISE(ABORT, 'time_span: a span stays on its owner'); END",
        )
        // ADR 12: a block stays on its page, and a page label, a notice, a database's parts and a cell on what they were made for.
        for ((table, columns) in listOf(BLOCK to listOf("page_id"), PAGE_LABEL to listOf("page_id", "label_id"), PAGE_NOTICE to listOf("page_id", "row_id"),
            PAGE_DATABASE to listOf("page_id"), PROPERTY to listOf("database_id", "target_database_id", "pair_property_id"),
            PAGE_RELATION to listOf("page_a", "page_b"), RELATION_LINK to listOf("property_id", "page_id", "target_id"),
            CHECKLIST_ITEM to listOf("checklist_id"), SAVED_CHART to listOf("chart_type"), CHART_SOURCE to listOf("chart_id", "source_kind", "source_id"),
            MASKING_ENTRY to listOf("day"), PROPERTY_OPTION to listOf("property_id"), PROPERTY_VALUE to listOf("page_id", "property_id"),
            VALUE_PICK to listOf("page_id", "property_id", "option_id"), PAGE_VIEW to listOf("database_id"),
            PAGE_CANVAS to listOf("page_id"), CANVAS_NODE to listOf("page_id", "type", "page_ref"), CANVAS_EDGE to listOf("page_id", "from_node_id", "to_node_id"),
        )) {
            add("DROP TRIGGER IF EXISTS ${table}_made_fixed")
            add(
                "CREATE TRIGGER ${table}_made_fixed BEFORE UPDATE ON $table WHEN " + columns.joinToString(" OR ") { "NEW.$it IS NOT OLD.$it" } +
                    " BEGIN SELECT RAISE(ABORT, '$table: what it was made for does not change'); END",
            )
        }
        add("DROP TRIGGER IF EXISTS item_activity_keep")
        add(
            "CREATE TRIGGER item_activity_keep BEFORE DELETE ON item WHEN OLD.kind = 'ACTIVITY' " +
                "BEGIN SELECT RAISE(ABORT, 'item: an activity is not deleted for good'); END",
        )
        for (table in SYNCED_TABLES) for (event in listOf("INSERT", "UPDATE", "DELETE")) {
            val name = "${table}_outbox_${event.lowercase()}"
            val row = if (event == "DELETE") "OLD" else "NEW"
            // A deleted row, by any path including a foreign key's cascade, takes its local merge state with it.
            val cleanup = if (event == "DELETE") "DELETE FROM sync_base WHERE id = OLD.id; DELETE FROM sync_ask WHERE id = OLD.id;" else ""
            add("DROP TRIGGER IF EXISTS $name")
            add("CREATE TRIGGER $name AFTER $event ON $table BEGIN INSERT INTO sync_outbox(id, tbl) VALUES ($row.id, '$table'); $cleanup END")
        }
        for (event in listOf("INSERT", "UPDATE")) {
            val name = "purge_outbox_${event.lowercase()}"
            add("DROP TRIGGER IF EXISTS $name")
            add("CREATE TRIGGER $name AFTER $event ON purge_registry BEGIN INSERT INTO sync_outbox(id, tbl) VALUES (NEW.id, NULL); END")
        }
    }

    override fun onCreate(connection: SQLiteConnection) = seedBlocks(connection)

    override fun onOpen(connection: SQLiteConnection) {
        statements.forEach(connection::execSQL)
        searchTriggers.forEach(connection::execSQL)
        rebuildSearchIfStale(connection)
    }
}
