package com.hazia.factotum.data

import android.app.ActivityManager
import android.app.AlarmManager
import android.app.PendingIntent
import android.app.job.JobInfo
import android.app.job.JobParameters
import android.app.job.JobScheduler
import android.app.job.JobService
import android.content.ComponentName
import android.content.Intent
import android.os.Build
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assume.assumeTrue
import org.junit.runner.RunWith
import kotlin.test.Test

/** Android 15's start history, apart so that older versions never load `ApplicationStartInfo`. */
@androidx.annotation.RequiresApi(35)
private object StartReasons {
    fun read(am: ActivityManager): String =
        am.getHistoricalProcessStartReasons(2).joinToString(";") { "forceStopped=${it.wasForceStopped()} reason=${it.reason}" }
}

/** The probe's job: it is never meant to run, only to be found pending, or not, at the next start. */
class ForceStopTraceJob : JobService() {
    override fun onStartJob(params: JobParameters?) = false
    override fun onStopJob(params: JobParameters?) = false
}

/**
 * SPEC:R206: what a force-stop of an app that is not running leaves for its next start to read,
 * beyond R61's exit history: a pending job, an alarm clock, a PendingIntent, and on Android 15 and
 * later `ApplicationStartInfo.wasForceStopped()`. Each step is its own `am instrument` run
 * (`tools/device/run.sh`); this probe reports and asserts nothing.
 */
@RunWith(AndroidJUnit4::class)
class ForceStopTraceOnDeviceTest {

    private val step: String? = InstrumentationRegistry.getArguments().getString("r206")
    private val alarms = context.getSystemService(AlarmManager::class.java)
    private val jobs = context.getSystemService(JobScheduler::class.java)

    private fun probe(flags: Int): PendingIntent? =
        PendingIntent.getBroadcast(context, 206, Intent("com.hazia.factotum.R206_PROBE").setPackage(context.packageName), flags or PendingIntent.FLAG_IMMUTABLE)

    private fun clock(): String {
        val next = alarms.nextAlarmClock ?: return "none"
        return "${next.triggerTime} by ${next.showIntent?.creatorPackage}"
    }

    /**
     * Step 1: a daily job, kept across a reboot, as the app would hold one, and an alarm clock an
     * hour away; the run then ends, or is force-stopped.
     */
    @Test
    fun arm() {
        assumeTrue(step == "arm" || step == "arm-and-stop")
        val job = JobInfo.Builder(206, ComponentName(context, ForceStopTraceJob::class.java)).setPeriodic(86_400_000).setPersisted(true).build()
        val scheduled = jobs.schedule(job) == JobScheduler.RESULT_SUCCESS
        val exact = Build.VERSION.SDK_INT < 31 || alarms.canScheduleExactAlarms()
        if (exact) alarms.setAlarmClock(AlarmManager.AlarmClockInfo(System.currentTimeMillis() + 3_600_000, probe(0)), probe(0)!!)
        report("R206 armed: job=$scheduled exact=$exact clock=${clock()}")
        if (step == "arm-and-stop") shell("am force-stop ${context.packageName}")
    }

    /** Step 2, the next start: every trace the app itself could read, then everything is cleared. */
    @Test
    fun theNextStartReadsEachTrace() {
        assumeTrue(step?.startsWith("read-") == true)
        val am = context.getSystemService(ActivityManager::class.java)
        val exit = am.getHistoricalProcessExitReasons(null, 0, 1).firstOrNull()
        val start = if (Build.VERSION.SDK_INT >= 35) StartReasons.read(am) else "n/a"
        val held = probe(PendingIntent.FLAG_NO_CREATE)
        report("R206 $step: API=${Build.VERSION.SDK_INT} job=${jobs.getPendingJob(206) != null} clock=${clock()} intent=${held != null} exit=${exit?.description} start=$start")
        jobs.cancel(206)
        held?.let { alarms.cancel(it); it.cancel() }
    }
}
