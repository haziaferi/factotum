package com.hazia.factotum.windows

import com.hazia.factotum.data.DeviceFiles
import com.hazia.factotum.data.SyncPassRefused
import com.hazia.factotum.data.SyncPassReport
import com.hazia.factotum.data.image.DesktopImageScaler
import com.hazia.factotum.data.openFactotumDatabase
import com.hazia.factotum.data.syncPass
import java.io.File
import java.io.PrintStream
import kotlin.system.exitProcess

/**
 * The Windows app until the screens (SPEC:R205): one sync pass, then exit. The one optional
 * argument is the sync folder, saved for later passes. Its files live in `%LOCALAPPDATA%\Factotum`
 * (SPEC:R204).
 */
fun main(args: Array<String>) {
    exitProcess(run(args, System.getenv("LOCALAPPDATA"), System.out, System.err))
}

/** The app's pass with its environment given, so tests run it; returns the exit code R205 lists. */
fun run(args: Array<String>, localAppData: String?, out: PrintStream, err: PrintStream): Int {
    if (args.size > 1) {
        err.println("Usage: factotum [sync folder]")
        return 2
    }
    if (localAppData.isNullOrEmpty()) {
        err.println("LOCALAPPDATA is not set.")
        return 1
    }
    // `"D:\Sync\"`, as cmd completes a folder, reaches Java as `D:\Sync"`, and through factotum.bat as
    // `D:\Sync" `: the quote left open takes the space before the launcher's `& call`. No Windows name
    // ends in a space or holds a quote.
    val folder = args.firstOrNull()?.trimEnd()?.removeSuffix("\"")
    val report = try {
        syncPass(DeviceFiles.inFolder(File(localAppData, "Factotum")), ::openFactotumDatabase, DesktopImageScaler(), folder)
    } catch (e: SyncPassRefused) {
        // Another pass running, or a sync folder that does not exist: say so, without a stack trace.
        err.println(e.message)
        return 1
    }
    out.println(said(report))
    return 0
}

/** The line a pass that ran prints (SPEC:R205). */
fun said(report: SyncPassReport): String {
    if (report.folder == null) return "No sync folder yet: give one as the argument."
    val rows = if (report.changed == 1) "1 row" else "${report.changed} rows"
    return "Synced with ${report.folder}: $rows changed." + if (report.renewed) " This device took a new id." else ""
}
