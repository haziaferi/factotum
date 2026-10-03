package com.factotum.data.page

import com.factotum.core.page.Placed
import com.factotum.core.page.keyBetween
import com.factotum.core.page.outlineOf
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.sync.RecordCodec
import com.factotum.data.sync.readChunked
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

data class Page(val id: String, val title: String, val icon: String?, val parentId: String?, val trashed: Boolean)

/** A block's type-specific attributes (Tendril's), each meaning something for some types only. */
data class BlockAttrs(
    val checked: Boolean? = null,
    val codeLanguage: String? = null,
    val calloutIcon: String? = null,
    val calloutColor: Long? = null,
    val mentionedPageId: String? = null,
    val referencedBlockId: String? = null,
    val toggleExpanded: Boolean? = null,
)

/** One block as drawn: [depth] under its parents, in outline order. */
data class BlockView(val id: String, val depth: Int, val type: BlockType, val content: String, val spans: String?, val parentId: String?, val attrs: BlockAttrs)

data class Revision(val id: Long, val reason: String, val title: String, val blockCount: Int, val at: Long, val noticeId: String?)

/** "Replaced by a sync" on [pageId]: [rowId] is the page (its title) or a block (its text), and [lostText] what it said. */
data class Notice(val id: String, val pageId: String, val rowId: String, val lostText: String, val lostSpans: String?)

/**
 * Pages and their blocks (Tendril's, ADR 12, per-row+revive): one row per block, ordered by a
 * fractional key; a page's title or a block's text that two devices change apart keeps the later
 * and puts the earlier in History with a notice; a later edit to any part of a trashed page, or of
 * a deleted block, brings it back (owner, 2026-10-03), and a page brings its trashed parents.
 *
 * A merge can leave what one device would refuse: two pages under each other, or a live page under
 * a trashed one. Such a page is shown at the top ([children]), so nothing is out of reach.
 */
internal class PageRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    /** The wall clock History's times are read from, in milliseconds. */
    private val wallMillis: () -> Long,
) {
    private val dao = db.pageDao()
    private val sync = db.syncDao()
    private val clock = writes.clock

    suspend fun create(title: String, parentId: String? = null, icon: String? = null): String {
        val id = newId()
        writes.write({
            parentId?.let { live(it) }
            mapOf(PAGE to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(PAGE, id, mapOf(
                MADE to Group(s, mapOf("kind" to "PAGE")),
                PAGE_TITLE to Group(s, mapOf("title" to title, "icon" to icon)),
                PLACE to Group(s, mapOf("parent_id" to parentId)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun rename(id: String, title: String) {
        snapshotIfDue(id)
        changeTitle(id, "title" to title)
    }

    suspend fun setIcon(id: String, icon: String?) = changeTitle(id, "icon" to icon)

    /** Moves [id] under [parentId], or to the top; never under itself or one of its own sub-pages. */
    suspend fun move(id: String, parentId: String?) = writes.write({
        live(id)
        if (parentId != null) {
            live(parentId)
            val pages = dao.allPages().associateBy { it.id }
            require(generateSequence(parentId) { pages[it]?.parentId }.take(pages.size + 1).none { it == id }) { "a page cannot go under itself" }
        }
        mapOf(PAGE to listOf(id))
    }) { store, _ -> store.put(requireNotNull(store.row(id)).edit(PLACE, clock.tick(), mapOf("parent_id" to parentId))) }

    /** Trashes [id] and every live page under it, with one stamp, so a restore brings the branch back together (owner, 2026-10-03). */
    suspend fun trash(id: String) = writes.write({
        live(id)
        mapOf(PAGE to listOf(id) + branch(id, dao.allPages()) { true }.filter { it.deletedAt == null }.map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        targets.getValue(PAGE).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to s.hlc))) }
    }

    /** Restores [id] and the pages under it that went to the trash with it. */
    suspend fun restore(id: String) = writes.write({
        val pages = dao.allPages()
        val page = requireNotNull(pages.firstOrNull { it.id == id && it.deletedAt != null }) { "page $id is not in the trash" }
        mapOf(PAGE to listOf(id) + branch(id, pages) { it.deletedAt == page.deletedAt }.map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        targets.getValue(PAGE).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to null))) }
    }

    /**
     * "Delete forever", from the trash: the page and the trashed pages under it, for good, with
     * their blocks and labels. A live page a sync left under them is moved to the top, not taken.
     */
    suspend fun purge(id: String) {
        var gone = emptyList<String>()
        var kept = emptyList<String>()
        writes.write({
            val pages = dao.allPages()
            require(pages.any { it.id == id && it.deletedAt != null }) { "only a page in the trash is deleted forever" }
            val trashed = branch(id, pages) { it.deletedAt != null }
            gone = listOf(id) + trashed.map { it.id }
            val inside = gone.toSet()
            kept = pages.filter { it.deletedAt == null && it.parentId in inside }.map { it.id }
            mapOf(PAGE to gone + kept)
        }) { store, _ ->
            if (kept.isNotEmpty()) {
                val s = clock.tick()
                kept.forEach { store.put(requireNotNull(store.row(it)).edit(PLACE, s, mapOf("parent_id" to null))) }
            }
            gone.forEach { writes.merger.purge(store, it) }
        }
    }

    suspend fun page(id: String): Page? = dao.pages(listOf(id)).singleOrNull()?.toPage()

    /**
     * The live pages shown directly under [parentId], or at the top, by title (Tendril). At the
     * top too: a page whose parent is missing or trashed, or which a merge put on a cycle.
     */
    suspend fun children(parentId: String? = null): List<Page> {
        val pages = dao.allPages().associateBy { it.id }
        return pages.values.filter { it.deletedAt == null && shownUnder(it, pages) == parentId }
            .sortedWith(compareBy({ it.title.lowercase() }, { it.id })).map { it.toPage() }
    }

    /** The trash: each trashed branch by its top page; a branch a merge closed into a cycle by its lowest id. */
    suspend fun trashed(): List<Page> {
        val pages = dao.allPages().associateBy { it.id }
        return pages.values.filter { it.deletedAt != null && (pages[it.parentId]?.deletedAt == null || cycleOf(it, pages).minOrNull() == it.id) }
            .sortedBy { it.id }.map { it.toPage() }
    }

    /** Adds a block to [pageId] after its sibling [after] (first when null), under the block [parent]. */
    suspend fun addBlock(pageId: String, after: String? = null, parent: String? = null, type: BlockType = BlockType.PARAGRAPH, content: String = "", spans: String? = null): String {
        val id = newId()
        snapshotIfDue(pageId)
        var key = ""
        writes.write({
            live(pageId)
            val blocks = dao.blocksOf(pageId).filter { it.deletedAt == null }
            parent?.let { p -> require(blocks.any { it.id == p }) { "no block $p on page $pageId" } }
            key = keyAfter(blocks.filter { it.parentBlockId == parent }, after)
            mapOf(BLOCK to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(BLOCK, id, mapOf(
                MADE to Group(s, mapOf("page_id" to pageId)),
                BLOCK_TYPE to Group(s, mapOf("type" to type.name)),
                BLOCK_TEXT to Group(s, mapOf("content" to content, "spans" to spans)),
                PLACE to Group(s, mapOf("parent_block_id" to parent, "sort_key" to key)),
                ATTRS to Group(s, attrValues(BlockAttrs())),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun setText(id: String, content: String, spans: String? = null) {
        snapshotIfDue(block(id).pageId)
        writes.edit(BLOCK, id, BLOCK_TEXT) { mapOf("content" to content, "spans" to spans) }
    }

    suspend fun setType(id: String, type: BlockType) = writes.edit(BLOCK, id, BLOCK_TYPE) { mapOf("type" to type.name) }

    suspend fun setAttrs(id: String, attrs: BlockAttrs) = writes.edit(BLOCK, id, ATTRS) { attrValues(attrs) }

    /** Moves block [id] after its sibling [after] (first when null), under the block [parent]; never under itself. */
    suspend fun moveBlock(id: String, after: String? = null, parent: String? = null) {
        val pageId = block(id).pageId
        snapshotIfDue(pageId)
        var key = ""
        writes.write({
            live(pageId)
            val blocks = dao.blocksOf(pageId).filter { it.deletedAt == null }
            val byId = blocks.associateBy { it.id }
            require(id in byId) { "no block $id" }
            if (parent != null) {
                require(parent in byId) { "no block $parent on page $pageId" }
                require(generateSequence(parent) { byId[it]?.parentBlockId }.take(blocks.size + 1).none { it == id }) { "a block cannot go under itself" }
            }
            key = keyAfter(blocks.filter { it.parentBlockId == parent && it.id != id }, after)
            mapOf(BLOCK to listOf(id))
        }) { store, _ -> store.put(requireNotNull(store.row(id)).edit(PLACE, clock.tick(), mapOf("parent_block_id" to parent, "sort_key" to key))) }
    }

    suspend fun deleteBlock(id: String) {
        snapshotIfDue(block(id).pageId)
        writes.edit(BLOCK, id, GONE) { s -> mapOf("deleted_at" to s.hlc) }
    }

    /** A page's live blocks in outline order (Tendril's `outlineOf`). */
    suspend fun outline(pageId: String): List<BlockView> {
        val blocks = dao.blocksOf(pageId).filter { it.deletedAt == null }.associateBy { it.id }
        return outlineOf(blocks.values.map { Placed(it.id, it.parentBlockId, it.sortKey) }).map { e ->
            val b = blocks.getValue(e.id)
            BlockView(b.id, e.depth, BlockType.valueOf(b.type), b.content, b.spans, b.parentBlockId, b.attrs())
        }
    }

    suspend fun revisions(pageId: String): List<Revision> =
        dao.revisionsOf(pageId).map { Revision(it.id, it.reason, it.title, it.blockCount.toInt(), it.at, it.noticeId) }

    /** Brings back the History version [revisionId]: the page's title and its blocks as they were, by their ids; blocks it did not have are deleted. */
    suspend fun restoreRevision(revisionId: Long) {
        val revision = requireNotNull(dao.revision(revisionId)) { "no revision $revisionId" }
        val wanted = decodeBlocks(revision.blocksJson).associateBy { it.getValue("id").jsonPrimitive.content }
        keep(revision.pageId, "RESTORE", null)
        writes.write({ mapOf(PAGE to listOf(revision.pageId), BLOCK to dao.blocksOf(revision.pageId).map { it.id }) }) { store, targets ->
            val s = clock.tick()
            val page = requireNotNull(store.row(revision.pageId))
            store.put(page.edit(PAGE_TITLE, s, page.groups.getValue(PAGE_TITLE).values + ("title" to revision.title)))
            for (id in targets.getValue(BLOCK)) {
                val row = requireNotNull(store.row(id))
                val b = wanted[id]
                if (b == null) {
                    if (row.groups.getValue(GONE).values["deleted_at"] == null) store.put(row.edit(GONE, s, mapOf("deleted_at" to s.hlc)))
                    continue
                }
                var r = row
                fun set(group: String, values: Map<String, Any?>) {
                    if (values.any { (k, v) -> r.groups.getValue(group).values[k] != v }) r = r.edit(group, s, values)
                }
                set(BLOCK_TYPE, mapOf("type" to b.text("type")))
                set(BLOCK_TEXT, mapOf("content" to b.text("content"), "spans" to b.text("spans")))
                set(PLACE, mapOf("parent_block_id" to b.text("parent"), "sort_key" to b.text("key")))
                set(ATTRS, attrValues(b.attrs()))
                set(GONE, mapOf("deleted_at" to null))
                store.put(r)
            }
        }
    }

    suspend fun notices(pageId: String): List<Notice> = dao.openNotices(pageId).map { Notice(it.id, it.pageId, it.rowId, it.lostText, it.lostSpans) }

    /** Dismisses [noticeId], on every device (owner, 2026-10-03). */
    suspend fun dismiss(noticeId: String) = writes.edit(PAGE_NOTICE, noticeId, DISMISSED) { s -> mapOf("dismissed_at" to s.hlc) }

    /**
     * After every import: each version a sync replaced goes into its page's History with a notice
     * (ADR 12), and a trashed page or a deleted block that a later edit touched comes back (revive),
     * with its trashed parents.
     */
    suspend fun settle() {
        sync.lost().forEach { keepLost(it.id) }
        revive()
    }

    /**
     * One replaced version, in one transaction: its MERGE revision, its notice, and its removal
     * from `sync_lost`. Nothing is kept when the text it lost to says the same (an icon or a
     * format changed apart), or when its notice has already been kept on this device.
     */
    private suspend fun keepLost(lostId: Long) {
        var create: Row? = null
        writes.write({
            val lost = sync.lost().single { it.id == lostId }
            sync.clearLost(listOf(lostId))
            val loser = RecordCodec.decodeGroup(lost.groupJson)
            val isTitle = lost.tbl == PAGE
            val text = loser.values[if (isTitle) "title" else "content"] as String
            val spans = if (isTitle) null else loser.values["spans"] as String?
            val block = if (isTitle) null else dao.blocks(listOf(lost.rowId)).singleOrNull()
            val page = dao.pages(listOf(block?.pageId ?: lost.rowId)).singleOrNull()
            val current = if (isTitle) page?.title else block?.content
            val notice = noticeId(lost.rowId, loser.stamp)
            if (page == null || current == text || dao.revisionsOf(page.id).any { it.noticeId == notice }) return@write emptyMap()
            val blocks = dao.blocksOf(page.id).filter { it.deletedAt == null || it.id == lost.rowId }
                .map { if (it.id == lost.rowId) it.copy(content = text, spans = spans, deletedAt = null) else it }
            dao.addRevision(PageRevisionEntity(0, page.id, "MERGE", if (isTitle) text else page.title, JsonArray(blocks.map { it.json() }).toString(), blocks.size.toLong(), wallMillis(), notice))
            dao.keepRevisions(page.id, KEPT)
            // Stamped with the lost version's own stamp: two devices write the same notice, and a
            // copy written late never undoes a dismissal the other has made since.
            create = Row(PAGE_NOTICE, notice, mapOf(
                MADE to Group(loser.stamp, mapOf("page_id" to page.id, "row_id" to lost.rowId, "lost_text" to text, "lost_spans" to spans)),
                DISMISSED to Group(loser.stamp, mapOf("dismissed_at" to null)),
            ))
            mapOf(PAGE_NOTICE to listOf(notice))
        }) { store, _ -> create?.let { if (store.row(it.id) == null) writes.merger.created(store, it) } }
    }

    /**
     * A trashed page or a deleted block comes back when a part of it was edited after its deletion:
     * for a page, its title or place, its blocks, its labels, or a live sub-page moved or made under
     * it; for a block, any of its groups. A page brings back its trashed parents.
     *
     * A revival is stamped just above the deletion it undoes, (its time, its device + "~"), not with a
     * fresh tick: every device writes the same row, any later trash or purge still outranks it, and a
     * page that comes back is never kept from a purge made after the edit that brought it back.
     */
    private suspend fun revive() {
        var back = emptyMap<String, Stamp>()
        writes.write({
            val pages = dao.allPages()
            val trashed = pages.filter { it.deletedAt != null }
            val blocks = readChunked(trashed.map { it.id }) { dao.blocksOfPages(it) }.groupBy { it.pageId }
            val labels = readChunked(trashed.map { it.id }) { dao.labelsOfPages(it) }.groupBy { it.pageId }
            val under = pages.filter { it.deletedAt == null }.groupBy { it.parentId }
            val byId = pages.associateBy { it.id }
            val found = HashMap<String, Stamp>()
            for (b in dao.deletedBlocks()) {
                if (b.edits().max() > Stamp(b.goneHlc, b.goneDevice)) found[b.id] = Stamp(b.goneHlc, b.goneDevice)
            }
            for (p in trashed) {
                val parts = listOf(Stamp(p.titleHlc, p.titleDevice), Stamp(p.placeHlc, p.placeDevice)) +
                    blocks[p.id].orEmpty().flatMap { it.edits() + Stamp(it.goneHlc, it.goneDevice) } +
                    labels[p.id].orEmpty().flatMap { listOf(Stamp(it.madeHlc, it.madeDevice), Stamp(it.goneHlc, it.goneDevice)) } +
                    under[p.id].orEmpty().map { Stamp(it.placeHlc, it.placeDevice) }
                val newest = parts.max()
                for (q in generateSequence(p) { byId[it.parentId] }.take(pages.size)) {
                    val gone = Stamp(q.goneHlc, q.goneDevice)
                    if (q.deletedAt != null && gone < newest) found[q.id] = gone
                }
            }
            back = found
            mapOf(PAGE to found.keys.filter { it in byId }, BLOCK to found.keys.filter { it !in byId })
        }) { store, _ ->
            for ((id, gone) in back) {
                store.put(requireNotNull(store.row(id)).edit(GONE, Stamp(gone.hlc, gone.device + "~"), mapOf("deleted_at" to null)))
            }
        }
    }

    private suspend fun changeTitle(id: String, change: Pair<String, String?>) = writes.write({
        live(id)
        mapOf(PAGE to listOf(id))
    }) { store, _ ->
        val row = requireNotNull(store.row(id))
        store.put(row.edit(PAGE_TITLE, clock.tick(), row.groups.getValue(PAGE_TITLE).values + change))
    }

    /** Keeps [pageId] in History as it is now; fifty kept. */
    private suspend fun keep(pageId: String, reason: String, notice: String?) {
        val page = dao.pages(listOf(pageId)).singleOrNull() ?: return
        val blocks = dao.blocksOf(pageId).filter { it.deletedAt == null }
        dao.addRevision(PageRevisionEntity(0, pageId, reason, page.title, JsonArray(blocks.map { it.json() }).toString(), blocks.size.toLong(), wallMillis(), notice))
        dao.keepRevisions(pageId, KEPT)
    }

    /** An EDIT revision before a change, unless one was kept in the last ten minutes (Tendril). */
    private suspend fun snapshotIfDue(pageId: String) {
        val last = dao.revisionsOf(pageId).firstOrNull { it.reason == "EDIT" }
        if (last == null || wallMillis() - last.at >= EDIT_EVERY_MS) keep(pageId, "EDIT", null)
    }

    private suspend fun block(id: String) = requireNotNull(dao.blocks(listOf(id)).singleOrNull()) { "no block $id" }

    private suspend fun live(id: String) = requireNotNull(dao.pages(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no page $id" }
}

private const val KEPT = 50
private const val EDIT_EVERY_MS = 10 * 60 * 1000L

/**
 * The key after the sibling [after] (first when null) among [siblings]. Siblings two devices placed
 * at one key read in id order, so the new key goes after the last of them.
 */
private fun keyAfter(siblings: List<BlockEntity>, after: String?): String {
    val ordered = siblings.sortedWith(compareBy({ it.sortKey }, { it.id }))
    val before = after?.let { a -> requireNotNull(ordered.firstOrNull { it.id == a }) { "no block $a here" }.sortKey }
    return keyBetween(before, ordered.firstOrNull { before == null || it.sortKey > before }?.sortKey)
}

/** Every page under [id], however deep, through pages that [through] lets the walk pass. */
private fun branch(id: String, pages: List<PageEntity>, through: (PageEntity) -> Boolean): List<PageEntity> {
    val children = pages.groupBy { it.parentId }
    val out = mutableListOf<PageEntity>()
    val seen = mutableSetOf(id)
    fun walk(of: String) {
        for (c in children[of].orEmpty()) if (through(c) && seen.add(c.id)) { out += c; walk(c.id) }
    }
    walk(id)
    return out
}

/** The pages on [page]'s cycle, when following its parents comes back to it (only a merge of two moves can make one); else none. */
private fun cycleOf(page: PageEntity, pages: Map<String, PageEntity>): List<String> {
    val walk = generateSequence(pages[page.parentId]) { pages[it.parentId] }.take(pages.size).map { it.id }.toList()
    val back = walk.indexOf(page.id)
    return if (back < 0) emptyList() else walk.take(back + 1)
}

private fun onCycle(page: PageEntity, pages: Map<String, PageEntity>) = cycleOf(page, pages).isNotEmpty()

/** Where a live page is shown: under its parent while that is live, else at the top. */
private fun shownUnder(page: PageEntity, pages: Map<String, PageEntity>): String? =
    page.parentId?.takeIf { pages[it]?.deletedAt == null && it in pages && !onCycle(page, pages) }

private fun BlockEntity.edits() = listOf(Stamp(typeHlc, typeDevice), Stamp(textHlc, textDevice), Stamp(placeHlc, placeDevice), Stamp(attrsHlc, attrsDevice))

private fun PageEntity.toPage() = Page(id, title, icon, parentId, deletedAt != null)

private fun BlockEntity.attrs() = BlockAttrs(checked, codeLanguage, calloutIcon, calloutColor, mentionedPageId, referencedBlockId, toggleExpanded)

private fun attrValues(a: BlockAttrs) = mapOf(
    "checked" to a.checked, "code_language" to a.codeLanguage, "callout_icon" to a.calloutIcon, "callout_color" to a.calloutColor,
    "mentioned_page_id" to a.mentionedPageId, "referenced_block_id" to a.referencedBlockId, "toggle_expanded" to a.toggleExpanded,
)

private fun String?.json() = this?.let(::JsonPrimitive) ?: JsonNull

private fun BlockEntity.json() = JsonObject(mapOf(
    "id" to JsonPrimitive(id), "type" to JsonPrimitive(type), "content" to JsonPrimitive(content), "spans" to spans.json(),
    "parent" to parentBlockId.json(), "key" to JsonPrimitive(sortKey), "checked" to (checked?.let(::JsonPrimitive) ?: JsonNull),
    "code_language" to codeLanguage.json(), "callout_icon" to calloutIcon.json(), "callout_color" to (calloutColor?.let(::JsonPrimitive) ?: JsonNull),
    "mentioned_page_id" to mentionedPageId.json(), "referenced_block_id" to referencedBlockId.json(),
    "toggle_expanded" to (toggleExpanded?.let(::JsonPrimitive) ?: JsonNull),
))

private fun decodeBlocks(text: String): List<JsonObject> = Json.parseToJsonElement(text).jsonArray.map { it.jsonObject }

private fun JsonObject.text(key: String) = this[key]?.jsonPrimitive?.contentOrNull

private fun JsonObject.attrs() = BlockAttrs(
    this["checked"]?.jsonPrimitive?.booleanOrNull, text("code_language"), text("callout_icon"), this["callout_color"]?.jsonPrimitive?.longOrNull,
    text("mentioned_page_id"), text("referenced_block_id"), this["toggle_expanded"]?.jsonPrimitive?.booleanOrNull,
)
