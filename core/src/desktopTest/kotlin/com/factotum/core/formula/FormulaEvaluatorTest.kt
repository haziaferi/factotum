package com.factotum.core.formula

// Ported from Tendril (Tendril android/app/src/test/.../domain/formula), with property keys for names.

import org.junit.Assert.assertEquals
import org.junit.Test
import kotlinx.datetime.LocalDate

/** Evaluates a formula against a fixed set of named values — the shape a real
 * resolver built from a row's stored cells would take, without any of the
 * database machinery around it. */
private fun eval(source: String, values: Map<String, FormulaValue> = emptyMap()): FormulaValue =
    evaluateFormula(parseFormula(source), { values[it] ?: FormulaValue.Empty })

class FormulaEvaluatorTest {

    @Test
    fun `arithmetic evaluates in the usual grouping`() {
        assertEquals(FormulaValue.Number(14.0), eval("2 + 3 * 4"))
        assertEquals(FormulaValue.Number(20.0), eval("(2 + 3) * 4"))
    }

    @Test
    fun `division by zero is Empty, not an exception or infinity`() {
        assertEquals(FormulaValue.Empty, eval("1 / 0"))
    }

    @Test
    fun `a property reference resolves through the supplied resolver`() {
        assertEquals(
            FormulaValue.Number(8.0),
            eval("prop(\"Points\") + prop(\"Bonus\")", mapOf("Points" to FormulaValue.Number(5.0), "Bonus" to FormulaValue.Number(3.0))),
        )
    }

    @Test
    fun `an unresolved property reference evaluates to Empty rather than throwing`() {
        assertEquals(FormulaValue.Empty, eval("prop(\"DoesNotExist\") + 1"))
    }

    @Test
    fun `plus concatenates when either side is text`() {
        assertEquals(FormulaValue.Text("Total: 3"), eval("\"Total: \" + prop(\"Score\")", mapOf("Score" to FormulaValue.Number(3.0))))
        assertEquals(FormulaValue.Text("ab"), eval("\"a\" + \"b\""))
    }

    @Test
    fun `concatenation drops a whole-number's trailing decimal, matching the rollup display form`() {
        assertEquals(FormulaValue.Text("Score: 3"), eval("\"Score: \" + prop(\"Score\")", mapOf("Score" to FormulaValue.Number(3.0))))
        assertEquals(FormulaValue.Text("Score: 3.5"), eval("\"Score: \" + prop(\"Score\")", mapOf("Score" to FormulaValue.Number(3.5))))
    }

    @Test
    fun `an Empty operand in string concatenation coerces to empty text, not a blanked whole result`() {
        assertEquals(FormulaValue.Text("Hello, "), eval("\"Hello, \" + prop(\"Name\")"))
    }

    @Test
    fun `an Empty operand in arithmetic propagates as Empty`() {
        assertEquals(FormulaValue.Empty, eval("prop(\"Missing\") + 1"))
        assertEquals(FormulaValue.Empty, eval("prop(\"Missing\") * 2"))
    }

    @Test
    fun `a type mismatch on subtraction, multiplication or division is Empty, not a crash`() {
        assertEquals(FormulaValue.Empty, eval("\"a\" - 1"))
        assertEquals(FormulaValue.Empty, eval("\"a\" * 2"))
        assertEquals(FormulaValue.Empty, eval("true / 2"))
    }

    @Test
    fun `comparisons work over numbers and over dates, and nowhere else`() {
        assertEquals(FormulaValue.Bool(true), eval("3 > 2"))
        assertEquals(
            FormulaValue.Bool(true),
            eval(
                "prop(\"Deadline\") > prop(\"Today\")",
                mapOf("Deadline" to FormulaValue.DateValue(LocalDate(2030, 1, 1)), "Today" to FormulaValue.DateValue(LocalDate(2026, 1, 1))),
            ),
        )
        assertEquals(FormulaValue.Empty, eval("\"a\" > \"b\""))
    }

    @Test
    fun `equality is well-defined across mismatched types, unlike arithmetic`() {
        assertEquals(FormulaValue.Bool(false), eval("1 == \"1\""))
        assertEquals(FormulaValue.Bool(true), eval("1 != \"1\""))
        assertEquals(FormulaValue.Bool(true), eval("3 == 3"))
    }

    @Test
    fun `two Empty values are equal to each other`() {
        assertEquals(FormulaValue.Bool(true), eval("prop(\"A\") == prop(\"B\")"))
    }

    @Test
    fun `and and or short-circuit — the right side is not evaluated once the left decides it`() {
        // A right side that would itself be a type error must never be reached once the left
        // side already settles the result — proven by using a right side that would otherwise
        // produce Empty (breaking the expected Bool result) if it were evaluated at all.
        assertEquals(FormulaValue.Bool(false), eval("false and (1 / 0 > 0)"))
        assertEquals(FormulaValue.Bool(true), eval("true or (1 / 0 > 0)"))
    }

    @Test
    fun `and and or evaluate the right side when the left does not already decide it`() {
        assertEquals(FormulaValue.Bool(true), eval("true and true"))
        assertEquals(FormulaValue.Bool(false), eval("true and false"))
        assertEquals(FormulaValue.Bool(false), eval("false or false"))
    }

    @Test
    fun `not negates a boolean and is Empty for anything else`() {
        assertEquals(FormulaValue.Bool(false), eval("not true"))
        assertEquals(FormulaValue.Empty, eval("not 3"))
    }

    @Test
    fun `unary minus negates a number and is Empty for anything else`() {
        assertEquals(FormulaValue.Number(-3.0), eval("-3"))
        assertEquals(FormulaValue.Empty, eval("-\"a\""))
    }

    @Test
    fun `if returns the matching branch without evaluating the other`() {
        assertEquals(FormulaValue.Number(1.0), eval("if(true, 1, 1 / 0)"))
        assertEquals(FormulaValue.Number(2.0), eval("if(false, 1 / 0, 2)"))
    }

    @Test
    fun `if with a non-boolean condition is Empty`() {
        assertEquals(FormulaValue.Empty, eval("if(1, 2, 3)"))
    }

    @Test
    fun `abs, round, min and max compute correctly and reject non-numbers as Empty`() {
        assertEquals(FormulaValue.Number(3.0), eval("abs(-3)"))
        assertEquals(FormulaValue.Number(3.0), eval("round(2.6)"))
        assertEquals(FormulaValue.Number(1.0), eval("min(3, 1, 2)"))
        assertEquals(FormulaValue.Number(3.0), eval("max(3, 1, 2)"))
        assertEquals(FormulaValue.Empty, eval("abs(\"x\")"))
        assertEquals(FormulaValue.Empty, eval("min(1, \"x\")"))
    }

    @Test
    fun `an unknown function name evaluates to Empty rather than throwing`() {
        // The type checker is responsible for catching this at save time; the evaluator itself
        // must still never crash a row's render over it.
        assertEquals(FormulaValue.Empty, eval("nosuchfunction(1)"))
    }
}
