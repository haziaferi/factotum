package com.factotum.core.checkin

import kotlinx.datetime.LocalDate

/*
 * Check-ins (ADR 05, own-axis): mood is its own axis, on Tendril's five words; energy and
 * pleasantness are Equipoise's two axes in 0..1. Nothing here averages or counts check-ins for a
 * screen: the engines below produce their own outputs, never a chart of the check-ins.
 */

/** Equipoise's two axes of one check-in, each in 0..1. [stability] is the chip Equipoise used to ask. */
data class CheckIn(val energy: Double, val pleasantness: Double, val stability: Stability = Stability.UNSET)

enum class Stability { JUMPY, STEADY, FLAT, UNSET }

/** A check-in with the day it was logged on, as an epoch day. Several per day are expected. */
data class Logged(val day: Int, val checkIn: CheckIn)

/** Tendril's mood words and hues, five steps, no red (Tendril §0.10 item 4). */
enum class Mood(val level: Int, val label: String, val hex: String) {
    AWFUL(1, "Awful", "#5A6E96"),
    BAD(2, "Bad", "#3F7EA6"),
    OKAY(3, "Okay", "#7C6BA3"),
    GOOD(4, "Good", "#2E8A76"),
    GREAT(5, "Great", "#6E8A2C");

    companion object {
        fun fromLevel(level: Int): Mood? = entries.firstOrNull { it.level == level }
    }
}

/** Tendril's energy words, five steps. */
enum class Energy(val level: Int, val label: String) {
    DRAINED(1, "Drained"),
    LOW(2, "Low"),
    STEADY(3, "Steady"),
    HIGH(4, "High"),
    FULL(5, "Full");

    companion object {
        fun fromLevel(level: Int): Energy? = entries.firstOrNull { it.level == level }
    }
}

/**
 * A step [level] of [levels] on Equipoise's 0..1 axis: the middle of its band, (k − 0.5) / n, so
 * Tendril's "Low" (2 of 5) is 0.3 and no step of an even scale sits on the 0.5 midline (ADR 05).
 */
fun axisValue(level: Int, levels: Int): Double {
    require(levels >= 2 && level in 1..levels) { "step $level of $levels" }
    return (level - 0.5) / levels
}

/** The step of [levels] an axis value falls in: [axisValue]'s inverse, and a continuous value's band. */
fun levelOf(value: Double, levels: Int): Int {
    require(levels >= 2 && value in 0.0..1.0) { "$value on $levels steps" }
    return minOf(levels, (value * levels).toInt() + 1)
}

/** A check-in may be about today or a past day, never one that has not happened (Tendril; owner, 2026-10-03). */
fun checkInOffered(day: LocalDate, today: LocalDate): Boolean = day <= today
