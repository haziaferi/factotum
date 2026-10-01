package com.factotum.data

import java.io.File

/**
 * Renames [dbPath] and its `-journal`, `-wal` and `-shm` files to `<name>.unopenable-<stamp>`, so
 * the new database is never opened beside the old one's journal. The database file moves last:
 * if a rename fails, it is still in place and the next start tries again.
 */
fun setAsideDatabaseFiles(dbPath: String, stamp: Long) {
    for (suffix in listOf("-journal", "-wal", "-shm", "")) {
        val file = File(dbPath + suffix)
        if (file.exists()) setAside(file, stamp)
    }
}

/** Renames [file] to `<name>.unopenable-<stamp>`; it is kept, never deleted. */
internal fun setAside(file: File, stamp: Long) {
    check(file.renameTo(File(file.path + UNOPENABLE_SUFFIX + stamp))) { "could not set aside ${file.path}" }
}
