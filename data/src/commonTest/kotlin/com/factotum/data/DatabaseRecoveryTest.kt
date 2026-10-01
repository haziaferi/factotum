package com.factotum.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertSame
import kotlin.test.assertTrue

class DatabaseRecoveryTest {

    /** A fake database whose probe fails for the first [failures] builds. */
    private class Fixture(
        private val failures: Int,
        private val failure: (Int) -> Throwable = { IllegalStateException("generation $it will not open") },
        private val closeThrows: Boolean = false,
        private val isUnopenable: (Throwable) -> Boolean = { true },
    ) {
        val events = mutableListOf<String>()
        private var builds = 0

        fun open() = openOrRecover(
            build = { events += "build"; ++builds },
            probe = { generation ->
                events += "probe($generation)"
                if (generation <= failures) throw failure(generation)
            },
            close = { events += "close($it)"; if (closeThrows) error("already closed") },
            setAside = { events += "setAside" },
            isUnopenable = isUnopenable,
        )
    }

    @Test
    fun aDatabaseThatOpensIsUsedAndNothingIsSetAside() {
        val f = Fixture(failures = 0)
        val result = f.open()

        assertFalse(result.recovered)
        assertEquals(1, result.database)
        assertEquals(listOf("build", "probe(1)"), f.events)
    }

    @Test
    fun aFailedProbeClosesBeforeSettingAsideThenRebuilds() {
        val f = Fixture(failures = 1)
        val result = f.open()

        assertTrue(result.recovered)
        assertEquals(2, result.database)
        assertEquals(listOf("build", "probe(1)", "close(1)", "setAside", "build", "probe(2)"), f.events)
    }

    @Test
    fun aFreshDatabaseThatStillFailsIsRethrownNotRecoveredAgain() {
        val f = Fixture(failures = 2)

        assertIs<IllegalStateException>(runCatching { f.open() }.exceptionOrNull())
        assertEquals(1, f.events.count { it == "setAside" })
        assertEquals(2, f.events.count { it == "build" })
    }

    @Test
    fun aFailureThatIsNotCorruptionIsRethrownWithTheFileLeftAlone() {
        val busy = IllegalStateException("database is locked")
        val f = Fixture(failures = 1, failure = { busy }, isUnopenable = { it !== busy })

        assertSame(busy, runCatching { f.open() }.exceptionOrNull())
        assertEquals(listOf("build", "probe(1)", "close(1)"), f.events)
    }

    @Test
    fun aDatabaseThatCannotBeClosedIsStillRecovered() {
        val f = Fixture(failures = 1, closeThrows = true)
        val result = f.open()

        assertTrue(result.recovered)
        assertEquals(2, result.database)
        assertEquals(listOf("build", "probe(1)", "close(1)", "setAside", "build", "probe(2)"), f.events)
    }
}
