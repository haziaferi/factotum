package com.factotum.data.page

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.sync.readChunked

/**
 * The Road Map's links between pages (Tendril's "Relate to…", ADR 12): undirected, one row per
 * pair. Taking one off is a deletion, and relating the two again brings it back (owner, 2026-10-03,
 * amending "add-only" for removal only). A link made to a page trashed on another device is an
 * edit to it, and brings it back (ADR 12's revive).
 */
internal class RelationRepository(db: FactotumDatabase, private val writes: LocalWrites) {
    private val dao = db.linkDao()
    private val pageDao = db.pageDao()
    private val clock = writes.clock

    suspend fun relate(a: String, b: String) = writes.write({
        require(a != b) { "a page is not related to itself" }
        page(a)
        page(b)
        mapOf(PAGE_RELATION to listOf(relationId(a, b)))
    }) { store, targets ->
        val id = targets.getValue(PAGE_RELATION).single()
        val s = clock.tick()
        val row = store.row(id)
        if (row == null) {
            val (low, high) = if (a < b) a to b else b to a
            writes.merger.created(store, Row(PAGE_RELATION, id, mapOf(
                MADE to Group(s, mapOf("page_a" to low, "page_b" to high)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        } else if (row.groups.getValue(GONE).values["deleted_at"] != null) {
            store.put(row.edit(GONE, s, mapOf("deleted_at" to null)))
        }
    }

    suspend fun unrelate(a: String, b: String) = writes.write({
        mapOf(PAGE_RELATION to listOfNotNull(dao.relations(listOf(relationId(a, b))).singleOrNull()?.takeIf { it.deletedAt == null }?.id))
    }) { store, targets ->
        val s = clock.tick()
        targets.getValue(PAGE_RELATION).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to s.hlc))) }
    }

    /** The live pages related to [pageId], by id; a template's links are not shown. */
    suspend fun related(pageId: String): List<String> {
        val others = dao.relationsOf(listOf(pageId)).filter { it.deletedAt == null }.map { if (it.pageA == pageId) it.pageB else it.pageA }
        return readChunked(others) { pageDao.pages(it) }.filter { it.deletedAt == null && it.isTemplate != true }.map { it.id }.sorted()
    }

    private suspend fun page(id: String) =
        requireNotNull(pageDao.pages(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null && it.isTemplate != true }) { "no page $id" }
}
