package com.factotum.data.label

import com.factotum.core.label.LabelScope
import com.factotum.core.label.colorForName
import com.factotum.core.label.nameKey
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemKind
import com.factotum.data.sync.StagedStore
import com.factotum.data.tracker.TRACKER

data class Label(val id: String, val name: String, val color: Long, val appliesTo: LabelScope, val sortOrder: Double)

/** Unicode composes one character in more than one way ("é" or "e" and an accent); names are kept, and compared, in one form. */
internal expect fun nfc(text: String): String

/** The key two label names are compared by: one Unicode form, then [nameKey]. */
internal fun labelKey(name: String): String = nameKey(nfc(name))

/**
 * Labels (ADR 08): one vocabulary for activities, habits and trackers (and pages, with ADR 12),
 * each carrying at most one. Names are unique ignoring case; a sync that finds two merges them
 * ([mergeDuplicates]). A label's scope only decides where it is offered: narrowing it leaves what
 * already carries it alone (owner, 2026-10-02).
 *
 * A merged label stays as a record of where it went (`merged_into`), and whatever names it reads
 * as the label it went into ([resolver]). Nothing that carried it is rewritten, so a merge never
 * overwrites a label a person chose meanwhile on another device.
 */
internal class LabelRepository(
    db: FactotumDatabase,
    private val writes: LocalWrites,
    private val newId: () -> String,
) {
    private val dao = db.labelDao()
    private val items = db.itemDao()
    private val trackers = db.trackerDao()
    private val clock = writes.clock

    /** A new label, last in the order, coloured from its name unless [color] is given (Tendril). */
    suspend fun create(name: String, appliesTo: LabelScope = LabelScope.ALL, color: Long? = null): String {
        val id = newId()
        var clean = ""
        var order = 0.0
        writes.write({
            clean = checkedName(name, except = null)
            order = (dao.liveLabels().maxOfOrNull { it.sortOrder } ?: 0.0) + 1
            mapOf(LABEL to listOf(id))
        }) { store, _ ->
            val s = clock.tick()
            writes.merger.created(store, Row(LABEL, id, mapOf(
                NAME to Group(s, mapOf("name" to clean)),
                LOOK to Group(s, mapOf("color" to (color ?: colorForName(clean)))),
                SCOPE to Group(s, mapOf("applies_to" to appliesTo.name)),
                ORDER to Group(s, mapOf("sort_order" to order)),
                GONE to Group(s, mapOf("deleted_at" to null, "merged_into" to null)),
            )))
        }
        return id
    }

    suspend fun rename(id: String, name: String) {
        var clean = ""
        change(id, NAME, check = { clean = checkedName(name, except = id) }) { mapOf("name" to clean) }
    }

    suspend fun recolor(id: String, color: Long) = change(id, LOOK) { mapOf("color" to color) }

    /** Where [id] is offered; what already carries it keeps it (owner, 2026-10-02). */
    suspend fun setScope(id: String, scope: LabelScope) = change(id, SCOPE) { mapOf("applies_to" to scope.name) }

    suspend fun setSortOrder(id: String, order: Double) = change(id, ORDER) { mapOf("sort_order" to order) }

    /** Deletes [id]; what carried it, or a label merged into it, carries no label, in the same write (Chronicle). */
    suspend fun delete(id: String) = writes.write({
        live(id)
        val same = dao.allLabels().let { all -> val r = resolver(all); all.map { it.id }.filter { r(it) == id } }
        mapOf(LABEL to listOf(id), ITEM to dao.itemsLabelled(same), TRACKER to dao.trackersLabelled(same))
    }) { store, targets ->
        val s = clock.tick()
        store.put(requireNotNull(store.row(id)).edit(GONE, s, mapOf("deleted_at" to s.hlc)))
        for (member in targets.getValue(ITEM) + targets.getValue(TRACKER)) {
            store.put(requireNotNull(store.row(member)).edit(LABELLED, s, mapOf("label_id" to null)))
        }
    }

    /** Every live label, in order. */
    suspend fun labels(): List<Label> = dao.liveLabels().map { it.toLabel() }

    /** The labels offered for an activity ([LabelScope.ACTIVITY]), a tracker ([LabelScope.TRACKER]) or anything else ([LabelScope.ALL]). */
    suspend fun offeredFor(scope: LabelScope): List<Label> =
        labels().filter { it.appliesTo == LabelScope.ALL || it.appliesTo == scope }

    /** The label the activity or habit [itemId] carries now: a merged one reads as the label it went into, a deleted one as none. */
    suspend fun labelOf(itemId: String): String? = items.items(listOf(itemId)).singleOrNull()?.labelId.let(resolver(dao.allLabels()))

    /** The label the tracker [trackerId] carries now, read as [labelOf] reads one. */
    suspend fun trackerLabelOf(trackerId: String): String? = trackers.trackers(listOf(trackerId)).singleOrNull()?.labelId.let(resolver(dao.allLabels()))

    /** Puts [labelId] on the activity or habit [itemId], or takes its label off with null. */
    suspend fun label(itemId: String, labelId: String?) = writes.write({
        val item = requireNotNull(items.items(listOf(itemId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no item $itemId" }
        val kind = ItemKind.valueOf(item.kind)
        require(kind == ItemKind.ACTIVITY || kind == ItemKind.HABIT) { "a ${item.kind} carries no label" }
        labelId?.let { offered(it, if (kind == ItemKind.ACTIVITY) LabelScope.ACTIVITY else LabelScope.ALL) }
        mapOf(ITEM to listOf(itemId))
    }) { store, _ -> setLabel(store, itemId, labelId) }

    /** Puts [labelId] on the tracker [trackerId] (Chronicle's category), or takes it off with null. */
    suspend fun labelTracker(trackerId: String, labelId: String?) = writes.write({
        requireNotNull(trackers.trackers(listOf(trackerId)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no tracker $trackerId" }
        labelId?.let { offered(it, LabelScope.TRACKER) }
        mapOf(TRACKER to listOf(trackerId))
    }) { store, _ -> setLabel(store, trackerId, labelId) }

    /**
     * After every import: live labels a sync left with one name (ignoring case and Unicode form)
     * merge into the one made first, whose id is the lowest, as ULIDs begin with the time; it keeps
     * its colour and scope (owner, 2026-10-02). Every device reaches the same result.
     */
    suspend fun mergeDuplicates() {
        var into: Map<String, String> = emptyMap()
        writes.write({
            into = dao.liveLabels().groupBy { labelKey(it.name) }.values.filter { it.size > 1 }
                .flatMap { same -> val first = same.minOf { it.id }; same.filter { it.id != first }.map { it.id to first } }.toMap()
            mapOf(LABEL to into.keys.toList())
        }) { store, _ ->
            if (into.isEmpty()) return@write
            val s = clock.tick()
            for ((id, survivor) in into) store.put(requireNotNull(store.row(id)).edit(GONE, s, mapOf("deleted_at" to s.hlc, "merged_into" to survivor)))
        }
    }

    private fun setLabel(store: StagedStore, id: String, labelId: String?) =
        store.put(requireNotNull(store.row(id)).edit(LABELLED, clock.tick(), mapOf("label_id" to labelId)))

    /** Changes one part of the live label [id], after [check], inside the write. */
    private suspend fun change(id: String, group: String, check: suspend () -> Unit = {}, values: () -> Map<String, Any?>) = writes.write({
        live(id)
        check()
        mapOf(LABEL to listOf(id))
    }) { store, _ -> store.put(requireNotNull(store.row(id)).edit(group, clock.tick(), values())) }

    private suspend fun live(id: String) = requireNotNull(dao.labels(listOf(id)).singleOrNull()?.takeIf { it.deletedAt == null }) { "no label $id" }

    private suspend fun checkedName(name: String, except: String?): String {
        val clean = nfc(name.trim())
        require(clean.isNotEmpty()) { "a label needs a name" }
        require(dao.liveLabels().none { it.id != except && labelKey(it.name) == labelKey(clean) }) { "there is already a label \"$clean\"" }
        return clean
    }

    private suspend fun offered(labelId: String, scope: LabelScope) {
        val label = live(labelId)
        val applies = LabelScope.valueOf(label.appliesTo)
        require(applies == LabelScope.ALL || applies == scope) { "label ${label.name} is not offered here" }
    }
}

/**
 * Reads a label id as the live label it stands for now: itself while live, the label it was
 * merged into (followed to the end), or none once deleted.
 */
internal fun resolver(labels: List<LabelEntity>): (String?) -> String? {
    val byId = labels.associateBy { it.id }
    return { start ->
        generateSequence(start?.let(byId::get)) { it.mergedInto?.let(byId::get) }.take(labels.size + 1)
            .firstOrNull { it.deletedAt == null }?.id
    }
}

private fun LabelEntity.toLabel() = Label(id, name, color, LabelScope.valueOf(appliesTo), sortOrder)
