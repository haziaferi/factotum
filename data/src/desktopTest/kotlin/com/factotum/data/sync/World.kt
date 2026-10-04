package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.HybridClock
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.Factotum
import com.factotum.data.item.DETAILS
import com.factotum.data.item.ITEM
import com.factotum.data.item.STATUS
import com.factotum.data.openFactotumDatabase
import com.factotum.data.image.DesktopImageScaler
import com.factotum.data.image.MemoryBlobStore
import com.factotum.data.settings.MemorySecretStore
import com.factotum.data.syncedTables
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalDateTime
import java.io.File
import kotlin.random.Random
import kotlin.test.assertEquals

/** The groups the ordinary-use workload edits: neither asks a person. */
val GROUPS = listOf(DETAILS, STATUS)

/** A table held in memory, for rows no real table has. Its saves fail once [savesLeft] runs out. */
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
    override fun fits(row: Row) = true
    override fun parents(row: Row) = emptyList<Pair<String, String>>()
}

/**
 * Devices sharing one folder through [syncthing], writing items through the real repository.
 * [truth] holds the newest version of every group any device wrote: what every device must hold
 * once sync settles (ADR 01's join).
 */
internal class World(private val dir: File, seed: Int, private val segmentBytes: Int = 16 * 1024, private val snapshotEvery: Int = 64) {
    val syncthing = SyncthingDouble(Random(seed))
    val truth = mutableMapOf<Pair<String, String>, Group>()
    private val opened = mutableListOf<FactotumDatabase>()

    /**
     * [id] is the sync identity; two devices given the same one model a cloned device id.
     * [extra] adds tables, or replaces a real one, for rows written straight into the folder.
     */
    inner class Device(val name: String, val id: String = name, extra: Map<String, RowTable> = emptyMap(), recovered: Boolean = false) {
        val clock = HybridClock(id, { syncthing.now })
        val db = openFactotumDatabase(File(dir, "$name.db")).database.also { opened += it }
        private val tables = db.syncedTables() + extra
        private var made = 0
        /** This device's secret store: a map, as the Keystore or DPAPI would hold it apart from everything else. */
        val secrets = MemorySecretStore()
        val blobs = MemoryBlobStore()
        /** The wall clock the time rules read, as a local date-time. */
        var now = LocalDateTime(2026, 10, 5, 12, 0)
        /** The production wiring, over this device's database and its copy of the folder. */
        val app = Factotum(
            db, syncthing.folder(name), id, clock, secrets, blobs, DesktopImageScaler(), { "$name-${made++}" }, { syncthing.now }, { now },
            recovered = recovered, tables = tables, segmentBytes = segmentBytes, snapshotEvery = snapshotEvery,
        )
        val writes = app.writes
        val settings = app.settings
        val items = app.items
        val reminders = app.reminders
        val occurrences = app.occurrences
        val habits = app.habits
        val trackers = app.trackers
        val time = app.time
        val activities = app.activities
        val labels = app.labels
        val checkIns = app.checkIns
        val pages = app.pages
        val databases = app.databases
        val canvases = app.canvases
        val journal = app.journal
        val relations = app.relations
        val templates = app.templates
        val checklists = app.checklists
        val charts = app.charts
        val regulation = app.regulation
        val ledger = app.ledger
        val rowTasks = app.rowTasks
        val images = app.images
        val sync = app.sync

        fun create(): String = runBlocking { items.createTask("$name@${syncthing.now}") }.also(::record)

        fun edit(rowId: String, group: String) {
            runBlocking {
                when (group) {
                    DETAILS -> items.rename(rowId, "$name@${syncthing.now}")
                    STATUS -> items.setImportance(rowId, syncthing.now)
                    else -> error("the workload does not edit $group")
                }
            }
            record(rowId)
        }

        fun purge(rowId: String) = runBlocking { items.purge(rowId) }

        private fun record(rowId: String) {
            for ((g, v) in rows().getValue(rowId).groups) {
                truth.merge(rowId to g, v) { old, new -> if (new.stamp > old.stamp) new else old }
            }
        }

        fun rows(): Map<String, Row> = runBlocking { tables.getValue(ITEM).all() }.associateBy { it.id }

        fun import() = runBlocking { app.import() }
        fun export() = runBlocking { app.export() }

        fun held(): Map<Pair<String, String>, Group> =
            rows().values.flatMap { r -> r.groups.map { (g, v) -> (r.id to g) to v } }.toMap()
    }

    /** Every device exports, every pair meets in full, and every device imports, until an import changes nothing. */
    fun settle(devices: List<Device>) {
        repeat(20) {
            devices.forEach { it.export() }
            for (a in devices) for (b in devices) if (a.name < b.name) syncthing.session(a.name, b.name)
            if (devices.sumOf { it.import().changed } == 0) return
        }
        error("sync did not settle")
    }

    fun assertJoined(devices: List<Device>) {
        for (d in devices) assertEquals(truth, d.held(), "device ${d.name} differs from the join")
    }

    fun close() = opened.forEach { it.close() }
}
