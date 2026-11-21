package com.hazia.factotum.data.sync

import androidx.room.Room
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.SQLiteDriver
import androidx.sqlite.SQLiteStatement
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import com.hazia.factotum.data.FactotumDatabase
import com.hazia.factotum.data.openDatabase
import java.io.File
import java.util.concurrent.atomic.AtomicInteger

/**
 * The bundled driver, counting every row a query reads from the purge registry, through every
 * connection Room opens (SPEC:R27: the registry is looked up by id, never loaded whole).
 */
internal class RegistryReads(private val driver: SQLiteDriver = BundledSQLiteDriver()) : SQLiteDriver by driver {
    val rows = AtomicInteger()

    override fun open(fileName: String): SQLiteConnection = Counting(driver.open(fileName))

    /** Opens [file] as the app does, through this driver. */
    fun database(file: File): FactotumDatabase =
        openDatabase(file, { Room.databaseBuilder<FactotumDatabase>(name = file.absolutePath) }, this).database

    private inner class Counting(private val connection: SQLiteConnection) : SQLiteConnection by connection {
        override fun prepare(sql: String): SQLiteStatement {
            val statement = connection.prepare(sql)
            if (!sql.trimStart().startsWith("SELECT", ignoreCase = true) || "purge_registry" !in sql) return statement
            return object : SQLiteStatement by statement {
                override fun step(): Boolean = statement.step().also { if (it) rows.incrementAndGet() }
            }
        }
    }
}
