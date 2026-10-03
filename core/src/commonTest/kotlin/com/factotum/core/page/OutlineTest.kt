package com.factotum.core.page

import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class OutlineTest {

    @Test
    fun blocksComeOutDepthFirstInKeyOrderAndTiesGoById() {
        val blocks = listOf(Placed("b", null, "k"), Placed("a", null, "h"), Placed("a1", "a", "h"), Placed("c2", null, "k"))

        assertEquals(listOf("a" to 0, "a1" to 1, "b" to 0, "c2" to 0), outlineOf(blocks).map { it.id to it.depth })
    }

    @Test
    fun anOrphanIsARootAndACycleIsBrokenWithNothingLost() {
        val blocks = listOf(Placed("x", "y", "1"), Placed("y", "x", "2"), Placed("z", "gone", "3"), Placed("x1", "x", "1"))

        assertEquals(listOf("x" to 0, "x1" to 1, "y" to 0, "z" to 0), outlineOf(blocks).map { it.id to it.depth })
    }

    @Test
    fun thereIsAlwaysAKeyBetweenTwoNeighboursAndItSortsBetweenThem() {
        assertEquals("i", keyBetween(null, null))
        val random = Random(7)
        val keys = mutableListOf(keyBetween(null, null))
        repeat(2_000) {
            // Mostly at one spot, the case that ran a Double out of room after about fifty.
            val i = if (random.nextInt(4) == 0) random.nextInt(keys.size + 1) else minOf(1, keys.size)
            val key = keyBetween(keys.getOrNull(i - 1), keys.getOrNull(i))
            assertTrue(!key.endsWith('0'), key)
            keys.add(i, key)
        }
        assertEquals(keys.sorted(), keys)
        assertEquals(keys.size, keys.toSet().size)
        assertTrue(keys.maxOf { it.length } < 400, "a key grows about a digit per halving")
    }
}
