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

    /** A version a keep-loser group lost to a later one: kept for the person to recover (ADR 12). */
    fun lost(row: Row, group: String, loser: Group)
}

/**
 * Applies a peer's rows and purge registry (ADR 01, hybrid+).
 *
 * Each group takes the higher stamp, except a group in [askGroups] that both sides changed since
 * their base to different values: that one is left alone and handed to a person. A group in
 * [keepLoserGroups] (ADR 12, a page's text) takes the later version even then, and the version it
 * replaced goes to [SyncStore.lost], so nothing typed is lost. A purge holds against every row that
 * has not been edited since it.
 */
class Merger(private val clock: HybridClock, private val askGroups: Set<String>, private val keepLoserGroups: Set<String> = emptySet()) {

    private val baseGroups = askGroups + keepLoserGroups

    /** A row created on this device: its creation is the base both sides start from. */
    fun created(store: SyncStore, row: Row) {
        store.put(row)
        baseGroups.forEach { g -> row.groups[g]?.let { store.putBase(row.id, g, it.stamp) } }
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
            if (name !in baseGroups) {
                if (theirs.stamp > mine.stamp) merged[name] = theirs
                continue
            }
            val base = store.base(local.id, name)
            // A version no newer than the base, such as one a log replays, brings nothing: it must
            // not move the base, or a later change from the other side would look uncontested.
            if (base != null && theirs.stamp <= base) continue
            if (name in keepLoserGroups) {
                val winner = if (theirs.stamp > mine.stamp) theirs else mine
                // Both changed it since the base, to different text: the earlier is kept, not dropped.
                if (mine.stamp != base && mine.values != theirs.values) store.lost(local.copy(groups = merged), name, if (winner === theirs) mine else theirs)
                merged[name] = winner
                // The base is the newest version read from a peer, not the winner: a local version
                // that won is still this device's own, and must meet a third device's text as a clash.
                store.putBase(local.id, name, theirs.stamp)
                continue
            }
            if (mine.stamp != base && mine.values != theirs.values && theirs.settles != mine.stamp) {
                // A replay older than the version already waiting must not replace it.
                if ((store.asked(local.id, name)?.stamp ?: theirs.stamp) <= theirs.stamp) store.ask(local.id, name, theirs)
                continue
            }
            // Only they changed it since the base, both changed it alike, or theirs answers the clash.
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

    /**
     * Settles a clash with no person: [settled] works the group out from the two versions, mine and
     * theirs, and must give every device the same group whichever side it holds. The base is their
     * stamp, as for [keepMine], so a third device's version still meets this one as a clash.
     */
    fun settle(store: SyncStore, id: String, group: String, settled: (Group, Group) -> Group) {
        val (local, theirs) = pending(store, id, group)
        store.put(local.copy(groups = local.groups + (group to settled(local.groups.getValue(group), theirs))))
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
