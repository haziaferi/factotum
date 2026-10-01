package com.factotum.data

import android.database.DatabaseErrorHandler
import android.database.sqlite.SQLiteDatabase
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.SQLiteDriver
import androidx.sqlite.driver.AndroidSQLiteConnection

/**
 * A driver that opens the framework database with a no-op corruption handler.
 *
 * `AndroidSQLiteDriver` passes no handler, so the framework's default one deletes a corrupt file
 * and opens an empty database before any of our code runs; [openOrRecover] would then never see
 * the corruption. With the no-op handler, the open throws instead.
 *
 * It wraps the database in [AndroidSQLiteConnection], which androidx.sqlite marks library-group
 * restricted; the stock driver's own wrapper is internal. An androidx.sqlite upgrade can break this.
 */
class KeepFileOnCorruptionDriver : SQLiteDriver {

    @Suppress("INAPPLICABLE_JVM_NAME") // KT-31420; mirrors AndroidSQLiteDriver
    @get:JvmName("hasConnectionPool")
    override val hasConnectionPool: Boolean
        get() = true

    override fun open(fileName: String): SQLiteConnection {
        val database = SQLiteDatabase.openDatabase(
            fileName,
            null,
            SQLiteDatabase.CREATE_IF_NECESSARY,
            DatabaseErrorHandler { },
        )
        @Suppress("RestrictedApi") // the only public wrapper for a framework SQLiteDatabase
        return AndroidSQLiteConnection(database)
    }
}
