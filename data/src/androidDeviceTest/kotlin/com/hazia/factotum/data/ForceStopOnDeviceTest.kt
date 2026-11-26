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

    /** The control's step 1: an alarm is set and the run ends normally. */
    @Test
    fun armThenFinish() {
        assumeTrue(step == "arm")
        arm()
    }

    /** Step 2, the next start: what the last process's end says, and whether the alarm is still set. */
    @Test
    fun theNextStartReadsWhatHappened() {
        assumeTrue(step == "read-stopped" || step == "read-finished")
        val last = context.getSystemService(ActivityManager::class.java).getHistoricalProcessExitReasons(null, 0, 3)
        last.forEach { report("R61 exit reason=${it.reason} status=${it.status} description=${it.description} at=${it.timestamp}") }
        val held = probe(PendingIntent.FLAG_NO_CREATE)
        report("R61 $step: probe=${held != null} alarms=${alarmLines()}")

        // Both ends are recorded as a user's request; only the description tells a force-stop.
        assertEquals(ApplicationExitInfo.REASON_USER_REQUESTED, last.first().reason)
        // The PendingIntent outlives a force-stop, so asking for it (FLAG_NO_CREATE) cannot tell one.
        assertNotNull(held)
        if (step == "read-stopped") {
            assertTrue(last.first().description.orEmpty().startsWith("stop ${context.packageName} due to from pid"), last.first().description)
            assertEquals(emptyList(), alarmLines(), "the force-stop left the alarm set")
        } else {
            assertTrue(last.first().description.orEmpty().endsWith("finished inst"), last.first().description)
            assertTrue(alarmLines().isNotEmpty(), "a run's plain end lost the alarm")
        }
        alarms.cancel(held)
        held.cancel()
    }
}
