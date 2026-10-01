package com.factotum.data.reminder

import kotlinx.datetime.LocalDateTime

enum class AlertKind { NOTIFICATION, ALARM }

/** Mnemo's modes: how insistent a reminder is. */
enum class AlertMode { EASE, SCHEDULE, ALERT }

/**
 * How a reminder alerts (ADR 03): the superset of Chronicle's and Mnemo's settings, per reminder.
 * [sound] and [vibration] keep Mnemo's three states: null is the default, "" is none, any other
 * value names one. A [nagRepeats] of 0 is Mnemo's nag off; [nagMinutes] bounds the nag, if set.
 */
data class Alert(
    val kind: AlertKind = AlertKind.NOTIFICATION,
    val nagRepeats: Long = 0,
    val nagMinutes: Long? = null,
    val sound: String? = null,
    val vibration: String? = null,
    val mode: AlertMode = AlertMode.SCHEDULE,
    val skin: String? = null,
    val exact: Boolean = false,
)

/** When one reminder next fires, and for which item. */
data class Firing(val reminderId: String, val itemId: String, val at: LocalDateTime)
