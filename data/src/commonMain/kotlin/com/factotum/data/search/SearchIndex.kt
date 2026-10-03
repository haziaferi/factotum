package com.factotum.data.search

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Fts4
import androidx.room.FtsOptions
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL

/**
 * The search index (ADR 10): one FTS4 table of text, folded by `unicode61` (case and accents),
 * and beside it the key of what each entry came from. Both are this device's alone, kept by
 * triggers on the synced tables and rebuilt from them when their counts disagree: nothing here syncs.
 */
@Fts4(tokenizer = FtsOptions.TOKENIZER_UNICODE61, tokenizerArgs = ["remove_diacritics=2"])
@Entity(tableName = "search_fts")
internal data class SearchTextEntity(
    @PrimaryKey @ColumnInfo(name = "rowid") val doc: Long,
    val text: String,
)

/**
 * What an index entry stands for: its [kind] and the id of the row ([rowKey]). An entry's FTS
 * document id is this row's [doc], so a trigger removes it by key, not by scanning the index.
 */
@Entity(tableName = "search_key", indices = [Index("kind", "row_key", unique = true)])
internal data class SearchKeyEntity(
    @PrimaryKey(autoGenerate = true) val doc: Long,
    val kind: String,
    @ColumnInfo(name = "row_key") val rowKey: String,
)

/** The kinds the index holds; a page's title is a name, a block's text is found inside a page. */
internal enum class SearchKind(val isName: Boolean) { ITEM(true), TRACKER(true), READING(false), SPAN(false), PAGE(true), BLOCK(false) }

/**
 * One table the index reads: its text, and when a row belongs in the index ([live]), both over a
 * row named `$` (NEW or OLD in a trigger, the table in a rebuild). [watched] are the columns whose
 * change re-indexes a row.
 */
private class Source(val kind: SearchKind, val table: String, val text: String, val live: String, val watched: List<String>)

/*
 * ADR 10's sources. A deleted row, a blank text, and an archived activity's or tracker's own name
 * leave the index; what was written under an archived one stays (owner, 2026-10-03). Whether what
 * a hit belongs to is itself deleted is read when searching.
 */
private val SOURCES = listOf(
    Source(SearchKind.ITEM, "item", "$.title", "$.deleted_at IS NULL AND COALESCE($.archived, 0) = 0 AND TRIM($.title) <> ''", listOf("title", "deleted_at", "archived")),
    Source(SearchKind.TRACKER, "tracker", "$.name", "$.deleted_at IS NULL AND $.archived = 0 AND TRIM($.name) <> ''", listOf("name", "deleted_at", "archived")),
    Source(
        SearchKind.READING, "tracker_reading", "TRIM(COALESCE($.label, '') || ' ' || COALESCE($.note, ''))",
        "$.deleted_at IS NULL AND TRIM(COALESCE($.label, '') || ' ' || COALESCE($.note, '')) <> ''", listOf("label", "note", "deleted_at"),
    ),
    Source(SearchKind.SPAN, "time_span", "$.comment", "$.deleted_at IS NULL AND TRIM(COALESCE($.comment, '')) <> ''", listOf("comment", "deleted_at")),
    Source(SearchKind.PAGE, "page", "$.title", "$.deleted_at IS NULL AND TRIM($.title) <> ''", listOf("title", "deleted_at")),
    Source(SearchKind.BLOCK, "block", "$.content", "$.deleted_at IS NULL AND TRIM($.content) <> ''", listOf("content", "deleted_at")),
)

private fun Source.over(row: String, sql: String) = sql.replace("$", row)

private fun Source.remove(row: String) =
    "DELETE FROM search_fts WHERE docid = (SELECT doc FROM search_key WHERE kind = '${kind.name}' AND row_key = $row.id); " +
        "DELETE FROM search_key WHERE kind = '${kind.name}' AND row_key = $row.id;"

private fun Source.add() =
    "INSERT INTO search_key(kind, row_key) SELECT '${kind.name}', NEW.id WHERE ${over("NEW", live)}; " +
        "INSERT INTO search_fts(docid, text) SELECT last_insert_rowid(), ${over("NEW", text)} WHERE ${over("NEW", live)};"

/** The search triggers, made again on every open like every other trigger (ADR 10, `SchemaTriggers`). */
internal val searchTriggers: List<String> = SOURCES.flatMap { s ->
    listOf(
        "DROP TRIGGER IF EXISTS ${s.table}_search_insert",
        "CREATE TRIGGER ${s.table}_search_insert AFTER INSERT ON ${s.table} BEGIN ${s.add()} END",
        "DROP TRIGGER IF EXISTS ${s.table}_search_update",
        "CREATE TRIGGER ${s.table}_search_update AFTER UPDATE OF ${s.watched.joinToString(", ")} ON ${s.table} BEGIN ${s.remove("OLD")} ${s.add()} END",
        "DROP TRIGGER IF EXISTS ${s.table}_search_delete",
        "CREATE TRIGGER ${s.table}_search_delete AFTER DELETE ON ${s.table} BEGIN ${s.remove("OLD")} END",
    )
}

/**
 * Rebuilds the index from its sources when it does not hold as many entries as rows belong in it:
 * a new or upgraded database (whose triggers were dropped for the upgrade, and whose migration
 * copies rows unchanged), a restore, a recovery (ADR 10). Within that, the triggers keep the text
 * current; a crash mid-rebuild leaves counts that differ, so the next open rebuilds again.
 */
internal fun rebuildSearchIfStale(connection: SQLiteConnection) {
    val wanted = SOURCES.sumOf { s -> connection.count("SELECT count(*) FROM ${s.table} WHERE ${s.over(s.table, s.live)}") }
    val held = connection.count("SELECT count(*) FROM search_key")
    if (wanted == held && held == connection.count("SELECT count(*) FROM search_fts")) return
    connection.execSQL("DELETE FROM search_fts")
    connection.execSQL("DELETE FROM search_key")
    for (s in SOURCES) {
        connection.execSQL("INSERT INTO search_key(kind, row_key) SELECT '${s.kind.name}', id FROM ${s.table} WHERE ${s.over(s.table, s.live)}")
        connection.execSQL(
            "INSERT INTO search_fts(docid, text) SELECT k.doc, ${s.over("t", s.text)} FROM ${s.table} t JOIN search_key k ON k.row_key = t.id " +
                "WHERE k.kind = '${s.kind.name}'",
        )
    }
}

private fun SQLiteConnection.count(sql: String): Long = prepare(sql).use { it.step(); it.getLong(0) }
