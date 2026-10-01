package com.factotum.data

import android.database.sqlite.SQLiteConstraintException
import android.database.sqlite.SQLiteDatabaseCorruptException

actual fun isCorruptDatabase(failure: Throwable): Boolean =
    generateSequence(failure) { it.cause }.any { it is SQLiteDatabaseCorruptException }

actual fun isConstraintViolation(failure: Throwable): Boolean =
    generateSequence(failure) { it.cause }.any { it is SQLiteConstraintException }
