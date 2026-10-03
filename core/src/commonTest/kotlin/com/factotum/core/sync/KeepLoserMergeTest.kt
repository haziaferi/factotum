package com.factotum.core.sync

import kotlin.test.Test
import kotlin.test.assertEquals

/** ADR 12's keep-loser groups: the later text wins, and every text it replaced reaches [SyncStore.lost] on some device. */
class KeepLoserMergeTest {

    private fun device(name: String) = Merger(HybridClock(name, { 0 }), emptySet(), setOf(TEXT)) to MemoryStore()

    private fun version(stamp: Long, device: String, text: String) = Row("block", "b", mapOf(TEXT to Group(Stamp(stamp, device), mapOf("text" to text))))

    private fun MemoryStore.text() = rows.getValue("b").groups.getValue(TEXT).values["text"]

    @Test
    fun theLaterTextWinsAndTheEarlierIsLostOnlyWhenBothChangedIt() {
        val (merger, store) = device("A")
        merger.created(store, version(1, "A", "start"))
        store.put(version(5, "A", "mine"))

        merger.import(store, listOf(version(7, "B", "theirs")), emptyMap())

        assertEquals("theirs", store.text())
        assertEquals(listOf<Any?>("mine"), store.losses.map { it.second.values["text"] })
        // Only they changed it since, and a replay brings nothing.
        merger.import(store, listOf(version(9, "B", "again"), version(7, "B", "theirs")), emptyMap())
        assertEquals(1, store.losses.size)
    }

    @Test
    fun withThreeDevicesEveryReplacedTextIsLostSomewhereWhateverTheOrder() {
        val texts = mapOf("A" to version(11, "A", "a"), "B" to version(12, "B", "b"), "C" to version(13, "C", "c"))
        for (me in texts.keys) for (first in texts.keys - me) {
            val (merger, store) = device(me)
            merger.created(store, version(1, "A", "start"))
            store.put(texts.getValue(me))
            merger.import(store, listOf(texts.getValue(first)), emptyMap())
            merger.import(store, listOf(texts.getValue((texts.keys - me - first).single())), emptyMap())

            assertEquals("c", store.text())
            // This device's own text, when it lost, is always among what it kept.
            if (me != "C") assertEquals(true, store.losses.any { it.second.values["text"] == me.lowercase() }, "$me after $first")
        }
    }

    private companion object {
        const val TEXT = "text"
    }
}
