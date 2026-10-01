package com.factotum.data

import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.execSQL
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.File
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class BundledDriverCorruptionTest {

    @get:Rule val tmp = TemporaryFolder()

    private val garbage = "this is not a database\n".toByteArray()
    private val driver = BundledSQLiteDriver()

    /** Opens [file] lazily, as Room does, so the open happens inside the probe. */
    private fun open(file: File) = openOrRecover(
        build = { lazy { driver.open(file.path) } },
        probe = { it.value.execSQL("SELECT count(*) FROM sqlite_master") },
        close = { if (it.isInitialized()) it.value.close() },
        setAside = { setAsideDatabaseFiles(file.path, stamp = 7) },
        isUnopenable = ::isCorruptDatabase,
    )

    @Test
    fun aCorruptFileIsSetAsideWithItsBytesIntact() {
        val file = tmp.newFile("factotum.db").apply { writeBytes(garbage) }

        val result = open(file)
        result.database.value.close()

        assertTrue(result.recovered)
        assertContentEquals(garbage, File(file.path + UNOPENABLE_SUFFIX + 7).readBytes())
        assertTrue(file.exists())
    }

    @Test
    fun aLockedDatabaseIsRethrownAndLeftInPlace() {
        val file = File(tmp.root, "factotum.db")
        val holder = driver.open(file.path)
        holder.execSQL("CREATE TABLE t(x)")
        holder.execSQL("BEGIN EXCLUSIVE")
        holder.execSQL("INSERT INTO t VALUES (1)")

        val failure = runCatching { open(file) }.exceptionOrNull()
        holder.execSQL("ROLLBACK")
        holder.close()

        assertTrue(failure?.message.orEmpty().contains("database is locked"), "expected the busy failure, got $failure")
        assertFalse(File(file.path + UNOPENABLE_SUFFIX + 7).exists())
        assertTrue(file.exists())
    }

    @Test
    fun theJournalWalAndShmFilesMoveWithTheDatabase() {
        val base = File(tmp.root, "factotum.db")
        val bytes = mapOf("" to 0, "-journal" to 1, "-wal" to 2, "-shm" to 3)
        bytes.forEach { (suffix, b) -> File(base.path + suffix).writeBytes(byteArrayOf(b.toByte())) }

        setAsideDatabaseFiles(base.path, stamp = 7)

        bytes.forEach { (suffix, b) ->
            assertContentEquals(byteArrayOf(b.toByte()), File(base.path + suffix + UNOPENABLE_SUFFIX + 7).readBytes())
            assertFalse(File(base.path + suffix).exists())
        }
    }
}
