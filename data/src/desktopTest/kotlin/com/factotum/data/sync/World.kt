package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.HybridClock
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import com.factotum.data.FactotumDatabase
import com.factotum.data.openFactotumDatabase
import kotlinx.coroutines.runBlocking
import java.io.File
import kotlin.random.Random
import kotlin.test.assertEquals

const val ITEM = "item"
val GROUPS = listOf("a", "b")

/** A table held in memory; each schema slice brings the real ones. Its saves fail once [savesLeft] runs out. */
internal class MemoryTable : RowTable {
    val rows = mutableMapOf<String, Row>()
    var savesLeft = Int.MAX_VALUE
    override suspend fun load(ids: Collection<String>) = ids.mapNotNull { rows[it] }
    override suspend fun all() = rows.values.toList()
    override suspend fun save(rows: Collection<Row>) {
        check(savesLeft-- > 0) { "disk full" }
        rows.forEach { this.rows[it.id] = it }
    }
    override suspend fun delete(ids: Collection<String>) = ids.forEach { rows.remove(it) }
}

/**
 * Devices sharing one folder through [syncthing]. [truth] holds the newest version of every group
 * any device wrote: what every device must hold once sync settles (ADR 01's join).
 */
internal class World(private val dir: File, seed: Int, private val segmentBytes: Int = 16 * 1024, private val snapshotEvery: Int = 64) {
    val syncthing = SyncthingDouble(Random(seed))
    val truth = mutableMapOf<Pair<String, String>, Group>()
    private val opened = mutableListOf<FactotumDatabase>()

    /** [id] is the sync identity; two devices given the same one model a cloned device id. */
    inner class Device(val name: String, val id: String = name, tables: Set<String> = setOf(ITEM)) {
        val clock = HybridClock(id, { syncthing.now })
        val db = openFactotumDatabase(File(dir, "$name.db")).database.also { opened += it }
        val table = MemoryTable()
        private val all = tables.associateWith { if (it == ITEM) table else MemoryTable() }
        val sync = FolderSync(db, syncthing.folder(name), id, clock, all, setOf("schedule"), segmentBytes, snapshotEvery)
        private var made = 0

        fun create(): String {
            val rowId = "$name-${made++}"
            val s = clock.tick()
            table.rows[rowId] = Row(ITEM, rowId, GROUPS.associateWith { g -> version(g, rowId, s) })
            changed(rowId)
            return rowId
        }

        fun edit(rowId: String, group: String) {
            val row = table.rows.getValue(rowId)
            table.rows[rowId] = row.copy(groups = row.groups + (group to version(group, rowId, clock.tick())))
            changed(rowId)
        }

        /** What the repository will do for "delete forever" (slice 02): remove, register, export. */
        fun purge(rowId: String) {
            val s = clock.tick()
            table.rows.remove(rowId)
            runBlocking { db.syncDao().putPurge(PurgeEntity(rowId, s.hlc, s.device)) }
            changed(rowId)
        }

        private fun version(group: String, rowId: String, s: Stamp): Group {
            val g = Group(s, mapOf("v" to "$name@${s.hlc}"))
            truth.merge(rowId to group, g) { old, new -> if (new.stamp > old.stamp) new else old }
            return g
        }

        private fun changed(rowId: String) = runBlocking {
            db.syncDao().putOutbox(listOf(OutboxEntity(id = rowId, table = ITEM)))
        }

        fun import() = runBlocking { sync.import() }
        fun export() = runBlocking { sync.export() }

        fun held(): Map<Pair<String, String>, Group> =
            table.rows.values.flatMap { r -> r.groups.map { (g, v) -> (r.id to g) to v } }.toMap()
    }

    /** Every device imports and exports, and every pair meets in full, until an import changes nothing. */
    fun settle(devices: List<Device>) {
        repeat(20) {
            for (a in devices) for (b in devices) if (a.name < b.name) syncthing.session(a.name, b.name)
            val changed = devices.sumOf { it.import().changed }
            devices.forEach { it.export() }
            if (changed == 0) return
        }
        error("sync did not settle")
    }

    fun assertJoined(devices: List<Device>) {
        for (d in devices) assertEquals(truth, d.held(), "device ${d.name} differs from the join")
    }

    fun close() = opened.forEach { it.close() }
}
