package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.core.sync.SyncStore

/**
 * The [SyncStore] one merge runs against. Everything it may look up is loaded first, and what it
 * changed is written back after, in the same transaction, so `:core` stays synchronous.
 *
 * Looking up an id that was not loaded is a bug in the loading, and throws rather than reading
 * as "no such row".
 */
internal class StagedStore private constructor(
    private val rows: MutableMap<String, Row?>,
    private val purges: MutableMap<String, Stamp>,
    private val bases: MutableMap<Pair<String, String>, Stamp>,
    private val asks: MutableMap<Pair<String, String>, Group>,
) : SyncStore {

    private val tableOf = rows.values.filterNotNull().associate { it.id to it.table }.toMutableMap()
    private val changedRows = mutableSetOf<String>()
    private val changedPurges = mutableSetOf<String>()
    private val changedBases = mutableSetOf<Pair<String, String>>()
    private val changedAsks = mutableSetOf<Pair<String, String>>()
    private val lostOnes = mutableListOf<LostEntity>()

    /**
     * Whether this merge took back a purge that was here: a row edited after its purge came back
     * (ADR 01), but the rows under it went with the purge here, through the foreign keys.
     */
    var undidPurge = false
        private set

    /** Ids whose row or purge this merge changed: the ones to export again. */
    val changed: Set<String> get() = changedRows + changedPurges

    override fun row(id: String): Row? {
        loaded(id)
        return rows[id]
    }

    override fun put(row: Row) {
        loaded(row.id)
        rows[row.id] = row
        tableOf[row.id] = row.table
        changedRows += row.id
    }

    override fun remove(id: String) {
        loaded(id)
        rows[id] = null
        changedRows += id
    }

    override fun purge(id: String): Stamp? {
        loaded(id)
        return purges[id]
    }

    override fun putPurge(id: String, stamp: Stamp) {
        loaded(id)
        purges[id] = stamp
        changedPurges += id
    }

    override fun removePurge(id: String) {
        if (id in purges) undidPurge = true
        loaded(id)
        purges.remove(id)
        changedPurges += id
    }

    override fun base(id: String, group: String): Stamp? {
        loaded(id)
        return bases[id to group]
    }

    override fun putBase(id: String, group: String, stamp: Stamp) {
        loaded(id)
        bases[id to group] = stamp
        changedBases += id to group
    }

    override fun ask(id: String, group: String, theirs: Group) {
        loaded(id)
        asks[id to group] = theirs
        changedAsks += id to group
    }

    override fun asked(id: String, group: String): Group? {
        loaded(id)
        return asks[id to group]
    }

    override fun lost(row: Row, group: String, loser: Group) {
        lostOnes += LostEntity(0, row.id, row.table, group, RecordCodec.encodeGroup(loser))
    }

    override fun clearAsk(id: String, group: String) {
        loaded(id)
        asks.remove(id to group)
        changedAsks += id to group
    }

    private fun loaded(id: String) = check(id in rows) { "row $id was not loaded for this merge" }

    /** Writes every change back; the triggers queue it for export and clear a removed row's bases and questions. */
    suspend fun flush(dao: SyncDao, tables: Map<String, RowTable>) {
        val (kept, removed) = changedRows.partition { rows[it] != null }
        kept.mapNotNull { rows[it] }.groupBy { it.table }.forEach { (t, rs) -> tables.getValue(t).save(rs) }
        removed.groupBy { tableOf.getValue(it) }.forEach { (t, ids) -> tables.getValue(t).delete(ids) }
        for (id in changedPurges) {
            val stamp = purges[id]
            if (stamp == null) dao.removePurge(id) else dao.putPurge(PurgeEntity(id, stamp.hlc, stamp.device))
        }
        val gone = removed.toSet()
        dao.putBases(changedBases.filter { it.first !in gone }.map { (id, g) -> bases.getValue(id to g).let { BaseEntity(id, g, it.hlc, it.device) } })
        val (asked, cleared) = changedAsks.filter { it.first !in gone }.partition { it in asks }
        dao.putAsks(asked.map { (id, g) -> AskEntity(id, g, RecordCodec.encodeGroup(asks.getValue(id to g))) })
        cleared.forEach { (id, g) -> dao.removeAsk(id, g) }
        if (lostOnes.isNotEmpty()) dao.addLost(lostOnes)
    }

    companion object {
        /** Under SQLite's 999 bound variables on Android's older builds. */
        const val CHUNK = 500

        /**
         * Loads what a merge or a local write can touch: the ids in [byTable] from their tables, the ids
         * in [anyTable] from whichever table holds them, and their purges, bases and questions.
         */
        suspend fun load(
            dao: SyncDao,
            tables: Map<String, RowTable>,
            byTable: Map<String, Collection<String>>,
            anyTable: Collection<String> = emptyList(),
        ): StagedStore {
            val ids = (byTable.values.flatten() + anyTable).distinct()
            val found = ids.associateWith<String, Row?> { null }.toMutableMap()
            val unplaced = anyTable.toMutableSet()
            for ((name, table) in tables) {
                // An id in [anyTable] can be in any table, until one table has it.
                val wanted = (byTable[name].orEmpty() + unplaced).distinct()
                wanted.chunked(CHUNK).forEach { chunk -> table.load(chunk).forEach { found[it.id] = it; unplaced -= it.id } }
            }
            val registry = mutableMapOf<String, Stamp>()
            val bases = mutableMapOf<Pair<String, String>, Stamp>()
            val asks = mutableMapOf<Pair<String, String>, Group>()
            ids.chunked(CHUNK).forEach { chunk ->
                dao.purges(chunk).forEach { registry[it.id] = it.stamp() }
                dao.bases(chunk).forEach { bases[it.id to it.grp] = it.stamp() }
                dao.asks(chunk).forEach { asks[it.id to it.grp] = RecordCodec.decodeGroup(it.theirs) }
            }
            return StagedStore(found, registry, bases, asks)
        }
    }
}

/** Reads [ids] in chunks of [StagedStore.CHUNK], under SQLite's 999 bound variables, as older Android builds have it. */
internal suspend fun <T> readChunked(ids: List<String>?, read: suspend (List<String>) -> List<T>): List<T> =
    ids.orEmpty().chunked(StagedStore.CHUNK).flatMap { read(it) }
