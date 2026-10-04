package com.factotum.core.sync

/**
 * One field group of a row: its values and the stamp of the last write to any of them.
 *
 * [settles] is set only by a person's answer to a clash: it names the other side's stamp that
 * the answer saw, so that device takes the answer instead of asking again.
 */
data class Group(
    val stamp: Stamp,
    val values: Map<String, Any?>,
    val settles: Stamp? = null,
) {
    init {
        // Clashes compare values with ==, so 5 and 5L would differ: one type per kind of value.
        // NaN never equals itself and JSON cannot carry it, so doubles must be finite.
        require(values.values.all { it == null || it is String || it is Long || it is Boolean || (it is Double && it.isFinite()) }) {
            "values must be String, Long, Boolean, finite Double or null: $values"
        }
    }
}

/** A synced row as the merge sees it. A [table]'s columns map onto its groups (ADR 01). Ids are unique across tables. */
data class Row(val table: String, val id: String, val groups: Map<String, Group>) {

    val newest: Stamp get() = groups.values.maxOf { it.stamp }

    /** A local write: [changes] land in [group], which takes [stamp]. */
    fun edit(group: String, stamp: Stamp, changes: Map<String, Any?>): Row {
        val old = requireNotNull(groups[group]) { "row $id has no group $group" }
        require(changes.keys.all { it in old.values }) { "fields outside group $group: ${changes.keys - old.values.keys}" }
        return copy(groups = groups + (group to Group(stamp, old.values + changes)))
    }

    /** [group] set to [values] with [stamp]: edited when the row has it, added when the line that wrote the row is older than the group. */
    fun set(group: String, stamp: Stamp, values: Map<String, Any?>): Row =
        if (group in groups) edit(group, stamp, values) else copy(groups = groups + (group to Group(stamp, values)))
}
