package com.factotum.data

import androidx.room.AutoMigration
import androidx.room.ConstructedBy
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.RoomDatabaseConstructor
import com.factotum.data.sync.AskEntity
import com.factotum.data.sync.BaseEntity
import com.factotum.data.sync.ClockEntity
import com.factotum.data.sync.KnownTablesEntity
import com.factotum.data.sync.OutboxEntity
import com.factotum.data.sync.PurgeEntity
import com.factotum.data.sync.ReadEntity
import com.factotum.data.sync.SyncDao

@Database(
    entities = [
        PurgeEntity::class, ClockEntity::class,
        BaseEntity::class, AskEntity::class, ReadEntity::class, OutboxEntity::class, KnownTablesEntity::class,
    ],
    version = 2,
    exportSchema = true,
    autoMigrations = [AutoMigration(from = 1, to = 2)],
)
@ConstructedBy(FactotumDatabaseConstructor::class)
abstract class FactotumDatabase : RoomDatabase() {
    internal abstract fun syncDao(): SyncDao
}

// Room's KSP processor generates the actual for each target.
@Suppress("KotlinNoActualForExpect")
expect object FactotumDatabaseConstructor : RoomDatabaseConstructor<FactotumDatabase>

const val DATABASE_NAME = "factotum.db"
