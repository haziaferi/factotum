package com.hazia.factotum.windows

import com.hazia.factotum.data.DeviceFiles
import com.hazia.factotum.data.SyncPassRefused
import com.hazia.factotum.data.image.DesktopImageScaler
import com.hazia.factotum.data.openFactotumDatabase
import com.hazia.factotum.data.syncPass
import java.io.File
import kotlin.system.exitProcess

/**
 * The Windows app until the screens (SPEC:R205): one sync pass, then exit. The one optional
 * argument is the sync folder, saved for later passes. Its files live in `%LOCALAPPDATA%\Factotum`
 * (SPEC:R204).
 */
fun main(args: Array<String>) {
    if (args.size > 1) {
        System.err.println("Usage: factotum [sync folder]")
        exitProcess(2)
    }
    val local = System.getenv("LOCALAPPDATA")
    if (local.isNullOrEmpty()) {
        System.err.println("LOCALAPPDATA is not set")
        exitProcess(1)
    }
    val report = try {
        syncPass(DeviceFiles.inFolder(File(local, "Factotum")), ::openFactotumDatabase, DesktopImageScaler(), args.firstOrNull())
    } catch (e: SyncPassRefused) {
        // Another pass running, or a sync folder that does not exist: say so, without a stack trace.
        System.err.println(e.message)
        exitProcess(1)
    }
    when {
        report.folder == null -> println("No sync folder yet: give one as the argument.")
        else -> println("Synced with ${report.folder}: ${report.changed} rows changed." + if (report.renewed) " This device took a new id." else "")
    }
}
