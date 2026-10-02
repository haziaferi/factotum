package com.factotum.data.item

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.sqlite.SQLiteConnection
import androidx.sqlite.execSQL
import com.factotum.core.plan.Overrides
import com.factotum.core.plan.TimeBlock
import com.factotum.core.sync.Group
import com.factotum.core.sync.Row
import com.factotum.core.sync.Stamp

internal const val HABIT_BLOCK = "habit_block"

/**
 * A time block of the day that habits sit in (Tendril's `HabitBlock`, ADR 06): minutes from
 * midnight, [endMinute] not part of it. One group, as Tendril merges the whole row. [name] is null
 * for a default block nobody renamed, shown in the app's language; [overrides] are its weekday
 * times in Tendril's text ([Overrides]), kept in the row so they merge with it. A habit names its
 * block without a foreign key: a deleted block leaves its habits at "any time", as in Tendril.
 */
@Entity(tableName = HABIT_BLOCK)
internal data class HabitBlockEntity(
    @PrimaryKey val id: String,
    val name: String?,
    @ColumnInfo(name = "start_minute") val startMinute: Long,
    @ColumnInfo(name = "end_minute") val endMinute: Long,
    val position: Long,
    /** One of Tendril's six: sunrise, sun, leaf, sunset, moon, star. */
    val icon: String?,
    /** Degrees on the colour wheel. */
    val hue: Long?,
    val overrides: String?,
    @ColumnInfo(name = "deleted_at") val deletedAt: Long?,
    val hlc: Long,
    val device: String,
) {
    fun toBlock() = TimeBlock(id, startMinute.toInt(), endMinute.toInt(), position.toInt(), Overrides.parse(overrides))
}

/**
 * The five blocks every database starts with (Tendril's defaults), under fixed ids and one fixed
 * stamp, so two devices that seed on their own hold the same five rows, and any real edit is newer.
 */
internal val DEFAULT_BLOCKS = listOf(
    HabitBlockEntity("block-morning", null, 390, 540, 0, "sunrise", 25, null, null, 0, SEED_DEVICE),
    HabitBlockEntity("block-midday", null, 540, 780, 1, "sun", 45, null, null, 0, SEED_DEVICE),
    HabitBlockEntity("block-afternoon", null, 780, 1080, 2, "leaf", 110, null, null, 0, SEED_DEVICE),
    HabitBlockEntity("block-evening", null, 1080, 1290, 3, "sunset", 265, null, null, 0, SEED_DEVICE),
    HabitBlockEntity("block-night", null, 1290, 1410, 4, "moon", 205, null, null, 0, SEED_DEVICE),
)

private const val SEED_DEVICE = "seed"

/** Writes [DEFAULT_BLOCKS] when the database is made, before the export triggers exist: every device has them already. */
internal fun seedBlocks(connection: SQLiteConnection) = DEFAULT_BLOCKS.forEach { b ->
    connection.execSQL(
        "INSERT OR IGNORE INTO $HABIT_BLOCK (id, name, start_minute, end_minute, position, icon, hue, overrides, deleted_at, hlc, device) " +
            "VALUES ('${b.id}', NULL, ${b.startMinute}, ${b.endMinute}, ${b.position}, '${b.icon}', ${b.hue}, NULL, NULL, ${b.hlc}, '${b.device}')",
    )
}

internal fun habitBlockTable(dao: ItemDao) =
    EntityTable(dao::blocks, dao::allBlocks, dao::putBlocks, dao::deleteBlocks, HabitBlockEntity::toRow, Row::toBlockEntity) { emptyList() }

internal fun HabitBlockEntity.toRow() = Row(HABIT_BLOCK, id, mapOf(
    WHOLE to Group(Stamp(hlc, device), mapOf(
        "name" to name, "start_minute" to startMinute, "end_minute" to endMinute, "position" to position, "icon" to icon,
        "hue" to hue, "overrides" to overrides, "deleted_at" to deletedAt,
    )),
))

/** Throws when [this] is not a block this version can read, its weekday times included. */
internal fun Row.toBlockEntity(): HabitBlockEntity {
    val g = groups.getValue(WHOLE)
    return HabitBlockEntity(
        id = id,
        name = g.values["name"] as String?,
        startMinute = g.values["start_minute"] as Long,
        endMinute = g.values["end_minute"] as Long,
        position = g.values["position"] as Long,
        icon = g.values["icon"] as String?,
        hue = g.values["hue"] as Long?,
        overrides = g.values["overrides"] as String?,
        deletedAt = g.values["deleted_at"] as Long?,
        hlc = g.stamp.hlc,
        device = g.stamp.device,
    ).also { it.toBlock() }
}
