package com.factotum.data

import androidx.room.RoomDatabase
import androidx.room.useReaderConnection
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.SQLiteDriver
import androidx.sqlite.execSQL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import java.io.File

/**
 * The one way the app opens its database on either platform: through [openOrRecover], so a
 * corrupt file is set aside rather than lost. Blocks while it probes; call it off the main thread.
 */
internal fun openDatabase(
    file: File,
    builder: () -> RoomDatabase.Builder<FactotumDatabase>,
    driver: SQLiteDriver,
    now: () -> Long = System::currentTimeMillis,
): DatabaseOpen<FactotumDatabase> {
    file.parentFile?.mkdirs()
    val tracked = TrackingDriver(driver)
    return openOrRecover(
        build = { builder().setDriver(tracked).setQueryCoroutineContext(Dispatchers.IO).addCallback(SchemaTriggers).build() },
        // Room opens lazily; a real read forces the open, schema creation and migrations.
        probe = { db ->
            runBlocking { db.useReaderConnection { it.usePrepared("SELECT count(*) FROM sqlite_master") { s -> s.step() } } }
        },
        close = {
            it.close()
            tracked.closeAll()
        },
        setAside = { setAsideDatabaseFiles(file.path, now()) },
        isUnopenable = ::isCorruptDatabase,
    )
}

/**
 * Before Room upgrades an older file, drops the app's triggers, which [SchemaTriggers] makes again
 * on every open. A migration that rebuilds a table (Room does, to add a column inside a table or a
 * key) renames a fresh copy into its place, and SQLite checks every trigger on that rename: one
 * that names the table, dropped a moment before, would stop the upgrade (found with slice 08).
 */
internal fun dropTriggersBeforeUpgrade(connection: SQLiteConnection) {
    val version = connection.prepare("PRAGMA user_version").use { it.step(); it.getLong(0) }
    if (version == 0L || version >= SCHEMA_VERSION) return
    val triggers = connection.prepare("SELECT name FROM sqlite_master WHERE type = 'trigger'").use { s -> buildList { while (s.step()) add(s.getText(0)) } }
    triggers.forEach { connection.execSQL("DROP TRIGGER IF EXISTS `$it`") }
}

/**
 * Remembers every connection it opens. Room keeps its connection open when its own open fails,
 * and Windows cannot rename an open file, so recovery closes them all before setting the file aside.
 */
private class TrackingDriver(private val driver: SQLiteDriver) : SQLiteDriver by driver {
    private val opened = mutableListOf<SQLiteConnection>()

    override fun open(fileName: String): SQLiteConnection =
        driver.open(fileName).also { synchronized(opened) { opened += it } }.also(::dropTriggersBeforeUpgrade)

    fun closeAll() = synchronized(opened) {
        opened.forEach { runCatching { it.close() } }
        opened.clear()
    }
}
