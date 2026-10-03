package com.factotum.core.formula

// Ported from Tendril (Tendril android/app/src/test/.../domain/formula), with property keys for names.

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class FormulaLexerTest {

    @Test
    fun `numbers, including decimals, tokenize as Number`() {
        val tokens = tokenizeFormula("3 3.5 0.25 42")
        val values = tokens.filterIsInstance<FormulaToken.Number>().map { it.value }
        assertEquals(listOf(3.0, 3.5, 0.25, 42.0), values)
    }

    @Test
    fun `a bare trailing dot is not consumed into the number`() {
        // "3." has no digit after the dot, so this must tokenize as Number(3) then Symbol(".") —
        // and "." is not a known symbol, so it should actually fail to tokenize at all.
        assertThrows(FormulaSyntaxError::class.java) { tokenizeFormula("3.") }
    }

    @Test
    fun `strings support escaped quotes and backslashes`() {
        val tokens = tokenizeFormula("\"a \\\"quoted\\\" word\" \"back\\\\slash\"")
        val strings = tokens.filterIsInstance<FormulaToken.Str>().map { it.value }
        assertEquals(listOf("a \"quoted\" word", "back\\slash"), strings)
    }

    @Test
    fun `an unterminated string throws, pointing at its opening quote`() {
        val error = assertThrows(FormulaSyntaxError::class.java) { tokenizeFormula("\"never closed") }
        assertEquals(0, error.position)
    }

    @Test
    fun `identifiers, including underscores and digits after the first letter, tokenize as Ident`() {
        val tokens = tokenizeFormula("prop and_or x2")
        val names = tokens.filterIsInstance<FormulaToken.Ident>().map { it.name }
        assertEquals(listOf("prop", "and_or", "x2"), names)
    }

    @Test
    fun `two-character operators are not split into two one-character tokens`() {
        // The symbol list checks "==" before "=" would ever be considered — there is no bare
        // "=" in this grammar at all, so this also proves single "=" is rejected outright.
        val tokens = tokenizeFormula("a == b != c <= d >= e")
        val symbols = tokens.filterIsInstance<FormulaToken.Symbol>().map { it.text }
        assertEquals(listOf("==", "!=", "<=", ">="), symbols)
    }

    @Test
    fun `a single equals sign is not a valid token`() {
        assertThrows(FormulaSyntaxError::class.java) { tokenizeFormula("a = b") }
    }

    @Test
    fun `every token remembers its source position`() {
        val tokens = tokenizeFormula("1 + 22")
        assertEquals(0, (tokens[0] as FormulaToken.Number).position)
        assertEquals(2, (tokens[1] as FormulaToken.Symbol).position)
        assertEquals(4, (tokens[2] as FormulaToken.Number).position)
    }

    @Test
    fun `the token stream always ends with End`() {
        assertEquals(true, tokenizeFormula("prop(\"X\")").last() is FormulaToken.End)
        assertEquals(true, tokenizeFormula("").last() is FormulaToken.End)
    }

    @Test
    fun `an unrecognised character throws at its own position`() {
        val error = assertThrows(FormulaSyntaxError::class.java) { tokenizeFormula("1 @ 2") }
        assertEquals(2, error.position)
    }
}
