package com.factotum.core.formula

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

/** What Factotum adds to Tendril's formulas: keys rewritten between names and ids, and rollups as one function. */
class FormulaKeysTest {

    @Test
    fun aFormulaTypedWithNamesIsStoredWithIdsAndReadBackWithTheNamesOfTheDay() {
        val typed = """if(prop("Done"), prop("Score") * 2, 0) + prop("Mystery")"""
        val ids = mapOf("Done" to "p1", "Score" to "p2")
        val stored = rewriteKeys(typed) { ids[it] }

        assertEquals("""if(prop("p1"), prop("p2") * 2, 0) + prop("Mystery")""", stored)
        assertEquals(setOf("p1", "p2", "Mystery"), parseFormula(stored).propertyReferences().map { it.key }.toSet())
        val renamed = mapOf("p1" to "Finished", "p2" to "Points \"x\"")
        assertEquals("""if(prop("Finished"), prop("Points \"x\"") * 2, 0) + prop("Mystery")""", rewriteKeys(stored) { renamed[it] })
    }

    @Test
    fun aStringThatIsNotAPropertyKeyIsLeftAlone() {
        assertEquals(""""Done" + prop("p2")""", rewriteKeys(""""Done" + prop("Score")""") { mapOf("Done" to "p1", "Score" to "p2")[it] })
    }

    @Test
    fun aRollupCountsRowsAndReadsWhatItCanOfTheRest() {
        assertEquals("3", rollup(RollupAggregation.COUNT, 3, emptyList()))
        assertEquals("7.5", rollup(RollupAggregation.SUM, 3, listOf("2", "5.5", "x")))
        assertEquals("0", rollup(RollupAggregation.SUM, 1, listOf("x")))
        assertEquals("2", rollup(RollupAggregation.MIN, 2, listOf("2", "5")))
        assertEquals("5", rollup(RollupAggregation.MAX, 2, listOf("2", "5")))
        assertEquals("2026-01-02", rollup(RollupAggregation.EARLIEST, 2, listOf("2026-03-01", "2026-01-02")))
        assertEquals("2026-03-01", rollup(RollupAggregation.LATEST, 2, listOf("2026-03-01", "2026-01-02")))
        assertEquals("a, b", rollup(RollupAggregation.SHOW_ORIGINAL, 2, listOf("a", "b")))
        assertNull(rollup(RollupAggregation.SUM, 0, emptyList()))
        assertNull(rollup(RollupAggregation.EARLIEST, 1, listOf("soon")))
    }
}
