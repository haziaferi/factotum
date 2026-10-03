package com.factotum.data.page

import com.factotum.core.page.keyBetween
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.sync.readChunked

/**
 * Tendril's templates (ADR 12, slice 12d): a template is a page of its own, flagged when made, kept
 * out of the tree, the links and the pickers. Saving one and making a page from one both copy the
 * structure, not the content (owner, 2026-10-03): a page's blocks; a database's properties with
 * their options, its views and its colour, never its rows or its doorway label; a canvas's whole
 * board, mind-map links included (Tendril dropped them). No sub-page or label is copied, and a copy
 * is independent of what it came from. Every copy is a new row with a new id, in one write.
 */
internal class TemplateRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val pageDao = db.pageDao()
    private val databases = db.databaseDao()
    private val canvases = db.canvasDao()
    private val clock = writes.clock

    /** A template copied from [pageId], at the top level. */
    suspend fun saveAsTemplate(pageId: String): String = copy(pageId, title = null, parentId = null, template = true)

    /** A new page from the template [templateId], titled [title], under [parentId]. */
    suspend fun create(templateId: String, title: String, parentId: String? = null): String {
        require(pageDao.pages(listOf(templateId)).singleOrNull()?.isTemplate == true) { "$templateId is not a template" }
        return copy(templateId, title, parentId, template = false)
    }

    /** The live templates, by title. */
    suspend fun templates(): List<Page> = pageDao.allPages().filter { it.isTemplate == true && it.deletedAt == null }
        .sortedWith(compareBy({ it.title.lowercase() }, { it.id })).map { Page(it.id, it.title, it.icon, it.parentId, false) }

    private suspend fun copy(sourceId: String, title: String?, parentId: String?, template: Boolean): String {
        val id = newId()
        var rows = emptyList<Row>()
        writes.write({
            val source = requireNotNull(pageDao.pages(listOf(sourceId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no page $sourceId" }
            parentId?.let { p -> requireNotNull(pageDao.pages(listOf(p)).singleOrNull()?.takeIf { it.deletedAt == null && it.isTemplate != true }) { "no page $p" } }
            val made = mutableListOf(newPageRow(id, UNSTAMPED, title ?: source.title, source.icon, parentId, source.kind, template))
            made += blocks(sourceId, id)
            made += database(sourceId, id, title ?: source.title, template)
            made += canvas(sourceId, id)
            rows = made
            made.groupBy({ it.table }, { it.id })
        }) { store, _ ->
            val s = clock.tick()
            rows.forEach { writes.merger.created(store, it.restamped(s)) }
        }
        return id
    }

    /** The source's live blocks under new ids, nested and ordered as they were; a reference to one of them follows it. */
    private suspend fun blocks(sourceId: String, pageId: String): List<Row> {
        val blocks = pageDao.blocksOf(sourceId).filter { it.deletedAt == null }
        val ids = blocks.associate { it.id to newId() }
        return blocks.map { b ->
            b.copy(id = ids.getValue(b.id), pageId = pageId, parentBlockId = b.parentBlockId?.let(ids::get), referencedBlockId = b.referencedBlockId?.let { ids[it] ?: it }).toRow()
        }
    }

    /**
     * The source's database part: the shell with its colour, the properties, the live options of each
     * and the live views, every reference among them following its copy. A relation column relates to
     * the same database with a new matching column there, or to the copy itself for a relation within
     * the source (owner, 2026-10-03); one whose database is gone is not copied. A template's relation
     * to another database has no matching column there (a template is kept out of every database):
     * the page made from it gets one.
     */
    private suspend fun database(sourceId: String, pageId: String, title: String, template: Boolean): List<Row> {
        val shell = databases.databases(listOf(shellId(sourceId))).singleOrNull() ?: return emptyList()
        val properties = databases.propertiesOf(sourceId)
        val liveTargets = properties.mapNotNull { it.targetDatabaseId }.distinct().filter { t ->
            t == sourceId || (databases.databases(listOf(shellId(t))).isNotEmpty() && pageDao.pages(listOf(t)).singleOrNull()?.deletedAt == null)
        }.toSet()
        val kept = properties.filter { it.type != PropertyType.RELATION.name || it.targetDatabaseId in liveTargets }
        val ids = kept.associate { it.id to newId() }
        val out = mutableListOf<Row>()
        out += shell.copy(id = shellId(pageId), pageId = pageId, labelId = null, blockedBy = shell.blockedBy?.let(ids::get)).toRow()
        val lastKey = HashMap<String, String?>()
        for (p in kept) {
            val outside = p.type == PropertyType.RELATION.name && p.targetDatabaseId != sourceId
            // A relation to another database gets a new matching column there, named after the copy, last.
            val pair = if (outside) newId().takeIf { !template } else p.pairPropertyId?.let(ids::get)
            out += p.copy(id = ids.getValue(p.id), databaseId = pageId, targetDatabaseId = p.targetDatabaseId?.let { if (it == sourceId) pageId else it }, pairPropertyId = pair).toRow()
            if (outside && pair != null) {
                val target = requireNotNull(p.targetDatabaseId)
                val key = keyBetween(lastKey.getOrPut(target) { databases.propertiesOf(target).maxOfOrNull { it.sortKey } }, null).also { lastKey[target] = it }
                out += PropertyEntity(pair, target, 0, "", title, 0, "", PropertyType.RELATION.name, 0, "", key, 0, "", pageId, ids.getValue(p.id)).toRow()
            }
        }
        val options = readChunked(kept.map { it.id }) { databases.optionsOf(it) }.filter { it.deletedAt == null }
        val optionIds = options.associate { it.id to newId() }
        options.forEach { o -> out += o.copy(id = optionIds.getValue(o.id), propertyId = ids.getValue(o.propertyId), mergedInto = null).toRow() }
        val all = ids + optionIds
        val relations = kept.filter { it.type == PropertyType.RELATION.name }.map { it.id }.toSet()
        for (v in databases.viewsOf(sourceId).filter { it.deletedAt == null }) {
            // A filter on a relation names rows of the source, which a copy has none of: only an empty-or-not test is kept.
            val keepsFilter = v.filterProperty in ids && (v.filterProperty !in relations || v.filterOp in setOf(FilterOp.IS_EMPTY.name, FilterOp.IS_NOT_EMPTY.name))
            val copy = v.copy(
                id = newId(), databaseId = pageId, groupBy = v.groupBy?.let(ids::get), dateProperty = v.dateProperty?.let(ids::get), endDateProperty = v.endDateProperty?.let(ids::get),
                shown = v.shown?.split(',')?.mapNotNull(ids::get)?.joinToString(","), sortProperty = v.sortProperty?.let(ids::get),
                filterProperty = v.filterProperty?.let(ids::get).takeIf { keepsFilter }, filterOp = v.filterOp.takeIf { keepsFilter },
                filterValue = v.filterValue?.let { all[it] ?: it }.takeIf { keepsFilter && v.filterProperty !in relations },
            )
            out += copy.toRow()
        }
        return out
    }

    /** The source's board: its layout, its live cards under new ids with their mind-map links, and the live lines between them. */
    private suspend fun canvas(sourceId: String, pageId: String): List<Row> {
        val shell = canvases.canvases(listOf(canvasShellId(sourceId))).singleOrNull() ?: return emptyList()
        val nodes = canvases.nodesOf(sourceId).filter { it.deletedAt == null }
        val ids = nodes.associate { it.id to newId() }
        val out = mutableListOf(shell.copy(id = canvasShellId(pageId), pageId = pageId).toRow())
        nodes.forEach { n -> out += n.copy(id = ids.getValue(n.id), pageId = pageId, parentId = n.parentId?.let(ids::get)).toRow() }
        canvases.edgesOf(sourceId).filter { it.deletedAt == null && it.fromNodeId in ids && it.toNodeId in ids }.forEach { e ->
            val copy = e.copy(id = newId(), pageId = pageId, fromNodeId = ids.getValue(e.fromNodeId), toNodeId = ids.getValue(e.toNodeId))
            out += copy.toRow()
        }
        return out
    }
}

/** A copied row's stamps before the write gives them theirs. */
private val UNSTAMPED = Stamp(0, "")

/** Every group of a copied row stamped [s]: a copy is a new row the person made now. */
private fun Row.restamped(s: Stamp) = copy(groups = groups.mapValues { (_, g) -> Group(s, g.values) })
