package com.factotum.core.formula

// Ported from Tendril (Tendril android/app/src/test/.../domain/formula), with property keys for names.

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class FormulaParserTest {

    @Test
    fun `a bare number literal parses`() {
        assertEquals(FormulaAst.NumberLit(3.0, 0), parseFormula("3"))
    }

    @Test
    fun `prop with a quoted name parses as PropertyRef, not a generic call`() {
        val ast = parseFormula("prop(\"Status\")")
        assertTrue(ast is FormulaAst.PropertyRef)
        assertEquals("Status", (ast as FormulaAst.PropertyRef).key)
    }

    @Test
    fun `prop without a quoted-string argument is a syntax error`() {
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("prop(3)") }
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("prop(x)") }
    }

    @Test
    fun `multiplication binds tighter than addition`() {
        // 2 + 3 * 4 must parse as 2 + (3 * 4), not (2 + 3) * 4.
        val ast = parseFormula("2 + 3 * 4") as FormulaAst.BinaryOp
        assertEquals("+", ast.op)
        assertEquals(FormulaAst.NumberLit(2.0, 0), ast.left)
        val right = ast.right as FormulaAst.BinaryOp
        assertEquals("*", right.op)
    }

    @Test
    fun `parentheses override the default grouping`() {
        val ast = parseFormula("(2 + 3) * 4") as FormulaAst.BinaryOp
        assertEquals("*", ast.op)
        val left = ast.left as FormulaAst.BinaryOp
        assertEquals("+", left.op)
    }

    @Test
    fun `comparison binds tighter than equality binds tighter than and-or`() {
        // "a > 1 and b == 2" must be (a > 1) and (b == 2), not some other grouping.
        val ast = parseFormula("prop(\"a\") > 1 and prop(\"b\") == 2") as FormulaAst.BinaryOp
        assertEquals("and", ast.op)
        assertEquals(">", (ast.left as FormulaAst.BinaryOp).op)
        assertEquals("==", (ast.right as FormulaAst.BinaryOp).op)
    }

    @Test
    fun `or binds looser than and, matching every C-family language`() {
        // "a and b or c" must be (a and b) or c.
        val ast = parseFormula("true and false or true") as FormulaAst.BinaryOp
        assertEquals("or", ast.op)
        assertEquals("and", (ast.left as FormulaAst.BinaryOp).op)
    }

    @Test
    fun `unary minus and not bind tighter than any binary operator`() {
        val ast = parseFormula("-2 + 3") as FormulaAst.BinaryOp
        assertEquals("+", ast.op)
        assertTrue(ast.left is FormulaAst.UnaryOp)
    }

    @Test
    fun `a function call parses its argument list in order`() {
        val ast = parseFormula("max(1, 2, 3)") as FormulaAst.Call
        assertEquals("max", ast.functionName)
        assertEquals(listOf(1.0, 2.0, 3.0), ast.args.map { (it as FormulaAst.NumberLit).value })
    }

    @Test
    fun `a zero-argument call parses to an empty argument list, not a syntax error`() {
        val ast = parseFormula("round()") as FormulaAst.Call
        assertTrue(ast.args.isEmpty())
    }

    @Test
    fun `nested calls parse correctly`() {
        val ast = parseFormula("abs(prop(\"X\") - prop(\"Y\"))") as FormulaAst.Call
        assertEquals("abs", ast.functionName)
        assertTrue(ast.args.single() is FormulaAst.BinaryOp)
    }

    @Test
    fun `an identifier that is not a known keyword and is not followed by a call is a syntax error`() {
        // Bare identifiers are not values in this grammar — only prop("X") reaches a property,
        // so "somefield" alone must fail loudly rather than silently mean prop("somefield").
        val error = assertThrows(FormulaSyntaxError::class.java) { parseFormula("somefield + 1") }
        assertTrue(error.message!!.contains("prop"))
    }

    @Test
    fun `unbalanced parentheses are a syntax error`() {
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("(1 + 2") }
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("1 + 2)") }
    }

    @Test
    fun `trailing garbage after a complete expression is a syntax error`() {
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("1 + 1 1") }
    }

    @Test
    fun `an empty formula is a syntax error, not an empty AST`() {
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("") }
    }

    @Test
    fun `true and false are boolean literals, not property references`() {
        assertEquals(FormulaAst.BoolLit(true, 0), parseFormula("true"))
        assertEquals(FormulaAst.BoolLit(false, 0), parseFormula("false"))
    }

    @Test
    fun `and, or and not cannot be used as values`() {
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("and") }
        assertThrows(FormulaSyntaxError::class.java) { parseFormula("1 + or") }
    }

    @Test
    fun `every AST node carries the source position it was parsed at`() {
        val ast = parseFormula("  prop(\"X\")") as FormulaAst.PropertyRef
        assertEquals(2, ast.position)
    }
}
