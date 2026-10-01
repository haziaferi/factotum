package com.factotum.data

import androidx.sqlite.SQLiteException

// androidx.sqlite exposes no result code; its own throw site formats "Error code: N, message: ...".
// Extended codes keep the primary code in the low byte.
private val errorCode = Regex("""^Error code: (\d+)""")
private const val SQLITE_CORRUPT = 11
private const val SQLITE_NOTADB = 26
private const val SQLITE_CONSTRAINT = 19

actual fun isCorruptDatabase(failure: Throwable): Boolean = reports(failure, SQLITE_CORRUPT, SQLITE_NOTADB)

actual fun isConstraintViolation(failure: Throwable): Boolean = reports(failure, SQLITE_CONSTRAINT)

private fun reports(failure: Throwable, vararg primary: Int): Boolean =
    generateSequence(failure) { it.cause }.any { t ->
        val code = (t as? SQLiteException)?.message?.let { errorCode.find(it) }?.groupValues?.get(1)?.toInt()
        code != null && (code and 0xFF) in primary
    }
