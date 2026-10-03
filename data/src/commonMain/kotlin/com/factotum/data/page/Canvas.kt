package com.factotum.data.page

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val PAGE_CANVAS = "page_canvas"
internal const val CANVAS_NODE = "canvas_node"
internal const val CANVAS_EDGE = "canvas_edge"

/*
 * ADR 01 groups for a canvas (ADR 12, slice 12c), one per thing written apart, so two cards moved
 * on two devices, or a card moved on one and retyped on another, both stand (owner, 2026-10-03). A
 * card's text and a line's label are kept when replaced, with a notice; the rest takes the later stamp.
 */
internal const val LAYOUT = "layout"
internal const val NODE_AT = "node_at"
internal const val NODE_SIZE = "node_size"
internal const val NODE_TEXT = "node_text"
internal const val NODE_TREE = "node_tree"
internal const val NODE_FOLD = "node_fold"
internal const val NODE_STRUCTURE = "node_structure"
internal const val NODE_Z = "node_z"
internal const val ARROW = "arrow"
internal const val EDGE_LABEL = "edge_label"

/** Tendril's card kinds: a text card, a card showing a page, and a frame that holds what lies inside it. */
enum class NodeType { TEXT, PAGE_EMBED, FRAME }

/** Tendril's board layouts, for the whole board or one card's subtree. */
enum class CanvasStructure { FREE, MAP, RIGHT, DOWN, TIMELINE, FISHBONE }

/** Which ends of a line carry an arrow. */
enum class EdgeDirection { NONE, ONE_WAY, TWO_WAY }

/** What makes a page a canvas (Tendril's `page_canvases`): its id is [canvasShellId], with the board's layout. */
@Entity(
    tableName = PAGE_CANVAS,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id", unique = true)],
)
internal data class PageCanvasEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val structure: String,
    @ColumnInfo(name = "layout_hlc") val layoutHlc: Long,
    @ColumnInfo(name = "layout_device") val layoutDevice: String,
)

internal fun canvasShellId(pageId: String) = "canvas:$pageId"

/**
 * A card on a canvas (Tendril's `canvas_nodes`). [pageRef] is a page card's page, with no foreign
 * key: a purged page leaves a placeholder, never a deleted card (owner, 2026-10-03). [parentId] is
 * the mind-map link, with no key either: a card read under a missing or deleted parent is a root.
 * A null [width] is a card sized by its text; a frame has both sizes.
 */
@Entity(
    tableName = CANVAS_NODE,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id"), Index("deleted_at")],
)
internal data class CanvasNodeEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    val type: String,
    @ColumnInfo(name = "page_ref") val pageRef: String?,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val x: Double,
    val y: Double,
    @ColumnInfo(name = "at_hlc") val atHlc: Long,
    @ColumnInfo(name = "at_device") val atDevice: String,
    val width: Double?,
    val height: Double?,
    @ColumnInfo(name = "size_hlc") val sizeHlc: Long,
    @ColumnInfo(name = "size_device") val sizeDevice: String,
    val text: String,
    @ColumnInfo(name = "text_hlc") val textHlc: Long,
    @ColumnInfo(name = "text_device") val textDevice: String,
    val hue: Long?,
    @ColumnInfo(name = "look_hlc") val lookHlc: Long,
    @ColumnInfo(name = "look_device") val lookDevice: String,
    @ColumnInfo(name = "parent_id") val parentId: String?,
    @ColumnInfo(name = "tree_hlc") val treeHlc: Long,
    @ColumnInfo(name = "tree_device") val treeDevice: String,
    val folded: Boolean,
    @ColumnInfo(name = "fold_hlc") val foldHlc: Long,
    @ColumnInfo(name = "fold_device") val foldDevice: String,
    val structure: String?,
    @ColumnInfo(name = "structure_hlc") val structureHlc: Long,
    @ColumnInfo(name = "structure_device") val structureDevice: String,
    @ColumnInfo(name = "z_key") val zKey: String,
    @ColumnInfo(name = "z_hlc") val zHlc: Long,
    @ColumnInfo(name = "z_device") val zDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/** A line between two cards (Tendril's `canvas_edges`), with an id of its own (ADR 12); drawn while both ends are live. */
@Entity(
    tableName = CANVAS_EDGE,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id"), Index("deleted_at")],
)
internal data class CanvasEdgeEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "from_node_id") val fromNodeId: String,
    @ColumnInfo(name = "to_node_id") val toNodeId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val direction: String,
    @ColumnInfo(name = "arrow_hlc") val arrowHlc: Long,
    @ColumnInfo(name = "arrow_device") val arrowDevice: String,
    val label: String?,
    @ColumnInfo(name = "label_hlc") val labelHlc: Long,
    @ColumnInfo(name = "label_device") val labelDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Dao
internal interface CanvasDao {
    @Query("SELECT * FROM page_canvas WHERE id IN (:ids)") suspend fun canvases(ids: List<String>): List<PageCanvasEntity>
    @Query("SELECT * FROM page_canvas ORDER BY id") suspend fun allCanvases(): List<PageCanvasEntity>
    @Upsert suspend fun putCanvases(rows: List<PageCanvasEntity>)
    @Query("DELETE FROM page_canvas WHERE id IN (:ids)") suspend fun deleteCanvases(ids: List<String>)

    @Query("SELECT * FROM canvas_node WHERE id IN (:ids)") suspend fun nodes(ids: List<String>): List<CanvasNodeEntity>
    @Query("SELECT * FROM canvas_node ORDER BY page_id, id") suspend fun allNodes(): List<CanvasNodeEntity>
    @Upsert suspend fun putNodes(rows: List<CanvasNodeEntity>)
    @Query("DELETE FROM canvas_node WHERE id IN (:ids)") suspend fun deleteNodes(ids: List<String>)

    @Query("SELECT * FROM canvas_edge WHERE id IN (:ids)") suspend fun edges(ids: List<String>): List<CanvasEdgeEntity>
    @Query("SELECT * FROM canvas_edge ORDER BY page_id, id") suspend fun allEdges(): List<CanvasEdgeEntity>
    @Upsert suspend fun putEdges(rows: List<CanvasEdgeEntity>)
    @Query("DELETE FROM canvas_edge WHERE id IN (:ids)") suspend fun deleteEdges(ids: List<String>)

    @Query("SELECT * FROM canvas_node WHERE page_id = :pageId") suspend fun nodesOf(pageId: String): List<CanvasNodeEntity>
    @Query("SELECT * FROM canvas_edge WHERE page_id = :pageId") suspend fun edgesOf(pageId: String): List<CanvasEdgeEntity>
    @Query("SELECT * FROM canvas_node WHERE page_id IN (:pageIds)") suspend fun nodesOfPages(pageIds: List<String>): List<CanvasNodeEntity>
    @Query("SELECT * FROM canvas_edge WHERE page_id IN (:pageIds)") suspend fun edgesOfPages(pageIds: List<String>): List<CanvasEdgeEntity>
    @Query("SELECT * FROM canvas_node WHERE deleted_at IS NOT NULL") suspend fun deletedNodes(): List<CanvasNodeEntity>
    @Query("SELECT * FROM canvas_edge WHERE deleted_at IS NOT NULL") suspend fun deletedEdges(): List<CanvasEdgeEntity>
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun canvasTable(dao: CanvasDao) =
    EntityTable(dao::canvases, dao::allCanvases, dao::putCanvases, dao::deleteCanvases, PageCanvasEntity::toRow, Row::toCanvasEntity) { listOf(PAGE to it.pageId) }

internal fun nodeTable(dao: CanvasDao) =
    EntityTable(dao::nodes, dao::allNodes, dao::putNodes, dao::deleteNodes, CanvasNodeEntity::toRow, Row::toNodeEntity) { listOf(PAGE to it.pageId) }

internal fun edgeTable(dao: CanvasDao) =
    EntityTable(dao::edges, dao::allEdges, dao::putEdges, dao::deleteEdges, CanvasEdgeEntity::toRow, Row::toEdgeEntity) { listOf(PAGE to it.pageId) }

internal fun PageCanvasEntity.toRow() = Row(PAGE_CANVAS, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId)),
    LAYOUT to stamped(layoutHlc, layoutDevice, mapOf("structure" to structure)),
))

internal fun Row.toCanvasEntity(): PageCanvasEntity {
    val made = groups.getValue(MADE)
    val layout = groups.getValue(LAYOUT)
    return PageCanvasEntity(id, made.values["page_id"] as String, made.stamp.hlc, made.stamp.device, layout.values["structure"] as String, layout.stamp.hlc, layout.stamp.device)
        .also { CanvasStructure.valueOf(it.structure) }
}

internal fun CanvasNodeEntity.toRow() = Row(CANVAS_NODE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "type" to type, "page_ref" to pageRef)),
    NODE_AT to stamped(atHlc, atDevice, mapOf("x" to x, "y" to y)),
    NODE_SIZE to stamped(sizeHlc, sizeDevice, mapOf("width" to width, "height" to height)),
    NODE_TEXT to stamped(textHlc, textDevice, mapOf("text" to text)),
    LOOK to stamped(lookHlc, lookDevice, mapOf("hue" to hue)),
    NODE_TREE to stamped(treeHlc, treeDevice, mapOf("parent_id" to parentId)),
    NODE_FOLD to stamped(foldHlc, foldDevice, mapOf("folded" to folded)),
    NODE_STRUCTURE to stamped(structureHlc, structureDevice, mapOf("structure" to structure)),
    NODE_Z to stamped(zHlc, zDevice, mapOf("z_key" to zKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))


internal fun Row.toNodeEntity(): CanvasNodeEntity {
    fun g(name: String) = groups.getValue(name)
    val made = g(MADE)
    val at = g(NODE_AT)
    val size = g(NODE_SIZE)
    val text = g(NODE_TEXT)
    val look = g(LOOK)
    val tree = g(NODE_TREE)
    val fold = g(NODE_FOLD)
    val structure = g(NODE_STRUCTURE)
    val z = g(NODE_Z)
    val gone = g(GONE)
    return CanvasNodeEntity(
        id, made.values["page_id"] as String, made.values["type"] as String, made.values["page_ref"] as String?, made.stamp.hlc, made.stamp.device,
        at.values["x"] as Double, at.values["y"] as Double, at.stamp.hlc, at.stamp.device,
        size.values["width"] as Double?, size.values["height"] as Double?, size.stamp.hlc, size.stamp.device,
        text.values["text"] as String, text.stamp.hlc, text.stamp.device,
        look.values["hue"] as Long?, look.stamp.hlc, look.stamp.device,
        tree.values["parent_id"] as String?, tree.stamp.hlc, tree.stamp.device,
        fold.values["folded"] as Boolean, fold.stamp.hlc, fold.stamp.device,
        structure.values["structure"] as String?, structure.stamp.hlc, structure.stamp.device,
        z.values["z_key"] as String, z.stamp.hlc, z.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { n -> NodeType.valueOf(n.type); n.structure?.let(CanvasStructure::valueOf) }
}

internal fun CanvasEdgeEntity.toRow() = Row(CANVAS_EDGE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "from_node_id" to fromNodeId, "to_node_id" to toNodeId)),
    ARROW to stamped(arrowHlc, arrowDevice, mapOf("direction" to direction)),
    EDGE_LABEL to stamped(labelHlc, labelDevice, mapOf("label" to label)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toEdgeEntity(): CanvasEdgeEntity {
    val made = groups.getValue(MADE)
    val arrow = groups.getValue(ARROW)
    val label = groups.getValue(EDGE_LABEL)
    val gone = groups.getValue(GONE)
    return CanvasEdgeEntity(
        id, made.values["page_id"] as String, made.values["from_node_id"] as String, made.values["to_node_id"] as String, made.stamp.hlc, made.stamp.device,
        arrow.values["direction"] as String, arrow.stamp.hlc, arrow.stamp.device,
        label.values["label"] as String?, label.stamp.hlc, label.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { EdgeDirection.valueOf(it.direction) }
}
