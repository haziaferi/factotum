package com.factotum.core.sync

const val SCHEDULE = "schedule"
const val STATUS = "status"
const val DAY = 86_400_000L

/** An in-memory [SyncStore]. */
class MemoryStore : SyncStore {
    val rows = mutableMapOf<String, Row>()
    val purges = mutableMapOf<String, Stamp>()
    private val bases = mutableMapOf<Pair<String, String>, Stamp>()
    private val asks = mutableMapOf<Pair<String, String>, Group>()

    /** What [lost] was handed: the row's id and the version it lost. */
    val losses = mutableListOf<Pair<String, Group>>()

    override fun row(id: String) = rows[id]
    override fun put(row: Row) { rows[row.id] = row }
    override fun remove(id: String) { rows.remove(id) }
    override fun purge(id: String) = purges[id]
    override fun putPurge(id: String, stamp: Stamp) { purges[id] = stamp }
    override fun removePurge(id: String) { purges.remove(id) }
    override fun base(id: String, group: String) = bases[id to group]
    override fun putBase(id: String, group: String, stamp: Stamp) { bases[id to group] = stamp }
    override fun ask(id: String, group: String, theirs: Group) { asks[id to group] = theirs }
    override fun asked(id: String, group: String) = asks[id to group]
    override fun clearAsk(id: String, group: String) { asks.remove(id to group) }
    override fun lost(row: Row, group: String, loser: Group) { losses += row.id to loser }
}

/** What a person sees of a reminder-shaped row. */
data class View(val due: Any?, val deleted: Boolean, val done: Any?)

/**
 * One device as `tools/sync_sim.py` models it: a reminder-shaped row with a schedule group
 * (`due`, `deleted`) and a status group (`done`), and a wall clock running [skew] ahead.
 */
class Device(name: String, private val skew: Long = 0) {
    private var now = 0L
    val clock = HybridClock(name, { now + skew })
    val store = MemoryStore()
    val merger = Merger(clock, askGroups = setOf(SCHEDULE))

    private fun at(time: Long): Stamp {
        now = time
        return clock.tick()
    }

    fun create(id: String, time: Long, due: String = "d0") {
        val s = at(time)
        merger.created(store, Row("reminder", id, mapOf(
            SCHEDULE to Group(s, mapOf("due" to due, "deleted" to null)),
            STATUS to Group(s, mapOf("done" to false)),
        )))
    }

    fun edit(id: String, time: Long, group: String, vararg changes: Pair<String, Any?>) {
        store.put(store.rows.getValue(id).edit(group, at(time), changes.toMap()))
    }

    fun delete(id: String, time: Long) = edit(id, time, SCHEDULE, "deleted" to time)

    fun purge(id: String, time: Long) {
        now = time
        merger.purge(store, id)
    }

    fun importFrom(peer: Device, time: Long) {
        now = time
        merger.import(store, peer.store.rows.values.toList(), peer.store.purges.toMap())
    }

    /** Null when the row is gone. */
    fun view(id: String): View? = store.rows[id]?.let {
        val schedule = it.groups.getValue(SCHEDULE).values
        View(schedule["due"], schedule["deleted"] != null, it.groups.getValue(STATUS).values["done"])
    }

    fun due(id: String = "x") = view(id)?.due
    fun gone(id: String) = view(id)?.deleted != false
    fun asked(id: String) = store.asked(id, SCHEDULE) != null
}

fun sync(devices: List<Device>, time: Long, rounds: Int = 3) {
    repeat(rounds) {
        for (a in devices) for (b in devices) if (a !== b) a.importFrom(b, time)
    }
}

/** Two devices holding the same row x, synced at time 1. */
fun pairWithX(): Pair<Device, Device> {
    val (a, b) = Device("A") to Device("B")
    a.create("x", 0)
    sync(listOf(a, b), 1)
    return a to b
}
