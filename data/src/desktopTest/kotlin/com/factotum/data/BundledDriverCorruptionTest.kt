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

    @Test
    fun aCorruptFileIsSetAsideWithItsBytesIntact() {
        val file = tmp.newFile(DATABASE_NAME).apply { writeBytes(garbage) }

        val open = openFactotumDatabase(file, now = { 7 })
        open.database.close()

        assertTrue(open.recovered)
        assertContentEquals(garbage, File(file.path + UNOPENABLE_SUFFIX + 7).readBytes())
        assertTrue(file.exists())
    }

    /** A file whose header and schema read fine but whose table pages are damaged: Room's own open fails. */
    @Test
    fun aDatabaseCorruptPastItsSchemaPageIsSetAsideToo() {
        val file = File(tmp.root, DATABASE_NAME)
        openFactotumDatabase(file).database.close()
        val bytes = file.readBytes()
        val pageSize = ((bytes[16].toInt() and 0xFF) shl 8) or (bytes[17].toInt() and 0xFF)
        for (i in pageSize until bytes.size) bytes[i] = 0x5A
        file.writeBytes(bytes)

        val open = openFactotumDatabase(file, now = { 8 })
        open.database.close()

        assertTrue(open.recovered)
        assertContentEquals(bytes, File(file.path + UNOPENABLE_SUFFIX + 8).readBytes())
    }

    @Test
    fun aLockedDatabaseIsRethrownAndLeftInPlace() {
        val file = File(tmp.root, DATABASE_NAME)
        val holder = BundledSQLiteDriver().open(file.path)
        holder.execSQL("CREATE TABLE t(x)")
        holder.execSQL("BEGIN EXCLUSIVE")
        holder.execSQL("INSERT INTO t VALUES (1)")

        val failure = runCatching { openFactotumDatabase(file).database.close() }.exceptionOrNull()
        holder.execSQL("ROLLBACK")
        holder.close()

        val messages = generateSequence(failure) { it.cause }.mapNotNull { it.message }.toList()
        assertTrue(messages.any { "database is locked" in it }, "expected the busy failure, got $failure")
        assertFalse(tmp.root.list()!!.any { UNOPENABLE_SUFFIX in it })
    }

    @Test
    fun theJournalWalAndShmFilesMoveWithTheDatabase() {
        val base = File(tmp.root, DATABASE_NAME)
        val bytes = mapOf("" to 0, "-journal" to 1, "-wal" to 2, "-shm" to 3)
        bytes.forEach { (suffix, b) -> File(base.path + suffix).writeBytes(byteArrayOf(b.toByte())) }

        setAsideDatabaseFiles(base.path, stamp = 7)

        bytes.forEach { (suffix, b) ->
            assertContentEquals(byteArrayOf(b.toByte()), File(base.path + suffix + UNOPENABLE_SUFFIX + 7).readBytes())
            assertFalse(File(base.path + suffix).exists())
        }
    }
}
