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

internal const val PAGE_DATABASE = "page_database"
internal const val PROPERTY = "property"
internal const val PROPERTY_OPTION = "property_option"
internal const val PROPERTY_VALUE = "property_value"
internal const val VALUE_PICK = "value_pick"
internal const val PAGE_VIEW = "page_view"

/*
 * ADR 01 groups for databases (ADR 12, slice 12b), one per thing written apart. A cell's value is
 * the one kept when replaced (ADR 12's notice); a name, a type or a view setting takes the later
 * stamp silently (owner, 2026-10-03).
 */
internal const val DOORWAY = "doorway"
internal const val LOOK = "look"
internal const val NAME = "name"
internal const val PROPERTY_TYPE = "property_type"
internal const val CELL = "cell"
internal const val VIEW_KIND = "view_kind"
internal const val VIEW_SHOW = "view_show"
internal const val VIEW_SORT = "view_sort"
internal const val VIEW_FILTER = "view_filter"
internal const val BLOCKED = "blocked"

/** Tendril's property types; formulas, rollups and intervals come with §7 step 3 (ADR 12, owner 2026-10-03). */
enum class PropertyType { TEXT, NUMBER, CHECKBOX, SELECT, MULTI_SELECT, DATE, URL, EMAIL, PHONE, RELATION }

/** Tendril's view types: how a database's rows are laid out. */
enum class ViewType { TABLE, BOARD, GALLERY, CALENDAR, TIMELINE }

/** Tendril's single view filter. */
enum class FilterOp { EQUALS, NOT_EQUALS, CONTAINS, IS_EMPTY, IS_NOT_EMPTY }

/**
 * What makes a page a database (ADR 12): one per page, its id [shellId] (every synced row's id is
 * unique across tables). Its members are the rows made in it, its sub-pages, and every page carrying
 * its doorway label (owner, 2026-10-03). The label has no foreign key (ADR 08, amended): a deleted
 * label reads as none. Properties and views name the page itself.
 */
@Entity(
    tableName = PAGE_DATABASE,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("page_id", unique = true)],
)
internal data class PageDatabaseEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "label_id") val labelId: String?,
    @ColumnInfo(name = "doorway_hlc") val doorwayHlc: Long,
    @ColumnInfo(name = "doorway_device") val doorwayDevice: String,
    /** Tendril's colour, 0 to 359; null is one derived from the title. */
    val hue: Long?,
    @ColumnInfo(name = "look_hlc") val lookHlc: Long,
    @ColumnInfo(name = "look_device") val lookDevice: String,
    /** The self-relation whose links say what blocks a row (Tendril's Timeline); null for none. */
    @ColumnInfo(name = "blocked_by") val blockedBy: String? = null,
    @ColumnInfo(name = "blocked_hlc") val blockedHlc: Long? = null,
    @ColumnInfo(name = "blocked_device") val blockedDevice: String? = null,
)

internal fun shellId(pageId: String) = "database:$pageId"

/** A column of a database (ADR 12: the schema is upserted by id and deleted only by a purge). */
@Entity(
    tableName = PROPERTY,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["database_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("database_id")],
)
internal data class PropertyEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "database_id") val databaseId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val name: String,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    val type: String,
    @ColumnInfo(name = "type_hlc") val typeHlc: Long,
    @ColumnInfo(name = "type_device") val typeDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "place_hlc") val placeHlc: Long,
    @ColumnInfo(name = "place_device") val placeDevice: String,
    /** A relation's database, written once in its making (a type never changes to or from a relation). */
    @ColumnInfo(name = "target_database_id") val targetDatabaseId: String? = null,
    /** A relation's matching column in [targetDatabaseId] (owner, 2026-10-03: a relation is always two-way). */
    @ColumnInfo(name = "pair_property_id") val pairPropertyId: String? = null,
)

/**
 * One of a Select's or a Multi-select's options, a row of its own so options added on two devices
 * both stay (owner, 2026-10-03). A deleted one reads as none and comes back when picked again; one
 * merged into another of its name reads as that one ([mergedInto]).
 */
@Entity(
    tableName = PROPERTY_OPTION,
    foreignKeys = [ForeignKey(PropertyEntity::class, ["id"], ["property_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("property_id")],
)
internal data class OptionEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "property_id") val propertyId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val name: String,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    val color: Long?,
    @ColumnInfo(name = "look_hlc") val lookHlc: Long,
    @ColumnInfo(name = "look_device") val lookDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "place_hlc") val placeHlc: Long,
    @ColumnInfo(name = "place_device") val placeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "merged_into") val mergedInto: String?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

/**
 * A page's value for one property, as text in one form per type (a decimal, `true`/`false`, an ISO
 * date, a Select's option id). Its id is [valueId], so two devices that fill one cell write one row;
 * a type change rewrites none of them (owner, 2026-10-03), and the value is read under the new type.
 */
@Entity(
    tableName = PROPERTY_VALUE,
    foreignKeys = [
        ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true),
        ForeignKey(PropertyEntity::class, ["id"], ["property_id"], onDelete = ForeignKey.CASCADE, deferred = true),
    ],
    indices = [Index("page_id"), Index("property_id")],
)
internal data class PropertyValueEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "property_id") val propertyId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val value: String?,
    @ColumnInfo(name = "cell_hlc") val cellHlc: Long,
    @ColumnInfo(name = "cell_device") val cellDevice: String,
)

internal fun valueId(pageId: String, propertyId: String) = "pv:$pageId:$propertyId"

/** One option picked in a Multi-select cell, a row of its own so picks made on two devices merge (owner, 2026-10-03). */
@Entity(
    tableName = VALUE_PICK,
    foreignKeys = [
        ForeignKey(PageEntity::class, ["id"], ["page_id"], onDelete = ForeignKey.CASCADE, deferred = true),
        ForeignKey(PropertyEntity::class, ["id"], ["property_id"], onDelete = ForeignKey.CASCADE, deferred = true),
    ],
    indices = [Index("page_id"), Index("property_id")],
)
internal data class ValuePickEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "page_id") val pageId: String,
    @ColumnInfo(name = "property_id") val propertyId: String,
    @ColumnInfo(name = "option_id") val optionId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

internal fun pickId(pageId: String, propertyId: String, optionId: String) = "pick:$pageId:$propertyId:$optionId"

/**
 * A view of a database (Tendril's): its layout, the columns it shows, one sort and one filter,
 * each a group of its own, so a sort and a filter changed on two devices both stand (owner, 2026-10-03).
 */
@Entity(
    tableName = PAGE_VIEW,
    foreignKeys = [ForeignKey(PageEntity::class, ["id"], ["database_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("database_id")],
)
internal data class ViewEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "database_id") val databaseId: String,
    @ColumnInfo(name = "made_hlc") val madeHlc: Long,
    @ColumnInfo(name = "made_device") val madeDevice: String,
    val name: String,
    @ColumnInfo(name = "name_hlc") val nameHlc: Long,
    @ColumnInfo(name = "name_device") val nameDevice: String,
    @ColumnInfo(name = "view_type") val viewType: String,
    @ColumnInfo(name = "group_by") val groupBy: String?,
    @ColumnInfo(name = "date_property") val dateProperty: String?,
    @ColumnInfo(name = "end_date_property") val endDateProperty: String?,
    @ColumnInfo(name = "kind_hlc") val kindHlc: Long,
    @ColumnInfo(name = "kind_device") val kindDevice: String,
    /** The property ids shown, comma-joined, in order; null shows them all. */
    val shown: String?,
    @ColumnInfo(name = "show_hlc") val showHlc: Long,
    @ColumnInfo(name = "show_device") val showDevice: String,
    @ColumnInfo(name = "sort_property") val sortProperty: String?,
    @ColumnInfo(name = "sort_descending") val sortDescending: Boolean,
    @ColumnInfo(name = "sort_hlc") val sortHlc: Long,
    @ColumnInfo(name = "sort_device") val sortDevice: String,
    @ColumnInfo(name = "filter_property") val filterProperty: String?,
    @ColumnInfo(name = "filter_op") val filterOp: String?,
    @ColumnInfo(name = "filter_value") val filterValue: String?,
    @ColumnInfo(name = "filter_hlc") val filterHlc: Long,
    @ColumnInfo(name = "filter_device") val filterDevice: String,
    @ColumnInfo(name = "sort_key") val sortKey: String,
    @ColumnInfo(name = "place_hlc") val placeHlc: Long,
    @ColumnInfo(name = "place_device") val placeDevice: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    @ColumnInfo(name = "gone_hlc") val goneHlc: Long,
    @ColumnInfo(name = "gone_device") val goneDevice: String,
)

@Dao
internal interface DatabaseDao {
    @Query("SELECT * FROM page_database WHERE id IN (:ids)") suspend fun databases(ids: List<String>): List<PageDatabaseEntity>
    @Query("SELECT * FROM page_database ORDER BY id") suspend fun allDatabases(): List<PageDatabaseEntity>
    @Upsert suspend fun putDatabases(rows: List<PageDatabaseEntity>)
    @Query("DELETE FROM page_database WHERE id IN (:ids)") suspend fun deleteDatabases(ids: List<String>)

    @Query("SELECT * FROM property WHERE id IN (:ids)") suspend fun properties(ids: List<String>): List<PropertyEntity>
    @Query("SELECT * FROM property ORDER BY database_id, id") suspend fun allProperties(): List<PropertyEntity>
    @Upsert suspend fun putProperties(rows: List<PropertyEntity>)
    @Query("DELETE FROM property WHERE id IN (:ids)") suspend fun deleteProperties(ids: List<String>)

    @Query("SELECT * FROM property_option WHERE id IN (:ids)") suspend fun options(ids: List<String>): List<OptionEntity>
    @Query("SELECT * FROM property_option ORDER BY property_id, id") suspend fun allOptions(): List<OptionEntity>
    @Upsert suspend fun putOptions(rows: List<OptionEntity>)
    @Query("DELETE FROM property_option WHERE id IN (:ids)") suspend fun deleteOptions(ids: List<String>)

    @Query("SELECT * FROM property_value WHERE id IN (:ids)") suspend fun values(ids: List<String>): List<PropertyValueEntity>
    @Query("SELECT * FROM property_value ORDER BY page_id, id") suspend fun allValues(): List<PropertyValueEntity>
    @Upsert suspend fun putValues(rows: List<PropertyValueEntity>)
    @Query("DELETE FROM property_value WHERE id IN (:ids)") suspend fun deleteValues(ids: List<String>)

    @Query("SELECT * FROM value_pick WHERE id IN (:ids)") suspend fun picks(ids: List<String>): List<ValuePickEntity>
    @Query("SELECT * FROM value_pick ORDER BY page_id, id") suspend fun allPicks(): List<ValuePickEntity>
    @Upsert suspend fun putPicks(rows: List<ValuePickEntity>)
    @Query("DELETE FROM value_pick WHERE id IN (:ids)") suspend fun deletePicks(ids: List<String>)

    @Query("SELECT * FROM page_view WHERE id IN (:ids)") suspend fun views(ids: List<String>): List<ViewEntity>
    @Query("SELECT * FROM page_view ORDER BY database_id, id") suspend fun allViews(): List<ViewEntity>
    @Upsert suspend fun putViews(rows: List<ViewEntity>)
    @Query("DELETE FROM page_view WHERE id IN (:ids)") suspend fun deleteViews(ids: List<String>)

    @Query("SELECT * FROM property WHERE database_id = :databaseId") suspend fun propertiesOf(databaseId: String): List<PropertyEntity>
    @Query("SELECT * FROM property_option WHERE property_id IN (:propertyIds)") suspend fun optionsOf(propertyIds: List<String>): List<OptionEntity>
    @Query("SELECT * FROM property_value WHERE page_id IN (:pageIds)") suspend fun valuesOfPages(pageIds: List<String>): List<PropertyValueEntity>
    @Query("SELECT * FROM property_value WHERE property_id = :propertyId") suspend fun valuesOf(propertyId: String): List<PropertyValueEntity>
    @Query("SELECT * FROM value_pick WHERE page_id IN (:pageIds) ORDER BY id") suspend fun picksOfPages(pageIds: List<String>): List<ValuePickEntity>
    @Query("SELECT * FROM value_pick WHERE property_id = :propertyId") suspend fun picksOf(propertyId: String): List<ValuePickEntity>
    @Query("SELECT * FROM page_view WHERE database_id = :databaseId") suspend fun viewsOf(databaseId: String): List<ViewEntity>
}

private fun stamped(hlc: Long, device: String, values: Map<String, Any?>) = Group(Stamp(hlc, device), values)

internal fun databaseTable(dao: DatabaseDao) =
    EntityTable(dao::databases, dao::allDatabases, dao::putDatabases, dao::deleteDatabases, PageDatabaseEntity::toRow, Row::toDatabaseEntity) { listOf(PAGE to it.pageId) }

internal fun propertyTable(dao: DatabaseDao) =
    EntityTable(dao::properties, dao::allProperties, dao::putProperties, dao::deleteProperties, PropertyEntity::toRow, Row::toPropertyEntity) { listOf(PAGE to it.databaseId) }

internal fun optionTable(dao: DatabaseDao) =
    EntityTable(dao::options, dao::allOptions, dao::putOptions, dao::deleteOptions, OptionEntity::toRow, Row::toOptionEntity) { listOf(PROPERTY to it.propertyId) }

internal fun valueTable(dao: DatabaseDao) =
    EntityTable(dao::values, dao::allValues, dao::putValues, dao::deleteValues, PropertyValueEntity::toRow, Row::toValueEntity) { listOf(PAGE to it.pageId, PROPERTY to it.propertyId) }

internal fun pickTable(dao: DatabaseDao) =
    EntityTable(dao::picks, dao::allPicks, dao::putPicks, dao::deletePicks, ValuePickEntity::toRow, Row::toPickEntity) { listOf(PAGE to it.pageId, PROPERTY to it.propertyId) }

internal fun viewTable(dao: DatabaseDao) =
    EntityTable(dao::views, dao::allViews, dao::putViews, dao::deleteViews, ViewEntity::toRow, Row::toViewEntity) { listOf(PAGE to it.databaseId) }

internal fun PageDatabaseEntity.toRow() = Row(PAGE_DATABASE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId)),
    DOORWAY to stamped(doorwayHlc, doorwayDevice, mapOf("label_id" to labelId)),
    LOOK to stamped(lookHlc, lookDevice, mapOf("hue" to hue)),
    BLOCKED to stamped(blockedHlc ?: 0, blockedDevice ?: "seed", mapOf("blocked_by" to blockedBy)),
))

internal fun Row.toDatabaseEntity(): PageDatabaseEntity {
    val made = groups.getValue(MADE)
    val door = groups.getValue(DOORWAY)
    val look = groups.getValue(LOOK)
    // A line written before blocked-by has no such group: nothing blocks.
    val blocked = groups[BLOCKED]
    return PageDatabaseEntity(
        id, made.values["page_id"] as String, made.stamp.hlc, made.stamp.device, door.values["label_id"] as String?, door.stamp.hlc, door.stamp.device,
        look.values["hue"] as Long?, look.stamp.hlc, look.stamp.device, blocked?.values?.get("blocked_by") as String?, blocked?.stamp?.hlc, blocked?.stamp?.device,
    )
}

internal fun PropertyEntity.toRow() = Row(PROPERTY, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("database_id" to databaseId, "target_database_id" to targetDatabaseId, "pair_property_id" to pairPropertyId)),
    NAME to stamped(nameHlc, nameDevice, mapOf("name" to name)),
    PROPERTY_TYPE to stamped(typeHlc, typeDevice, mapOf("type" to type)),
    PLACE to stamped(placeHlc, placeDevice, mapOf("sort_key" to sortKey)),
))

internal fun Row.toPropertyEntity(): PropertyEntity {
    val made = groups.getValue(MADE)
    val name = groups.getValue(NAME)
    val type = groups.getValue(PROPERTY_TYPE)
    val place = groups.getValue(PLACE)
    return PropertyEntity(
        id, made.values["database_id"] as String, made.stamp.hlc, made.stamp.device,
        name.values["name"] as String, name.stamp.hlc, name.stamp.device,
        type.values["type"] as String, type.stamp.hlc, type.stamp.device,
        place.values["sort_key"] as String, place.stamp.hlc, place.stamp.device,
        made.values["target_database_id"] as String?, made.values["pair_property_id"] as String?,
    ).also { PropertyType.valueOf(it.type) }
}

internal fun OptionEntity.toRow() = Row(PROPERTY_OPTION, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("property_id" to propertyId)),
    NAME to stamped(nameHlc, nameDevice, mapOf("name" to name)),
    LOOK to stamped(lookHlc, lookDevice, mapOf("color" to color)),
    PLACE to stamped(placeHlc, placeDevice, mapOf("sort_key" to sortKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt, "merged_into" to mergedInto)),
))

internal fun Row.toOptionEntity(): OptionEntity {
    val made = groups.getValue(MADE)
    val name = groups.getValue(NAME)
    val look = groups.getValue(LOOK)
    val place = groups.getValue(PLACE)
    val gone = groups.getValue(GONE)
    return OptionEntity(
        id, made.values["property_id"] as String, made.stamp.hlc, made.stamp.device,
        name.values["name"] as String, name.stamp.hlc, name.stamp.device,
        look.values["color"] as Long?, look.stamp.hlc, look.stamp.device,
        place.values["sort_key"] as String, place.stamp.hlc, place.stamp.device,
        gone.values["deleted_at"] as Long?, gone.values["merged_into"] as String?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun PropertyValueEntity.toRow() = Row(PROPERTY_VALUE, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "property_id" to propertyId)),
    CELL to stamped(cellHlc, cellDevice, mapOf("value" to value)),
))

internal fun Row.toValueEntity(): PropertyValueEntity {
    val made = groups.getValue(MADE)
    val cell = groups.getValue(CELL)
    return PropertyValueEntity(
        id, made.values["page_id"] as String, made.values["property_id"] as String, made.stamp.hlc, made.stamp.device,
        cell.values["value"] as String?, cell.stamp.hlc, cell.stamp.device,
    )
}

internal fun ValuePickEntity.toRow() = Row(VALUE_PICK, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("page_id" to pageId, "property_id" to propertyId, "option_id" to optionId)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toPickEntity(): ValuePickEntity {
    val made = groups.getValue(MADE)
    val gone = groups.getValue(GONE)
    return ValuePickEntity(
        id, made.values["page_id"] as String, made.values["property_id"] as String, made.values["option_id"] as String,
        made.stamp.hlc, made.stamp.device, gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    )
}

internal fun ViewEntity.toRow() = Row(PAGE_VIEW, id, mapOf(
    MADE to stamped(madeHlc, madeDevice, mapOf("database_id" to databaseId)),
    NAME to stamped(nameHlc, nameDevice, mapOf("name" to name)),
    VIEW_KIND to stamped(kindHlc, kindDevice, mapOf("view_type" to viewType, "group_by" to groupBy, "date_property" to dateProperty, "end_date_property" to endDateProperty)),
    VIEW_SHOW to stamped(showHlc, showDevice, mapOf("shown" to shown)),
    VIEW_SORT to stamped(sortHlc, sortDevice, mapOf("sort_property" to sortProperty, "sort_descending" to sortDescending)),
    VIEW_FILTER to stamped(filterHlc, filterDevice, mapOf("filter_property" to filterProperty, "filter_op" to filterOp, "filter_value" to filterValue)),
    PLACE to stamped(placeHlc, placeDevice, mapOf("sort_key" to sortKey)),
    GONE to stamped(goneHlc, goneDevice, mapOf("deleted_at" to deletedAt)),
))

internal fun Row.toViewEntity(): ViewEntity {
    val made = groups.getValue(MADE)
    val name = groups.getValue(NAME)
    val kind = groups.getValue(VIEW_KIND)
    val show = groups.getValue(VIEW_SHOW)
    val sort = groups.getValue(VIEW_SORT)
    val filter = groups.getValue(VIEW_FILTER)
    val place = groups.getValue(PLACE)
    val gone = groups.getValue(GONE)
    return ViewEntity(
        id, made.values["database_id"] as String, made.stamp.hlc, made.stamp.device,
        name.values["name"] as String, name.stamp.hlc, name.stamp.device,
        kind.values["view_type"] as String, kind.values["group_by"] as String?, kind.values["date_property"] as String?, kind.values["end_date_property"] as String?,
        kind.stamp.hlc, kind.stamp.device,
        show.values["shown"] as String?, show.stamp.hlc, show.stamp.device,
        sort.values["sort_property"] as String?, sort.values["sort_descending"] as Boolean, sort.stamp.hlc, sort.stamp.device,
        filter.values["filter_property"] as String?, filter.values["filter_op"] as String?, filter.values["filter_value"] as String?, filter.stamp.hlc, filter.stamp.device,
        place.values["sort_key"] as String, place.stamp.hlc, place.stamp.device,
        gone.values["deleted_at"] as Long?, gone.stamp.hlc, gone.stamp.device,
    ).also { v -> ViewType.valueOf(v.viewType); v.filterOp?.let(FilterOp::valueOf) }
}
