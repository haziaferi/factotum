package com.factotum.core.label

/*
 * Labels (ADR 08): one vocabulary across activities, habits, trackers and pages. Names are unique
 * ignoring case, and two labels a sync finds with one name merge into the one made first (owner,
 * 2026-10-02). A new label's colour comes from its name, as Tendril's does, so a label made again
 * with the same name looks the same on every device.
 */

/** What a label is offered for: everything, or only activities or only trackers (Chronicle's `appliesTo`). */
enum class LabelScope { ALL, ACTIVITY, TRACKER }

/** The form two names are compared in: Unicode lower case, so "Health" and "HEALTH" are one name, and "Ärger" and "ärger" too. */
fun nameKey(name: String): String = name.trim().lowercase()

/**
 * Tendril's palette (`LabelColors`), as ARGB. Eight is load-bearing: the colour is the name's hash
 * modulo the count, so a ninth would recolour every label.
 */
val LABEL_PALETTE: List<Long> = listOf(0xFFA9708D, 0xFF98693F, 0xFF6E8C70, 0xFF4A5568, 0xFFB68E51, 0xFF879FBA, 0xFF9669BC, 0xFFC6A790)

/** A new label's colour: Tendril's `LabelColors.forName`, with Java's string hash written out so every platform agrees. */
fun colorForName(name: String): Long {
    var hash = 0
    for (c in name) hash = 31 * hash + c.code
    return LABEL_PALETTE[hash.mod(LABEL_PALETTE.size)]
}
