package com.factotum.data

import android.database.sqlite.SQLiteDatabaseCorruptException
import androidx.sqlite.SQLiteDriver
import androidx.sqlite.driver.AndroidSQLiteDriver
import androidx.sqlite.execSQL
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertTrue

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [36])
class KeepFileOnCorruptionDriverTest {

    @get:Rule val tmp = TemporaryFolder()

    private val garbage = "this is not a database\n".toByteArray()

    /** Opens [file] through [driver] lazily, as Room does, so the open happens inside the probe. */
    private fun open(driver: SQLiteDriver, file: File) = openOrRecover(
        build = { lazy { driver.open(file.path) } },
        probe = { it.value.execSQL("SELECT count(*) FROM sqlite_master") },
        close = { if (it.isInitialized()) it.value.close() },
        setAside = { setAsideDatabaseFiles(file.path, stamp = 1) },
        isUnopenable = ::isCorruptDatabase,
    )

    @Test
    fun aCorruptFileIsSetAsideWithItsBytesIntact() {
        val file = tmp.newFile("factotum.db").apply { writeBytes(garbage) }

        val result = open(KeepFileOnCorruptionDriver(), file)
        result.database.value.close()

        assertTrue(result.recovered, "the probe never saw the corrupt file")
        assertContentEquals(garbage, File(file.path + UNOPENABLE_SUFFIX + 1).readBytes())
        assertTrue(file.exists())
    }

    @Test
    fun theFrameworkReportsCorruptionAsItsTypedException() {
        val file = tmp.newFile("typed.db").apply { writeBytes(garbage) }

        val failure = runCatching {
            KeepFileOnCorruptionDriver().open(file.path).execSQL("SELECT count(*) FROM sqlite_master")
        }.exceptionOrNull()

        assertIs<SQLiteDatabaseCorruptException>(failure)
    }

    /** The control: the stock driver destroys the evidence before any of our code runs. */
    @Test
    fun theStockDriverDeletesACorruptFile() {
        val file = tmp.newFile("stock.db").apply { writeBytes(garbage) }

        val result = open(AndroidSQLiteDriver(), file)
        result.database.value.close()

        assertFalse(result.recovered)
        assertFalse(File(file.path + UNOPENABLE_SUFFIX + 1).exists())
        assertEquals(0, tmp.root.listFiles()!!.count { it.readBytes().contentEquals(garbage) })
    }
}
