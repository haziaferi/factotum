package com.factotum.data.page

import com.factotum.core.page.keyBetween
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.sync.StagedStore
import com.factotum.data.sync.readChunked

/**
 * A page card's page: live, in the Trash, deleted for good (owner, 2026-10-03: the card stays
 * either way), or not on this device yet, as when it waits on a page above it.
 */
enum class PageState { LIVE, TRASHED, DELETED, ABSENT }

/**
 * A card as drawn. [parentId] is its mind-map parent while that is a live card of this board, else
 * null; [pageState] is a page card's page's state.
 */
data class CanvasNode(
    val id: String, val type: NodeType, val x: Double, val y: Double, val width: Double?, val height: Double?, val text: String,
    val hue: Int?, val parentId: String?, val folded: Boolean, val structure: CanvasStructure?, val pageRef: String?, val pageState: PageState?,
)

data class CanvasEdge(val id: String, val from: String, val to: String, val direction: EdgeDirection, val label: String?)

/**
 * Tendril's canvas (ADR 12, slice 12c): a canvas page, its cards and the lines between them, each a
 * row synced per ADR 01 group. Moving a card carries its mind-map subtree; deleting one deletes its
 * lines, lifts its children to its parent, and takes the frames that follow it, in one stamp, so a
 * later edit that brings it back brings them back too (owner, 2026-10-03).
 */
internal class CanvasRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val pages: PageRepository,
) {
    private val dao = db.canvasDao()
    private val pageDao = db.pageDao()
    private val syncDao = db.syncDao()
    private val clock = writes.clock

    /** A new canvas page under [parentId], laid out freely. */
    suspend fun create(title: String, parentId: String? = null): String {
        val id = newId()
        writes.write({
            parentId?.let { livePage(it) }
            mapOf(PAGE to listOf(id), PAGE_CANVAS to listOf(canvasShellId(id)))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, newPageRow(id, s, title, null, parentId, CANVAS_KIND))
            writes.merger.created(store, Row(PAGE_CANVAS, canvasShellId(id), mapOf(
                MADE to Group(s, mapOf("page_id" to id)),
                LAYOUT to Group(s, mapOf("structure" to CanvasStructure.FREE.name)),
            )))
        }
        return id
    }

    suspend fun structure(canvasId: String): CanvasStructure = CanvasStructure.valueOf(shell(canvasId).structure)

    suspend fun setStructure(canvasId: String, structure: CanvasStructure) = write(canvasId, PAGE_CANVAS, canvasShellId(canvasId), { shell(canvasId) }) {
        it.edit(LAYOUT, clock.tick(), mapOf("structure" to structure.name))
    }

    /** A text card at ([x], [y]), on top; under [parent] as a mind-map child, which unfolds the parent. */
    suspend fun addText(canvasId: String, x: Double, y: Double, text: String = "", parent: String? = null): String =
        add(canvasId, NodeType.TEXT, x, y, text, null, null, null, parent)

    /** A card showing [pageId]. */
    suspend fun addPageCard(canvasId: String, pageId: String, x: Double, y: Double): String =
        add(canvasId, NodeType.PAGE_EMBED, x, y, "", pageId, null, null, null) { livePage(pageId) }

    /** A frame: what lies wholly inside its box is in it (Tendril's rule, worked out by the screen that draws the boxes). */
    suspend fun addFrame(canvasId: String, x: Double, y: Double, width: Double, height: Double, label: String = ""): String {
        size(width, height)
        return add(canvasId, NodeType.FRAME, x, y, label, null, width, height, null)
    }

    /** The live cards, bottom to top (frames first, as Tendril draws them, then by stacking key). */
    suspend fun nodes(canvasId: String): List<CanvasNode> {
        val nodes = dao.nodesOf(canvasId).filter { it.deletedAt == null }
        val byId = nodes.associateBy { it.id }
        val refIds = nodes.mapNotNull { it.pageRef }.distinct()
        val refs = readChunked(refIds) { pageDao.pages(it) }.associateBy { it.id }
        val purged = readChunked(refIds.filter { it !in refs }) { syncDao.purges(it) }.map { it.id }.toSet()
        return nodes.sortedWith(compareBy({ it.type != NodeType.FRAME.name }, { it.zKey }, { it.id })).map { n ->
            CanvasNode(
                n.id, NodeType.valueOf(n.type), n.x, n.y, n.width, n.height, n.text, n.hue?.toInt(), shownParent(n, byId), n.folded,
                n.structure?.let(CanvasStructure::valueOf), n.pageRef,
                n.pageRef?.let { r -> refs[r]?.let { if (it.deletedAt == null) PageState.LIVE else PageState.TRASHED } ?: if (r in purged) PageState.DELETED else PageState.ABSENT },
            )
        }
    }

    /** The live lines whose two ends are live cards. */
    suspend fun edges(canvasId: String): List<CanvasEdge> {
        val live = dao.nodesOf(canvasId).filter { it.deletedAt == null }.map { it.id }.toSet()
        return dao.edgesOf(canvasId).filter { it.deletedAt == null && it.fromNodeId in live && it.toNodeId in live }.sortedBy { it.id }
            .map { CanvasEdge(it.id, it.fromNodeId, it.toNodeId, EdgeDirection.valueOf(it.direction), it.label) }
    }

    /**
     * Moves card [id] to ([x], [y]), carrying its mind-map subtree by the same distance (frames do not
     * ride along), in one write: the move is written when the card is dropped, not on every step. A
     * carried card's move is the app's, not a person's, so it never brings back one deleted elsewhere.
     */
    suspend fun moveNode(id: String, x: Double, y: Double) {
        finite(x, y)
        pages.snapshotIfDue(liveNode(id).pageId)
        var moves = emptyMap<String, Pair<Double, Double>>()
        writeNodes({
            val node = liveNode(id)
            val nodes = dao.nodesOf(node.pageId).filter { it.deletedAt == null }
            val dx = x - node.x
            val dy = y - node.y
            moves = (listOf(node) + carried(node, nodes)).associate { it.id to (it.x + dx to it.y + dy) }
            moves.keys.toList()
        }) { store, s ->
            moves.forEach { (n, at) -> store.put(requireNotNull(store.row(n)).edit(NODE_AT, if (n == id) s else automatic(s), mapOf("x" to at.first, "y" to at.second))) }
        }
    }

    /**
     * Moves several cards of one board at once, as a tidy or a frame carrying its contents does: the
     * app's moves, which never bring back a card deleted elsewhere; each card keeps its own later
     * position (owner, 2026-10-03).
     */
    suspend fun moveNodes(canvasId: String, positions: Map<String, Pair<Double, Double>>) {
        positions.values.forEach { finite(it.first, it.second) }
        shell(canvasId)
        pages.snapshotIfDue(canvasId)
        writeNodes({
            positions.keys.forEach { require(liveNode(it).pageId == canvasId) { "card $it is not on $canvasId" } }
            positions.keys.toList()
        }) { store, s -> positions.forEach { (n, at) -> store.put(requireNotNull(store.row(n)).edit(NODE_AT, automatic(s), mapOf("x" to at.first, "y" to at.second))) } }
    }

    /** A card's width ([height] null: its height follows its text), or a frame's size. */
    suspend fun resize(id: String, width: Double?, height: Double?) = node(id, NODE_SIZE, { n ->
        if (n.type == NodeType.FRAME.name) size(requireNotNull(width), requireNotNull(height)) else require(height == null && (width == null || width > 0 && width.isFinite())) { "a card has a width only" }
    }) { mapOf("width" to width, "height" to height) }

    /** A text card's text or a frame's label. */
    suspend fun setText(id: String, text: String) = node(id, NODE_TEXT, { n -> require(n.type != NodeType.PAGE_EMBED.name) { "a page card shows its page's title" } }) { mapOf("text" to text) }

    suspend fun setHue(id: String, hue: Int?) = node(id, LOOK, { require(hue == null || hue in 0..359) { "a hue is 0 to 359" } }) { mapOf("hue" to hue?.toLong()) }

    suspend fun setFolded(id: String, folded: Boolean) = node(id, NODE_FOLD, {}) { mapOf("folded" to folded) }

    /** A subtree's own layout, or the board's (null). */
    suspend fun setNodeStructure(id: String, structure: CanvasStructure?) = node(id, NODE_STRUCTURE, {}) { mapOf("structure" to structure?.name) }

    /** Puts card [id] under [parent] in the mind map, or at its root; never under itself, one of its own, or a frame. */
    suspend fun setParent(id: String, parent: String?) = node(id, NODE_TREE, { n ->
        if (parent != null) {
            val p = liveNode(parent)
            require(p.pageId == n.pageId && p.type != NodeType.FRAME.name) { "a card goes under a card of its board" }
            require(parent != id && descendants(id, dao.nodesOf(n.pageId).filter { it.deletedAt == null }).none { it.id == parent }) { "a card cannot go under itself" }
        }
    }) { mapOf("parent_id" to parent) }

    /** Puts card [id] on top of the board, the stacking a later "bring to front" would write. */
    suspend fun bringToFront(id: String) {
        var key = ""
        node(id, NODE_Z, { n -> key = keyBetween(dao.nodesOf(n.pageId).filter { it.deletedAt == null && it.id != id }.maxOfOrNull { it.zKey }, null) }) { mapOf("z_key" to key) }
    }

    /**
     * Deletes card [id] in one stamp: its lines, and the frames that follow it, go with it; its
     * children are lifted to its parent (Tendril). A later edit to it anywhere brings back it and
     * what was deleted with it (owner, 2026-10-03).
     */
    suspend fun deleteNode(id: String) {
        var lines = emptyList<String>()
        var frames = emptyList<String>()
        var children = emptyList<String>()
        var lifted: String? = null
        val canvasId = liveNode(id).pageId
        pages.snapshotIfDue(canvasId)
        writes.write({
            val node = liveNode(id)
            val nodes = dao.nodesOf(node.pageId).filter { it.deletedAt == null }
            frames = nodes.filter { it.parentId == id && it.type == NodeType.FRAME.name }.map { it.id }
            val going = (frames + id).toSet()
            lines = dao.edgesOf(node.pageId).filter { it.deletedAt == null && (it.fromNodeId in going || it.toNodeId in going) }.map { it.id }
            children = nodes.filter { it.parentId == id && it.type != NodeType.FRAME.name }.map { it.id }
            // A parent that is one of its own children (a cycle a merge made) lifts them to the root.
            lifted = node.parentId?.takeIf { p -> p !in children && nodes.any { it.id == p } }
            mapOf(CANVAS_NODE to listOf(id) + frames + children, CANVAS_EDGE to lines)
        }) { store, _ ->
            val s = clock.tick()
            (listOf(id) + frames + lines).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to s.hlc))) }
            // The lift is the deletion's doing: stamped as the app's, so it is no edit that brings anything back,
            // and a revival of the card can tell which children to take back.
            children.forEach { store.put(requireNotNull(store.row(it)).edit(NODE_TREE, automatic(s), mapOf("parent_id" to lifted))) }
        }
    }

    /** A line from card [from] to card [to] of one board; never from a card to itself. */
    suspend fun addEdge(from: String, to: String, direction: EdgeDirection = EdgeDirection.NONE, label: String? = null): String {
        val id = newId()
        var canvasId = ""
        pages.snapshotIfDue(liveNode(from).pageId)
        writes.write({
            require(from != to) { "a line joins two cards" }
            val a = liveNode(from)
            require(liveNode(to).pageId == a.pageId) { "a line joins cards of one board" }
            canvasId = a.pageId
            mapOf(CANVAS_EDGE to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(CANVAS_EDGE, id, mapOf(
                MADE to Group(s, mapOf("page_id" to canvasId, "from_node_id" to from, "to_node_id" to to)),
                ARROW to Group(s, mapOf("direction" to direction.name)),
                EDGE_LABEL to Group(s, mapOf("label" to label)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun setDirection(id: String, direction: EdgeDirection) = edge(id, ARROW) { mapOf("direction" to direction.name) }

    suspend fun setLabel(id: String, label: String?) = edge(id, EDGE_LABEL) { mapOf("label" to label?.takeIf { it.isNotBlank() }) }

    suspend fun deleteEdge(id: String) = edge(id, GONE) { s -> mapOf("deleted_at" to s.hlc) }

    /**
     * After every import, on every canvas (owner, 2026-10-03): a deleted card comes back when one of
     * its parts, a line drawn to it, or a child put under it is stamped after its deletion, and brings
     * back what was deleted with it; a deleted line comes back when it was edited after its deletion,
     * with any end deleted before that edit. A revival is stamped just above the deletion it undoes,
     * as a revived page is, so every device writes the same row.
     */
    suspend fun settle() {
        var back = emptyMap<String, Stamp>()
        var lifts = emptyMap<String, Pair<String, Stamp>>()
        writes.write({
            val deletedNodes = dao.deletedNodes()
            val deletedEdges = dao.deletedEdges()
            if (deletedNodes.isEmpty() && deletedEdges.isEmpty()) return@write emptyMap()
            val boards = (deletedNodes.map { it.pageId } + deletedEdges.map { it.pageId }).distinct()
            val nodes = readChunked(boards) { dao.nodesOfPages(it) }
            val edges = readChunked(boards) { dao.edgesOfPages(it) }
            val gone = nodes.filter { it.deletedAt != null }.associateBy { it.id }
            val found = HashMap<String, Stamp>()
            fun touch(nodeId: String, at: Stamp) {
                val n = gone[nodeId] ?: return
                if (at > n.gone()) found[n.id] = n.gone()
            }
            for (n in gone.values) latestByHand(n.edits())?.let { touch(n.id, it) }
            for (e in edges) {
                // A line drawn or edited, never one deleted, is what brings its ends back.
                val newest = latestByHand(e.edits() + Stamp(e.madeHlc, e.madeDevice)) ?: continue
                if (e.deletedAt != null && (latestByHand(e.edits()) ?: continue) > e.gone()) found[e.id] = e.gone()
                if (e.deletedAt == null || e.id in found) { touch(e.fromNodeId, newest); touch(e.toNodeId, newest) }
            }
            nodes.filter { it.deletedAt == null }.forEach { c -> Stamp(c.treeHlc, c.treeDevice).takeIf { it.byHand }?.let { s -> c.parentId?.let { touch(it, s) } } }
            // What was deleted in one stamp with a card that comes back comes back with it: its lines, the
            // frames that follow it, the lines of those frames, and the children its deletion lifted.
            val relift = HashMap<String, Pair<String, Stamp>>()
            for (n in found.keys.mapNotNull(gone::get)) {
                val frames = nodes.filter { it.deletedAt != null && it.gone() == n.gone() && it.parentId == n.id }.map { it.id }
                frames.forEach { found[it] = n.gone() }
                val with = (frames + n.id).toSet()
                edges.filter { it.deletedAt != null && it.gone() == n.gone() && (it.fromNodeId in with || it.toNodeId in with) }.forEach { found[it.id] = it.gone() }
                val lift = automatic(n.gone())
                nodes.filter { it.deletedAt == null && Stamp(it.treeHlc, it.treeDevice) == lift }.forEach { relift[it.id] = n.id to automatic(lift) }
            }
            back = found
            lifts = relift
            val nodeIds = nodes.map { it.id }.toSet()
            mapOf(CANVAS_NODE to found.keys.filter { it in nodeIds } + relift.keys, CANVAS_EDGE to found.keys.filter { it !in nodeIds })
        }) { store, _ ->
            for ((id, at) in back) store.put(requireNotNull(store.row(id)).edit(GONE, automatic(at), mapOf("deleted_at" to null)))
            for ((id, under) in lifts) store.put(requireNotNull(store.row(id)).edit(NODE_TREE, under.second, mapOf("parent_id" to under.first)))
        }
    }

    private suspend fun add(
        canvasId: String, type: NodeType, x: Double, y: Double, text: String, pageRef: String?, width: Double?, height: Double?, parent: String?,
        check: suspend () -> Unit = {},
    ): String {
        finite(x, y)
        val id = newId()
        var z = ""
        var unfold = false
        shell(canvasId)
        pages.snapshotIfDue(canvasId)
        writes.write({
            shell(canvasId)
            check()
            val nodes = dao.nodesOf(canvasId).filter { it.deletedAt == null }
            if (parent != null) {
                val p = requireNotNull(nodes.firstOrNull { it.id == parent && it.type != NodeType.FRAME.name }) { "no card $parent here to go under" }
                unfold = p.folded
            }
            z = keyBetween(nodes.maxOfOrNull { it.zKey }, null)
            mapOf(CANVAS_NODE to listOfNotNull(id, parent.takeIf { unfold }))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(CANVAS_NODE, id, mapOf(
                MADE to Group(s, mapOf("page_id" to canvasId, "type" to type.name, "page_ref" to pageRef)),
                NODE_AT to Group(s, mapOf("x" to x, "y" to y)),
                NODE_SIZE to Group(s, mapOf("width" to width, "height" to height)),
                NODE_TEXT to Group(s, mapOf("text" to text)),
                LOOK to Group(s, mapOf("hue" to null)),
                NODE_TREE to Group(s, mapOf("parent_id" to parent)),
                NODE_FOLD to Group(s, mapOf("folded" to false)),
                NODE_STRUCTURE to Group(s, mapOf("structure" to null)),
                NODE_Z to Group(s, mapOf("z_key" to z)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
            if (unfold && parent != null) store.put(requireNotNull(store.row(parent)).edit(NODE_FOLD, s, mapOf("folded" to false)))
        }
        return id
    }

    /** Changes one group of a live card, after [check] inside the write. */
    private suspend fun node(id: String, group: String, check: suspend (CanvasNodeEntity) -> Unit, values: (Stamp) -> Map<String, Any?>) {
        pages.snapshotIfDue(liveNode(id).pageId)
        writeNodes({ check(liveNode(id)); listOf(id) }) { store, s -> store.put(requireNotNull(store.row(id)).edit(group, s, values(s))) }
    }

    private suspend fun edge(id: String, group: String, values: (Stamp) -> Map<String, Any?>) {
        val e = liveEdge(id)
        pages.snapshotIfDue(e.pageId)
        writes.write({ liveEdge(id); mapOf(CANVAS_EDGE to listOf(id)) }) { store, _ ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(id)).edit(group, s, values(s)))
        }
    }

    private suspend fun writeNodes(ids: suspend () -> List<String>, block: (StagedStore, Stamp) -> Unit) =
        writes.write({ mapOf(CANVAS_NODE to ids()) }) { store, _ -> block(store, clock.tick()) }

    private suspend fun write(canvasId: String, table: String, id: String, check: suspend () -> Unit, change: (Row) -> Row) {
        check()
        pages.snapshotIfDue(canvasId)
        writes.write({ check(); mapOf(table to listOf(id)) }) { store, _ -> store.put(change(requireNotNull(store.row(id)))) }
    }

    /** A card of a live canvas: an edit to a trashed one's would bring it back (ADR 12's revive). */
    private suspend fun liveNode(id: String) = requireNotNull(dao.nodes(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no card $id" }.also { shell(it.pageId) }

    private suspend fun liveEdge(id: String) = requireNotNull(dao.edges(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no line $id" }.also { shell(it.pageId) }

    private suspend fun shell(canvasId: String) = requireNotNull(dao.canvases(listOf(canvasShellId(canvasId))).singleOrNull()?.takeIf { livePageOrNull(canvasId) != null }) { "no canvas $canvasId" }

    private suspend fun livePageOrNull(id: String) = pageDao.pages(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }

    private suspend fun livePage(id: String) = requireNotNull(livePageOrNull(id)) { "no page $id" }
}

internal const val CANVAS_KIND = "CANVAS"

private fun finite(x: Double, y: Double) = require(x.isFinite() && y.isFinite()) { "a position is a finite point" }

private fun size(width: Double, height: Double) = require(width > 0 && height > 0 && width.isFinite() && height.isFinite()) { "a frame has a size" }

/** The cards a move of [node] carries: its subtree but its frames, and never a card above it (a cycle a merge made). */
private fun carried(node: CanvasNodeEntity, nodes: List<CanvasNodeEntity>): List<CanvasNodeEntity> {
    val byId = nodes.associateBy { it.id }
    val above = generateSequence(node.parentId?.let(byId::get)) { it.parentId?.let(byId::get) }.take(nodes.size).map { it.id }.toSet()
    return descendants(node.id, nodes).filter { it.type != NodeType.FRAME.name && it.id !in above }
}

/** Every card under [id] in the mind map, however deep; a cycle a merge made is walked once. */
private fun descendants(id: String, nodes: List<CanvasNodeEntity>): List<CanvasNodeEntity> {
    val children = nodes.groupBy { it.parentId }
    val out = mutableListOf<CanvasNodeEntity>()
    val seen = mutableSetOf(id)
    fun walk(of: String) {
        for (c in children[of].orEmpty()) if (seen.add(c.id)) { out += c; walk(c.id) }
    }
    walk(id)
    return out
}

/** A card's parent as drawn: a live card of its board not on a cycle with it, else none (the card is a root). */
private fun shownParent(n: CanvasNodeEntity, live: Map<String, CanvasNodeEntity>): String? {
    val parent = n.parentId?.let(live::get) ?: return null
    val onCycle = generateSequence(parent) { it.parentId?.let(live::get) }.take(live.size).any { it.id == n.id }
    return parent.id.takeIf { !onCycle }
}

internal fun CanvasNodeEntity.gone() = Stamp(goneHlc, goneDevice)

internal fun CanvasNodeEntity.edits() = listOf(
    Stamp(atHlc, atDevice), Stamp(sizeHlc, sizeDevice), Stamp(textHlc, textDevice), Stamp(lookHlc, lookDevice), Stamp(treeHlc, treeDevice),
    Stamp(foldHlc, foldDevice), Stamp(structureHlc, structureDevice), Stamp(zHlc, zDevice),
)

internal fun CanvasEdgeEntity.gone() = Stamp(goneHlc, goneDevice)

internal fun CanvasEdgeEntity.edits() = listOf(Stamp(arrowHlc, arrowDevice), Stamp(labelHlc, labelDevice))
