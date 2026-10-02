package com.factotum.data.search

import androidx.room.Dao
import androidx.room.Query
import com.factotum.data.FactotumDatabase
import com.factotum.data.item.ItemEntity
import com.factotum.data.item.ItemKind
import com.factotum.data.item.MIDNIGHT
import com.factotum.data.item.TaskStatus
import com.factotum.data.sync.StagedStore
import com.factotum.data.item.dtstartOf
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

/**
 * One hit. [kind] is ITEM, TRACKER, READING (a Log's note) or SPAN (a session's comment); [text]
 * is what matched, with [snippet] marking the matched words between characters 2 and 3; [owner]
 * names what a Log or a session belongs to, archived or not; [at] is the hit's own time; [done]
 * marks a finished thing: a task or reminder done or skipped, an event that has ended (owner, 2026-10-03).
 */
data class SearchHit(
    val kind: String,
    val id: String,
    val text: String,
    val snippet: String,
    val owner: String?,
    val at: LocalDateTime?,
    val done: Boolean,
)

internal class IndexHit(val kind: String, val rowKey: String, val text: String, val snippet: String)

@Dao
internal interface SearchDao {
    @Query(
        "SELECT k.kind AS kind, k.row_key AS rowKey, f.text AS text, snippet(search_fts, char(2), char(3), '…', -1, 12) AS snippet " +
            "FROM search_fts f JOIN search_key k ON k.doc = f.docid WHERE search_fts MATCH :match",
    )
    suspend fun matching(match: String): List<IndexHit>
}

/**
 * Search (ADR 10) over tasks, events, reminders, habits and activities by name, trackers by name,
 * Logs' notes and sessions' comments: every term a word's beginning, all terms required, case and
 * accents folded. From two letters on; names first, then text found inside, newest first (owner,
 * 2026-10-03). Nothing deleted, or under something deleted, is found.
 */
internal class SearchRepository(db: FactotumDatabase) {
    private val dao = db.searchDao()
    private val items = db.itemDao()
    private val trackers = db.trackerDao()
    private val times = db.timeDao()

    /** Hits for [query] at [now]: an event that has ended by then is marked finished. */
    suspend fun search(query: String, now: LocalDateTime): List<SearchHit> {
        val terms = WORD.findAll(query).map { it.value }.toList()
        if (terms.sumOf { it.length } < 2) return emptyList()
        val hits = dao.matching(terms.joinToString(" ") { "$it*" })
        val byKind = hits.groupBy({ SearchKind.valueOf(it.kind) }, { it.rowKey })
        val readings = chunked(byKind[SearchKind.READING]) { trackers.readings(it) }.associateBy { it.id }
        val spans = chunked(byKind[SearchKind.SPAN]) { times.spans(it) }.associateBy { it.id }
        // Items, and the parents above them: what is under something deleted is not found.
        val itemRows = HashMap<String, ItemEntity>()
        var wanted = (byKind[SearchKind.ITEM].orEmpty() + spans.values.map { it.itemId }).toSet()
        while (wanted.isNotEmpty()) {
            chunked(wanted.toList()) { items.items(it) }.forEach { itemRows[it.id] = it }
            wanted = itemRows.values.mapNotNull { it.parentId }.filter { it !in itemRows }.toSet()
        }
        val trackerIds = byKind[SearchKind.TRACKER].orEmpty() + readings.values.map { it.trackerId } + itemRows.values.mapNotNull { it.trackerId }
        val trackerRows = chunked(trackerIds.distinct()) { trackers.trackers(it) }.associateBy { it.id }
        // An item is gone when deleted, under a deleted parent, or a habit whose tracker is deleted (ADR 06).
        fun itemLive(id: String): Boolean = itemRows[id]?.let {
            it.deletedAt == null && (it.trackerId == null || trackerRows[it.trackerId]?.deletedAt == null) && (it.parentId == null || itemLive(it.parentId))
        } == true

        val found = hits.mapNotNull { h ->
            when (SearchKind.valueOf(h.kind)) {
                SearchKind.ITEM -> itemRows[h.rowKey]?.takeIf { itemLive(it.id) }?.let { i ->
                    val at = i.startDate?.let { dtstartOf(it, i.startTime) } ?: i.dueDate?.let { LocalDateTime(LocalDate.parse(it), MIDNIGHT) }
                    SearchHit(h.kind, i.id, h.text, h.snippet, null, at, i.finishedBy(now))
                }
                SearchKind.TRACKER -> trackerRows[h.rowKey]?.takeIf { it.deletedAt == null }?.let { SearchHit(h.kind, it.id, h.text, h.snippet, null, null, false) }
                SearchKind.READING -> readings[h.rowKey]?.let { r ->
                    trackerRows[r.trackerId]?.takeIf { it.deletedAt == null }?.let { t -> SearchHit(h.kind, r.id, h.text, h.snippet, t.name, LocalDateTime.parse(r.at), false) }
                }
                SearchKind.SPAN -> spans[h.rowKey]?.takeIf { itemLive(it.itemId) }?.let { s ->
                    SearchHit(h.kind, s.id, h.text, h.snippet, itemRows.getValue(s.itemId).title, LocalDateTime.parse(s.startedAt), false)
                }
            }
        }
        val (names, inside) = found.partition { SearchKind.valueOf(it.kind).isName }
        return names.sortedWith(NEWEST.thenBy { it.text }.thenBy { it.id }) + inside.sortedWith(NEWEST.thenBy { it.id })
    }
}

/** A finished thing (owner, 2026-10-03): a task or reminder done or skipped, or a one-off event that has ended (a repeating one goes on). */
private fun ItemEntity.finishedBy(now: LocalDateTime): Boolean = when (kind) {
    ItemKind.EVENT.name -> repeat.kind == null && (endDate ?: startDate)?.let { LocalDateTime(LocalDate.parse(it), LocalTime.parse(endTime ?: startTime ?: "23:59")) < now } == true
    else -> status == TaskStatus.DONE.name || status == TaskStatus.SKIPPED.name
}

/** Reads [ids] in chunks under SQLite's 999 bound variables, as older Android builds have it. */
private suspend fun <T> chunked(ids: List<String>?, read: suspend (List<String>) -> List<T>): List<T> =
    ids.orEmpty().chunked(StagedStore.CHUNK).flatMap { read(it) }

/** A word as Tendril and Chronicle split one: letters and digits, with any accent written apart from its letter. */
private val WORD = Regex("[\\p{L}\\p{N}][\\p{L}\\p{N}\\p{M}]*")

/** Newest first; what has no time of its own after what has. */
private val NEWEST = compareBy<SearchHit>({ it.at == null }).thenByDescending { it.at }
