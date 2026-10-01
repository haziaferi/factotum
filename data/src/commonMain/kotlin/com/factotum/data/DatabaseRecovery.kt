package com.factotum.data

class DatabaseOpen<T>(
    val database: T,
    /** True when [openOrRecover] set an unopenable file aside to get here. */
    val recovered: Boolean,
)

/**
 * Builds the database and proves it opens; if the probe fails in a way [isUnopenable] accepts,
 * closes it, sets its file aside (never deletes it) and builds once more.
 *
 * [probe] must run a real statement: Room opens lazily, so a broken file only throws on first
 * use. Any other failure (a locked file, a full disk) is rethrown with the file untouched, and so
 * is a second failure, because a fresh database that will not open means the old file was not
 * the problem.
 */
fun <T> openOrRecover(
    build: () -> T,
    probe: (T) -> Unit,
    close: (T) -> Unit,
    setAside: () -> Unit,
    isUnopenable: (Throwable) -> Boolean,
): DatabaseOpen<T> {
    val first = build()
    val failure = runCatching { probe(first) }.exceptionOrNull()
        ?: return DatabaseOpen(first, recovered = false)

    // A failed close must not stop recovery, nor hide the original failure.
    runCatching { close(first) }
    if (!isUnopenable(failure)) throw failure
    setAside()

    val second = build()
    probe(second)
    return DatabaseOpen(second, recovered = true)
}

/** True when [failure] or one of its causes reports SQLITE_CORRUPT or SQLITE_NOTADB. */
expect fun isCorruptDatabase(failure: Throwable): Boolean

/** True when [failure] or one of its causes reports SQLITE_CONSTRAINT: a CHECK trigger, a foreign key or a unique key refused a write. */
expect fun isConstraintViolation(failure: Throwable): Boolean

/** Marks a file set aside because it would not open; not `.bak`, since the app makes no backups. */
const val UNOPENABLE_SUFFIX = ".unopenable-"
