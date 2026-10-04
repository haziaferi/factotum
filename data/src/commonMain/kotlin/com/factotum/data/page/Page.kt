package com.factotum.data.page

import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import com.factotum.core.image.BlobName
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.item.EntityTable

internal const val PAGE = "page"
internal const val BLOCK = "block"
internal const val PAGE_LABEL = "page_label"
internal const val PAGE_NOTICE = "page_notice"

/*
 * ADR 01 groups, one per thing written apart (ADR 12, per-row): a row's making (written once), a
 * page's title, a block's type, text, place and attributes, and a row's deletion. A page's title
 * and a block's text keep the version they replace when two devices change them apart (ADR 12's
 * notice); the other groups take the later stamp.
 */
internal const val MADE = "made"
internal const val PAGE_TITLE = "page_title"
internal const val PLACE = "place"
internal const val BLOCK_TYPE = "block_type"
internal const val BLOCK_TEXT = "block_text"
internal const val ATTRS = "attrs"
internal const val BLOCK_IMAGE = "block_image"
internal const val GONE = "gone"
internal const val DISMISSED = "dismissed"

/**
 * The groups whose replaced version is kept for the person (ADR 12): a page's title, a block's text
 * and picture (decision 14, answer 25), a database cell, a card's text and a line's label.
 */
internal val KEEP_LOSER_GROUPS = setOf(PAGE_TITLE, BLOCK_TEXT, BLOCK_IMAGE, CELL, NODE_TEXT, EDGE_LABEL)

/** Tendril's block types; an IMAGE block's caption is its text, and its picture a group of its own. */
enum class BlockType {
    PARAGRAPH, HEADING_1, HEADING_2, HEADING_3, BULLETED, NUMBERED, TODO, QUOTE, CODE, DIVIDER, IMAGE, TOGGLE, CALLOUT,
    PAGE_MENTION, CANVAS, BLOCK_REFERENCE,
}

/**
 * A page (Tendril's, ADR 12): a title and an icon, a place in the tree under [parentId], and a
 * deletion that a later edit to any part of it undoes (revive). Sub-pages go with their parent:
 * to the trash with it, and for good with it ("delete forever", owner 2026-10-03).
 */
@Entity(
    tableName = PAGE,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["parent_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("parent_id")],
)
internal data class PageEntity(
    @PrimaryKey val id: String,
    val kind: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val title: String,
    val icon: String?,
    @ColumnInfo(name = "title_hlc") val titleHlc: Long,
    @ColumnInfo(name = "title_device") val titleDevice: String,
    @ColumnInfo(name = "parent_id") val parentId: String?,
    @ColumnInfo(name = "place_hlc") val placeHlc: Long,
    @ColumnInfo(name = "place_device") val placeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
    /** A template (ADR 12, owner 2026-10-03): written once, in the page's making; null on a page that is not one. */
    @ColumnInfo(name = "is_template") val isTemplate: Boolean? = null,
)

/**
 * One block of a page (ADR 12, per-row): its type, its text with Tendril's formatting spans (JSON,
 * offsets into the text, so the two travel together), its place (a parent block and a fractional
 * sort key), the attributes some types have, and a deletion a later edit undoes (owner, 2026-10-03).
 */
@Entity(
    tableName = BLOCK,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id")],
)
internal data class BlockEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val type: String,
    @ColumnInfo(name = "type_hlc") val typeHlc: Long,
    @ColumnInfo(name = "type_device") val typeDevice: String,
    val content: String,
    val spans: String?,
    @ColumnInfo(name = "text_hlc") val textHlc: Long,
    @ColumnInfo(name = "text_device") val textDevice: String,
    @ColumnInfo(name = "parent_block_id") val parentBlockId: String?,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "place_hlc") val placeHlc: Long,
    @ColumnInfo(name = "place_device") val placeDevice: String,
    val checked: Boolean?,
    @ColumnInfo(name = "code_language") val codeLanguage: String?,
    @ColumnInfo(name = "callout_icon") val calloutIcon: String?,
    @ColumnInfo(name = "callout_color") val calloutColor: Long?,
    @ColumnInfo(name = "mentioned_page_id") val mentionedPageId: String?,
    @ColumnInfo(name = "referenced_block_id") val referencedBlockId: String?,
    @ColumnInfo(name = "toggle_expanded") val toggleExpanded: Boolean?,
    @ColumnInfo(name = "attrs_hlc") val attrsHlc: Long,
    @ColumnInfo(name = "attrs_device") val attrsDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
    /**
     * An image block's picture: its blob's name ([com.factotum.core.image.BlobName]) and size, a
     * group of its own, so a picture replaced on two devices keeps the later and puts the earlier in
     * History (answer 25), and a toggle or a caption changed apart never touches it. Null for none.
     */
    val image: String? = null,
    @ColumnInfo(name = "image_width") val imageWidth: Long? = null,
    @ColumnInfo(name = "image_height") val imageHeight: Long? = null,
    @ColumnInfo(name = "image_hlc") val imageHlc: Long? = null,
    @ColumnInfo(name = "image_device") val imageDevice: String? = null,
)

/**
 * A label on a page (ADR 08: a page carries many). Its id is [pageLabelId], so two devices that put
 * one label on one page write one row; taking it off and putting it back are stamps on its deletion.
 */
@Entity(
    tableName = PAGE_LABEL,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id"), Index("label_id")],
)
internal data class PageLabelEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "label_id") val labelId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

internal fun pageLabelId(pageId: String, labelId: String) = "page_label:$pageId:$labelId"

/**
 * "Replaced by a sync" (ADR 12): a page's title or a block's text that two devices changed apart,
 * the earlier version kept in each device's History. It syncs and shows on every device until it
 * is dismissed on one (owner, 2026-10-03). Its id names the replaced version, so the two devices,
 * which each keep it, write one notice; it is stamped with that version's stamp, so the second
 * device to write it never undoes a dismissal the first device's copy has had since.
 */
@Entity(
    tableName = PAGE_NOTICE,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id")],
)
internal data class PageNoticeEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "row_id") val rowId: String,
    /** The replaced title or text, so a device that never held it can still bring it back. */
    @ColumnInfo(name = "lost_text") val lostText: String,
    @ColumnInfo(name = "lost_spans") val lostSpans: String?,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "dismissed_at") val dismissedAt: Long?,
    @ColumnInfo(name = "dismissed_hlc") val dismissedHlc: Long,
    @ColumnInfo(name = "dismissed_device") val dismissedDevice: String,
    /** A replaced picture (answer 25): its blob's name and size; [lostText] is then empty. */
    @ColumnInfo(name = "lost_image") val lostImage: String? = null,
    @ColumnInfo(name = "lost_image_width") val lostImageWidth: Long? = null,
    @ColumnInfo(name = "lost_image_height") val lostImageHeight: Long? = null,
)

internal fun noticeId(rowId: String, lost: Stamp) = "notice:$rowId:${lost.hlc}:${lost.device}"

/**
 * A page as it was (Tendril's History, ADR 12): this device's alone, never synced. EDIT before a
 * change, at most one each ten minutes; MERGE for a version a sync replaced, linked to its notice;
 * RESTORE when one is brought back. Fifty kept per page.
 */
@Entity(
    tableName = "page_revision",
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id")],
)
internal data class PageRevisionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long,
    @ColumnInfo(name = "page_id") val pageId: String,
    val reason: String,
    val title: String,
    @ColumnInfo(name = "blocks_json") val blocksJson: String,
    @ColumnInfo(name = "block_count") val blockCount: Long,
    /** When it was kept, by this device's wall clock, in milliseconds. */
    val at: Long,
    @ColumnInfo(name = "notice_id") val noticeId: String?,
    /** The page's database cells as they were, a JSON object of property id to stored value. */
    @ColumnInfo(name = "cells_json") val cellsJson: String? = null,
    /** A canvas's cards and lines as they were: their groups by id, as record lines encode them. */
    @ColumnInfo(name = "canvas_json") val canvasJson: String? = null,
)

@Dao
internal interface PageDao {
    @Query("SELECT * FROM page WHERE id IN (:ids)") suspend fun pages(ids: List<String>): List<PageEntity>
    @Query("SELECT * FROM page ORDER BY parent_id IS NOT NULL, id") suspend fun allPages(): List<PageEntity>
    @Upsert suspend fun putPages(rows: List<PageEntity>)
    @Query("DELETE FROM page WHERE id IN (:ids)") suspend fun deletePages(ids: List<String>)

    @Query("SELECT * FROM block WHERE id IN (:ids)") suspend fun blocks(ids: List<String>): List<BlockEntity>
    @Query("SELECT * FROM block ORDER BY page_id, id") suspend fun allBlocks(): List<BlockEntity>
    @Upsert suspend fun putBlocks(rows: List<BlockEntity>)
    @Query("DELETE FROM block WHERE id IN (:ids)") suspend fun deleteBlocks(ids: List<String>)

    @Query("SELECT * FROM page_label WHERE id IN (:ids)") suspend fun pageLabels(ids: List<String>): List<PageLabelEntity>
    @Query("SELECT * FROM page_label ORDER BY page_id, id") suspend fun allPageLabels(): List<PageLabelEntity>
    @Upsert suspend fun putPageLabels(rows: List<PageLabelEntity>)
    @Query("DELETE FROM page_label WHERE id IN (:ids)") suspend fun deletePageLabels(ids: List<String>)

    @Query("SELECT * FROM page_notice WHERE id IN (:ids)") suspend fun notices(ids: List<String>): List<PageNoticeEntity>
    @Query("SELECT * FROM page_notice ORDER BY page_id, id") suspend fun allNotices(): List<PageNoticeEntity>
    @Upsert suspend fun putNotices(rows: List<PageNoticeEntity>)
    @Query("DELETE FROM page_notice WHERE id IN (:ids)") suspend fun deleteNotices(ids: List<String>)

    /** Every page, live or trashed: the tree and the revive pass read it whole. */

    @Query("SELECT * FROM block WHERE deleted_at IS NOT NULL") suspend fun deletedBlocks(): List<BlockEntity>
    @Query("SELECT * FROM block WHERE image IS NOT NULL") suspend fun pictured(): List<BlockEntity>
    @Query("SELECT lost_image FROM page_notice WHERE lost_image IS NOT NULL AND dismissed_at IS NULL") suspend fun lostImages(): List<String>
    @Query("SELECT blocks_json FROM page_revision") suspend fun revisionBlocks(): List<String>
    @Query("SELECT * FROM page WHERE parent_id = :parentId") suspend fun childrenOf(parentId: String): List<PageEntity>
    @Query("SELECT * FROM block WHERE page_id = :pageId") suspend fun blocksOf(pageId: String): List<BlockEntity>
    @Query("SELECT * FROM block WHERE page_id IN (:pageIds)") suspend fun blocksOfPages(pageIds: List<String>): List<BlockEntity>
    @Query("SELECT * FROM page_label WHERE page_id IN (:pageIds)") suspend fun labelsOfPages(pageIds: List<String>): List<PageLabelEntity>
    @Query("SELECT * FROM page_label WHERE label_id IN (:labelIds) AND deleted_at IS NULL") suspend fun pagesLabelled(labelIds: List<String>): List<PageLabelEntity>
    @Query("SELECT * FROM page_notice WHERE page_id = :pageId AND dismissed_at IS NULL ORDER BY id") suspend fun openNotices(pageId: String): List<PageNoticeEntity>

    @Insert suspend fun addRevision(row: PageRevisionEntity): Long
    @Query("SELECT * FROM page_revision WHERE page_id = :pageId ORDER BY at DESC, id DESC") suspend fun revisionsOf(pageId: String): List<PageRevisionEntity>
    @Query("SELECT * FROM page_revision WHERE id = :id") suspend fun revision(id: Long): PageRevisionEntity?
    @Query("DELETE FROM page_revision WHERE page_id = :pageId AND id NOT IN (SELECT id FROM page_revision WHERE page_id = :pageId ORDER BY at DESC, id DESC LIMIT :keep)")
    suspend fun keepRevisions(pageId: String, keep: Int)
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun pageTable(dao: PageDao) = EntityTable(dao::pages, dao::allPages, dao::putPages, dao::deletePages, PageEntity::toRow, Row::toPageEntity) {
    listOfNotNull(it.parentId?.let { p -> PAGE to p })
}

internal fun blockTable(dao: PageDao) = EntityTable(dao::blocks, dao::allBlocks, dao::putBlocks, dao::deleteBlocks, BlockEntity::toRow, Row::toBlockEntity) {
    listOf(PAGE to it.pageId)
}

internal fun pageLabelTable(dao: PageDao) =
    EntityTable(dao::pageLabels, dao::allPageLabels, dao::putPageLabels, dao::deletePageLabels, PageLabelEntity::toRow, Row::toPageLabelEntity) {
        listOf(PAGE to it.pageId)
    }

internal fun noticeTable(dao: PageDao) = EntityTable(dao::notices, dao::allNotices, dao::putNotices, dao::deleteNotices, PageNoticeEntity::toRow, Row::toNoticeEntity) {
    listOf(PAGE to it.pageId)
}

internal fun PageEntity.toRow() = Row(PAGE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("kind" to kind, "is_template" to (isTemplate == true))),
    PAGE_TITLE to stamped(titleHlc, titleDevice, mapOf("title" to title, "icon" to icon)),
    PLACE to stamped(placeHlc, placeDevice, mapOf("parent_id" to parentId)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toPageEntity(): PageEntity {
    val made = groups.getValue(MADE)
    val title = groups.getValue(PAGE_TITLE)
    val place = groups.getValue(PLACE)
    val gone = groups.getValue(GONE)
    return PageEntity(
        id, made.values["kind"] as String, made.stamp.hlc, made.stamp.device,
        title.values["title"] as String, title.values["icon"] as String?, title.stamp.hlc, title.stamp.device,
        place.values["parent_id"] as String?, place.stamp.hlc, place.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
        // A line written before templates has no flag: not a template.
        isTemplate = (made.values["is_template"] as Boolean?)?.takeIf { it },
    )
}

internal fun BlockEntity.toRow() = Row(BLOCK, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId)),
    BLOCK_TYPE to stamped(typeHlc, typeDevice, mapOf("type" to type)),
    BLOCK_TEXT to stamped(textHlc, textDevice, mapOf("content" to content, "spans" to spans)),
    PLACE to stamped(placeHlc, placeDevice, mapOf("parent_block_id" to parentBlockId, "sort_key" to sortKey)),
    ATTRS to stamped(attrsHlc, attrsDevice, mapOf(
        "checked" to checked, "code_language" to codeLanguage, "callout_icon" to calloutIcon, "callout_color" to calloutColor,
        "mentioned_page_id" to mentionedPageId, "referenced_block_id" to referencedBlockId, "toggle_expanded" to toggleExpanded,
    )),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
) + listOfNotNull(imageHlc?.let { BLOCK_IMAGE to stamped(it, requireNotNull(imageDevice), mapOf("image" to image, "width" to imageWidth, "height" to imageHeight)) }))

internal fun Row.toBlockEntity(): BlockEntity {
    val made = groups.getValue(MADE)
    val type = groups.getValue(BLOCK_TYPE)
    val text = groups.getValue(BLOCK_TEXT)
    val place = groups.getValue(PLACE)
    val a = groups.getValue(ATTRS)
    val gone = groups.getValue(GONE)
    // Only a block ever given a picture has the group, and a line written before pictures has none.
    val image = groups[BLOCK_IMAGE]
    return BlockEntity(
        id, made.values["page_id"] as String, made.stamp.hlc, made.stamp.device,
        type.values["type"] as String, type.stamp.hlc, type.stamp.device,
        text.values["content"] as String, text.values["spans"] as String?, text.stamp.hlc, text.stamp.device,
        place.values["parent_block_id"] as String?, place.values["sort_key"] as String, place.stamp.hlc, place.stamp.device,
        a.values["checked"] as Boolean?, a.values["code_language"] as String?, a.values["callout_icon"] as String?, a.values["callout_color"] as Long?,
        a.values["mentioned_page_id"] as String?, a.values["referenced_block_id"] as String?, a.values["toggle_expanded"] as Boolean?,
        a.stamp.hlc, a.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
        image?.values?.get("image") as String?, image?.values?.get("width") as Long?, image?.values?.get("height") as Long?, image?.stamp?.hlc, image?.stamp?.device,
    ).also { b -> BlockType.valueOf(b.type); checkPicture(b.image, b.imageWidth, b.imageHeight) }
}

/** A picture a line names is a blob name this app writes, with a size; a line that says otherwise is refused, not shown. */
private fun checkPicture(name: String?, width: Long?, height: Long?) {
    if (name == null) return
    require(BlobName.isValid(name) && width != null && width > 0 && height != null && height > 0) { "not a picture: $name ${width}x$height" }
}

internal fun PageLabelEntity.toRow() = Row(PAGE_LABEL, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "label_id" to labelId)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toPageLabelEntity(): PageLabelEntity {
    val made = groups.getValue(MADE)
    val gone = groups.getValue(GONE)
    return PageLabelEntity(
        id, made.values["page_id"] as String, made.values["label_id"] as String, made.stamp.hlc, made.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun PageNoticeEntity.toRow() = Row(PAGE_NOTICE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "row_id" to rowId, "lost_text" to lostText, "lost_spans" to lostSpans) +
        (if (lostImage != null) mapOf("lost_image" to lostImage, "lost_image_width" to lostImageWidth, "lost_image_height" to lostImageHeight) else emptyMap())),
    DISMISSED to stamped(dismissedHlc, dismissedDevice, mapOf("dismissed_at" to dismissedAt)),
))

internal fun Row.toNoticeEntity(): PageNoticeEntity {
    val made = groups.getValue(MADE)
    val d = groups.getValue(DISMISSED)
    return PageNoticeEntity(
        id, made.values["page_id"] as String, made.values["row_id"] as String, made.values["lost_text"] as String, made.values["lost_spans"] as String?,
        made.stamp.hlc, made.stamp.device, d.values["dismissed_at"] as Long?, d.stamp.hlc, d.stamp.device,
        made.values["lost_image"] as String?, made.values["lost_image_width"] as Long?, made.values["lost_image_height"] as Long?,
    ).also { checkPicture(it.lostImage, it.lostImageWidth, it.lostImageHeight) }
}
