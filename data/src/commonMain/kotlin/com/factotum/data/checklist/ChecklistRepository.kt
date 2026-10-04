package com.factotum.data.checklist

import com.factotum.core.page.keyAfter
import com.factotum.core.page.keyBetween
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.label.nfc
import com.factotum.data.page.automatic
import com.factotum.data.page.byHand

data class Checklist(val id: String, val name: String)

/** An item as it reads now: [checked] only when ticked since the checklist's last reset. */
data class ChecklistItem(val id: String, val text: String, val checked: Boolean)

/**
 * Chronicle's checklists (decision 14): standalone lists, each run again by a reset. Lists and items
 * keep a manual order, a new list first (owner, 2026-10-03); a deletion wins over an edit made apart
 * and is undone from the Trash; a list deleted takes its live items with it, in one stamp, and
 * comes back with them.
 */
internal class ChecklistRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val dao = db.checklistDao()
    private val clock = writes.clock

    /** A new checklist, first in the order. */
    suspend fun create(name: String): String {
        val id = newId()
        var key = ""
        writes.write({
            key = keyBetween(null, dao.allChecklists().filter { it.deletedAt == null }.minOfOrNull { it.sortKey })
            mapOf(CHECKLIST to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(CHECKLIST, id, mapOf(
                NAME to Group(s, mapOf("name" to checkedName(name))),
                ORDER to Group(s, mapOf("sort_key" to key)),
                RUN to Group(s, emptyMap()),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun rename(id: String, name: String) = writes.edit(CHECKLIST, id, NAME, { live(id) }) { mapOf("name" to checkedName(name)) }

    /** Moves [id] after [after] (first when null). */
    suspend fun move(id: String, after: String?) {
        var key = ""
        writes.edit(CHECKLIST, id, ORDER, {
            live(id)
            key = keyAfter(dao.allChecklists().filter { it.deletedAt == null && it.id != id }.map { it.id to it.sortKey }, after)
        }) { mapOf("sort_key" to key) }
    }

    /** Starts a new run: every tick made before now reads as cleared, on every device, whenever it syncs. */
    suspend fun reset(id: String) = writes.edit(CHECKLIST, id, RUN, { live(id) }) { emptyMap() }

    /**
     * Deletes [id] with its live items. The items' deletion is the list's doing, an app's own stamp
     * (`~`), so a restore brings back every item a list's deletion took, on whichever device deleted
     * it, and none deleted by hand.
     */
    suspend fun delete(id: String) = writes.write({
        live(id)
        mapOf(CHECKLIST to listOf(id), CHECKLIST_ITEM to dao.itemsOf(id).filter { it.deletedAt == null }.map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(id)).edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        // Stamped just above the item's own last deletion stamp, not now: an item another device deleted
        // by hand, unseen here, keeps that deletion, and a restore of the list leaves it deleted.
        targets.getValue(CHECKLIST_ITEM).forEach { item ->
            val row = requireNotNull(store.row(item))
            store.put(row.edit(GONE, automatic(row.groups.getValue(GONE).stamp), mapOf("deleted_at" to s.hlc)))
        }
    }

    /** Restores [id] from the Trash, with the items a deletion of the list took. */
    suspend fun restore(id: String) = writes.write({
        requireNotNull(dao.checklists(listOf(id)).singleOrNull()?.takeIf { it.deletedAt != null }) { "checklist $id is not in the Trash" }
        mapOf(CHECKLIST to listOf(id), CHECKLIST_ITEM to dao.itemsOf(id).filter { it.deletedAt != null && !Stamp(it.goneHlc, it.goneDevice).byHand }.map { it.id })
    }) { store, targets ->
        val s = clock.tick()
        (targets.getValue(CHECKLIST) + targets.getValue(CHECKLIST_ITEM)).forEach { store.put(requireNotNull(store.row(it)).edit(GONE, s, mapOf("deleted_at" to null))) }
    }

    /** The live checklists, in their order. */
    suspend fun checklists(): List<Checklist> =
        dao.allChecklists().filter { it.deletedAt == null }.sortedWith(compareBy({ it.sortKey }, { it.id })).map { Checklist(it.id, it.name) }

    /** The checklists in the Trash. */
    suspend fun trashed(): List<Checklist> = dao.allChecklists().filter { it.deletedAt != null }.map { Checklist(it.id, it.name) }

    /** An item after [after] (last when null) on the live checklist [checklistId]. */
    suspend fun addItem(checklistId: String, text: String, after: String? = null): String {
        val id = newId()
        var key = ""
        writes.write({
            live(checklistId)
            key = keyAfter(liveItems(checklistId).map { it.id to it.sortKey }, after, last = after == null)
            mapOf(CHECKLIST_ITEM to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(CHECKLIST_ITEM, id, mapOf(
                MADE to Group(s, mapOf("checklist_id" to checklistId)),
                TEXT to Group(s, mapOf("text" to checkedText(text))),
                CHECK to Group(s, mapOf("checked" to false)),
                ORDER to Group(s, mapOf("sort_key" to key)),
                GONE to Group(s, mapOf("deleted_at" to null)),
            )))
        }
        return id
    }

    suspend fun setText(itemId: String, text: String) = writes.edit(CHECKLIST_ITEM, itemId, TEXT, { liveItem(itemId) }) { mapOf("text" to checkedText(text)) }

    suspend fun check(itemId: String, checked: Boolean) = writes.edit(CHECKLIST_ITEM, itemId, CHECK, { liveItem(itemId) }) { mapOf("checked" to checked) }

    /** Moves an item after [after] (first when null) on its checklist. */
    suspend fun moveItem(itemId: String, after: String?) {
        var key = ""
        writes.edit(CHECKLIST_ITEM, itemId, ORDER, {
            val item = liveItem(itemId)
            key = keyAfter(liveItems(item.checklistId).filter { it.id != itemId }.map { it.id to it.sortKey }, after)
        }) { mapOf("sort_key" to key) }
    }

    suspend fun deleteItem(itemId: String) = writes.edit(CHECKLIST_ITEM, itemId, GONE, { liveItem(itemId) }) { s -> mapOf("deleted_at" to s.hlc) }

    /** Brings back an item deleted from a live checklist. */
    suspend fun restoreItem(itemId: String) = writes.edit(CHECKLIST_ITEM, itemId, GONE, {
        val item = requireNotNull(dao.items(listOf(itemId)).singleOrNull()?.takeIf { it.deletedAt != null }) { "item $itemId is not in the Trash" }
        live(item.checklistId)
    }) { mapOf("deleted_at" to null) }

    /** A live checklist's deleted items, for its Trash. */
    suspend fun trashedItems(checklistId: String): List<ChecklistItem> =
        dao.itemsOf(live(checklistId).id).filter { it.deletedAt != null }.map { ChecklistItem(it.id, it.text, false) }

    /** A checklist's live items, in order, each ticked only if ticked since its last reset. */
    suspend fun items(checklistId: String): List<ChecklistItem> {
        val list = live(checklistId)
        val reset = Stamp(list.runHlc, list.runDevice)
        return liveItems(checklistId).sortedWith(compareBy({ it.sortKey }, { it.id }))
            .map { ChecklistItem(it.id, it.text, it.checked && Stamp(it.checkHlc, it.checkDevice) > reset) }
    }

    private suspend fun liveItems(checklistId: String) = dao.itemsOf(checklistId).filter { it.deletedAt == null }

    private suspend fun live(id: String) = requireNotNull(dao.checklists(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no checklist $id" }

    /** An item of a live checklist: a list in the Trash keeps its items as they are. */
    private suspend fun liveItem(id: String) =
        requireNotNull(dao.items(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no item $id" }.also { live(it.checklistId) }
}

/** A name is never blank (Chronicle kept the old one on a blank rename; here a blank is refused). */
private fun checkedName(name: String) = nfc(name.trim()).also { require(it.isNotEmpty()) { "a checklist needs a name" } }

private fun checkedText(text: String) = nfc(text.trim()).also { require(it.isNotEmpty()) { "an item needs text" } }

