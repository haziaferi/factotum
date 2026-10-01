package com.factotum.data

import android.content.Context
import androidx.room.Room

fun openFactotumDatabase(context: Context): DatabaseOpen<FactotumDatabase> {
    val app = context.applicationContext
    return openDatabase(
        file = app.getDatabasePath(DATABASE_NAME),
        builder = { Room.databaseBuilder<FactotumDatabase>(app, DATABASE_NAME) },
        driver = KeepFileOnCorruptionDriver(),
    )
}
