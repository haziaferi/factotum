package com.factotum.data

import com.factotum.core.time.LONG_RUN
import com.factotum.data.settings.PersonalSettings
import kotlinx.datetime.LocalTime
import kotlin.time.Duration

/** Personal settings fixed for a test: midnight and 12 hours unless given. */
internal class FixedSettings(private val start: LocalTime = LocalTime(0, 0), private val limit: Duration = LONG_RUN) : PersonalSettings {
    override suspend fun dayStart() = start
    override suspend fun longRun() = limit
}
