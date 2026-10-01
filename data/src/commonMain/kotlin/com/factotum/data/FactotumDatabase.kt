package com.factotum.data

import androidx.room.AutoMigration
import androidx.room.ConstructedBy
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.RoomDatabaseConstructor
import com.factotum.data.item.COMPLETION
import com.factotum.data.item.CompletionEntity
import com.factotum.data.item.completionTable
import com.factotum.data.item.ITEM
import com.factotum.data.item.ItemDao
import com.factotum.data.item.ItemEntity
import com.factotum.data.item.itemTable
import com.factotum.data.reminder.REMINDER
import com.factotum.data.reminder.ReminderDao
import com.factotum.data.reminder.ReminderEntity
import com.factotum.data.reminder.reminderTable
import com.factotum.data.sync.AskEntity
import com.factotum.data.sync.BaseEntity
import com.factotum.data.sync.ClockEntity
import com.factotum.data.sync.KnownTablesEntity
import com.factotum.data.sync.OutboxEntity
import com.factotum.data.sync.PurgeEntity
import com.factotum.data.sync.ReadEntity
import com.factotum.data.sync.RowTable
import com.factotum.data.sync.SyncDao
import com.factotum.data.sync.WaitingEntity

@Database(
    entities = [
        PurgeEntity::class, ClockEntity::class,
        BaseEntity::class, AskEntity::class, ReadEntity::class, OutboxEntity::class, KnownTablesEntity::class,
        WaitingEntity::class, ItemEntity::class, CompletionEntity::class, ReminderEntity::class,
    ],
    version = 4,
    exportSchema = true,
    autoMigrations = [AutoMigration(from = 1, to = 2), AutoMigration(from = 2, to = 3), AutoMigration(from = 3, to = 4)],
)
@ConstructedBy(FactotumDatabaseConstructor::class)
abstract class FactotumDatabase : RoomDatabase() {
    internal abstract fun syncDao(): SyncDao
    internal abstract fun itemDao(): ItemDao
    internal abstract fun reminderDao(): ReminderDao
}

/** The synced tables, by the name their folder records carry; [SchemaTriggers] queues writes to each for export. */
internal val SYNCED_TABLES = listOf(ITEM, COMPLETION, REMINDER)

internal fun FactotumDatabase.syncedTables(): Map<String, RowTable> =
    itemDao().let { mapOf(ITEM to itemTable(it), COMPLETION to completionTable(it), REMINDER to reminderTable(reminderDao())) }
        .also { check(it.keys.toList() == SYNCED_TABLES) { "every synced table needs its export triggers" } }

// Room's KSP processor generates the actual for each target.
@Suppress("KotlinNoActualForExpect")
expect object FactotumDatabaseConstructor : RoomDatabaseConstructor<FactotumDatabase>

const val DATABASE_NAME = "factotum.db"
