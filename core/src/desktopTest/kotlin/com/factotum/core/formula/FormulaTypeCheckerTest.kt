package com.factotum.core.formula

// Ported from Tendril (Tendril android/app/src/test/.../domain/formula), with property keys for names.

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

private fun node(name: String, formula: String) = FormulaNode(name, parseFormula(formula))

/** A fixed little database's worth of properties for the checker to resolve `prop()` references
 * against: "Points"/"Score" are numbers, "Name" is text, "Done" is a checkbox, "Deadline" is a
 * date, "Project" is a relation. Anything else is unknown. */
private val TEST_LOOKUP: (String) -> FormulaPropertyKind? = { name ->
    when (name) {
        "Points", "Score" -> FormulaPropertyKind.Typed(FormulaType.NUMBER)
        "Name" -> FormulaPropertyKind.Typed(FormulaType.TEXT)
        "Done" -> FormulaPropertyKind.Typed(FormulaType.BOOLEAN)
        "Deadline" -> FormulaPropertyKind.Typed(FormulaType.DATE)
        "Project" -> FormulaPropertyKind.Relation
        else -> null
    }
}

private fun check(formula: String): FormulaCheckResult =
    checkAllFormulas(listOf(node("Under test", formula)), TEST_LOOKUP).getValue("Under test")

class FormulaTypeCheckerTest {

    @Test
    fun `a well-typed formula over known properties checks clean and infers the right type`() {
        val result = check("prop(\"Points\") + prop(\"Score\")")
        assertTrue(result.errors.isEmpty())
        assertEquals(FormulaType.NUMBER, result.type)
    }

    @Test
    fun `a reference to a property that does not exist is an error naming it`() {
        val result = check("prop(\"NoSuchColumn\") + 1")
        assertEquals(1, result.errors.size)
        assertTrue(result.errors.single().message.contains("NoSuchColumn"))
    }

    @Test
    fun `a bare relation reference is an error, not silently treated as some value`() {
        val result = check("prop(\"Project\")")
        assertEquals(1, result.errors.size)
        assertTrue(result.errors.single().message.contains("relation"))
    }

    @Test
    fun `mismatched arithmetic operand types are caught`() {
        val result = check("prop(\"Name\") - prop(\"Points\")")
        assertTrue(result.errors.isNotEmpty())
    }

    @Test
    fun `plus allows number-number and text-anything, matching the evaluator's own concat rule`() {
        assertTrue(check("prop(\"Points\") + prop(\"Score\")").errors.isEmpty())
        assertTrue(check("\"Score: \" + prop(\"Points\")").errors.isEmpty())
        assertEquals(FormulaType.TEXT, check("\"Score: \" + prop(\"Points\")").type)
    }

    @Test
    fun `and-or require two booleans`() {
        assertTrue(check("prop(\"Done\") and true").errors.isEmpty())
        assertTrue(check("prop(\"Points\") and true").errors.isNotEmpty())
    }

    @Test
    fun `comparisons require two numbers or two dates, and reject a mix`() {
        assertTrue(check("prop(\"Points\") > prop(\"Score\")").errors.isEmpty())
        assertTrue(check("prop(\"Deadline\") > prop(\"Deadline\")").errors.isEmpty())
        assertTrue(check("prop(\"Points\") > prop(\"Deadline\")").errors.isNotEmpty())
    }

    @Test
    fun `equality never errors, even across mismatched types`() {
        assertTrue(check("prop(\"Points\") == prop(\"Name\")").errors.isEmpty())
        assertEquals(FormulaType.BOOLEAN, check("prop(\"Points\") == prop(\"Name\")").type)
    }

    @Test
    fun `if requires exactly three arguments and a boolean condition`() {
        assertTrue(check("if(prop(\"Done\"), 1, 2)").errors.isEmpty())
        assertTrue(check("if(prop(\"Points\"), 1, 2)").errors.isNotEmpty()) // condition not boolean
        assertTrue(check("if(prop(\"Done\"), 1)").errors.isNotEmpty()) // wrong arity
    }

    @Test
    fun `if's two branches must agree in type`() {
        assertTrue(check("if(prop(\"Done\"), 1, 2)").errors.isEmpty())
        assertTrue(check("if(prop(\"Done\"), 1, \"two\")").errors.isNotEmpty())
    }

    @Test
    fun `abs, round, min and max require numeric arguments and correct arity`() {
        assertTrue(check("abs(prop(\"Points\"))").errors.isEmpty())
        assertTrue(check("abs(prop(\"Name\"))").errors.isNotEmpty())
        assertTrue(check("abs()").errors.isNotEmpty())
        assertTrue(check("min(prop(\"Points\"), prop(\"Score\"))").errors.isEmpty())
        assertTrue(check("min()").errors.isNotEmpty())
    }

    @Test
    fun `an unknown function name is an error`() {
        assertTrue(check("notarealfunction(1)").errors.isNotEmpty())
    }

    @Test
    fun `one bad sub-expression does not cascade into a second error at the operator above it`() {
        // prop("NoSuchColumn") is already an error; the "+ 1" around it should not ALSO be
        // flagged for "operand type unknown" — that would turn one mistake into a wall of noise.
        val result = check("prop(\"NoSuchColumn\") + 1")
        assertEquals(1, result.errors.size)
    }

    @Test
    fun `a formula referencing a checked COMPUTED property sees that property's inferred type`() {
        val nodes = listOf(
            node("Doubled", "prop(\"Base\") * 2"),
            node("Base", "prop(\"Points\")"),
        )
        val results = checkAllFormulas(nodes, TEST_LOOKUP)
        assertTrue("Base" + results.getValue("Base").errors, results.getValue("Base").errors.isEmpty())
        assertTrue("Doubled" + results.getValue("Doubled").errors, results.getValue("Doubled").errors.isEmpty())
        assertEquals(FormulaType.NUMBER, results.getValue("Doubled").type)
    }

    @Test
    fun `a formula referencing a COMPUTED property whose OWN formula is broken degrades to ANY rather than a second error`() {
        val nodes = listOf(
            node("DependsOnBroken", "prop(\"Broken\") + 1"),
            node("Broken", "prop(\"NoSuchColumn\")"),
        )
        val results = checkAllFormulas(nodes, TEST_LOOKUP)
        assertTrue(results.getValue("Broken").errors.isNotEmpty())
        // "+ 1" against an ANY-typed broken reference must not itself add a second, redundant
        // error — Broken's own error is the one thing worth showing.
        assertTrue(results.getValue("DependsOnBroken").errors.isEmpty())
        assertEquals(FormulaType.ANY, results.getValue("DependsOnBroken").type)
    }

    @Test
    fun `a cycle across the whole database is reported for every property in it`() {
        val nodes = listOf(node("A", "prop(\"B\")"), node("B", "prop(\"A\")"))
        val results = checkAllFormulas(nodes, TEST_LOOKUP)
        assertTrue(results.getValue("A").errors.isNotEmpty())
        assertTrue(results.getValue("B").errors.isNotEmpty())
    }

    @Test
    fun `every reported error carries the source position of the offending token`() {
        val result = check("1 + prop(\"NoSuchColumn\")")
        assertEquals(4, result.errors.single().position)
    }
}
