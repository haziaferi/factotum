package com.hazia.factotum.windows

import com.hazia.factotum.data.SyncPassReport
import org.junit.Rule
import org.junit.rules.TemporaryFolder
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.PrintStream
import kotlin.test.Test
import kotlin.test.assertEquals

/** SPEC:R205: every line the Windows app prints, and its exit codes, as R205's Values list them. */
class MainTest {

    @get:Rule val tmp = TemporaryFolder()

    private class Ran(val code: Int, val out: String, val err: String)

    private fun app(vararg args: String, local: String? = tmp.root.path): Ran {
        val out = ByteArrayOutputStream()
        val err = ByteArrayOutputStream()
        val code = run(arrayOf(*args), local, PrintStream(out, true), PrintStream(err, true))
        return Ran(code, out.toString().trim(), err.toString().trim())
    }

    @Test
    fun everyCaseExitsAndPrintsAsR205Lists() {
        val sync = tmp.newFolder("sync")
        val missing = File(tmp.root, "nowhere")

        val none = app()
        val given = app(sync.path)
        val saved = app()
        val refused = app(missing.path)
        val usage = app("a", "b")
        val noLocal = app(local = null)

        assertEquals(Ran(0, "No sync folder yet: give one as the argument.", "").text(), none.text())
        assertEquals(Ran(0, "Synced with ${sync.absolutePath}: 0 rows changed.", "").text(), given.text())
        assertEquals(given.text(), saved.text())
        assertEquals(Ran(1, "", "No sync folder at ${missing.absolutePath}.").text(), refused.text())
        assertEquals(Ran(2, "", "Usage: factotum [sync folder]").text(), usage.text())
        assertEquals(Ran(1, "", "LOCALAPPDATA is not set.").text(), noLocal.text())
    }

    /** cmd completes a folder as `"D:\Sync\"`, which reaches the app as `D:\Sync"`, and through factotum.bat as `D:\Sync" `. */
    @Test
    fun aQuoteLeftByATrailingBackslashIsDropped() {
        val sync = tmp.newFolder("sync")
        val line = "Synced with ${sync.absolutePath}: 0 rows changed."

        assertEquals(line, app(sync.path + "\"").out)
        assertEquals(line, app(sync.path + "\" ").out)
    }

    @Test
    fun oneChangedRowIsPrintedAsOneRow() {
        assertEquals("Synced with D:\\Sync: 1 row changed.", said(SyncPassReport("d", "D:\\Sync", 1, false)))
        assertEquals("Synced with D:\\Sync: 2 rows changed.", said(SyncPassReport("d", "D:\\Sync", 2, false)))
    }

    @Test
    fun aNewIdIsSaidAfterTheSyncLine() {
        assertEquals("Synced with D:\\Sync: 0 rows changed. This device took a new id.", said(SyncPassReport("d", "D:\\Sync", 0, true)))
    }

    private fun Ran.text() = "exit=$code out=[$out] err=[$err]"
}
