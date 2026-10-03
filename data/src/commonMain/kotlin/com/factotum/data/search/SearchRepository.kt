package com.factotum.data.search

import androidx.room.Dao
import androidx.room.Query
import com.factotum.data.FactotumDatabase
import com.factotum.data.item.ItemEntity
import com.factotum.data.item.ItemKind
import com.factotum.data.item.MIDNIGHT
import com.factotum.data.item.TaskStatus
import com.factotum.data.sync.readChunked
import com.factotum.data.item.dtstartOf
import com.factotum.data.page.PageEntity
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime

/**
 * One hit. [kind] is ITEM, TRACKER, READING (a Log's note), SPAN (a session's comment), PAGE (a
 * page's title) or BLOCK (a block's text); [text] is what matched, with [snippet] marking the
 * matched words between characters 2 and 3; [owner] names what a Log, a session or a block
 * belongs to, archived or not; [at] is the hit's own time; [done]
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
 * Search (ADR 10) over tasks, events, reminders, habits and activities by name, trackers and pages
 * by name, Logs' notes, sessions' comments and pages' blocks: every term a word's beginning, all terms required, case and
 * accents folded. From two letters on; names first, then text found inside, newest first (owner,
 * 2026-10-03). Nothing deleted, or under something deleted, is found.
 */
internal class SearchRepository(db: FactotumDatabase) {
    private val dao = db.searchDao()
    private val items = db.itemDao()
    private val trackers = db.trackerDao()
    private val times = db.timeDao()
    private val pages = db.pageDao()

    /** Hits for [query] at [now]: an event that has ended by then is marked finished. */
    suspend fun search(query: String, now: LocalDateTime): List<SearchHit> {
        val terms = WORD.findAll(query).map { it.value }.toList()
        if (terms.sumOf { it.length } < 2) return emptyList()
        val hits = dao.matching(terms.joinToString(" ") { "$it*" })
        val byKind = hits.groupBy({ SearchKind.valueOf(it.kind) }, { it.rowKey })
        val readings = readChunked(byKind[SearchKind.READING]) { trackers.readings(it) }.associateBy { it.id }
        val spans = readChunked(byKind[SearchKind.SPAN]) { times.spans(it) }.associateBy { it.id }
        // Items, and the parents above them: what is under something deleted is not found.
        val itemRows = HashMap<String, ItemEntity>()
        var wanted = (byKind[SearchKind.ITEM].orEmpty() + spans.values.map { it.itemId }).toSet()
        while (wanted.isNotEmpty()) {
            readChunked(wanted.toList()) { items.items(it) }.forEach { itemRows[it.id] = it }
            wanted = itemRows.values.mapNotNull { it.parentId }.filter { it !in itemRows }.toSet()
        }
        val trackerIds = byKind[SearchKind.TRACKER].orEmpty() + readings.values.map { it.trackerId } + itemRows.values.mapNotNull { it.trackerId }
        val trackerRows = readChunked(trackerIds.distinct()) { trackers.trackers(it) }.associateBy { it.id }
        val blocks = readChunked(byKind[SearchKind.BLOCK]) { pages.blocks(it) }.associateBy { it.id }
        // Pages, and the pages above them: what is under a trashed page is not found.
        val pageRows = HashMap<String, PageEntity>()
        var wantedPages = (byKind[SearchKind.PAGE].orEmpty() + blocks.values.map { it.pageId }).toSet()
        while (wantedPages.isNotEmpty()) {
            readChunked(wantedPages.toList()) { pages.pages(it) }.forEach { pageRows[it.id] = it }
            wantedPages = pageRows.values.mapNotNull { it.parentId }.filter { it !in pageRows }.toSet()
        }
        // A merge can leave two pages under each other; the walk stops where it would repeat.
        fun pageLive(id: String): Boolean =
            generateSequence(pageRows[id]) { it.parentId?.let(pageRows::get) }.take(pageRows.size).all { it.deletedAt == null } && id in pageRows
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
                SearchKind.PAGE -> h.rowKey.takeIf(::pageLive)?.let { SearchHit(h.kind, it, h.text, h.snippet, null, null, false) }
                SearchKind.BLOCK -> blocks[h.rowKey]?.takeIf { pageLive(it.pageId) }?.let { b ->
                    SearchHit(h.kind, b.id, h.text, h.snippet, pageRows.getValue(b.pageId).title, null, false)
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

/** A word as Tendril and Chronicle split one: letters and digits, with any accent written apart from its letter. */
private val WORD = Regex("[\\p{L}\\p{N}][\\p{L}\\p{N}\\p{M}]*")

/** Newest first; what has no time of its own after what has. */
private val NEWEST = compareBy<SearchHit>({ it.at == null }).thenByDescending { it.at }
