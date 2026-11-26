package com.hazia.factotum.data

import android.content.Context
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.room.execSQL
import androidx.room.useReaderConnection
import androidx.room.useWriterConnection
import androidx.sqlite.SQLiteStatement
import androidx.test.platform.app.InstrumentationRegistry
import com.hazia.factotum.core.time.LONG_RUN
import com.hazia.factotum.data.item.ItemRepository
import com.hazia.factotum.data.reminder.ReminderRepository
import com.hazia.factotum.data.settings.PersonalSettings
import com.hazia.factotum.data.sync.loadClock
import com.hazia.factotum.data.time.ActivityRepository
import com.hazia.factotum.data.time.TimeRepository
import com.hazia.factotum.data.tracker.TrackerRepository
import kotlinx.coroutines.runBlocking
import kotlinx.datetime.LocalTime

/** What a device test prints for the record; `adb logcat -s FactotumDevice` reads it. */
internal fun report(line: String) {
    Log.i("FactotumDevice", line)
}

internal val context: Context get() = InstrumentationRegistry.getInstrumentation().targetContext

/** A shell command run as the shell user, which may force-stop and read `dumpsys`. */
internal fun shell(command: String): String =
    ParcelFileDescriptor.AutoCloseInputStream(InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommand(command))
        .bufferedReader().use { it.readText() }

private object DeviceSettings : PersonalSettings {
    override suspend fun dayStart() = LocalTime(0, 0)
    override suspend fun longRun() = LONG_RUN
}

/** The app's own database, opened as the Android app opens it (the framework driver), made anew. */
internal class DeviceDatabase : AutoCloseable {
    init {
        context.deleteDatabase(DATABASE_NAME)
    }

    val db: FactotumDatabase = openFactotumDatabase(context).database
    private var n = 0
    private val writes = LocalWrites(db, runBlocking { db.syncDao().loadClock("A") { 1_000 } })
    private val newId = { "id-${n++}" }
    val items = ItemRepository(db, writes, newId)
    val reminders = ReminderRepository(db, writes, newId, DeviceSettings)
    val activities = ActivityRepository(db, writes, newId, DeviceSettings)
    val time = TimeRepository(db, writes, newId, DeviceSettings)
    val trackers = TrackerRepository(db, writes, newId)

    fun <T> read(sql: String, row: (SQLiteStatement) -> T): List<T> =
        runBlocking { db.useReaderConnection { c -> c.usePrepared(sql) { s -> buildList { while (s.step()) add(row(s)) } } } }

    fun write(sql: String) = runBlocking { db.useWriterConnection { it.execSQL(sql) } }

    /** The message a refused write fails with; the test fails if the write goes through. */
    fun refused(sql: String): String {
        val failure = runCatching { write(sql) }.exceptionOrNull() ?: error("the database took: $sql")
        return failure.message.orEmpty()
    }

    override fun close() {
        db.close()
        context.deleteDatabase(DATABASE_NAME)
    }
}
