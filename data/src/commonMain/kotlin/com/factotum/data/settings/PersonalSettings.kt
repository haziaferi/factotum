package com.factotum.data.settings

import kotlinx.datetime.LocalTime
import kotlin.time.Duration

/**
 * The PERSONAL settings the repositories read on every call (ADR 09), so a change made on another
 * device applies as soon as it is imported. [SettingsRepository] is the real one; it is required,
 * so no repository can be built that silently ignores the person's setting.
 */
interface PersonalSettings {
    /** Which day a Log or a span counts for (ADR 06). */
    suspend fun dayStart(): LocalTime

    /** How long a timer runs before it is asked about (ADR 07). */
    suspend fun longRun(): Duration
}
