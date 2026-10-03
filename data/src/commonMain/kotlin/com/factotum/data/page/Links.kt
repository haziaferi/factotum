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

internal const val PAGE_RELATION = "page_relation"
internal const val RELATION_LINK = "relation_link"

/**
 * Two pages related on the Road Map (Tendril's "Relate to…", ADR 12): undirected, one row per pair
 * whoever relates them ([relationId]), so relating from either side or on two devices makes one. It
 * can be taken off, and relating again brings it back (owner, 2026-10-03). The map draws pages, so
 * a page deleted for good takes its links with it.
 */
@Entity(
    tableName = PAGE_RELATION,
    foreignKeys = [
        ForeignKey(PageEntity::class, ["id"], ["page_a"], onDelete = ForeignKey.CASCADE, deferred = true),
        ForeignKey(PageEntity::class, ["id"], ["page_b"], onDelete = ForeignKey.CASCADE, deferred = true),
    ],
    indices = [Index("page_a"), Index("page_b")],
)
internal data class PageRelationEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_a") val pageA: String,
    @ColumnInfo(name = "page_b") val pageB: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/** The pair's one id, the lower page id first. */
internal fun relationId(a: String, b: String) = if (a < b) "relation:$a:$b" else "relation:$b:$a"

/**
 * One link in a database relation (owner, 2026-10-03): row [pageId] of the relation [propertyId]'s
 * database is linked to [targetId] in the related one. A relation is two columns, one in each
 * database, and both read this one row, stored under the column with the lower id, so the two can
 * never disagree. Neither page has a foreign key: one deleted for good reads as a placeholder from
 * the other side, whichever side holds the link (owner, 2026-10-03).
 */
@Entity(
    tableName = RELATION_LINK,
    foreignKeys = [ForeignKey(PropertyEntity::class, ["id"], ["property_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id"), Index("property_id"), Index("target_id")],
)
internal data class RelationLinkEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "property_id") val propertyId: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "target_id") val targetId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

internal fun linkId(propertyId: String, pageId: String, targetId: String) = "link:$propertyId:$pageId:$targetId"

@Dao
internal interface LinkDao {
    @Query("SELECT * FROM page_relation WHERE id IN (:ids)") suspend fun relations(ids: List<String>): List<PageRelationEntity>
    @Query("SELECT * FROM page_relation ORDER BY id") suspend fun allRelations(): List<PageRelationEntity>
    @Upsert suspend fun putRelations(rows: List<PageRelationEntity>)
    @Query("DELETE FROM page_relation WHERE id IN (:ids)") suspend fun deleteRelations(ids: List<String>)

    @Query("SELECT * FROM relation_link WHERE id IN (:ids)") suspend fun links(ids: List<String>): List<RelationLinkEntity>
    @Query("SELECT * FROM relation_link ORDER BY id") suspend fun allLinks(): List<RelationLinkEntity>
    @Upsert suspend fun putLinks(rows: List<RelationLinkEntity>)
    @Query("DELETE FROM relation_link WHERE id IN (:ids)") suspend fun deleteLinks(ids: List<String>)

    // Each binds its list once: a chunk of StagedStore.CHUNK ids bound twice would pass SQLite's 999 on older Android.
    @Query("SELECT * FROM page_relation WHERE page_a IN (:pageIds)") suspend fun relationsFrom(pageIds: List<String>): List<PageRelationEntity>
    @Query("SELECT * FROM page_relation WHERE page_b IN (:pageIds)") suspend fun relationsTo(pageIds: List<String>): List<PageRelationEntity>
    @Query("SELECT * FROM relation_link WHERE page_id IN (:pageIds)") suspend fun linksFrom(pageIds: List<String>): List<RelationLinkEntity>
    @Query("SELECT * FROM relation_link WHERE target_id IN (:pageIds)") suspend fun linksTo(pageIds: List<String>): List<RelationLinkEntity>
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun relationTable(dao: LinkDao) =
    EntityTable(dao::relations, dao::allRelations, dao::putRelations, dao::deleteRelations, PageRelationEntity::toRow, Row::toRelationEntity) {
        listOf(PAGE to it.pageA, PAGE to it.pageB)
    }

internal fun linkTable(dao: LinkDao) =
    EntityTable(dao::links, dao::allLinks, dao::putLinks, dao::deleteLinks, RelationLinkEntity::toRow, Row::toLinkEntity) {
        listOf(PROPERTY to it.propertyId)
    }

internal fun PageRelationEntity.toRow() = Row(PAGE_RELATION, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_a" to pageA, "page_b" to pageB)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toRelationEntity(): PageRelationEntity {
    val made = groups.getValue(MADE)
    val gone = groups.getValue(GONE)
    return PageRelationEntity(
        id, made.values["page_a"] as String, made.values["page_b"] as String, made.stamp.hlc, made.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun RelationLinkEntity.toRow() = Row(RELATION_LINK, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("property_id" to propertyId, "page_id" to pageId, "target_id" to targetId)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toLinkEntity(): RelationLinkEntity {
    val made = groups.getValue(MADE)
    val gone = groups.getValue(GONE)
    return RelationLinkEntity(
        id, made.values["property_id"] as String, made.values["page_id"] as String, made.values["target_id"] as String, made.stamp.hlc, made.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

/** The Road Map links that touch any of [pageIds]. */
internal suspend fun LinkDao.relationsOf(pageIds: List<String>): List<PageRelationEntity> = (relationsFrom(pageIds) + relationsTo(pageIds)).distinctBy { it.id }

/** The relation links that touch any of [pageIds], from either side. */
internal suspend fun LinkDao.linksTouching(pageIds: List<String>): List<RelationLinkEntity> = (linksFrom(pageIds) + linksTo(pageIds)).distinctBy { it.id }
