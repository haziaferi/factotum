package com.factotum.data.item

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.factotum.core.recurrence.EditChanges
import com.factotum.core.recurrence.EditScope
import com.factotum.core.recurrence.OccurrenceEdit
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp
import kotlinx.datetime.DayOfWeek
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalDateTime
import kotlinx.datetime.LocalTime
import kotlinx.datetime.isoDayNumber
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

internal const val OCCURRENCE_EDIT = "occurrence_edit"

/**
 * ADR 11's occurrence-edit log: one table for every repeating item, insert-once and
 * tombstone-once, so its one group changes only when `deleted_at` is set (undo; a trigger refuses
 * anything else). `created_*` is the edit's ADR 01 stamp, which orders the edits; `seen` lists the
 * ids of the edits on the same place its author had seen, which tells a clash from a correction.
 */
@Entity(
    tableName = OCCURRENCE_EDIT,
    foreignKeys = [ForeignKey(ItemEntity::class, ["id"], ["item_id"], onDelete = ForeignKey.CASCADE, deferred = true)],
    indices = [Index("item_id")],
)
internal data class OccurrenceEditEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "item_id") val itemId: String,
    val scope: String,
    val at: String?,
    val date: String?,
    /** WEEK or FROM narrowed to some weekdays, Monday as bit 0; 0 for every day. */
    val days: Long,
    /** Only the fields the edit sets, as compact JSON ([EditCodec]). */
    val changes: String,
    @ColumnInfo(name = "created_hlc") val createdHlc: Long,
    @ColumnInfo(name = "created_device") val createdDevice: String,
    /** Comma-separated edit ids (ULIDs hold no comma); empty when the author had seen none. */
    val seen: String,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
)

internal fun occurrenceEditTable(dao: ItemDao) =
    EntityTable(dao::edits, dao::allEdits, dao::putEdits, dao::deleteEdits, OccurrenceEditEntity::toRow, Row::toEditEntity) {
        listOf(ITEM to it.itemId)
    }

internal fun OccurrenceEditEntity.toRow() = Row(OCCURRENCE_EDIT, id, mapOf(
    WHOLE to Group(Stamp(hlc, device), mapOf(
        "item_id" to itemId, "scope" to scope, "at" to at, "date" to date, "days" to days, "changes" to changes,
        "created_hlc" to createdHlc, "created_device" to createdDevice, "seen" to seen,
        "deleted_at" to deletedAt,
    )),
))

/** Throws when [this] is not an occurrence edit this version can read. */
internal fun Row.toEditEntity(): OccurrenceEditEntity {
    val g = groups.getValue(WHOLE)
    return OccurrenceEditEntity(
        id = id,
        itemId = g.values["item_id"] as String,
        scope = g.values["scope"] as String,
        at = g.values["at"] as String?,
        date = g.values["date"] as String?,
        days = g.values["days"] as Long,
        changes = g.values["changes"] as String,
        createdHlc = g.values["created_hlc"] as Long,
        createdDevice = g.values["created_device"] as String,
        seen = g.values["seen"] as String,
        deletedAt = g.values["deleted_at"] as Long?,
        hlc = g.stamp.hlc,
        device = g.stamp.device,
    ).also { it.toEdit() }
}

internal fun OccurrenceEditEntity.toEdit() = OccurrenceEdit(
    id = id,
    scope = EditScope.valueOf(scope),
    at = at?.let(LocalDateTime::parse),
    date = date?.let(LocalDate::parse),
    days = daysOf(days),
    changes = EditCodec.decode(changes),
    created = Stamp(createdHlc, createdDevice),
    seen = seen.split(',').filter { it.isNotEmpty() }.toSet(),
)

internal fun daysOf(mask: Long): Set<DayOfWeek> = DayOfWeek.entries.filter { mask and (1L shl (it.isoDayNumber - 1)) != 0L }.toSet()

internal fun maskOf(days: Set<DayOfWeek>): Long = days.sumOf { 1L shl (it.isoDayNumber - 1) }

/**
 * [EditChanges] as the compact JSON the `changes` column holds: only the fields set, under ADR 11's
 * names (skip, moved_to, time, duration, title, rule, week_days), plus the habit fields it carries.
 */
internal object EditCodec {

    fun encode(c: EditChanges): String {
        val fields = linkedMapOf<String, JsonElement>()
        if (c.skip) fields["skip"] = JsonPrimitive(true)
        c.movedTo?.let { fields["moved_to"] = JsonPrimitive(it.toString()) }
        c.time?.let { fields["time"] = JsonPrimitive(it.toString()) }
        c.durationMin?.let { fields["duration"] = JsonPrimitive(it) }
        c.title?.let { fields["title"] = JsonPrimitive(it) }
        c.rule?.let { r ->
            fields["rule"] = JsonObject(recurrenceValues(r).filterValues { it != null }.mapValues { (_, v) -> primitive(v) })
        }
        c.weekDays?.let { fields["week_days"] = JsonPrimitive(maskOf(it)) }
        c.others.forEach { (k, raw) -> fields[k] = Json.parseToJsonElement(raw) }
        return JsonObject(fields).toString()
    }

    fun decode(text: String): EditChanges {
        val o = Json.parseToJsonElement(text).jsonObject
        val known = setOf("skip", "deleted", "moved_to", "time", "duration", "title", "rule", "week_days")
        return EditChanges(
            // ADR 11 lists both skip and deleted; an occurrence deleted is one skipped.
            skip = o["skip"]?.jsonPrimitive?.boolean ?: o["deleted"]?.jsonPrimitive?.boolean ?: false,
            movedTo = o["moved_to"]?.jsonPrimitive?.content?.let(LocalDate::parse),
            time = o["time"]?.jsonPrimitive?.content?.let(LocalTime::parse),
            durationMin = o["duration"]?.jsonPrimitive?.long,
            title = o["title"]?.jsonPrimitive?.content,
            rule = o["rule"]?.jsonObject?.let { r ->
                fun s(k: String) = r[k]?.jsonPrimitive?.content
                fun n(k: String) = r[k]?.jsonPrimitive?.long
                recurrenceOf(s("recurrence_kind"), s("rrule"), n("rand_min_days"), n("rand_max_days"), n("window_days"), s("window_start"), s("window_end"))
            },
            weekDays = o["week_days"]?.jsonPrimitive?.long?.let(::daysOf),
            others = o.filterKeys { it !in known }.mapValues { (_, v) -> v.toString() },
        )
    }

    private fun primitive(v: Any?): JsonElement = when (v) {
        null -> JsonNull
        is String -> JsonPrimitive(v)
        is Long -> JsonPrimitive(v)
        else -> throw IllegalArgumentException("not a rule value: $v")
    }
}
