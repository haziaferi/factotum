package com.factotum.data

import androidx.room.RoomDatabase
import com.factotum.data.item.COMPLETION
import com.factotum.data.item.ITEM
import com.factotum.data.reminder.REMINDER
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL

/**
 * The triggers Room's annotations cannot declare, dropped and created again on every open so an
 * upgrade never keeps an old body:
 * - each table's rules on `item`, `completion` and `reminder`, standing in for CHECK constraints
 *   (ADR 02, ADR 03);
 * - the sync outbox: every write to a synced table, and every purge, queues the row for export
 *   (ADR 13), so no write path can forget to; a deleted row's base and pending questions go too.
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
            AND (NEW.recurrence_kind IS NULL OR NEW.recurrence_kind IN ('RRULE', 'RULE_SET', 'RANDOM_DAYS', 'RANDOM_WINDOW'))
            AND (NEW.rrule IS NOT NULL) = (NEW.recurrence_kind IS 'RRULE' OR NEW.recurrence_kind IS 'RULE_SET')
            AND (NEW.recurrence_kind IS NOT 'RULE_SET' OR instr(NEW.rrule, char(10)) > 0)
            AND (NEW.rand_min_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_DAYS')
            AND (NEW.rand_max_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_DAYS')
            AND (NEW.rand_min_days IS NULL OR (NEW.rand_min_days >= 1 AND NEW.rand_max_days >= NEW.rand_min_days))
            AND (NEW.window_days IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_start IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_end IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')
            AND (NEW.window_days IS NULL OR (NEW.window_days BETWEEN 1 AND 127 AND NEW.window_end > NEW.window_start)),
        0)
    """.trimIndent()

    /** ADR 02's kind rules, and ADR 03's: a standalone reminder has a status and always a date and time. */
    private val itemRules = """
        NEW.kind IN ('TASK', 'EVENT', 'REMINDER')
        AND (NEW.kind = 'TASK' OR (NEW.due_date IS NULL AND NEW.capacity_rank IS NULL AND NEW.parent_id IS NULL))
        AND (NEW.kind = 'EVENT' OR (NEW.end_date IS NULL AND NEW.end_time IS NULL AND NEW.status IN ('PENDING', 'DONE', 'SKIPPED')))
        AND (NEW.kind <> 'EVENT' OR NEW.status IS NULL)
        AND (NEW.kind <> 'REMINDER' OR (NEW.start_date IS NOT NULL AND NEW.start_time IS NOT NULL))
        AND $recurrenceRules
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
    )

    private val statements: List<String> = buildList {
        for ((table, rule) in rules) for (event in listOf("INSERT", "UPDATE")) {
            val name = "${table}_rules_${event.lowercase()}"
            add("DROP TRIGGER IF EXISTS $name")
            add("CREATE TRIGGER $name BEFORE $event ON $table WHEN NOT ($rule) BEGIN SELECT RAISE(ABORT, '$table: a row breaks its rules'); END")
        }
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

    override fun onOpen(connection: SQLiteConnection) {
        statements.forEach(connection::execSQL)
    }
}
