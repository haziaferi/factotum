package com.factotum.core.formula

/** One formula of a database for checking: its property's key and its parsed expression. */
data class FormulaNode(val key: String, val ast: FormulaAst)

/** A cycle among formulas, as the path that closes it: `["Total", "Subtotal", "Total"]`. */
class FormulaCycleException(val cyclePath: List<String>) : Exception("circular formula reference: ${cyclePath.joinToString(" -> ")}")

/**
 * [nodes] in an order where each formula comes after every formula it names, so a check can read
 * the type of one already checked. A key that is not among [nodes] is a plain property, a leaf.
 * A cycle is an error naming its path (Tendril's: a depth limit would not say where the loop is).
 */
fun topologicallySortFormulas(nodes: List<FormulaNode>): List<FormulaNode> {
    val byKey = nodes.associateBy { it.key }
    val visited = mutableSetOf<String>()
    val onStack = LinkedHashSet<String>()
    val result = mutableListOf<FormulaNode>()

    fun visit(key: String) {
        if (key in visited) return
        if (key in onStack) throw FormulaCycleException(onStack.dropWhile { it != key } + key)
        val node = byKey[key] ?: return
        onStack += key
        node.ast.propertyReferences().forEach { visit(it.key) }
        onStack -= key
        visited += key
        result += node
    }

    nodes.forEach { visit(it.key) }
    return result
}

data class FormulaError(val message: String, val position: Int)

/** What a key names outside the formulas checked together: a plain property of a type, or a relation, which no formula reads yet. */
sealed class FormulaPropertyKind {
    data class Typed(val formulaType: FormulaType) : FormulaPropertyKind()
    data object Relation : FormulaPropertyKind()
}

/** A formula's checked type, [FormulaType.ANY] whenever it has an error. */
data class FormulaCheckResult(val type: FormulaType, val errors: List<FormulaError>)

/**
 * Checks every formula of a database, in dependency order, so one naming another sees its checked
 * type. [lookup] answers for every key not among [nodes] (null: no such property). A cycle is an
 * error on every formula on it.
 */
fun checkAllFormulas(nodes: List<FormulaNode>, lookup: (String) -> FormulaPropertyKind?): Map<String, FormulaCheckResult> {
    val ordered = try {
        topologicallySortFormulas(nodes)
    } catch (cycle: FormulaCycleException) {
        return cycle.cyclePath.toSet().associateWith { FormulaCheckResult(FormulaType.ANY, listOf(FormulaError(cycle.message.orEmpty(), 0))) }
    }
    val checker = Checker(nodes.map { it.key }.toSet(), lookup)
    return ordered.associate { node ->
        val errors = mutableListOf<FormulaError>()
        val type = checker.infer(node.ast, errors).takeIf { errors.isEmpty() } ?: FormulaType.ANY
        checker.computed[node.key] = type
        node.key to FormulaCheckResult(type, errors)
    }
}

private class Checker(private val formulas: Set<String>, private val lookup: (String) -> FormulaPropertyKind?) {
    val computed = mutableMapOf<String, FormulaType>()

    fun infer(ast: FormulaAst, errors: MutableList<FormulaError>): FormulaType = when (ast) {
        is FormulaAst.NumberLit -> FormulaType.NUMBER
        is FormulaAst.StringLit -> FormulaType.TEXT
        is FormulaAst.BoolLit -> FormulaType.BOOLEAN
        is FormulaAst.PropertyRef -> if (ast.key in formulas) computed[ast.key] ?: FormulaType.ANY else when (val kind = lookup(ast.key)) {
            null -> FormulaType.ANY.also { errors += FormulaError("no property named \"${ast.key}\" on this database", ast.position) }
            is FormulaPropertyKind.Typed -> kind.formulaType
            FormulaPropertyKind.Relation -> FormulaType.ANY.also {
                errors += FormulaError("\"${ast.key}\" is a relation — formulas can't traverse relations yet, only reference plain properties", ast.position)
            }
        }
        is FormulaAst.UnaryOp -> {
            val operand = infer(ast.operand, errors)
            val expected = if (ast.op == "not") FormulaType.BOOLEAN else FormulaType.NUMBER
            if (operand != FormulaType.ANY && operand != expected) errors += FormulaError("'${ast.op}' needs a ${expected.word}, got ${operand.word}", ast.position)
            expected
        }
        is FormulaAst.BinaryOp -> binary(ast, errors)
        is FormulaAst.Call -> call(ast, errors)
    }

    private fun binary(ast: FormulaAst.BinaryOp, errors: MutableList<FormulaError>): FormulaType {
        val left = infer(ast.left, errors)
        val right = infer(ast.right, errors)
        // One side already broken: no second error on top of it.
        val unknown = left == FormulaType.ANY || right == FormulaType.ANY
        fun fail(message: String) { if (!unknown) errors += FormulaError(message, ast.position) }
        return when (ast.op) {
            "and", "or" -> FormulaType.BOOLEAN.also {
                if (left != FormulaType.BOOLEAN || right != FormulaType.BOOLEAN) fail("'${ast.op}' needs two booleans, got ${left.word} and ${right.word}")
            }
            "==", "!=" -> FormulaType.BOOLEAN
            "<", "<=", ">", ">=" -> FormulaType.BOOLEAN.also {
                if (!(left == right && (left == FormulaType.NUMBER || left == FormulaType.DATE))) fail("'${ast.op}' compares two numbers or two dates, got ${left.word} and ${right.word}")
            }
            "+" -> when {
                unknown -> FormulaType.ANY
                left == FormulaType.NUMBER && right == FormulaType.NUMBER -> FormulaType.NUMBER
                left == FormulaType.TEXT || right == FormulaType.TEXT -> FormulaType.TEXT
                else -> FormulaType.ANY.also { fail("'+' needs two numbers, or a text on one side to concatenate — got ${left.word} and ${right.word}") }
            }
            "-", "*", "/" -> FormulaType.NUMBER.also {
                if (left != FormulaType.NUMBER || right != FormulaType.NUMBER) fail("'${ast.op}' needs two numbers, got ${left.word} and ${right.word}")
            }
            else -> FormulaType.ANY
        }
    }

    private fun call(ast: FormulaAst.Call, errors: MutableList<FormulaError>): FormulaType {
        val types = ast.args.map { infer(it, errors) }
        fun arity(min: Int, max: Int = min) {
            if (ast.args.size < min || ast.args.size > max) {
                val expected = if (min == max) plural(min, "argument") else "$min to $max arguments"
                errors += FormulaError("${ast.functionName}(...) needs $expected, got ${ast.args.size}", ast.position)
            }
        }
        fun numbers() = types.forEachIndexed { i, t ->
            if (t != FormulaType.ANY && t != FormulaType.NUMBER) errors += FormulaError("${ast.functionName}(...) argument ${i + 1} must be a number, got ${t.word}", ast.args[i].position)
        }
        return when (ast.functionName) {
            "if" -> {
                arity(3)
                if (types.isNotEmpty() && types[0] != FormulaType.ANY && types[0] != FormulaType.BOOLEAN) {
                    errors += FormulaError("if(...)'s first argument must be a boolean condition, got ${types[0].word}", ast.args[0].position)
                }
                if (types.size != 3) return FormulaType.ANY
                val (then, otherwise) = types[1] to types[2]
                if (then != FormulaType.ANY && otherwise != FormulaType.ANY && then != otherwise) {
                    errors += FormulaError("if(...)'s two branches must be the same type, got ${then.word} and ${otherwise.word}", ast.position)
                }
                if (then != FormulaType.ANY) then else otherwise
            }
            "abs", "round" -> FormulaType.NUMBER.also { arity(1); numbers() }
            "min", "max" -> FormulaType.NUMBER.also { arity(1, Int.MAX_VALUE); numbers() }
            else -> FormulaType.ANY.also { errors += FormulaError("unknown function \"${ast.functionName}\"", ast.position) }
        }
    }
}

private val FormulaType.word get() = name.lowercase()

private fun plural(n: Int, one: String) = if (n == 1) "1 $one" else "$n ${one}s"
