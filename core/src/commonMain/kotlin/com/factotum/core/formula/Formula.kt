package com.factotum.core.formula

/**
 * Tendril's formula language (ADR 12, §7 step 3): its tokens, its syntax tree and its parser.
 * A property is named `prop("…")`; what is between the quotes is a key, a property's name as a
 * person types it and its id as Factotum stores it ([rewriteKeys]), so a rename never breaks a
 * formula (owner, 2026-10-03). Precedence, loosest first: `or`, `and`, `==` `!=`, `<` `<=` `>`
 * `>=`, `+` `-`, `*` `/`, unary `-` `not`, then literals, `prop(…)`, calls and parentheses.
 */
sealed class FormulaAst {
    /** Where in the source this node starts, for an error that points at it. */
    abstract val position: Int

    data class NumberLit(val value: Double, override val position: Int) : FormulaAst()
    data class StringLit(val value: String, override val position: Int) : FormulaAst()
    data class BoolLit(val value: Boolean, override val position: Int) : FormulaAst()
    data class PropertyRef(val key: String, override val position: Int) : FormulaAst()
    data class Call(val functionName: String, val args: List<FormulaAst>, override val position: Int) : FormulaAst()
    data class UnaryOp(val op: String, val operand: FormulaAst, override val position: Int) : FormulaAst()
    data class BinaryOp(val op: String, val left: FormulaAst, val right: FormulaAst, override val position: Int) : FormulaAst()
}

/** Every `prop(…)` in an expression, depth first. */
fun FormulaAst.propertyReferences(): List<FormulaAst.PropertyRef> = when (this) {
    is FormulaAst.PropertyRef -> listOf(this)
    is FormulaAst.Call -> args.flatMap { it.propertyReferences() }
    is FormulaAst.UnaryOp -> operand.propertyReferences()
    is FormulaAst.BinaryOp -> left.propertyReferences() + right.propertyReferences()
    is FormulaAst.NumberLit, is FormulaAst.StringLit, is FormulaAst.BoolLit -> emptyList()
}

class FormulaSyntaxError(message: String, val position: Int) : Exception(message)

sealed class FormulaToken {
    abstract val position: Int

    data class Number(val value: Double, override val position: Int) : FormulaToken()

    /** A string literal; [end] is just past its closing quote, so [rewriteKeys] can replace it whole. */
    data class Str(val value: String, override val position: Int, val end: Int) : FormulaToken()
    data class Ident(val name: String, override val position: Int) : FormulaToken()
    data class Symbol(val text: String, override val position: Int) : FormulaToken()
    data class End(override val position: Int) : FormulaToken()
}

private val SYMBOLS = listOf("==", "!=", "<=", ">=", "(", ")", ",", "+", "-", "*", "/", "<", ">")

/** The tokens of [source], left to right; the first character nothing starts with is an error at its offset. */
fun tokenizeFormula(source: String): List<FormulaToken> {
    val tokens = mutableListOf<FormulaToken>()
    var i = 0
    while (i < source.length) {
        val c = source[i]
        when {
            c.isWhitespace() -> i++

            c == '"' -> {
                val start = i
                val sb = StringBuilder()
                i++
                while (i < source.length && source[i] != '"') {
                    if (source[i] == '\\' && i + 1 < source.length) {
                        sb.append(
                            when (val esc = source[i + 1]) {
                                '"' -> '"'; '\\' -> '\\'; 'n' -> '\n'; 't' -> '\t'
                                else -> throw FormulaSyntaxError("unknown escape \\$esc in string", i)
                            },
                        )
                        i += 2
                    } else {
                        sb.append(source[i])
                        i++
                    }
                }
                if (i >= source.length) throw FormulaSyntaxError("unterminated string starting here", start)
                i++
                tokens += FormulaToken.Str(sb.toString(), start, i)
            }

            c.isDigit() -> {
                val start = i
                while (i < source.length && source[i].isDigit()) i++
                if (i < source.length && source[i] == '.' && i + 1 < source.length && source[i + 1].isDigit()) {
                    i++
                    while (i < source.length && source[i].isDigit()) i++
                }
                tokens += FormulaToken.Number(source.substring(start, i).toDouble(), start)
            }

            c.isLetter() || c == '_' -> {
                val start = i
                while (i < source.length && (source[i].isLetterOrDigit() || source[i] == '_')) i++
                tokens += FormulaToken.Ident(source.substring(start, i), start)
            }

            else -> {
                val symbol = SYMBOLS.firstOrNull { source.startsWith(it, i) } ?: throw FormulaSyntaxError("unexpected character '$c'", i)
                tokens += FormulaToken.Symbol(symbol, i)
                i += symbol.length
            }
        }
    }
    tokens += FormulaToken.End(source.length)
    return tokens
}

/** Parses [source]; the first malformed input is an error at its character, with no attempt to go on. */
fun parseFormula(source: String): FormulaAst {
    val parser = Parser(tokenizeFormula(source))
    return parser.parseOr().also { parser.expectEnd() }
}

/**
 * [source] with each `prop("key")` given [rename]'s key instead, the rest kept as written: a
 * formula typed with names is stored with ids, and read back with the names of the day. A key
 * [rename] does not know is kept.
 */
fun rewriteKeys(source: String, rename: (String) -> String?): String = rewriteKeysMapped(source, rename).first

/**
 * As [rewriteKeys], with a map from a position in the result back to one in [source], so an error
 * found in a formula stored with ids points at the character the person typed. An error never
 * points inside a key, so a position maps by the lengths the keys before it changed by.
 */
fun rewriteKeysMapped(source: String, rename: (String) -> String?): Pair<String, (Int) -> Int> {
    val tokens = tokenizeFormula(source)
    val out = StringBuilder()
    var copied = 0
    // (where a replaced key ends in the result, how much longer the result is from there on)
    val shifts = mutableListOf<Pair<Int, Int>>()
    for (i in 0 until tokens.size - 3) {
        val prop = tokens[i] as? FormulaToken.Ident ?: continue
        val open = tokens[i + 1] as? FormulaToken.Symbol
        val key = tokens[i + 2] as? FormulaToken.Str ?: continue
        if (prop.name != "prop" || open?.text != "(") continue
        val renamed = rename(key.value) ?: continue
        out.append(source, copied, key.position).append(quote(renamed))
        copied = key.end
        shifts += out.length to out.length - copied
    }
    out.append(source, copied, source.length)
    return out.toString() to { at -> at - (shifts.lastOrNull { it.first <= at }?.second ?: 0) }
}

private fun quote(text: String) = "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\t", "\\t") + "\""

private class Parser(private val tokens: List<FormulaToken>) {
    private var pos = 0
    private fun peek(): FormulaToken = tokens[pos]
    private fun advance(): FormulaToken = tokens[pos].also { pos++ }

    private fun isSymbol(text: String): Boolean = (peek() as? FormulaToken.Symbol)?.text == text
    private fun isKeyword(name: String): Boolean = (peek() as? FormulaToken.Ident)?.name == name

    private fun expectSymbol(text: String) {
        if (!isSymbol(text)) throw FormulaSyntaxError("expected '$text'", peek().position)
        advance()
    }

    fun expectEnd() {
        if (peek() !is FormulaToken.End) throw FormulaSyntaxError("unexpected trailing input", peek().position)
    }

    fun parseOr(): FormulaAst = binary(::parseAnd) { isKeyword("or") }

    private fun parseAnd(): FormulaAst = binary(::parseEquality) { isKeyword("and") }

    private fun parseEquality(): FormulaAst = binary(::parseComparison) { isSymbol("==") || isSymbol("!=") }

    private fun parseComparison(): FormulaAst = binary(::parseAdditive) { isSymbol("<") || isSymbol("<=") || isSymbol(">") || isSymbol(">=") }

    private fun parseAdditive(): FormulaAst = binary(::parseMultiplicative) { isSymbol("+") || isSymbol("-") }

    private fun parseMultiplicative(): FormulaAst = binary(::parseUnary) { isSymbol("*") || isSymbol("/") }

    /** One left-associative precedence level: operands from [operand], joined while [atOperator]. */
    private fun binary(operand: () -> FormulaAst, atOperator: () -> Boolean): FormulaAst {
        var left = operand()
        while (atOperator()) {
            val op = advance()
            val text = if (op is FormulaToken.Symbol) op.text else (op as FormulaToken.Ident).name
            left = FormulaAst.BinaryOp(text, left, operand(), op.position)
        }
        return left
    }

    private fun parseUnary(): FormulaAst {
        if (isSymbol("-")) return advance().position.let { FormulaAst.UnaryOp("-", parseUnary(), it) }
        if (isKeyword("not")) return advance().position.let { FormulaAst.UnaryOp("not", parseUnary(), it) }
        return parsePrimary()
    }

    private fun parsePrimary(): FormulaAst = when (val token = peek()) {
        is FormulaToken.Number -> { advance(); FormulaAst.NumberLit(token.value, token.position) }
        is FormulaToken.Str -> { advance(); FormulaAst.StringLit(token.value, token.position) }
        is FormulaToken.Symbol -> if (token.text == "(") {
            advance()
            parseOr().also { expectSymbol(")") }
        } else {
            throw FormulaSyntaxError("unexpected '${token.text}'", token.position)
        }
        is FormulaToken.Ident -> parseIdentStart(token)
        is FormulaToken.End -> throw FormulaSyntaxError("expected an expression", token.position)
    }

    private fun parseIdentStart(token: FormulaToken.Ident): FormulaAst {
        advance()
        return when (token.name) {
            "true" -> FormulaAst.BoolLit(true, token.position)
            "false" -> FormulaAst.BoolLit(false, token.position)
            "and", "or", "not" -> throw FormulaSyntaxError("'${token.name}' is not a value here", token.position)
            "prop" -> {
                expectSymbol("(")
                val key = peek() as? FormulaToken.Str
                    ?: throw FormulaSyntaxError("prop(...) needs a property name in quotes, like prop(\"Status\")", peek().position)
                advance()
                expectSymbol(")")
                FormulaAst.PropertyRef(key.value, token.position)
            }
            else -> {
                if (!isSymbol("(")) throw FormulaSyntaxError("'${token.name}' is not a known name — did you mean prop(\"${token.name}\")?", token.position)
                advance()
                val args = mutableListOf<FormulaAst>()
                if (!isSymbol(")")) {
                    args += parseOr()
                    while (isSymbol(",")) {
                        advance()
                        args += parseOr()
                    }
                }
                expectSymbol(")")
                FormulaAst.Call(token.name, args, token.position)
            }
        }
    }
}
