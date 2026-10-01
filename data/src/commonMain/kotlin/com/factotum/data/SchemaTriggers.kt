package com.factotum.data

import androidx.room.RoomDatabase
import com.factotum.data.item.COMPLETION
import com.factotum.data.item.ITEM
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL

/**
 * The triggers Room's annotations cannot declare, dropped and created again on every open so an
 * upgrade never keeps an old body:
 * - each kind's rules on `item` and `completion`, standing in for CHECK constraints (ADR 02);
 * - the sync outbox: every write to a synced table, and every purge, queues the row for export
 *   (ADR 13), so no write path can forget to; a deleted row's base and pending questions go too.
 */
internal object SchemaTriggers : RoomDatabase.Callback() {

    private val itemRules = """
        NEW.kind IN ('TASK', 'EVENT')
        AND (NEW.kind = 'TASK' OR (NEW.due_date IS NULL AND NEW.status IS NULL AND NEW.capacity_rank IS NULL AND NEW.parent_id IS NULL))
        AND (NEW.kind = 'EVENT' OR (NEW.end_date IS NULL AND NEW.end_time IS NULL AND NEW.status IN ('PENDING', 'DONE', 'SKIPPED')))
    """.trimIndent()

    private val rules = mapOf(
        ITEM to itemRules,
        COMPLETION to "NEW.status IN ('DONE', 'SKIPPED')",
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
