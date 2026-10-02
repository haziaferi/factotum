package com.factotum.data

import androidx.sqlite.SQLiteConnection
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.execSQL
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.io.File

/**
 * Writes [file] as a database of [version], exactly as Room's exported schema describes it, then
 * lets [fill] put rows in it; opening it with the app's database then runs the real migrations.
 */
internal fun createAtVersion(file: File, version: Int, fill: (SQLiteConnection) -> Unit = {}) {
    val schema = Json.parseToJsonElement(File("schemas/com.factotum.data.FactotumDatabase/$version.json").readText())
        .jsonObject.getValue("database").jsonObject
    val connection = BundledSQLiteDriver().open(file.path)
    try {
        for (entity in schema.getValue("entities").jsonArray.map { it.jsonObject }) {
            val table = entity.getValue("tableName").jsonPrimitive.content
            val sql = listOf(entity.getValue("createSql")) + entity["indices"]?.jsonArray?.map { it.jsonObject.getValue("createSql") }.orEmpty()
            sql.forEach { connection.execSQL(it.jsonPrimitive.content.replace("\${TABLE_NAME}", table)) }
        }
        schema.getValue("setupQueries").jsonArray.forEach { connection.execSQL(it.jsonPrimitive.content) }
        connection.execSQL("PRAGMA user_version = $version")
        fill(connection)
    } finally {
        connection.close()
    }
}
