package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.HybridClock
import com.factotum.core.sync.Row
import com.factotum.data.FactotumDatabase
import com.factotum.data.LocalWrites
import com.factotum.data.item.DETAILS
import com.factotum.data.item.ITEM
import com.factotum.data.item.HabitRepository
import com.factotum.data.item.ItemRepository
import com.factotum.data.item.OccurrenceRepository
import com.factotum.data.item.STATUS
import com.factotum.data.openFactotumDatabase
import com.factotum.data.reminder.ReminderRepository
import com.factotum.data.tracker.TrackerRepository
import com.factotum.data.time.ActivityRepository
import com.factotum.data.time.TimeRepository
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
    inner class Device(val name: String, val id: String = name, extra: Map<String, RowTable> = emptyMap()) {
        val clock = HybridClock(id, { syncthing.now })
        val db = openFactotumDatabase(File(dir, "$name.db")).database.also { opened += it }
        private val tables = db.syncedTables() + extra
        private var made = 0
        private val writes = LocalWrites(db, clock)
        private val newId = { "$name-${made++}" }
        val items = ItemRepository(db, writes, newId)
        val reminders = ReminderRepository(db, writes, newId)
        val occurrences = OccurrenceRepository(db, writes, newId)
        val habits = HabitRepository(db, writes, newId)
        val trackers = TrackerRepository(db, writes, newId)
        val time = TimeRepository(db, writes, newId)
        val activities = ActivityRepository(db, writes, newId)
        /** The wall clock the time rules read, as a local date-time. */
        var now = LocalDateTime(2026, 10, 5, 12, 0)
        val sync = FolderSync(db, syncthing.folder(name), id, clock, tables, segmentBytes, snapshotEvery, afterImport = { time.endFinished(now) })

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

        fun import() = runBlocking { sync.import() }
        fun export() = runBlocking { sync.export() }

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
