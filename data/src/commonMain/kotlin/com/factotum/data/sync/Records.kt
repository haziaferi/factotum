package com.factotum.data.sync

import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.double
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long
import kotlinx.serialization.json.longOrNull

/** One line of a sync folder file (ADR 13): a row with every group, or a purge. */
internal sealed interface Record

internal data class RowRecord(val row: Row) : Record

internal data class PurgeRecord(val id: String, val stamp: Stamp) : Record

/**
 * Compact JSON, one record per line (§3.13 requirement 4):
 * `{"t":table,"id":id,"g":{group:{"h":hlc,"d":device,"v":{field:value},"s":[hlc,device]}}}`
 * for a row (`s` only on an answered clash), and `{"p":id,"h":hlc,"d":device}` for a purge.
 *
 * A Long is written without a decimal point and a Double always with one, so each value reads
 * back as the type it was written with, and a clash compares like with like.
 */
internal object RecordCodec {

    fun encode(record: Record): String = when (record) {
        is RowRecord -> JsonObject(mapOf(
            "t" to JsonPrimitive(record.row.table),
            "id" to JsonPrimitive(record.row.id),
            "g" to JsonObject(record.row.groups.mapValues { (_, g) -> group(g) }),
        ))
        is PurgeRecord -> JsonObject(mapOf(
            "p" to JsonPrimitive(record.id),
            "h" to JsonPrimitive(record.stamp.hlc),
            "d" to JsonPrimitive(record.stamp.device),
        ))
    }.toString()

    /** @throws IllegalArgumentException when [line] is not a record this version can read. */
    fun decode(line: String): Record {
        val o = Json.parseToJsonElement(line).jsonObject
        o["p"]?.let { return PurgeRecord(it.string(), stamp(o)) }
        val groups = field(o, "g").jsonObject.mapValues { (_, g) -> group(g.jsonObject) }
        require(groups.isNotEmpty()) { "a row with no groups" }
        return RowRecord(Row(field(o, "t").string(), field(o, "id").string(), groups))
    }

    fun encodeGroup(g: Group): String = group(g).toString()

    fun decodeGroup(text: String): Group = group(Json.parseToJsonElement(text).jsonObject)

    private fun group(g: Group): JsonObject {
        val fields = mutableMapOf(
            "h" to JsonPrimitive(g.stamp.hlc),
            "d" to JsonPrimitive(g.stamp.device),
            "v" to JsonObject(g.values.mapValues { (_, v) -> value(v) }),
        )
        g.settles?.let { fields["s"] = JsonArray(listOf(JsonPrimitive(it.hlc), JsonPrimitive(it.device))) }
        return JsonObject(fields)
    }

    private fun group(o: JsonObject): Group = Group(
        stamp = stamp(o),
        values = field(o, "v").jsonObject.mapValues { (_, v) -> value(v) },
        settles = o["s"]?.jsonArray?.let {
            require(it.size == 2) { "settles is [hlc, device]" }
            Stamp(it[0].jsonPrimitive.long, it[1].string())
        },
    )

    private fun stamp(o: JsonObject) = Stamp(field(o, "h").jsonPrimitive.long, field(o, "d").string())

    private fun value(v: Any?): JsonElement = when (v) {
        null -> JsonNull
        is String -> JsonPrimitive(v)
        is Long -> JsonPrimitive(v)
        is Boolean -> JsonPrimitive(v)
        is Double -> JsonPrimitive(v)
        else -> throw IllegalArgumentException("not a group value: $v")
    }

    private fun value(e: JsonElement): Any? {
        if (e is JsonNull) return null
        val p = e.jsonPrimitive
        if (p.isString) return p.content
        return p.booleanOrNull ?: p.longOrNull ?: p.double
    }

    private fun field(o: JsonObject, name: String) = requireNotNull(o[name]) { "missing \"$name\"" }

    private fun JsonElement.string(): String {
        val p = jsonPrimitive
        require(p.isString) { "expected a string: $p" }
        return p.content
    }
}
