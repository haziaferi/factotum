package com.factotum.data

import androidx.room.Room
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import java.io.File

fun openFactotumDatabase(file: File, now: () -> Long = System::currentTimeMillis): DatabaseOpen<FactotumDatabase> =
    openDatabase(
        file = file,
        builder = { Room.databaseBuilder<FactotumDatabase>(name = file.absolutePath) },
        driver = BundledSQLiteDriver(),
        now = now,
    )
