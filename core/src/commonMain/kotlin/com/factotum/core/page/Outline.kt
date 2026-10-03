package com.factotum.core.page

/** A block as the outline reads it: its place among its siblings, by [sortKey] and then [id]. */
data class Placed(val id: String, val parentId: String?, val sortKey: String)

/** One block in drawing order, with how deep it is indented. */
data class OutlineEntry(val id: String, val depth: Int)

/**
 * A page's blocks in the order they are drawn: each block, then its subtree, depth first, siblings
 * by sort key and then id (so two devices' blocks placed at one key keep one order). Every block
 * comes out (Tendril's `outlineOf`): a child whose parent is not on the page is a root, and a
 * parent cycle, which only a merge can make, is broken where the walk would repeat.
 */
fun outlineOf(blocks: List<Placed>): List<OutlineEntry> {
    val byId = blocks.associateBy { it.id }
    val sorted = blocks.sortedWith(compareBy({ it.sortKey }, { it.id }))

    // A root has no parent here, or is on a cycle: following its parents comes back to it. A block
    // hanging off a cycle is not on it, and is drawn beneath it. (Tendril's check made it a root too.)
    fun isRoot(block: Placed): Boolean {
        var current = block.parentId?.let(byId::get) ?: return true
        val seen = mutableSetOf<String>()
        while (true) {
            if (current.id == block.id) return true
            if (!seen.add(current.id)) return false
            current = current.parentId?.let(byId::get) ?: return false
        }
    }

    val children = LinkedHashMap<String, MutableList<Placed>>()
    val roots = mutableListOf<Placed>()
    for (block in sorted) {
        if (isRoot(block)) roots += block else children.getOrPut(requireNotNull(block.parentId)) { mutableListOf() } += block
    }
    val out = mutableListOf<OutlineEntry>()
    val emitted = mutableSetOf<String>()
    fun walk(block: Placed, depth: Int) {
        if (!emitted.add(block.id)) return
        out += OutlineEntry(block.id, depth)
        children[block.id]?.forEach { walk(it, depth + 1) }
    }
    roots.forEach { walk(it, 0) }
    return out
}

private const val DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"

/**
 * A sort key between two neighbours, [before] and [after] (either null at an end), as text that
 * sorts character by character (ADR 12's fractional order, after Greenspan's fractional indexing).
 * There is always room: a key grows a digit where its neighbours are adjacent, so placing a block
 * never re-keys its siblings, and so never writes over a move or a deletion made on another device.
 * No key ends in `0`, which is what keeps a key between any two.
 */
fun keyBetween(before: String?, after: String?): String {
    require(after == null || (before ?: "") < after) { "keys out of order: $before, $after" }
    return midpoint(before ?: "", after)
}

private fun midpoint(a: String, b: String?): String {
    if (b != null) {
        // A shared beginning is kept, and the rest is placed between.
        var n = 0
        while ((a.getOrNull(n) ?: '0') == b[n]) n++
        if (n > 0) return b.substring(0, n) + midpoint(a.substring(minOf(n, a.length)), b.substring(n))
    }
    val low = if (a.isEmpty()) 0 else DIGITS.indexOf(a[0])
    val high = if (b == null) DIGITS.length else DIGITS.indexOf(b[0])
    if (high - low > 1) return DIGITS[(low + high + 1) / 2].toString()
    // Adjacent first digits: a longer b leaves its first digit free; otherwise go a digit deeper after a.
    if (b != null && b.length > 1) return b.substring(0, 1)
    return DIGITS[low] + midpoint(if (a.isEmpty()) "" else a.substring(1), null)
}
