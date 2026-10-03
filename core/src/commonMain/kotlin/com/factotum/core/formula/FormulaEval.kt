package com.factotum.core.formula

import kotlinx.datetime.LocalDate
import kotlin.math.abs
import kotlin.math.round

/** A formula's result, or a value on the way to one; [Empty] is a blank cell or a value an operator could not use. */
sealed class FormulaValue {
    data class Number(val value: Double) : FormulaValue()
    data class Text(val value: String) : FormulaValue()
    data class Bool(val value: Boolean) : FormulaValue()
    data class DateValue(val value: LocalDate) : FormulaValue()
    data object Empty : FormulaValue()
}

/** A formula's declared type, checked before any row exists; [ANY] is one not knowable, which checks against everything. */
enum class FormulaType { NUMBER, TEXT, BOOLEAN, DATE, ANY }

/**
 * Evaluates [ast] on one row, [resolve] giving each `prop(…)` key's value. It never throws: an
 * operator on a value it cannot use, an unknown key, a division by zero, each reads as
 * [FormulaValue.Empty], so one bad cell blanks itself and nothing else. `and` and `or` evaluate
 * their right side only when the left does not decide.
 */
fun evaluateFormula(ast: FormulaAst, resolve: (String) -> FormulaValue): FormulaValue = when (ast) {
    is FormulaAst.NumberLit -> FormulaValue.Number(ast.value)
    is FormulaAst.StringLit -> FormulaValue.Text(ast.value)
    is FormulaAst.BoolLit -> FormulaValue.Bool(ast.value)
    is FormulaAst.PropertyRef -> resolve(ast.key)
    is FormulaAst.UnaryOp -> when (val operand = evaluateFormula(ast.operand, resolve)) {
        is FormulaValue.Number -> if (ast.op == "-") FormulaValue.Number(-operand.value) else FormulaValue.Empty
        is FormulaValue.Bool -> if (ast.op == "not") FormulaValue.Bool(!operand.value) else FormulaValue.Empty
        else -> FormulaValue.Empty
    }
    is FormulaAst.BinaryOp -> evaluateBinary(ast, resolve)
    is FormulaAst.Call -> evaluateCall(ast, resolve)
}

/** A value as cell text: a whole number without its fraction (`3`, not `3.0`), [FormulaValue.Empty] as null. */
fun FormulaValue.toCellText(): String? = when (this) {
    is FormulaValue.Number -> formatNumber(value)
    is FormulaValue.Text -> value
    is FormulaValue.Bool -> value.toString()
    is FormulaValue.DateValue -> value.toString()
    FormulaValue.Empty -> null
}

/** A number as text: a whole one without its fraction while a Long holds it exactly, any other as Kotlin writes it. */
fun formatNumber(value: Double): String = if (value == kotlin.math.floor(value) && kotlin.math.abs(value) < 1e15) value.toLong().toString() else value.toString()

private fun evaluateBinary(ast: FormulaAst.BinaryOp, resolve: (String) -> FormulaValue): FormulaValue {
    if (ast.op == "and" || ast.op == "or") {
        val left = evaluateFormula(ast.left, resolve) as? FormulaValue.Bool ?: return FormulaValue.Empty
        if (ast.op == "and" && !left.value) return FormulaValue.Bool(false)
        if (ast.op == "or" && left.value) return FormulaValue.Bool(true)
        return evaluateFormula(ast.right, resolve) as? FormulaValue.Bool ?: FormulaValue.Empty
    }
    val left = evaluateFormula(ast.left, resolve)
    val right = evaluateFormula(ast.right, resolve)
    return when (ast.op) {
        "==" -> FormulaValue.Bool(left.sameAs(right))
        "!=" -> FormulaValue.Bool(!left.sameAs(right))
        "+" -> when {
            left is FormulaValue.Number && right is FormulaValue.Number -> FormulaValue.Number(left.value + right.value)
            left is FormulaValue.Text || right is FormulaValue.Text -> FormulaValue.Text(left.toCellText().orEmpty() + right.toCellText().orEmpty())
            else -> FormulaValue.Empty
        }
        "-", "*", "/" -> {
            if (left !is FormulaValue.Number || right !is FormulaValue.Number) return FormulaValue.Empty
            when (ast.op) {
                "-" -> FormulaValue.Number(left.value - right.value)
                "*" -> FormulaValue.Number(left.value * right.value)
                else -> if (right.value == 0.0) FormulaValue.Empty else FormulaValue.Number(left.value / right.value)
            }
        }
        else -> {
            val order = when {
                left is FormulaValue.Number && right is FormulaValue.Number -> left.value.compareTo(right.value)
                left is FormulaValue.DateValue && right is FormulaValue.DateValue -> left.value.compareTo(right.value)
                else -> return FormulaValue.Empty
            }
            when (ast.op) {
                "<" -> FormulaValue.Bool(order < 0)
                "<=" -> FormulaValue.Bool(order <= 0)
                ">" -> FormulaValue.Bool(order > 0)
                ">=" -> FormulaValue.Bool(order >= 0)
                else -> FormulaValue.Empty
            }
        }
    }
}

/** Equal values of one type, numbers compared as numbers (`0 == -0`); values of two types are unequal, and two blanks equal. */
private fun FormulaValue.sameAs(other: FormulaValue): Boolean = when {
    this is FormulaValue.Number && other is FormulaValue.Number -> value == other.value
    else -> this == other
}

private fun evaluateCall(ast: FormulaAst.Call, resolve: (String) -> FormulaValue): FormulaValue {
    val args = ast.args.map { evaluateFormula(it, resolve) }
    val numbers = args.map { it as? FormulaValue.Number }
    return when (ast.functionName) {
        "if" -> {
            val cond = args.getOrNull(0) as? FormulaValue.Bool
            if (cond == null || args.size != 3) FormulaValue.Empty else if (cond.value) args[1] else args[2]
        }
        "abs" -> numbers.singleOrNull()?.let { FormulaValue.Number(abs(it.value)) } ?: FormulaValue.Empty
        // Half to even, as Tendril (round(2.5) is 2); how a half reads waits for the screens.
        "round" -> numbers.singleOrNull()?.let { FormulaValue.Number(round(it.value)) } ?: FormulaValue.Empty
        "min" -> if (numbers.any { it == null }) FormulaValue.Empty else numbers.filterNotNull().minByOrNull { it.value } ?: FormulaValue.Empty
        "max" -> if (numbers.any { it == null }) FormulaValue.Empty else numbers.filterNotNull().maxByOrNull { it.value } ?: FormulaValue.Empty
        else -> FormulaValue.Empty
    }
}

/** What a rollup computes over the related rows' values of one property (Tendril's). */
enum class RollupAggregation { COUNT, SUM, MIN, MAX, EARLIEST, LATEST, SHOW_ORIGINAL }

/**
 * A rollup's cell text over [rows] related rows, [values] being the target property's value as
 * text on each that has one: COUNT counts the rows, SUM, MIN and MAX read numbers, EARLIEST and LATEST
 * dates, SHOW_ORIGINAL lists the values. A value that does not read as what is asked is skipped;
 * nothing to aggregate is blank.
 */
fun rollup(aggregation: RollupAggregation, rows: Int, values: List<String>): String? {
    if (aggregation == RollupAggregation.COUNT) return rows.toString()
    val numbers = values.mapNotNull { it.toDoubleOrNull() }
    val dates = values.mapNotNull { runCatching { LocalDate.parse(it) }.getOrNull() }
    return when (aggregation) {
        // Tendril's: values none of which is a number sum to 0.
        RollupAggregation.SUM -> values.takeIf { it.isNotEmpty() }?.let { formatNumber(numbers.sum()) }
        RollupAggregation.MIN -> numbers.minOrNull()?.let(::formatNumber)
        RollupAggregation.MAX -> numbers.maxOrNull()?.let(::formatNumber)
        RollupAggregation.EARLIEST -> dates.minOrNull()?.toString()
        RollupAggregation.LATEST -> dates.maxOrNull()?.toString()
        RollupAggregation.SHOW_ORIGINAL -> values.takeIf { it.isNotEmpty() }?.joinToString(", ")
        RollupAggregation.COUNT -> rows.toString()
    }
}
