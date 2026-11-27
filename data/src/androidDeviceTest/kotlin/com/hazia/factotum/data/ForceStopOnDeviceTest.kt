package com.hazia.factotum.data

import android.app.ActivityManager
import android.app.AlarmManager
import android.app.ApplicationExitInfo
import android.app.PendingIntent
import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assume.assumeTrue
import org.junit.runner.RunWith
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/**
 * SPEC:R61, the platform half: what a force-stop does to an app's alarms, and what the next start
 * can read of it. Each step is its own `am instrument` run, since a force-stop ends the process
 * (`tools/device/run.sh` runs them in order); a plain `connectedAndroidDeviceTest` skips them all.
 */
@RunWith(AndroidJUnit4::class)
class ForceStopOnDeviceTest {

    private val step: String? = InstrumentationRegistry.getArguments().getString("r61")
    private val alarms = context.getSystemService(AlarmManager::class.java)

    private fun probe(flags: Int): PendingIntent? =
        PendingIntent.getBroadcast(context, 61, Intent("com.hazia.factotum.R61_PROBE").setPackage(context.packageName), flags or PendingIntent.FLAG_IMMUTABLE)

    private fun alarmLines() = shell("dumpsys alarm").lines().filter { context.packageName in it && ("RTC" in it || "ELAPSED" in it) }

    private fun arm() {
        alarms.set(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + 3_600_000, probe(0)!!)
        assertNotNull(probe(PendingIntent.FLAG_NO_CREATE))
        report("R61 armed: ${alarmLines()}")
    }

    /** Step 1: an alarm is set, then the app is force-stopped as Settings does it; the run ends as a crash. */
    @Test
    fun armThenForceStop() {
        assumeTrue(step == "arm-and-stop")
        arm()
        shell("am force-stop ${context.packageName}")
    }

    /** Step 1 for Settings' own button: an alarm is set and the process waits to be force-stopped by hand. */
    @Test
    fun armThenWait() {
        assumeTrue(step == "arm-and-wait")
        arm()
        Thread.sleep(90_000)
    }

    /**
     * Step 1 of the control and of the idle case: an alarm is set and the run ends normally, so the
     * process is gone; the idle case is then force-stopped from outside, as Settings stops an app
     * that is not running.
     */
    @Test
    fun armThenFinish() {
        assumeTrue(step == "arm")
        arm()
    }

    /**
     * Step 2, the next start: what the last process's end says, and whether the alarm is still set.
     * - `read-finished`, the control: nothing stopped the app, and the alarm is still set.
     * - `read-stopped`: force-stopped while running; the stop is recorded, and the alarm is gone.
     * - `read-stopped-idle`: force-stopped while not running; the alarm is gone, and **no** end is
     *   recorded for the stop, so the exit history cannot tell this case at all.
     */
    @Test
    fun theNextStartReadsWhatHappened() {
        assumeTrue(step in setOf("read-finished", "read-stopped", "read-stopped-idle"))
        val last = context.getSystemService(ActivityManager::class.java).getHistoricalProcessExitReasons(null, 0, 3)
        last.forEach { report("R61 exit reason=${it.reason} status=${it.status} description=${it.description} at=${it.timestamp}") }
        val held = probe(PendingIntent.FLAG_NO_CREATE)
        val set = alarmLines()
        report("R61 $step: probe=${held != null} alarms=$set")

        // Every end here is recorded as a user's request; only the description tells a force-stop.
        assertEquals(ApplicationExitInfo.REASON_USER_REQUESTED, last.first().reason)
        val description = last.first().description.orEmpty()
        when (step) {
            "read-stopped" -> {
                // Android 16 puts "[FORCE STOP] " before every description, a run's own end included.
                assertTrue("stop ${context.packageName} due to from pid" in description, description)
                assertEquals(emptyList(), set, "the force-stop left the alarm set")
            }
            "read-stopped-idle" -> {
                assertTrue(description.endsWith("finished inst"), "a stop of an idle app was recorded after all: $description")
                assertEquals(emptyList(), set, "the force-stop left the alarm set")
            }
            else -> {
                assertTrue(description.endsWith("finished inst"), description)
                assertTrue(set.isNotEmpty(), "a run's plain end lost the alarm")
            }
        }
        // On API 32 the PendingIntent mostly outlives a force-stop, but not always (gone in 3 of 18 reads,
        // 2026-11-27), so asking for it (FLAG_NO_CREATE) cannot tell one; recorded only. Android 15
        // is documented to cancel it in the stopped state.
        held?.let { alarms.cancel(it); it.cancel() }
    }
}
