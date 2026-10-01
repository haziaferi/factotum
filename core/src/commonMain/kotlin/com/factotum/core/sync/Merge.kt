package com.factotum.core.sync

/** What the merge reads and writes on this device; the importer in `:data` stages it over the database. */
interface SyncStore {
    fun row(id: String): Row?
    fun put(row: Row)
    fun remove(id: String)

    /** The permanent purge registry (ADR 01): the stamp of [id]'s purge, if it was purged. Never expires. */
    fun purge(id: String): Stamp?
    fun putPurge(id: String, stamp: Stamp)
    fun removePurge(id: String)

    /** The last stamp both sides agreed on for an asking group; local only, never synced. */
    fun base(id: String, group: String): Stamp?
    fun putBase(id: String, group: String, stamp: Stamp)

    /** A clash a person must settle: [theirs] waits beside the local group, which is left as it is. */
    fun ask(id: String, group: String, theirs: Group)
    fun asked(id: String, group: String): Group?
    fun clearAsk(id: String, group: String)
}

/**
 * Applies a peer's rows and purge registry (ADR 01, hybrid+).
 *
 * Each group takes the higher stamp, except a group in [askGroups] that both sides changed since
 * their base to different values: that one is left alone and handed to a person. A purge holds
 * against every row that has not been edited since it.
 */
class Merger(private val clock: HybridClock, private val askGroups: Set<String>) {

    /** A row created on this device: its creation is the base both sides start from. */
    fun created(store: SyncStore, row: Row) {
        store.put(row)
        askGroups.forEach { g -> row.groups[g]?.let { store.putBase(row.id, g, it.stamp) } }
    }

    /** "Delete forever": the row goes, and its purge travels so no peer brings it back. */
    fun purge(store: SyncStore, id: String) {
        store.putPurge(id, clock.tick())
        store.remove(id)
    }

    fun import(store: SyncStore, rows: Iterable<Row>, purges: Map<String, Stamp>) {
        purges.values.forEach(clock::observe)
        // Entries already held were applied when they arrived; only new or earlier ones need a sweep.
        for ((id, stamp) in purges) {
            val known = store.purge(id)
            if (known != null && stamp >= known) continue
            store.putPurge(id, stamp)
            val local = store.row(id) ?: continue
            if (local.newest > stamp) store.removePurge(id) else store.remove(id)
        }
        for (incoming in rows) {
            incoming.groups.values.forEach { clock.observe(it.stamp) }
            val purge = store.purge(incoming.id)
            if (purge != null) {
                if (incoming.newest <= purge) continue
                store.removePurge(incoming.id)
            }
            val local = store.row(incoming.id)
            if (local == null) {
                created(store, incoming)
            } else {
                val merged = mergeRow(store, local, incoming)
                if (merged != local) store.put(merged)
            }
        }
    }

    private fun mergeRow(store: SyncStore, local: Row, incoming: Row): Row {
        val merged = local.groups.toMutableMap()
        for ((name, theirs) in incoming.groups) {
            val mine = merged[name]
            if (mine == null) {
                merged[name] = theirs
                continue
            }
            if (name !in askGroups) {
                if (theirs.stamp > mine.stamp) merged[name] = theirs
                continue
            }
            val base = store.base(local.id, name)
            if (mine.stamp != base && theirs.stamp != base && mine.values != theirs.values && theirs.settles != mine.stamp) {
                store.ask(local.id, name, theirs)
                continue
            }
            val winner = if (theirs.stamp > mine.stamp) theirs else mine
            merged[name] = winner
            if (winner.stamp != base) store.putBase(local.id, name, winner.stamp)
            if (store.asked(local.id, name) != null) store.clearAsk(local.id, name)
        }
        return local.copy(groups = merged)
    }

    /**
     * "Keep mine": the local group is re-stamped so it wins everywhere, settling the pending clash.
     * The base becomes their stamp, the last one both sides have seen; a further change is asked again.
     */
    fun keepMine(store: SyncStore, id: String, group: String) {
        val (local, theirs) = pending(store, id, group)
        clock.observe(theirs.stamp)
        val mine = local.groups.getValue(group).copy(stamp = clock.tick(), settles = theirs.stamp)
        store.put(local.copy(groups = local.groups + (group to mine)))
        store.putBase(id, group, theirs.stamp)
        store.clearAsk(id, group)
    }

    /** "Take theirs": the other side's group replaces the local one, stamp and all. */
    fun takeTheirs(store: SyncStore, id: String, group: String) {
        val (local, theirs) = pending(store, id, group)
        store.put(local.copy(groups = local.groups + (group to theirs)))
        store.putBase(id, group, theirs.stamp)
        store.clearAsk(id, group)
    }

    /** "Keep both": keep mine, and their version becomes a new row with [newId] and fresh stamps. */
    fun keepBoth(store: SyncStore, id: String, group: String, newId: String): Row {
        val (local, theirs) = pending(store, id, group)
        keepMine(store, id, group)
        val stamp = clock.tick()
        val copy = Row(local.table, newId, (local.groups + (group to theirs)).mapValues { (_, g) -> Group(stamp, g.values) })
        created(store, copy)
        return copy
    }

    private fun pending(store: SyncStore, id: String, group: String): Pair<Row, Group> =
        requireNotNull(store.row(id)) { "no row $id" } to
            requireNotNull(store.asked(id, group)) { "no clash pending on $id/$group" }
}
