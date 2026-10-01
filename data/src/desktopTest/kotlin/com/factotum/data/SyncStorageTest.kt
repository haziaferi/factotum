package com.factotum.data

import com.factotum.core.sync.Stamp
import com.factotum.core.sync.Ulid
import com.factotum.data.sync.PurgeEntity
import com.factotum.data.sync.loadClock
import com.factotum.data.sync.saveClock
import com.factotum.data.sync.stamp
import kotlinx.coroutines.runBlocking
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class SyncStorageTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun <T> withDatabase(file: File, block: suspend (FactotumDatabase) -> T): T {
        val db = openFactotumDatabase(file).database
        try {
            return runBlocking { block(db) }
        } finally {
            db.close()
        }
    }

    @Test
    fun aPurgeOutlivesAReopen() {
        val file = File(tmp.root, DATABASE_NAME)
        withDatabase(file) { it.syncDao().putPurge(PurgeEntity("01J0000000000000000000000X", 42, "A")) }

        val purges = withDatabase(file) { it.syncDao().purges() }

        assertEquals(listOf(Stamp(42, "A")), purges.map { it.stamp() })
    }

    @Test
    fun theClockResumesAheadOfAWallClockSetBackwards() {
        val file = File(tmp.root, DATABASE_NAME)
        withDatabase(file) { db ->
            val clock = db.syncDao().loadClock("A") { 1_000_000 }
            clock.tick()
            db.syncDao().saveClock(clock)
        }

        val next = withDatabase(file) { db -> db.syncDao().loadClock("A") { 5 }.tick() }

        assertEquals(1_000_001, next.hlc)
    }

    @Test
    fun theDeviceIdIsMadeOnceAndKept() {
        val file = File(tmp.root, "device.id")

        val first = deviceId(file)

        assertTrue(Ulid.isValid(first))
        assertEquals(first, deviceId(file))
    }

    @Test
    fun anUnreadableDeviceIdIsSetAsideAndReplaced() {
        val file = File(tmp.root, "device.id").apply { writeText("garbled") }

        val id = deviceId(file, now = { 9 })

        assertTrue(Ulid.isValid(id))
        assertNotEquals("garbled", id)
        assertEquals("garbled", File(file.path + UNOPENABLE_SUFFIX + 9).readText())
    }
}
