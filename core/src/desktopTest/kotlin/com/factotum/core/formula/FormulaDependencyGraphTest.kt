package com.factotum.core.formula

// Ported from Tendril (Tendril android/app/src/test/.../domain/formula), with property keys for names.

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

private fun node(name: String, formula: String) = FormulaNode(name, parseFormula(formula))

class FormulaDependencyGraphTest {

    @Test
    fun `independent formulas sort in the order given`() {
        val nodes = listOf(node("A", "1"), node("B", "2"))
        assertEquals(listOf("A", "B"), topologicallySortFormulas(nodes).map { it.key })
    }

    @Test
    fun `a formula referencing another COMPUTED property is ordered after it`() {
        val nodes = listOf(
            node("Total", "prop(\"Subtotal\") + 1"),
            node("Subtotal", "1 + 1"),
        )
        val order = topologicallySortFormulas(nodes).map { it.key }
        assertTrue("Subtotal must precede Total: $order", order.indexOf("Subtotal") < order.indexOf("Total"))
    }

    @Test
    fun `a reference to a non-COMPUTED property is not an edge — it does not need to appear in nodes at all`() {
        // "Points" isn't in `nodes`; if this were treated as a graph edge it would throw looking
        // it up. It must sort cleanly, since a plain stored property is a leaf resolved by
        // resolver, not something this graph tracks.
        val nodes = listOf(node("Total", "prop(\"Points\") + 1"))
        assertEquals(listOf("Total"), topologicallySortFormulas(nodes).map { it.key })
    }

    @Test
    fun `a direct two-node cycle is rejected and the path names both properties`() {
        val nodes = listOf(
            node("A", "prop(\"B\")"),
            node("B", "prop(\"A\")"),
        )
        val error = assertThrows(FormulaCycleException::class.java) { topologicallySortFormulas(nodes) }
        assertEquals(listOf("A", "B", "A"), error.cyclePath)
    }

    @Test
    fun `a three-node cycle is rejected and the path names all three, closed on itself`() {
        val nodes = listOf(
            node("A", "prop(\"B\")"),
            node("B", "prop(\"C\")"),
            node("C", "prop(\"A\")"),
        )
        val error = assertThrows(FormulaCycleException::class.java) { topologicallySortFormulas(nodes) }
        assertEquals(listOf("A", "B", "C", "A"), error.cyclePath)
    }

    @Test
    fun `a formula referencing its own name is a self-cycle`() {
        val nodes = listOf(node("Total", "prop(\"Total\") + 1"))
        val error = assertThrows(FormulaCycleException::class.java) { topologicallySortFormulas(nodes) }
        assertEquals(listOf("Total", "Total"), error.cyclePath)
    }

    @Test
    fun `a diamond dependency — two paths converging on the same node — is not mistaken for a cycle`() {
        // Total depends on both Left and Right, which both depend on Base. Base is visited
        // (and marked fully visited) via the first path, and must not be re-flagged as "on the
        // stack" when the second path reaches it.
        val nodes = listOf(
            node("Total", "prop(\"Left\") + prop(\"Right\")"),
            node("Left", "prop(\"Base\") * 2"),
            node("Right", "prop(\"Base\") * 3"),
            node("Base", "1"),
        )
        val order = topologicallySortFormulas(nodes).map { it.key }
        assertTrue(order.indexOf("Base") < order.indexOf("Left"))
        assertTrue(order.indexOf("Base") < order.indexOf("Right"))
        assertTrue(order.indexOf("Left") < order.indexOf("Total"))
        assertTrue(order.indexOf("Right") < order.indexOf("Total"))
    }

    @Test
    fun `a cycle reachable only through one of several independent formulas is still found`() {
        val nodes = listOf(
            node("Standalone", "1 + 1"),
            node("A", "prop(\"B\")"),
            node("B", "prop(\"A\")"),
        )
        assertThrows(FormulaCycleException::class.java) { topologicallySortFormulas(nodes) }
    }
}
