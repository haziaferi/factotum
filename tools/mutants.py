"""Fail-before check: each mutant breaks one decided rule and must be killed by the tests named for
it; the restored tree must pass. Run from the repo root:  python tools/mutants.py [slice]

A mutant counts as killed only when a named test appears as a failure in the JUnit XML, never on a
bare non-zero exit (a build that did not run would otherwise look like a kill).
"""
import glob
import os
import re
import shutil
import subprocess
import sys

GRADLEW = os.path.abspath("gradlew.bat" if os.name == "nt" else "gradlew")
MERGE = "core/src/commonMain/kotlin/com/factotum/core/sync/Merge.kt"
OPEN = "data/src/jvmCommon/kotlin/com/factotum/data/OpenDatabase.kt"
FOLDER = "data/src/commonMain/kotlin/com/factotum/data/sync/FolderSync.kt"
STAGED = "data/src/commonMain/kotlin/com/factotum/data/sync/StagedStore.kt"
CODEC = "data/src/commonMain/kotlin/com/factotum/data/sync/Records.kt"
TRIGGERS = "data/src/commonMain/kotlin/com/factotum/data/SchemaTriggers.kt"
REPO = "data/src/commonMain/kotlin/com/factotum/data/item/ItemRepository.kt"
ITEMDAO = "data/src/commonMain/kotlin/com/factotum/data/item/ItemDao.kt"
WRITES = "data/src/commonMain/kotlin/com/factotum/data/LocalWrites.kt"
REMREPO = "data/src/commonMain/kotlin/com/factotum/data/reminder/ReminderRepository.kt"
REMDAO = "data/src/commonMain/kotlin/com/factotum/data/reminder/ReminderDao.kt"
RRULE = "core/src/commonMain/kotlin/com/factotum/core/recurrence/RRule.kt"
RECUR = "core/src/commonMain/kotlin/com/factotum/core/recurrence/Recurrence.kt"
CRON = "core/src/commonMain/kotlin/com/factotum/core/recurrence/Cron.kt"

# slice -> [(name, file, old, new, test task, tests that must fail)]
SLICES = {
    "01": [
        ("no ask (hybrid, not hybrid+)", MERGE, "if (mine.stamp != base && mine.values",
         "if (false && mine.values", ":core:desktopTest", {"mnemoSameTimeShown", "mnemoDeleteVsEditShown", "chronicleTieConverges"}),
        ("purge ignored on import", MERGE, "if (incoming.newest <= purge) continue", "if (false) continue",
         ":core:desktopTest", {"tendrilPurgeHolds"}),
        ("answers do not settle", MERGE, " && theirs.settles != mine.stamp", "",
         ":core:desktopTest", {"keepMineWinsEverywhere"}),
        ("a version no newer than the base is merged", MERGE, "            if (base != null && theirs.stamp <= base) continue\n", "",
         ":core:desktopTest", {"aReplayedOldVersionIsNotAskedAbout"}),
        ("an older replay replaces the pending question", MERGE, "if ((store.asked(local.id, name)?.stamp ?: theirs.stamp) <= theirs.stamp) ", "",
         ":core:desktopTest", {"aPendingQuestionIsNotReplacedByAnOlderReplay"}),
        ("Room's leaked connection kept open", OPEN, "            tracked.closeAll()\n", "",
         ":data:desktopTest", {"aDatabaseCorruptPastItsSchemaPageIsSetAsideToo"}),
    ],
    "13": [
        ("conflict copies not read", FOLDER, "val copy = FolderLayout.isConflictCopy(name)", "val copy = false",
         ":data:desktopTest", {"aClonedDeviceIdsClashIsMergedAndTheCopyRemoved"}),
        ("own clash not re-read", FOLDER, "val shared = owner == device && names.any(FolderLayout::isConflictCopy)",
         "val shared = false", ":data:desktopTest", {"aClonedDeviceIdsClashIsMergedAndTheCopyRemoved"}),
        ("log never compacted", FOLDER, "if (held.size >= snapshotEvery) {", "if (false) {",
         ":data:desktopTest", {"androidFiles1y_aYearKeepsEachDeviceToItsSegmentsAndOneSnapshot", "aPurgeReachesAPeerAndOutlivesCompaction"}),
        ("unfinished last line read", FOLDER, "    return lines\n}", "    if (start < bytes.size) lines += Line(bytes.decodeToString(start, bytes.size), bytes.size)\n    return lines\n}",
         ":data:desktopTest", {"aLineStillBeingWrittenWaitsForItsNewline", "onlyNewlineTerminatedLinesAreRead"}),
        ("positions kept when the tables change", FOLDER, "        dao.clearReads()\n", "",
         ":data:desktopTest", {"aLineForATableThisVersionLacksIsReadAgainOnceItHasIt"}),
        ("one transaction per file, not per chunk", FOLDER, "lines.chunked(MERGE_LINES)", "listOf(lines).filter { it.isNotEmpty() }",
         ":data:desktopTest", {"aBigFileIsMergedInChunksEachWithItsReadPosition"}),
        ("purges not exported", FOLDER, " ?: purges[id]?.let { PurgeRecord(id, it) }", "",
         ":data:desktopTest", {"aPurgeReachesAPeerThroughTheLog"}),
        ("unchanged files read again", FOLDER, "if (folder.size(path) == from) continue", "if (false) continue",
         ":data:desktopTest", {"aPeerFileIsReadOnlyWhenItHasGrown"}),
        ("Long and Double read alike", CODEC, "p.booleanOrNull ?: p.longOrNull ?: p.double", "p.booleanOrNull ?: p.double",
         ":data:desktopTest", {"aRowReadsBackWithEveryValueItsOwnType"}),
        ("a refused line stops the import", FOLDER, "                if (!isConstraintViolation(e)) throw e\n                // A backstop", "                throw e\n                // A backstop",
         ":data:desktopTest", {"aRowThatBreaksItsKindsRulesIsDroppedNotKeptWaiting"}),
        ("a line naming a purged parent waits forever", FOLDER, "                absent.any { it in purged } -> dropped += line.first\n", "",
         ":data:desktopTest", {"aSubtaskWhoseParentWasPurgedIsDroppedNotKeptWaiting"}),
        ("waiting lines never retried", FOLDER, "report + retryWaiting()", "report",
         ":data:desktopTest", {"aSubtaskThatArrivesBeforeItsParentWaitsForIt"}),
        ("a row that does not fit is merged", FOLDER, "tables[it.row.table]?.fits(it.row) == true", "it.row.table in tables",
         ":data:desktopTest", {"aRowThatDoesNotFitItsTableIsSkipped"}),
    ],
    "02": [
        ("kind rules dropped", TRIGGERS, '        ITEM to itemRules,\n', "",
         ":data:desktopTest", {"sharedEventHasNoTaskState_theDatabaseRefusesIt", "theKindRulesHoldAfterAReopen"}),
        ("completion status unchecked", TRIGGERS, '        COMPLETION to "NEW.status IN (\'DONE\', \'SKIPPED\')",\n', "",
         ":data:desktopTest", {"tendrilCompletionLog_eachOccurrenceKeepsItsOutcomeAndNoOtherStatusIsTaken"}),
        ("writes not queued for export", TRIGGERS, "for (table in SYNCED_TABLES)", "for (table in emptyList<String>())",
         ":data:desktopTest", {"stRetiredLoser_aWipedDevicesChangeSurvives", "aVersionOutlivesTheLossOfItsAuthorsFiles"}),
        ("a deleted parent keeps its subtasks", REPO, "listOf(id) + dao.liveChildren(id)", "listOf(id)",
         ":data:desktopTest", {"tendrilSubtaskCascade_aDeletedParentTakesItsSubtasks"}),
        ("rescheduling undeletes", REPO, ' - "deleted_at")', ")",
         ":data:desktopTest", {"rescheduleLeavesADeletedItemDeleted"}),
        ("a deleted row keeps its merge state", TRIGGERS, "DELETE FROM sync_base WHERE id = OLD.id; DELETE FROM sync_ask WHERE id = OLD.id;", "",
         ":data:desktopTest", {"aPurgedParentTakesItsSubtasksPendingQuestionWithIt"}),
        ("the clock is not saved with a write", WRITES, "                sync.saveClock(clock)\n", "",
         ":data:desktopTest", {"eachWriteSavesTheClockWithIt"}),
    ],
    "03": [
        ("alert settings unchecked", TRIGGERS, "        REMINDER to reminderRules,\n", "",
         ":data:desktopTest", {"chronicleAlertSettings_storedPerReminderAndUnknownValuesRefused"}),
        ("a standalone reminder without a time", TRIGGERS, "\n        AND (NEW.kind <> 'REMINDER' OR (NEW.start_date IS NOT NULL AND NEW.start_time IS NOT NULL))", "",
         ":data:desktopTest", {"aStandaloneReminderNeedsATime"}),
        ("a done item's reminder still fires", REMDAO, " +\n            \"AND (i.status IS NULL OR i.status = 'PENDING')\"", "",
         ":data:desktopTest", {"tendrilQuietWhenDone_aDoneTasksReminderNoLongerFires", "mnemoStandaloneDone_theRowStaysAndStopsFiring"}),
        ("a deleted item's reminder still fires", REMDAO, "AND i.deleted_at IS NULL AND i.start_date", "AND i.start_date",
         ":data:desktopTest", {"tendrilCascade_aDeletedTaskSilencesItsReminderAndAPurgedOneRemovesIt"}),
        ("a deleted reminder still fires", REMDAO, "\"WHERE r.deleted_at IS NULL AND ", "\"WHERE ",
         ":data:desktopTest", {"aDeletedReminderNoLongerFires"}),
        ("the anchor is ignored", REMREPO, "private val anchor = s.anchorTime?.let(LocalTime::parse) ?: MIDNIGHT", "private val anchor = MIDNIGHT",
         ":data:desktopTest", {"tendrilAnchorDateOnly_theDayBeforeAtNine"}),
        ("a snooze is ignored", REMREPO, "return listOfNotNull(snoozed, first(after, skip = snoozedFrom)).minOrNull()", "return first(after, skip = snoozedFrom)",
         ":data:desktopTest", {"aSnoozeMovesTheFiringAndLeavesTheItemsTimeAlone"}),
        ("a snooze outlives the firing it snoozed", REMREPO, "snoozedFrom != null && isDue(snoozedFrom)", "snoozedFrom != null",
         ":data:desktopTest", {"aSnoozeFromBeforeARescheduleNoLongerApplies", "aRescheduleThatDoesNotPassTheSnoozeStillMovesTheFiring", "aRetimedReminderDropsItsSnooze"}),
        ("standalone reminders crowd the day", ITEMDAO, "OR :showReminders)", "OR :showReminders OR 1)",
         ":data:desktopTest", {"sharedTimelineUnchanged_standaloneRemindersShowOnlyWhenAsked"}),
        ("a reminder on an undated item is taken", REMREPO, "require(item.startDate != null && ", "require(",
         ":data:desktopTest", {"aReminderOnAnItemWithNoDateIsRefused"}),
        ("a reminder on a deleted item is taken", REMREPO, " && item.deletedAt == null)", ")",
         ":data:desktopTest", {"aReminderOnADeletedItemIsRefused"}),
        ("an item with reminders loses its date", REPO, "require(start != null || reminders.remindersOf(id).isEmpty())", "require(true)",
         ":data:desktopTest", {"anItemWithRemindersKeepsItsStartDate"}),
        ("a standalone reminder's item outlives its last reminder", REMREPO, "if (standalone && last) listOf(itemId) else emptyList()", "emptyList()",
         ":data:desktopTest", {"deletingAStandaloneRemindersOnlyReminderDeletesItsItem"}),
        ("keep both leaves the copy without reminders", REPO, "reminders.remindersOf(id).forEach { copied[it.id] = newId() }", "Unit",
         ":data:desktopTest", {"keepingBothTimesOfAStandaloneReminderKeepsBothFiring"}),
    ],
    "04": [
        ("COUNT counted from the window", RRULE, "var period = if (count == null) firstPeriodNear(start, from) else 0L", "var period = firstPeriodNear(start, from)",
         ":core:desktopTest", {"countCountsFromTheStartEvenForALaterWindow"}),
        ("BYSETPOS ignored", RRULE, "    if (bySetPos.isEmpty()) return times\n", "    return times\n",
         ":core:desktopTest", {"bySetPosPicksWithinEachPeriod"}),
        ("an unknown part is ignored", RRULE, "if (name !in KNOWN || name in parts) return null", "if (name in parts) return null",
         ":core:desktopTest", {"aRuleWithAPartTheExpanderLacksIsRefusedNotGuessed"}),
        ("a year begins at the start's month", RRULE, "LocalDateTime(LocalDate(start.date.year, 1, 1).plus(step, DateTimeUnit.YEAR), MIDNIGHT)",
         "LocalDateTime(firstOfMonth(start.date).plus(step * 12, DateTimeUnit.MONTH), MIDNIGHT)",
         ":core:desktopTest", {"aYearlyRuleKeepsItsLastYearsEarlierMonths"}),
        ("cron's day OR weekday read as AND", CRON, "-> Recurrence.RuleSet(listOf(byMonthDay, byWeekday))", "-> Recurrence.Rule(byMonthDay.copy(byDay = byWeekday.byDay))",
         ":core:desktopTest", {"theNineFixedRulesGiveTheOwnerAppsOccurrences"}),
        ("draws seeded without the item", RECUR, 'kind: String) = "$itemId|$date|$kind"', 'kind: String) = "$date|$kind"',
         ":core:desktopTest", {"chronicleRandomDays_gapsOfTwoToFourDaysAtTheSameTimeTheSameOnEveryDevice"}),
        ("recurrence rules dropped", TRIGGERS, "        AND $recurrenceRules\n", "",
         ":data:desktopTest", {"eachKindKeepsToItsOwnColumns"}),
        ("rescheduling drops the recurrence", REPO, 'schedule(start, at, endDate, endTime, due) - "deleted_at")', 'schedule(start, at, endDate, endTime, due) - "deleted_at" + recurrenceValues(null))',
         ":data:desktopTest", {"reschedulingKeepsTheRecurrenceAndMovesItsStart"}),
        ("a resolved occurrence still fires", REMREPO, ".filter { it.date !in resolved }", "",
         ":data:desktopTest", {"aResolvedOccurrenceDoesNotFire"}),
        ("a whole-day repeat fires at its occurrence's midnight", REMREPO, "if (s.startTime != null || recurrence?.setsTimes == true) occurrence.time else anchor", "occurrence.time",
         ":data:desktopTest", {"aWholeDayRepeatingTaskFiresAtTheReminderAnchor"}),
        ("a whole-day rule's own times are ignored", REMREPO, " || recurrence?.setsTimes == true", "",
         ":data:desktopTest", {"aWholeDayItemWhoseRuleSetsTimesFiresAtThem"}),
        ("one unreadable rule silences every reminder", REMREPO, "            return@mapNotNull null\n", "            throw IllegalStateException(\"unreadable\")\n",
         ":data:desktopTest", {"aRuleThisVersionCannotReadSilencesOnlyItsOwnReminder"}),
        ("a recurrence column can stand alone", TRIGGERS, "            AND (NEW.window_start IS NOT NULL) = (NEW.recurrence_kind IS 'RANDOM_WINDOW')\n", "",
         ":data:desktopTest", {"noColumnOfARecurrenceKindStandsAlone"}),
        ("a missing month day falls back to the weekday", RRULE,
         "byMonthDay.isNotEmpty() && plainDays.isNotEmpty() -> fromMonthDay.filter { it.dayOfWeek in plainDays }\n        byMonthDay.isNotEmpty() -> fromMonthDay",
         "fromMonthDay.isNotEmpty() && plainDays.isNotEmpty() -> fromMonthDay.filter { it.dayOfWeek in plainDays }\n        fromMonthDay.isNotEmpty() -> fromMonthDay",
         ":core:desktopTest", {"aMonthDayAndAWeekdayMeanBoth"}),
        ("WEEKLY takes BYMONTHDAY and ignores it", RRULE, "            if (frequency == Frequency.WEEKLY && byMonthDay.isNotEmpty()) return null\n", "",
         ":core:desktopTest", {"aRuleThatCouldNeverOccurOrOverflowsIsRefused"}),
        ("a huge interval is taken", RRULE, "n in 1..MAX_INTERVAL", "n >= 1",
         ":core:desktopTest", {"aRuleThatCouldNeverOccurOrOverflowsIsRefused"}),
    ],
}


def run(task):
    module = task.split(":")[1]
    results = "%s/build/test-results/desktopTest" % module
    shutil.rmtree(results, ignore_errors=True)
    with open("mutants.log", "w") as log:
        code = subprocess.call([GRADLEW, "--offline", task], stdout=log, stderr=log)
    failed = set()
    for xml in glob.glob(results + "/*.xml"):
        failed |= set(re.findall(r'testcase name="([^"\[]+)[^"]*"[^>]*>\s*<failure', open(xml, encoding="utf-8").read()))
    return code, failed


def main(slices):
    # Every pattern first: a stale one should stop the run before any build, not halfway through.
    for key in slices:
        for name, path, old, *_ in SLICES[key]:
            assert open(path, encoding="utf-8").read().count(old) == 1, "%s: pattern not found once in %s" % (name, path)
    survivors = []
    for key in slices:
        for name, path, old, new, task, expected in SLICES[key]:
            original = open(path, "rb").read()
            text = original.decode("utf-8")
            try:
                open(path, "wb").write(text.replace(old, new).encode("utf-8"))
                code, failed = run(task)
            finally:
                open(path, "wb").write(original)
            missed = expected - failed
            print("%-36s exit=%d failed: %s%s" % (name, code, ", ".join(sorted(failed)) or "NOTHING",
                                                  "  MISSED: " + ", ".join(sorted(missed)) if missed else ""))
            if missed:
                survivors.append(name)
    for task in sorted({m[4] for key in slices for m in SLICES[key]}):
        code, failed = run(task)
        print("%-36s exit=%d failures: %s" % ("control " + task, code, ", ".join(sorted(failed)) or "none"))
        assert code == 0 and not failed, "control must pass, or no kill above means anything"
    os.remove("mutants.log")
    assert not survivors, "survived: %s" % survivors


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(SLICES))
