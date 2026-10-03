package com.factotum.data.page

import com.factotum.core.label.LabelScope
import com.factotum.core.page.keyBetween
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.label.labelKey
import com.factotum.data.label.nfc
import com.factotum.data.label.resolver
import com.factotum.data.sync.readChunked
import kotlinx.datetime.LocalDate

data class Property(val id: String, val name: String, val type: PropertyType)

data class SelectOption(val id: String, val name: String, val color: Long?)

/**
 * A cell as read under its property's type now (a type change rewrites no value, owner 2026-10-03):
 * [text] for the text types and the names of the options, [number], [date] and [checked] when the
 * stored text reads as one, and [options] the live options picked, merged ones read as their target.
 */
data class Cell(val text: String?, val number: Double?, val date: LocalDate?, val checked: Boolean, val options: List<String>)

data class DatabaseRow(val pageId: String, val title: String, val cells: Map<String, Cell>)

/** A Board column: the rows whose Select is [optionId], or that have none ([optionId] null, first). */
data class BoardColumn(val optionId: String?, val rows: List<DatabaseRow>)

data class View(
    val id: String, val name: String, val type: ViewType, val groupBy: String?, val dateProperty: String?, val endDateProperty: String?,
    val shown: List<String>?, val sortProperty: String?, val sortDescending: Boolean, val filterProperty: String?, val filterOp: FilterOp?, val filterValue: String?,
)

/**
 * Tendril's page databases (ADR 12, slice 12b): a database page, its properties, a Select's options
 * as rows, each page's values, and views. Its rows are the pages made in it (its sub-pages) and the
 * pages carrying its doorway label (owner, 2026-10-03). Every row syncs per ADR 01 group; a cell is
 * kept when a sync replaces it, like a block's text (ADR 12).
 */
internal class DatabaseRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
    private val pages: PageRepository,
) {
    private val dao = db.databaseDao()
    private val pageDao = db.pageDao()
    private val labels = db.labelDao()
    private val clock = writes.clock

    /** A new database page under [parentId], with one table view. */
    suspend fun create(title: String, parentId: String? = null): String {
        val id = newId()
        val view = newId()
        writes.write({
            parentId?.let { live(it) }
            mapOf(PAGE to listOf(id), PAGE_DATABASE to listOf(shellId(id)), PAGE_VIEW to listOf(view))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, newPageRow(id, s, title, null, parentId, DATABASE_KIND))
            writes.merger.created(store, Row(PAGE_DATABASE, shellId(id), mapOf(
                MADE to Group(s, mapOf("page_id" to id)),
                DOORWAY to Group(s, mapOf("label_id" to null)),
                LOOK to Group(s, mapOf("hue" to null)),
            )))
            writes.merger.created(store, newView(view, id, s, "Table", ViewType.TABLE, keyBetween(null, null)))
        }
        return id
    }

    /** The label whose pages are rows too (ADR 08's doorway), or none. */
    suspend fun setDoorway(databaseId: String, labelId: String?) = writes.write({
        shell(databaseId)
        labelId?.let { l -> require(labels.labels(listOf(l)).singleOrNull()?.takeIf { it.deletedAt == null && LabelScope.valueOf(it.appliesTo) == LabelScope.ALL } != null) { "label $l is not offered here" } }
        mapOf(PAGE_DATABASE to listOf(shellId(databaseId)))
    }) { store, _ -> store.put(requireNotNull(store.row(shellId(databaseId))).edit(DOORWAY, clock.tick(), mapOf("label_id" to labelId))) }

    suspend fun setHue(databaseId: String, hue: Int?) {
        require(hue == null || hue in 0..359) { "a hue is 0 to 359" }
        writes.write({ shell(databaseId); mapOf(PAGE_DATABASE to listOf(shellId(databaseId))) }) { store, _ ->
            store.put(requireNotNull(store.row(shellId(databaseId))).edit(LOOK, clock.tick(), mapOf("hue" to hue?.toLong())))
        }
    }

    /** The database's rows: the pages made in it and the pages carrying its doorway label, by id (a ULID begins with the time it was made). */
    suspend fun members(databaseId: String): List<String> {
        val shell = shell(databaseId)
        val made = pageDao.childrenOf(databaseId).filter { it.deletedAt == null }.map { it.id }
        val all = labels.allLabels()
        val r = resolver(all)
        val doorway = shell.labelId?.let(r)
        val labelled = if (doorway == null) emptyList() else {
            val carrying = readChunked(all.map { it.id }.filter { r(it) == doorway }) { pageDao.pagesLabelled(it) }.map { it.pageId }.distinct()
            readChunked(carrying) { pageDao.pages(it) }.filter { it.deletedAt == null && it.id != databaseId }.map { it.id }
        }
        return (made + labelled).distinct().sorted()
    }

    suspend fun properties(databaseId: String): List<Property> =
        dao.propertiesOf(databaseId).sortedWith(compareBy({ it.sortKey }, { it.id })).map { Property(it.id, it.name, PropertyType.valueOf(it.type)) }

    /** Adds a property after [after] (first when null). */
    suspend fun addProperty(databaseId: String, name: String, type: PropertyType, after: String? = null): String {
        val id = newId()
        var key = ""
        writes.write({
            shell(databaseId)
            key = placeAfter(dao.propertiesOf(databaseId).map { it.id to it.sortKey }, after)
            mapOf(PROPERTY to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(PROPERTY, id, mapOf(
                MADE to Group(s, mapOf("database_id" to databaseId)),
                NAME to Group(s, mapOf("name" to checkedName(name))),
                PROPERTY_TYPE to Group(s, mapOf("type" to type.name)),
                PLACE to Group(s, mapOf("sort_key" to key)),
            )))
        }
        return id
    }

    suspend fun renameProperty(id: String, name: String) = edit(PROPERTY, id, NAME, { property(id) }) { mapOf("name" to checkedName(name)) }

    suspend fun moveProperty(id: String, after: String?) {
        var key = ""
        edit(PROPERTY, id, PLACE, { key = placeAfter(dao.propertiesOf(property(id).databaseId).filter { it.id != id }.map { it.id to it.sortKey }, after) }) { mapOf("sort_key" to key) }
    }

    /**
     * Changes a property's type. No value is rewritten (owner, 2026-10-03): each is read under the
     * new type, and changing back reads it as before. A change to a Select or a Multi-select makes
     * an option for each stored text no option has yet, so those values read as picked.
     */
    suspend fun setType(id: String, type: PropertyType) {
        var made = emptyList<Pair<String, String>>()
        var last: String? = null
        writes.write({
            property(id)
            if (type == PropertyType.SELECT || type == PropertyType.MULTI_SELECT) {
                val options = dao.optionsOf(listOf(id))
                val known = options.map { it.id }.toSet() + options.filter { it.deletedAt == null }.map { labelKey(it.name) }
                val texts = dao.valuesOf(id).mapNotNull { it.value }
                    .flatMap { if (type == PropertyType.MULTI_SELECT) it.split(',') else listOf(it) }.map { nfc(it.trim()) }
                    .filter { it.isNotEmpty() && it !in known && labelKey(it) !in known }.distinctBy(::labelKey)
                made = texts.map { newId() to it }
                last = options.maxOfOrNull { it.sortKey }
            }
            mapOf(PROPERTY to listOf(id), PROPERTY_OPTION to made.map { it.first })
        }) { store, _ ->
            val s = clock.tick()
            store.put(requireNotNull(store.row(id)).edit(PROPERTY_TYPE, s, mapOf("type" to type.name)))
            for ((optionId, name) in made) {
                last = keyBetween(last, null)
                writes.merger.created(store, newOption(optionId, id, s, name, null, last!!))
            }
        }
    }

    /** Deletes a property for good, with its values and options (ADR 12: the schema is deleted only by a purge). */
    suspend fun deleteProperty(id: String) = writes.write({ property(id); mapOf(PROPERTY to listOf(id)) }) { store, _ -> writes.merger.purge(store, id) }

    /** The live options of a Select or Multi-select, in order. */
    suspend fun options(propertyId: String): List<SelectOption> =
        dao.optionsOf(listOf(propertyId)).filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id })).map { SelectOption(it.id, it.name, it.color) }

    /** A new option, last; its name is not another live option's of this property, ignoring case. */
    suspend fun addOption(propertyId: String, name: String, color: Long? = null): String {
        val id = newId()
        var clean = ""
        var key = ""
        writes.write({
            choice(propertyId)
            clean = uniqueOption(propertyId, name, except = null)
            key = keyBetween(dao.optionsOf(listOf(propertyId)).maxOfOrNull { it.sortKey }, null)
            mapOf(PROPERTY_OPTION to listOf(id))
        }) { store, _ -> writes.merger.created(store, newOption(id, propertyId, clock.tick(), clean, color, key)) }
        return id
    }

    suspend fun renameOption(id: String, name: String) {
        var clean = ""
        edit(PROPERTY_OPTION, id, NAME, { clean = uniqueOption(liveOption(id).propertyId, name, except = id) }) { mapOf("name" to clean) }
    }

    suspend fun recolorOption(id: String, color: Long?) = edit(PROPERTY_OPTION, id, LOOK, { liveOption(id) }) { mapOf("color" to color) }

    suspend fun moveOption(id: String, after: String?) {
        var key = ""
        edit(PROPERTY_OPTION, id, PLACE, {
            val option = liveOption(id)
            key = placeAfter(dao.optionsOf(listOf(option.propertyId)).filter { it.deletedAt == null && it.id != id }.map { it.id to it.sortKey }, after)
        }) { mapOf("sort_key" to key) }
    }

    /** Deletes an option: the cells that picked it read as empty and keep the pick, which brings it back if made again elsewhere (owner, 2026-10-03). */
    suspend fun deleteOption(id: String) = edit(PROPERTY_OPTION, id, GONE, { liveOption(id) }) { s -> mapOf("deleted_at" to s.hlc, "merged_into" to null) }

    /** Sets a text, URL, e-mail or phone cell; blank clears it. */
    suspend fun setText(pageId: String, propertyId: String, text: String?) =
        setCell(pageId, propertyId, setOf(PropertyType.TEXT, PropertyType.URL, PropertyType.EMAIL, PropertyType.PHONE)) { text?.takeIf { it.isNotBlank() } }

    suspend fun setNumber(pageId: String, propertyId: String, number: Double?) = setCell(pageId, propertyId, setOf(PropertyType.NUMBER)) {
        number?.also { require(it.isFinite()) { "a number is finite" } }?.let(::canonical)
    }

    suspend fun setChecked(pageId: String, propertyId: String, checked: Boolean) = setCell(pageId, propertyId, setOf(PropertyType.CHECKBOX)) { checked.toString() }

    suspend fun setDate(pageId: String, propertyId: String, date: LocalDate?) = setCell(pageId, propertyId, setOf(PropertyType.DATE)) { date?.toString() }

    /** Picks a Select's option, or none; moving a Board card is this. */
    suspend fun setOption(pageId: String, propertyId: String, optionId: String?) = setCell(pageId, propertyId, setOf(PropertyType.SELECT)) {
        optionId?.also { o -> require(liveOption(o).propertyId == propertyId) { "option $o is not $propertyId's" } }
    }

    /** Picks an option in a Multi-select cell; picks made on two devices both stay (owner, 2026-10-03). */
    suspend fun pick(pageId: String, propertyId: String, optionId: String) = pages.snapshotIfDue(pageId).let { writes.write({
        member(pageId, property(propertyId), setOf(PropertyType.MULTI_SELECT))
        require(liveOption(optionId).propertyId == propertyId) { "option $optionId is not $propertyId's" }
        mapOf(VALUE_PICK to listOf(pickId(pageId, propertyId, optionId)))
    }) { store, targets ->
        val id = targets.getValue(VALUE_PICK).single()
        val s = clock.tick()
        val row = store.row(id)
        if (row == null) {
            writes.merger.created(store, Row(VALUE_PICK, id, mapOf(
                MADE to Group(s, mapOf("page_id" to pageId, "property_id" to propertyId, "option_id" to optionId)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        } else if (row.groups.getValue(GONE).values["deleted_at"] != null) {
            store.put(row.edit(GONE, s, mapOf("deleted_at" to null)))
        }
    } }

    /**
     * Takes an option out of a Multi-select cell, with any option merged into it, as the cell shows
     * them as one; a pick the cell's text makes (it was another type before) is taken out of the text.
     */
    suspend fun unpick(pageId: String, propertyId: String, optionId: String) {
        pages.snapshotIfDue(pageId)
        var text: String? = null
        writes.write({
            property(propertyId)
            val options = dao.optionsOf(listOf(propertyId))
            val r = optionResolver(options)
            val tokens = tokensOf(dao.values(listOf(valueId(pageId, propertyId))).singleOrNull()?.value)
            val kept = tokens.filter { optionOfToken(it, options, r) != optionId }
            text = kept.joinToString(", ").ifEmpty { null }
            mapOf(
                VALUE_PICK to dao.picksOfPages(listOf(pageId)).filter { it.propertyId == propertyId && it.deletedAt == null && r(it.optionId) == optionId }.map { it.id },
                PROPERTY_VALUE to if (kept.size != tokens.size) listOf(valueId(pageId, propertyId)) else emptyList(),
            )
        }) { store, targets ->
            val s = clock.tick()
            targets.getValue(VALUE_PICK).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to s.hlc))) }
            targets.getValue(PROPERTY_VALUE).forEach { store.put(requireNotNull(store.row(it)).edit(CELL, s, mapOf("value" to text))) }
        }
    }

    /** The cells of [pageId] for [databaseId]'s properties, read under their types now. */
    suspend fun cells(databaseId: String, pageId: String): Map<String, Cell> = read(databaseId, listOf(pageId)).single().cells

    /** The live views, in order; a shown property deleted since is left out. */
    suspend fun views(databaseId: String): List<View> {
        val properties = dao.propertiesOf(databaseId).map { it.id }.toSet()
        return dao.viewsOf(databaseId).filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id }))
            .map { v -> v.toView().let { it.copy(shown = it.shown?.filter(properties::contains)) } }
    }

    suspend fun addView(databaseId: String, name: String, type: ViewType): String {
        val id = newId()
        var key = ""
        writes.write({
            shell(databaseId)
            key = placeAfter(dao.viewsOf(databaseId).filter { it.deletedAt == null }.map { it.id to it.sortKey }, null, last = true)
            mapOf(PAGE_VIEW to listOf(id))
        }) { store, _ -> writes.merger.created(store, newView(id, databaseId, clock.tick(), checkedName(name), type, key)) }
        return id
    }

    suspend fun renameView(id: String, name: String) = edit(PAGE_VIEW, id, NAME, { liveView(id) }) { mapOf("name" to checkedName(name)) }

    /** A view's layout: its type, the Select a Board groups by, and the dates a Calendar or a Timeline reads. */
    suspend fun setLayout(id: String, type: ViewType, groupBy: String? = null, dateProperty: String? = null, endDateProperty: String? = null) =
        edit(PAGE_VIEW, id, VIEW_KIND, {
            val view = liveView(id)
            groupBy?.let { ofType(view.databaseId, it, PropertyType.SELECT) }
            dateProperty?.let { ofType(view.databaseId, it, PropertyType.DATE) }
            endDateProperty?.let { ofType(view.databaseId, it, PropertyType.DATE) }
        }) { mapOf("view_type" to type.name, "group_by" to groupBy, "date_property" to dateProperty, "end_date_property" to endDateProperty) }

    /** The properties a view shows, in order; null shows them all. */
    suspend fun setShown(id: String, shown: List<String>?) = edit(PAGE_VIEW, id, VIEW_SHOW, {
        val view = liveView(id)
        require(shown == null || shown.distinct().size == shown.size) { "a property is shown once" }
        shown?.forEach { ofType(view.databaseId, it, null) }
    }) { mapOf("shown" to shown?.joinToString(",")) }

    suspend fun setSort(id: String, propertyId: String?, descending: Boolean = false) = edit(PAGE_VIEW, id, VIEW_SORT, {
        propertyId?.let { ofType(liveView(id).databaseId, it, null) }
    }) { mapOf("sort_property" to propertyId, "sort_descending" to descending) }

    suspend fun setFilter(id: String, propertyId: String?, op: FilterOp? = null, value: String? = null) = edit(PAGE_VIEW, id, VIEW_FILTER, {
        require((propertyId == null) == (op == null)) { "a filter has a property and a test" }
        propertyId?.let { ofType(liveView(id).databaseId, it, null) }
    }) { mapOf("filter_property" to propertyId, "filter_op" to op?.name, "filter_value" to value) }

    suspend fun moveView(id: String, after: String?) {
        var key = ""
        edit(PAGE_VIEW, id, PLACE, {
            val view = liveView(id)
            key = placeAfter(dao.viewsOf(view.databaseId).filter { it.deletedAt == null && it.id != id }.map { it.id to it.sortKey }, after)
        }) { mapOf("sort_key" to key) }
    }

    /** Deletes a view; a database keeps at least one. */
    suspend fun deleteView(id: String) = edit(PAGE_VIEW, id, GONE, {
        val view = liveView(id)
        require(dao.viewsOf(view.databaseId).count { it.deletedAt == null } > 1) { "a database keeps one view" }
    }) { s -> mapOf("deleted_at" to s.hlc) }

    /**
     * A view's rows: the members passing its filter, in its sort (typed: numbers as numbers, dates
     * as dates, a Select by its options' order), an empty cell last either way, then oldest first.
     * A setting naming a property that is gone reads as no setting; a filter naming an option merged
     * since reads as the option it went into.
     */
    suspend fun rows(viewId: String): List<DatabaseRow> {
        val view = liveView(viewId)
        val properties = dao.propertiesOf(view.databaseId).associateBy { it.id }
        val options = readChunked(properties.keys.toList()) { dao.optionsOf(it) }
        val optionOrder = options.associate { it.id to orderKey(it) }
        var rows = read(view.databaseId, members(view.databaseId))
        val filter = view.filterProperty?.let(properties::get)
        if (filter != null && view.filterOp != null) {
            val type = PropertyType.valueOf(filter.type)
            val op = FilterOp.valueOf(view.filterOp)
            val value = if (type == PropertyType.SELECT || type == PropertyType.MULTI_SELECT) view.filterValue?.let { optionResolver(options)(it) ?: it } else view.filterValue
            rows = rows.filter { passes(it.cells.getValue(filter.id), type, op, value) }
        }
        val sort = view.sortProperty?.let(properties::get) ?: return rows
        val type = PropertyType.valueOf(sort.type)
        val (empty, full) = rows.partition { isEmpty(it.cells.getValue(sort.id), type) }
        val byValue = Comparator<DatabaseRow> { a, b -> compare(a.cells.getValue(sort.id), b.cells.getValue(sort.id), type, optionOrder) }
        return full.sortedWith(if (view.sortDescending) byValue.reversed() else byValue) + empty
    }

    /** A Board: a column for no option, then one per live option in order. Null when the view groups by no Select (the screen's empty state). */
    suspend fun board(viewId: String): List<BoardColumn>? {
        val view = liveView(viewId)
        val property = view.groupBy?.let { dao.properties(listOf(it)).singleOrNull() }?.takeIf { it.type == PropertyType.SELECT.name } ?: return null
        val rows = rows(viewId)
        val columns = listOf<String?>(null) + options(property.id).map { it.id }
        return columns.map { o -> BoardColumn(o, rows.filter { it.cells.getValue(property.id).options.firstOrNull() == o }) }
    }

    /**
     * After every import: an option deleted on one device and picked later on another, itself or an
     * option merged into it, comes back (owner, 2026-10-03), stamped just above its deletion as a
     * revived page is; then live options of one property with one name merge into the one with the
     * lowest id, the one made first (owner, 2026-10-03, ADR 08's rule). A merge is stamped just above
     * the merged option's own last stamp, not with a fresh tick: every device writes the same row, and
     * a merge is never an edit that would bring back a trashed database (ADR 12's revive).
     */
    suspend fun settle() {
        var back = emptyMap<String, Stamp>()
        writes.write({
            val all = dao.allOptions()
            val byId = all.associateBy { it.id }
            val deleted = all.filter { it.deletedAt != null && it.mergedInto == null }.associateBy { it.id }
            val found = HashMap<String, Stamp>()
            if (deleted.isNotEmpty()) {
                fun touch(optionId: String?, at: Stamp) {
                    val end = generateSequence(optionId?.let(byId::get)) { it.mergedInto?.let(byId::get) }.take(all.size + 1).lastOrNull()
                    val o = end?.id?.let(deleted::get) ?: return
                    if (at.byHand && at > Stamp(o.goneHlc, o.goneDevice)) found[o.id] = Stamp(o.goneHlc, o.goneDevice)
                }
                val properties = all.filter { it.deletedAt != null }.map { it.propertyId }.distinct()
                properties.flatMap { dao.valuesOf(it) }.forEach { touch(it.value, Stamp(it.cellHlc, it.cellDevice)) }
                properties.flatMap { dao.picksOf(it) }.filter { it.deletedAt == null }.forEach { touch(it.optionId, maxOf(Stamp(it.madeHlc, it.madeDevice), Stamp(it.goneHlc, it.goneDevice))) }
            }
            back = found
            mapOf(PROPERTY_OPTION to found.keys.toList())
        }) { store, _ ->
            for ((id, gone) in back) store.put(requireNotNull(store.row(id)).edit(GONE, automatic(gone), mapOf("deleted_at" to null, "merged_into" to null)))
        }
        var into = emptyMap<String, Pair<String, Stamp>>()
        writes.write({
            into = dao.allOptions().filter { it.deletedAt == null }.groupBy { it.propertyId to labelKey(it.name) }.values.filter { it.size > 1 }
                .flatMap { same -> val first = same.minOf { it.id }; same.filter { it.id != first }.map { it.id to (first to it.lastStamp()) } }.toMap()
            mapOf(PROPERTY_OPTION to into.keys.toList())
        }) { store, _ ->
            for ((id, merge) in into) {
                val (survivor, last) = merge
                store.put(requireNotNull(store.row(id)).edit(GONE, automatic(last), mapOf("deleted_at" to last.hlc, "merged_into" to survivor)))
            }
        }
    }

    private suspend fun read(databaseId: String, pageIds: List<String>): List<DatabaseRow> {
        val properties = dao.propertiesOf(databaseId)
        val options = readChunked(properties.map { it.id }) { dao.optionsOf(it) }
        val r = optionResolver(options)
        val byProperty = options.groupBy { it.propertyId }
        val values = readChunked(pageIds) { dao.valuesOfPages(it) }.associateBy { it.pageId to it.propertyId }
        val picks = readChunked(pageIds) { dao.picksOfPages(it) }.filter { it.deletedAt == null }.groupBy({ it.pageId to it.propertyId }, { it.optionId })
        val titles = readChunked(pageIds) { pageDao.pages(it) }.associate { it.id to it.title }
        return pageIds.map { pageId ->
            DatabaseRow(pageId, titles[pageId].orEmpty(), properties.associate { p ->
                val raw = values[pageId to p.id]?.value
                p.id to cellOf(PropertyType.valueOf(p.type), raw, picks[pageId to p.id].orEmpty(), byProperty[p.id].orEmpty(), r)
            })
        }
    }

    private suspend fun setCell(pageId: String, propertyId: String, types: Set<PropertyType>, value: suspend () -> String?) {
        pages.snapshotIfDue(pageId)
        var v: String? = null
        writes.write({
            member(pageId, property(propertyId), types)
            v = value()
            mapOf(PROPERTY_VALUE to listOf(valueId(pageId, propertyId)))
        }) { store, targets ->
            val id = targets.getValue(PROPERTY_VALUE).single()
            val s = clock.tick()
            val row = store.row(id)
            if (row == null) {
                if (v == null) return@write
                // No base: another device may fill this cell first, under the same id, and the two
                // must meet as a clash, not as one side's agreed version (ADR 12's notice).
                store.put(Row(PROPERTY_VALUE, id, mapOf(
                    MADE to Group(s, mapOf("page_id" to pageId, "property_id" to propertyId)),
                    CELL to Group(s, mapOf("value" to v)),
                )))
            } else if (row.groups.getValue(CELL).values["value"] != v) {
                store.put(row.edit(CELL, s, mapOf("value" to v)))
            }
        }
    }

    /** Changes one group of a row, after [check] inside the write. */
    private suspend fun edit(table: String, id: String, group: String, check: suspend () -> Unit, values: (Stamp) -> Map<String, Any?>) = writes.write({
        check()
        mapOf(table to listOf(id))
    }) { store, _ -> val s = clock.tick(); store.put(requireNotNull(store.row(id)).edit(group, s, values(s))) }

    private suspend fun member(pageId: String, property: PropertyEntity, types: Set<PropertyType>) {
        require(PropertyType.valueOf(property.type) in types) { "${property.name} is a ${property.type}" }
        val db = property.databaseId
        val page = pageDao.pages(listOf(pageId)).singleOrNull()?.takeIf { it.deletedAt == null && it.id != db }
        val r = resolver(labels.allLabels())
        val doorway = shell(db).labelId?.let(r)
        val labelled = doorway != null && pageDao.labelsOfPages(listOf(pageId)).any { it.deletedAt == null && r(it.labelId) == doorway }
        require(page != null && (page.parentId == db || labelled)) { "page $pageId is not a row of $db" }
    }

    private suspend fun ofType(databaseId: String, propertyId: String, type: PropertyType?) {
        val p = property(propertyId)
        require(p.databaseId == databaseId) { "$propertyId is not this database's" }
        require(type == null || p.type == type.name) { "${p.name} is not a $type" }
    }

    private suspend fun uniqueOption(propertyId: String, name: String, except: String?): String {
        val clean = checkedName(name)
        require(dao.optionsOf(listOf(propertyId)).none { it.deletedAt == null && it.id != except && labelKey(it.name) == labelKey(clean) }) { "there is already an option \"$clean\"" }
        return clean
    }

    private suspend fun choice(propertyId: String) = property(propertyId).also {
        require(it.type == PropertyType.SELECT.name || it.type == PropertyType.MULTI_SELECT.name) { "${it.name} has no options" }
    }

    private suspend fun shell(id: String) = requireNotNull(dao.databases(listOf(shellId(id))).singleOrNull()?.takeIf { pageDao.pages(listOf(id)).singleOrNull()?.deletedAt == null }) { "no database $id" }

    /** A property of a live database: an edit to a trashed one's would bring it back (ADR 12's revive). */
    private suspend fun property(id: String) = requireNotNull(dao.properties(listOf(id)).singleOrNull()) { "no property $id" }.also { shell(it.databaseId) }

    private suspend fun liveOption(id: String) = requireNotNull(dao.options(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no option $id" }.also { property(it.propertyId) }

    private suspend fun liveView(id: String) = requireNotNull(dao.views(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no view $id" }.also { shell(it.databaseId) }

    private suspend fun live(id: String) = requireNotNull(pageDao.pages(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no page $id" }
}

internal const val DATABASE_KIND = "DATABASE"

private fun checkedName(name: String): String = nfc(name.trim()).also { require(it.isNotEmpty()) { "a name is needed" } }

/** A key after [after] (first when null, or last when [last]) among (id, key) pairs. */
private fun placeAfter(siblings: List<Pair<String, String>>, after: String?, last: Boolean = false): String {
    val ordered = siblings.sortedWith(compareBy({ it.second }, { it.first }))
    if (last) return keyBetween(ordered.lastOrNull()?.second, null)
    val before = after?.let { a -> requireNotNull(ordered.firstOrNull { it.first == a }) { "no $a here" }.second }
    return keyBetween(before, ordered.firstOrNull { before == null || it.second > before }?.second)
}

/** A stored text read as a Multi-select's: its comma-separated parts. */
private fun tokensOf(raw: String?): List<String> = raw?.split(',')?.map { it.trim() }?.filter { it.isNotEmpty() }.orEmpty()

/** The live option a stored text names: an option id of this property (read through merges), or a live option's name. */
private fun optionOfToken(token: String, options: List<OptionEntity>, resolve: (String?) -> String?): String? =
    if (options.any { it.id == token }) resolve(token) else options.firstOrNull { it.deletedAt == null && labelKey(it.name) == labelKey(token) }?.id

/** An option's place, ties between options placed apart broken by id as the Board breaks them. */
private fun orderKey(o: OptionEntity) = o.sortKey + "\u0000" + o.id

private fun OptionEntity.lastStamp() = listOf(Stamp(madeHlc, madeDevice), Stamp(nameHlc, nameDevice), Stamp(lookHlc, lookDevice), Stamp(placeHlc, placeDevice), Stamp(goneHlc, goneDevice)).max()

/** Reads an option id as the live option it stands for: itself, the one it was merged into, or none once deleted. */
private fun optionResolver(options: List<OptionEntity>): (String?) -> String? {
    val byId = options.associateBy { it.id }
    return { start ->
        generateSequence(start?.let(byId::get)) { it.mergedInto?.let(byId::get) }.take(options.size + 1).firstOrNull { it.deletedAt == null }?.id
    }
}

/**
 * One cell under [type]. A stored text is read for what it can be: an option's id or name for a
 * Select (so text changed into a Select reads as picked), a number, a date, `true`; a text type
 * reads an option id as its name. A Multi-select is its picks and any options its text names.
 */
private fun cellOf(type: PropertyType, raw: String?, picks: List<String>, options: List<OptionEntity>, resolve: (String?) -> String?): Cell {
    val names = options.associate { it.id to it.name }
    val order = options.associate { it.id to orderKey(it) }
    val picked = when (type) {
        // A Multi-select changed into a Select reads its first pick.
        PropertyType.SELECT -> listOfNotNull(raw?.let { optionOfToken(it, options, resolve) } ?: picks.mapNotNull(resolve).minByOrNull { order.getValue(it) })
        PropertyType.MULTI_SELECT -> (picks.mapNotNull(resolve) + tokensOf(raw).mapNotNull { optionOfToken(it, options, resolve) }).distinct()
        else -> emptyList()
    }
    val text = when (type) {
        PropertyType.SELECT, PropertyType.MULTI_SELECT -> picked.joinToString(", ") { names.getValue(it) }.ifEmpty { null }
        else -> raw?.let { if (it in names) resolve(it)?.let(names::getValue) else it }
            ?: picks.mapNotNull(resolve).distinct().joinToString(", ") { names.getValue(it) }.ifEmpty { null }
    }
    return Cell(
        text = text,
        number = raw?.toDoubleOrNull()?.takeIf { it.isFinite() },
        date = raw?.let { runCatching { LocalDate.parse(it) }.getOrNull() },
        checked = raw == "true",
        options = picked,
    )
}

private fun isEmpty(cell: Cell, type: PropertyType) = when (type) {
    PropertyType.NUMBER -> cell.number == null
    PropertyType.DATE -> cell.date == null
    PropertyType.CHECKBOX -> !cell.checked
    PropertyType.SELECT, PropertyType.MULTI_SELECT -> cell.options.isEmpty()
    else -> cell.text == null
}

private fun compare(a: Cell, b: Cell, type: PropertyType, optionOrder: Map<String, String>): Int = when (type) {
    PropertyType.NUMBER -> compareValues(a.number, b.number)
    PropertyType.DATE -> compareValues(a.date, b.date)
    PropertyType.CHECKBOX -> compareValues(a.checked, b.checked)
    PropertyType.SELECT, PropertyType.MULTI_SELECT -> compareValues(a.options.firstOrNull()?.let(optionOrder::get), b.options.firstOrNull()?.let(optionOrder::get))
    else -> compareValues(a.text?.lowercase(), b.text?.lowercase())
}

/** Tendril's single filter, typed: a Select or Multi-select is compared by option id, a number as a number, a date as a date. */
private fun passes(cell: Cell, type: PropertyType, op: FilterOp, value: String?): Boolean {
    fun equal(): Boolean = when (type) {
        PropertyType.SELECT, PropertyType.MULTI_SELECT -> value in cell.options
        PropertyType.NUMBER -> value?.toDoubleOrNull()?.let { it == cell.number } == true
        PropertyType.DATE -> value != null && runCatching { LocalDate.parse(value) }.getOrNull() == cell.date
        PropertyType.CHECKBOX -> (value == "true") == cell.checked
        else -> cell.text != null && value != null && cell.text.equals(value, ignoreCase = true)
    }
    return when (op) {
        FilterOp.IS_EMPTY -> isEmpty(cell, type)
        FilterOp.IS_NOT_EMPTY -> !isEmpty(cell, type)
        FilterOp.EQUALS -> equal()
        FilterOp.NOT_EQUALS -> !equal()
        FilterOp.CONTAINS -> when (type) {
            PropertyType.SELECT, PropertyType.MULTI_SELECT -> value in cell.options
            else -> value != null && cell.text?.contains(value, ignoreCase = true) == true
        }
    }
}

/** A number in one form: a whole number without a fraction, any other as Kotlin writes a Double. */
private fun canonical(n: Double): String = if (n == kotlin.math.floor(n) && kotlin.math.abs(n) < 1e15) n.toLong().toString() else n.toString()

private fun newOption(id: String, propertyId: String, s: Stamp, name: String, color: Long?, key: String) = Row(PROPERTY_OPTION, id, mapOf(
    MADE to Group(s, mapOf("property_id" to propertyId)),
    NAME to Group(s, mapOf("name" to name)),
    LOOK to Group(s, mapOf("color" to color)),
    PLACE to Group(s, mapOf("sort_key" to key)),
    GONE to Group(s, mapOf("deleted_at" to null, "merged_into" to null)),
))

private fun newView(id: String, databaseId: String, s: Stamp, name: String, type: ViewType, key: String) = Row(PAGE_VIEW, id, mapOf(
    MADE to Group(s, mapOf("database_id" to databaseId)),
    NAME to Group(s, mapOf("name" to name)),
    VIEW_KIND to Group(s, mapOf("view_type" to type.name, "group_by" to null, "date_property" to null, "end_date_property" to null)),
    VIEW_SHOW to Group(s, mapOf("shown" to null)),
    VIEW_SORT to Group(s, mapOf("sort_property" to null, "sort_descending" to false)),
    VIEW_FILTER to Group(s, mapOf("filter_property" to null, "filter_op" to null, "filter_value" to null)),
    PLACE to Group(s, mapOf("sort_key" to key)),
    GONE to Group(s, mapOf("deleted_at" to null)),
))

private fun ViewEntity.toView() = View(
    id, name, ViewType.valueOf(viewType), groupBy, dateProperty, endDateProperty, shown?.split(',')?.filter { it.isNotEmpty() },
    sortProperty, sortDescending, filterProperty, filterOp?.let(FilterOp::valueOf), filterValue,
)
