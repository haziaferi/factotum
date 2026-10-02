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
EDITS = "core/src/commonMain/kotlin/com/factotum/core/recurrence/OccurrenceEdits.kt"
OCCREPO = "data/src/commonMain/kotlin/com/factotum/data/item/OccurrenceRepository.kt"
PRESENCE = "core/src/commonMain/kotlin/com/factotum/core/habit/HabitPresence.kt"
HABITS = "data/src/commonMain/kotlin/com/factotum/data/item/HabitRepository.kt"
TRACKERS = "data/src/commonMain/kotlin/com/factotum/data/tracker/TrackerRepository.kt"
PLANNER = "core/src/commonMain/kotlin/com/factotum/core/plan/Planner.kt"
DATABASE = "data/src/commonMain/kotlin/com/factotum/data/FactotumDatabase.kt"
EDITCODEC = "data/src/commonMain/kotlin/com/factotum/data/item/OccurrenceEditTable.kt"
TOTALS = "core/src/commonMain/kotlin/com/factotum/core/time/TimeTotals.kt"
TIMEREPO = "data/src/commonMain/kotlin/com/factotum/data/time/TimeRepository.kt"
TIMESPAN = "data/src/commonMain/kotlin/com/factotum/data/time/TimeSpan.kt"
ACTIVITIES = "data/src/commonMain/kotlin/com/factotum/data/time/ActivityRepository.kt"
LABELKEY = "core/src/commonMain/kotlin/com/factotum/core/label/Labels.kt"
LABELS = "data/src/commonMain/kotlin/com/factotum/data/label/LabelRepository.kt"
REGISTRY = "core/src/commonMain/kotlin/com/factotum/core/settings/Settings.kt"
SETTINGS = "data/src/commonMain/kotlin/com/factotum/data/settings/SettingsRepository.kt"
STORES = "data/src/commonMain/kotlin/com/factotum/data/settings/SettingStores.kt"

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
        ("a standalone reminder without a time", TRIGGERS, "            AND (NEW.kind <> 'REMINDER' OR (NEW.start_date IS NOT NULL AND NEW.start_time IS NOT NULL))\n", "",
         ":data:desktopTest", {"aStandaloneReminderNeedsATime"}),
        ("a done item's reminder still fires", REMDAO, " +\n            \"AND (i.status IS NULL OR i.status = 'PENDING')\"", "",
         ":data:desktopTest", {"tendrilQuietWhenDone_aDoneTasksReminderNoLongerFires", "mnemoStandaloneDone_theRowStaysAndStopsFiring"}),
        ("a deleted item's reminder still fires", REMDAO, "AND i.deleted_at IS NULL AND t.deleted_at", "AND t.deleted_at",
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
        ("a resolved occurrence still fires", REMREPO, ".filter { (it.original ?: it.at) !in resolved && !habit.paused(it, timed(it)) }", ".filter { !habit.paused(it, timed(it)) }",
         ":data:desktopTest", {"aResolvedOccurrenceDoesNotFire"}),
        ("a whole-day repeat fires at its occurrence's midnight", REMREPO, "if (timed(o)) o.at.time else blockStart(o) ?: anchor", "o.at.time",
         ":data:desktopTest", {"aWholeDayRepeatingTaskFiresAtTheReminderAnchor"}),
        ("a whole-day rule's own times are ignored", EDITS, " || inForceOn(o.original?.date ?: o.at.date, edits)?.setsTimes == true", "",
         ":data:desktopTest", {"aWholeDayItemWhoseRuleSetsTimesFiresAtThem"}),
        ("one unreadable rule silences every reminder", REMREPO, "        } catch (_: IllegalArgumentException) {\n            return null\n", "        } catch (_: IllegalArgumentException) {\n            throw IllegalStateException(\"unreadable\")\n",
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
    "11": [
        ("edits apply in arrival order", EDITS, "val ordered = edits.sortedBy { it.created }", "val ordered = edits",
         ":core:desktopTest", {"sharedConcurrentMovesOnce_twoMovesOfOneOccurrenceLeaveItOnce"}),
        ("a correction counts as a clash", EDITS, "b.id !in a.seen && a.id !in b.seen &&", "",
         ":core:desktopTest", {"aCorrectionMadeAfterSeeingTheOtherEditIsNoClash"}),
        ("any shared field is a clash", EDITS, "shared.any { a.changes.schedule[it] != b.changes.schedule[it] } &&", "true &&",
         ":core:desktopTest", {"ownerOccurrenceClashAsks_twoRetimesAskAndARetimeAgainstARenameDoesNot"}),
        ("an added occurrence replaces the series one", EDITS, "shown[edit.id] = if (c.skip)", "shown[at] = if (c.skip)",
         ":core:desktopTest", {"anAddedOccurrenceAtASeriesTimeKeepsBoth"}),
        ("an occurrence moved in from outside is lost", EDITS, "(series(from, to) + named)", "series(from, to)",
         ":core:desktopTest", {"anOccurrenceMovedInFromOutsideTheWindowShows"}),
        ("a later-created earlier rule leaves the older running", EDITS, "segments.drop(i + 1).mapNotNull { it.first }.minOrNull()",
         "segments.drop(i + 1).mapNotNull { it.first }.filter { start == null || it > start }.minOrNull()",
         ":core:desktopTest", {"aLaterCreatedRuleWithAnEarlierDateEndsTheEarlierCreatedOne"}),
        ("edits carry no seen ids", OCCREPO, '"seen" to seen.joinToString(",")', '"seen" to ""',
         ":data:desktopTest", {"aRetimeMadeAfterSeeingTheOtherIsACorrectionNotAClash"}),
        ("reminders ignore occurrence edits", REMREPO, 'occurrencesWithEdits(s.itemId, dtstart, "", null, edits, from, to, habit.lastDone)', 'occurrencesWithEdits(s.itemId, dtstart, "", null, emptyList(), from, to, habit.lastDone)',
         ":data:desktopTest", {"aSkippedOccurrenceDoesNotFireAndAMovedOneFiresAtItsNewTime"}),
        ("an undone edit still applies", ITEMDAO, '"SELECT * FROM occurrence_edit WHERE item_id = :itemId AND deleted_at IS NULL"', '"SELECT * FROM occurrence_edit WHERE item_id = :itemId"',
         ":data:desktopTest", {"undoingASkipBringsTheOccurrenceBackEverywhere"}),
        ("edit rules dropped", TRIGGERS, "        OCCURRENCE_EDIT to editRules,\n", "",
         ":data:desktopTest", {"anEditMustNameWhatItsScopeCovers"}),
        ("keep both keeps one", OCCREPO, "                write(question.itemId, \"both-${earlier.id}\", EditScope.EXTRA,", "                if (false) write(question.itemId, \"both-${earlier.id}\", EditScope.EXTRA,",
         ":data:desktopTest", {"keepingBothKeepsTwoOccurrences"}),
        ("an edit reaches occurrences by their original date", EDITS, "if (o != null && edit.reaches(o.at)) shown[key] = change(o, c)",
         "if (o != null && key is LocalDateTime && edit.reaches(key)) shown[key] = change(o, c)",
         ":core:desktopTest", {"fromNowOnReachesOccurrencesWhereTheyAreNow"}),
        ("a confirmed week keeps the series' days", EDITS, "shown.entries.filter { (_, o) -> o != null && confirm.reaches(o.at) }.forEach { shown.remove(it.key) }", "Unit",
         ":core:desktopTest", {"aConfirmedWeekReplacesTheSeriesDaysAndKeepsWhatWasMovedOrAddedThere"}),
        ("a settled clash is asked again", EDITS, " &&\n                    here.none { c -> a.id in c.seen && b.id in c.seen }", "",
         ":core:desktopTest", {"aLaterEditThatHasSeenBothSettlesTheClash"}),
        ("a FROM week pattern is ignored", EDITS, "val weekly = e.changes.weekDays?.takeIf { e.scope == EditScope.FROM }", "val weekly = e.changes.weekDays?.takeIf { false }",
         ":core:desktopTest", {"aNewWeeklyPatternFromADate"}),
        ("an answer undoes instead of correcting", OCCREPO, "        val schedule = kept.changes\n", "        val schedule = EditChanges()\n",
         ":data:desktopTest", {"keepingOneEditsTimeStillMergesTheOthersTitle", "twoDevicesAnsweringDifferentlyAreAskedAgain"}),
        ("keeping both twice makes two", OCCREPO, '"both-${earlier.id}"', "newId()",
         ":data:desktopTest", {"twoDevicesKeepingBothMakeOneAddedOccurrence"}),
        ("an edit can be rewritten", TRIGGERS, "OR NEW.days IS NOT OLD.days OR NEW.changes IS NOT OLD.changes", "OR NEW.days IS NOT OLD.days",
         ":data:desktopTest", {"anEditIsWrittenOnceAndUndoneOnce"}),
        ("completions are kept by day", REMREPO, "map { LocalDateTime.parse(it.occurrence) }.toSet()", "map { LocalDateTime.parse(it.occurrence).date }.toSet().let { days -> days.map { LocalDateTime(it, MIDNIGHT) }.toSet() }",
         ":data:desktopTest", {"twoOccurrencesOnOneDayAreResolvedApart"}),
        ("an added midnight occurrence counts as timed", EDITS, "if (it == null) at.time != MIDNIGHT else", "if (it == null) true else",
         ":data:desktopTest", {"anAddedOccurrenceOnAWholeDayItemFiresAtTheAnchor"}),
    ],
    "06": [
        ("a no counts as presence", PRESENCE, "yes == true || rating != null", "yes != null || rating != null",
         ":core:desktopTest", {"aYesAnyRatingAndANumberAboveZeroCountAndANoDoesNot"}),
        ("a zero counts as presence", PRESENCE, "(number ?: 0.0) > 0.0", "number != null",
         ":core:desktopTest", {"aYesAnyRatingAndANumberAboveZeroCountAndANoDoesNot"}),
        ("the day always starts at midnight", PRESENCE, "if (at.time < dayStart) at.date.plus(-1, DateTimeUnit.DAY) else at.date", "at.date",
         ":core:desktopTest", {"aLogAfterMidnightCountsForYesterdayWhenTheDayStartsLater"}),
        ("a rolling habit ignores its last Log", RECUR, "lastDone?.plus(every, unit) ?: dtstart.date", "dtstart.date",
         ":core:desktopTest", {"aRollingHabitIsDueAPeriodAfterItsLastLog"}),
        ("an overdue rolling habit waits a period", RECUR, "var day = maxOf(due, from.date)", "var day = if (due < from.date) from.date.plus(every, unit) else due",
         ":core:desktopTest", {"anOverdueRollingHabitIsDueToday"}),
        ("a paused habit still shows", OCCREPO, "            .filter { !habit.paused(it, recurrence.timed(it, edits, item.startTime != null)) }\n", "\n",
         ":data:desktopTest", {"tendrilPauseWindow_noOccurrencesWhilePausedAndOnlyHabitsPause"}),
        ("a paused habit still fires", REMREPO, "!in resolved && !habit.paused(it, timed(it)) }", "!in resolved }",
         ":data:desktopTest", {"aPausedHabitsReminderIsQuietUntilThePauseEnds"}),
        ("a Logged occurrence still fires", REMREPO, "habit.unlogged(recurrence.occurrencesWithEdits(", "(recurrence.occurrencesWithEdits(",
         ":data:desktopTest", {"sharedOneReminderPath_aHabitsReminderIsAReminderRowAndQuietOnceLogged"}),
        ("a Log naming nothing quiets the whole day", HABITS, "            if (n > 0) left[day] = n - 1\n            n == 0", "            n == 0 && day !in left",
         ":data:desktopTest", {"aLogNamingNoOccurrenceQuietsOnlyOneOfTheDays"}),
        ("a deleted tracker keeps its habits", TRACKERS, "mapOf(TRACKER to listOf(trackerId), ITEM to habits,", "mapOf(TRACKER to listOf(trackerId), ITEM to emptyList(),",
         ":data:desktopTest", {"deletingATrackerDeletesItsHabitsAndDeletingAHabitKeepsTheTracker"}),
        ("a habit on a tracker deleted elsewhere still fires", REMDAO, "AND t.deleted_at IS NULL ", "",
         ":data:desktopTest", {"aHabitMadeOnATrackerDeletedElsewhereCountsAsDeleted"}),
        ("a purge leaves goals behind", TRACKERS, "        targets.getValue(GOAL).forEach { writes.merger.purge(store, it) }\n", "",
         ":data:desktopTest", {"aTrackersGoalsGoWithIt"}),
        ("a Log of the wrong kind is taken", TRACKERS, "        require(fits) { \"a $type tracker Logs a ${type.lowercase()}\" }\n", "",
         ":data:desktopTest", {"aSecondDailyGoalAChoiceHabitAndAValueOfTheWrongKindAreRefused"}),
        ("undo takes the latest time", TRACKERS, ".maxByOrNull { Stamp(it.hlc, it.device) }", ".maxByOrNull { it.at }",
         ":data:desktopTest", {"undoTakesTheLogMadeLastNotTheLatestTime"}),
        ("tracker rules dropped", TRIGGERS, "        TRACKER to trackerRules,\n", "",
         ":data:desktopTest", {"trackerAndReadingRulesHold"}),
        ("reading rules dropped", TRIGGERS, "        TRACKER_READING to readingRules,\n", "",
         ":data:desktopTest", {"trackerAndReadingRulesHold"}),
        ("a habit needs no tracker", TRIGGERS, "            AND (NEW.tracker_id IS NOT NULL) = (NEW.kind = 'HABIT')\n", "",
         ":data:desktopTest", {"trackerAndReadingRulesHold"}),
        ("any item pauses", TRIGGERS, "            AND (NEW.kind = 'HABIT' OR (NEW.pause_from IS NULL AND NEW.pause_until IS NULL AND NEW.block_id IS NULL AND NEW.duration_min IS NULL))\n", "",
         ":data:desktopTest", {"tendrilPauseWindow_noOccurrencesWhilePausedAndOnlyHabitsPause", "tendrilPlannerFields_aHabitKeepsItsBlockAndLengthAndATaskMayNot"}),
        ("a task may lose its status", TRIGGERS, "            AND (NEW.status IS NULL) = (NEW.kind IN ('EVENT', 'HABIT', 'ACTIVITY'))\n", "",
         ":data:desktopTest", {"aTaskWithoutAStatusIsRefused"}),
    ],
    "06b": [
        ("a block's end is part of it", PLANNER, "t >= it.start && t < it.end", "t >= it.start && t <= it.end",
         ":core:desktopTest", {"aSetTimeAtABlocksStartBelongsToThatBlockAndAtItsEndToTheNext"}),
        ("weekday times ignored", PLANNER, "blocks.map { it.on(d.dayOfWeek) }", "blocks",
         ":core:desktopTest", {"aWeekdayTimeMovesTheBlockOnThatDayOnlyAndALaterOneWins"}),
        ("the first weekday time wins", PLANNER, "overrides.lastOrNull { day in it.days }", "overrides.firstOrNull { day in it.days }",
         ":core:desktopTest", {"aWeekdayTimeMovesTheBlockOnThatDayOnlyAndALaterOneWins"}),
        ("suggestions ignore the week's load", PLANNER, "    habits.forEach { addLoad(it, weekly = false) }\n", "",
         ":core:desktopTest", {"aSuggestionKeepsTheBusiestDayLightest", "onATieForTheBusiestDayTheEvenerWeekWins"}),
        ("no tiebreak by even load", PLANNER, ", { p ->\n                days.sumOf", ", { p -> 0L + 0 * \n                days.sumOf",
         ":core:desktopTest", {"onATieForTheBusiestDayTheEvenerWeekWins"}),
        ("a confirmed week is still suggested", PLANNER, "if (h.confirmed || n == 0)", "if (n == 0)",
         ":core:desktopTest", {"confirmedDaysArePlacedAsConfirmedWhateverTheSuggestionWas"}),
        ("a suggestion leaves no load", PLANNER, "        pick.forEach { load[it] = load.getValue(it) + h.durationMin }\n", "",
         ":core:desktopTest", {"aLaterNAWeekHabitIsSuggestedOnTheLoadTheEarlierOnesLeft"}),
        ("n a day ignores its slots", PLANNER, "return o.original?.let { slots?.getOrNull(it.time.second) } ?: habitBlock", "return habitBlock",
         ":core:desktopTest", {"nADaySpreadsEvenlyOverTheBlocksInTheirOrderOrSitsInTheBlocksItNames"}),
        ("an edit's no-block falls back", PLANNER, "o.block?.let { return it.value }", "o.block?.value?.let { return it }",
         ":core:desktopTest", {"anEditsBlockWinsAndNoBlockMeansAnyTime"}),
        ("an edit's time is ignored", PLANNER, "if (h.setTime || rule?.setsTimes == true || o.ownTime)", "if (h.setTime || rule?.setsTimes == true)",
         ":core:desktopTest", {"anOccurrenceAnEditGaveATimeIsPlacedByThatTime"}),
        ("the day's rule sets no time", PLANNER, "if (h.setTime || rule?.setsTimes == true || o.ownTime)", "if (h.setTime || o.ownTime)",
         ":core:desktopTest", {"aRuleSetFromADateIsTheOnePlacedFromThen"}),
        ("the rule in force is the item's own", EDITS, "Recurrence? = patternsOf(edits.sortedBy { it.created }).ruleOn(day) ?: this", "Recurrence? = this",
         ":core:desktopTest", {"aRuleSetFromADateIsTheOnePlacedFromThen"}),
        ("a confirmed day before the start", EDITS, "if (confirmed >= dtstart && ", "if (",
         ":core:desktopTest", {"aConfirmedDayOutsideTheHabitsDaysOrBeforeItsStartIsNotPlaced"}),
        ("a confirmed day off the habit's days", EDITS, "(rule !is Recurrence.Planned || day in rule.days)", "true",
         ":core:desktopTest", {"aConfirmedDayOutsideTheHabitsDaysOrBeforeItsStartIsNotPlaced"}),
        ("n a day on every day", RECUR, "if (day.dayOfWeek in days) {\n                    for (i in 0 until n)", "if (true) {\n                    for (i in 0 until n)",
         ":core:desktopTest", {"aPlannedDaysOccurrencesHaveNoTimeOfTheirOwnAndOnlyItsDays"}),
        ("no blocks on a new database", TRIGGERS, "    override fun onCreate(connection: SQLiteConnection) = seedBlocks(connection)\n\n", "",
         ":data:desktopTest", {"aNewDatabaseHasTendrilsFiveBlocks", "twoDevicesSeedTheSameBlocksAndAnEditOnOneReachesTheOther"}),
        ("no blocks on an upgrade", DATABASE, "onPostMigrate(connection: SQLiteConnection) = seedBlocks(connection)", "onPostMigrate(connection: SQLiteConnection) = Unit",
         ":data:desktopTest", {"aDatabaseUpgradedToTimeBlocksGetsTheDefaults"}),
        ("named blocks need not match n", TRIGGERS, "+ 1 = NEW.plan_n", "+ 1 > 0",
         ":data:desktopTest", {"plannedAndBlockRulesHold"}),
        ("empty block ids", TRIGGERS, "\n                        AND instr(',' || NEW.plan_blocks || ',', ',,') = 0", "",
         ":data:desktopTest", {"plannedAndBlockRulesHold"}),
        ("n a day with a set time", TRIGGERS, " AND NEW.start_time IS NULL\n", "\n",
         ":data:desktopTest", {"plannedAndBlockRulesHold"}),
        ("a task may be planned", TRIGGERS, "NOT IN ('ROLLING', 'PLANNED')", "NOT IN ('ROLLING')",
         ":data:desktopTest", {"plannedAndBlockRulesHold"}),
        ("block rules dropped", TRIGGERS, "        HABIT_BLOCK to blockRules,\n", "",
         ":data:desktopTest", {"plannedAndBlockRulesHold"}),
        ("a paused habit is planned", HABITS, "\n                    .filter { o -> !state.paused(o, recurrence.timed(o, mine, h.startTime != null)) },", ",",
         ":data:desktopTest", {"aPausedHabitAndOneWhoseTrackerIsDeletedAreNotPlanned"}),
        ("a paused day is suggested", HABITS, " && !state.pausedOn(d) &&", " &&",
         ":data:desktopTest", {"aSuggestionAvoidsTheDaysOtherHabitsFillAndThePausedOnes"}),
        ("a skipped day is suggested", HABITS, "mine.none { it.changes.skip && it.reaches(LocalDateTime(d, start.time)) }", "true",
         ":data:desktopTest", {"aSuggestionAvoidsTheDaysOtherHabitsFillAndThePausedOnes"}),
        ("a whole-day occurrence counts for the day before", HABITS, "if (timed) dayOf(o.at, dayStart) else o.at.date", "dayOf(o.at, dayStart)",
         ":data:desktopTest", {"aWholeDayOccurrenceIsPausedOnItsOwnDateWhenTheDayStartsLater"}),
        ("any week's confirmation counts", HABITS, "it.scope == EditScope.WEEK && it.date == monday && ", "it.scope == EditScope.WEEK && ",
         ":data:desktopTest", {"anNAWeekHabitIsSuggestedUntilThisWeekIsConfirmedThenPlaced"}),
        ("habits on one tracker share a pause", HABITS, "pauseFrom = h.pauseFrom?.let(LocalDate::parse)", "pauseFrom = habits.last { it.trackerId == h.trackerId }.pauseFrom?.let(LocalDate::parse)",
         ":data:desktopTest", {"twoHabitsOnOneTrackerPauseOnTheirOwn"}),
        ("an edit's block is not written", EDITCODEC, '        c.block?.let { fields["block"] = JsonPrimitive(it.value) }\n', "",
         ":data:desktopTest", {"anOccurrencesBlockTravelsInItsEditAndNoneMeansAnyTime"}),
        ("no block reads as unchanged", EDITCODEC, 'o["block"]?.jsonPrimitive?.let { Patch(it.contentOrNull) }', 'o["block"]?.jsonPrimitive?.contentOrNull?.let { Patch(it) }',
         ":data:desktopTest", {"anOccurrencesBlockTravelsInItsEditAndNoneMeansAnyTime"}),
        ("n a day reminds at the anchor", REMREPO, "blockStart(o) ?: anchor", "anchor",
         ":data:desktopTest", {"anNADayHabitRemindsAtTheStartOfEachOfItsBlocks", "aLoggedOccurrenceIsQuietAndABlocksOwnDayAndOrderAreFollowed"}),
        ("reminders ignore a block's weekday times", REMREPO, "?.on(o.at.dayOfWeek)?.let", "?.let",
         ":data:desktopTest", {"aLoggedOccurrenceIsQuietAndABlocksOwnDayAndOrderAreFollowed"}),
        ("firings taken in occurrence order", REMREPO, ".filter { (after == null || it > after) && it != skip }\n                    .minOrNull()",
         ".firstOrNull { (after == null || it > after) && it != skip }",
         ":data:desktopTest", {"aLoggedOccurrenceIsQuietAndABlocksOwnDayAndOrderAreFollowed"}),
        ("the search starts at the last firing", REMREPO, "LocalDateTime(it.date.plus(-back, DateTimeUnit.DAY), MIDNIGHT)",
         "LocalDateTime(it.date.plus(-(s.offsetMin.floorDiv(MINUTES_PER_DAY) + 1), DateTimeUnit.DAY), it.time)",
         ":data:desktopTest", {"aWholeDayItemRemindedBeforeItsAnchorStillFiresLaterThatDay", "anNADayHabitRemindsAtTheStartOfEachOfItsBlocks"}),
    ],
    "07": [
        ("overlaps counted twice", TOTALS, "val from = reached?.let { maxOf(it, start) } ?: start", "val from = start",
         ":core:desktopTest", {"overlappingSpansCountOnceAndApartOnesAddUp"}),
        ("a span counts for the day it ends", TOTALS, "spans.groupBy { dayOf(it.start, dayStart) }", "spans.groupBy { dayOf(it.end ?: now, dayStart) }",
         ":core:desktopTest", {"aSpanCountsWhollyForTheDayItStarted"}),
        ("the goal week starts on Sunday", TOTALS, "today.plus(1 - today.dayOfWeek.isoDayNumber, DateTimeUnit.DAY)", "today.plus(-today.dayOfWeek.isoDayNumber, DateTimeUnit.DAY)",
         ":core:desktopTest", {"goalWindowsAreTheDayTheWeekFromMondayTheMonthFromThe1stAndAMilestones400Days"}),
        ("a kept timer is asked again at once", TOTALS, "secondsBetween(maxOf(span.start, keptAt ?: span.start), now)", "secondsBetween(span.start, now)",
         ":core:desktopTest", {"aTimerIsAskedAboutPastTwelveHoursAndAgainTwelveHoursAfterItWasKept"}),
        ("habits in a block by id only", PLANNER, "compareBy<Placed>({ it.sortOrder }, { it.itemId },", "compareBy<Placed>({ it.itemId },",
         ":core:desktopTest", {"habitsInABlockFollowTheirManualOrderThenTheirId"}),
        ("finishing a task leaves its timer", REPO, "TIME_SPAN to if (status == TaskStatus.PENDING) emptyList() else times.runningOf(listOf(id))", "TIME_SPAN to emptyList<String>()",
         ":data:desktopTest", {"finishingOrDeletingATaskOrHabitStopsItsTimerAndALogDoesNot"}),
        ("deleting a task leaves its timer", REPO, "mapOf(ITEM to ids, TIME_SPAN to times.runningOf(ids))", "mapOf(ITEM to ids, TIME_SPAN to emptyList())",
         ":data:desktopTest", {"finishingOrDeletingATaskOrHabitStopsItsTimerAndALogDoesNot"}),
        ("resolving any occurrence stops today's timer", REPO, ", occurrence = occurrence.date)", ")",
         ":data:desktopTest", {"resolvingAPastOccurrenceLeavesTodaysTimerRunning"}),
        ("deleting a tracker leaves its habits' timers", TRACKERS, "TIME_SPAN to times.runningOf(habits))", "TIME_SPAN to emptyList())",
         ":data:desktopTest", {"finishingOrDeletingATaskOrHabitStopsItsTimerAndALogDoesNot"}),
        ("no sweep after an import", FOLDER, ".also { afterImport() }", "",
         ":data:desktopTest", {"aTaskFinishedOnAnotherDeviceStopsTheTimerHereWhenItArrives"}),
        ("keep rewrites the span's end", TIMEREPO, 'store.put(row.edit(KEPT, clock.tick(), mapOf("kept_at" to seconds(at))))',
         'store.put(row.edit(KEPT, clock.tick(), mapOf("kept_at" to seconds(at))).edit(END, clock.tick(), mapOf("ended_at" to null)))',
         ":data:desktopTest", {"aStaleKeepOrStartEditDoesNotReopenOrReviveASpan"}),
        ("an edit rewrites the end", TIMEREPO, 'set(END, "ended_at", end?.let(::seconds))', 'edited = edited.edit(END, s, mapOf("ended_at" to end?.let(::seconds)))',
         ":data:desktopTest", {"aCommentWrittenOnOneDeviceDoesNotReopenATimerStoppedOnAnother"}),
        ("an edit rewrites deletion", TIMEREPO, 'set(START, "started_at", seconds(start))', 'set(START, "started_at", seconds(start)); edited = edited.edit(GONE, s, mapOf("deleted_at" to null))',
         ":data:desktopTest", {"aStaleKeepOrStartEditDoesNotReopenOrReviveASpan"}),
        ("a deleted span is edited", TIMEREPO, '            require(row.value(GONE, "deleted_at") == null) { "span $spanId is deleted" }\n', "",
         ":data:desktopTest", {"aDeletedSpanOrOneOnADeletedOwnerIsNotEditedAndDeletingTwiceChangesNothing"}),
        ("a stopped span is kept", TIMEREPO, 'require(row.value(END, "ended_at") == null && row.value(GONE, "deleted_at") == null) { "span $spanId is not running" }', "Unit",
         ":data:desktopTest", {"endingAtTheLimitCountsFromTheLastKeep"}),
        ("the limit ignores a keep", TIMEREPO, "maxOf(span.start, span.keptAt ?: span.start).toInstant", "span.start.toInstant",
         ":data:desktopTest", {"endingAtTheLimitCountsFromTheLastKeep"}),
        ("deleting twice restamps", TIMEREPO, 'if (row.value(GONE, "deleted_at") == null) {', "if (true) {",
         ":data:desktopTest", {"aDeletedSpanOrOneOnADeletedOwnerIsNotEditedAndDeletingTwiceChangesNothing"}),
        ("totals ignore a later day start", TIMEREPO, "LocalDateTime(days.max().plus(1, DateTimeUnit.DAY), dayStart)", "LocalDateTime(days.max().plus(1, DateTimeUnit.DAY), MIDNIGHT)",
         ":data:desktopTest", {"aPersonalDayStartingLaterCountsAnEarlySpanForTheDayBefore"}),
        ("a deleted owner's time counts", TIMESPAN, "\"WHERE s.deleted_at IS NULL AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') \" +\n            \"AND s.started_at",
         "\"WHERE s.deleted_at IS NULL AND t.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') \" +\n            \"AND s.started_at",
         ":data:desktopTest", {"aDeletedOwnerOrADeletedTrackersHabitDropsOutOfTotals"}),
        ("a deleted tracker's habit counts", TIMESPAN, "\"WHERE s.deleted_at IS NULL AND i.deleted_at IS NULL AND t.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') \" +\n            \"AND s.started_at",
         "\"WHERE s.deleted_at IS NULL AND i.deleted_at IS NULL AND i.kind IN ('TASK', 'HABIT', 'ACTIVITY') \" +\n            \"AND s.started_at",
         ":data:desktopTest", {"aHabitMadeOnATrackerDeletedElsewhereDropsOutOfTotals"}),
        ("an activity may be purged", REPO, '        require(dao.items(listOf(id)).singleOrNull()?.kind != ItemKind.ACTIVITY.name) { "an activity is deleted, never deleted forever" }\n', "",
         ":data:desktopTest", {"chronicleActivityDeleteRefused_anActivityIsNeverDeletedForGoodButIsDeletedWithItsTime"}),
        ("an activity row may be deleted", TRIGGERS, "BEFORE DELETE ON item WHEN OLD.kind = 'ACTIVITY' ", "BEFORE DELETE ON item WHEN 0 ",
         ":data:desktopTest", {"chronicleActivityDeleteRefused_anActivityIsNeverDeletedForGoodButIsDeletedWithItsTime"}),
        ("deleting an activity leaves its time", ACTIVITIES, '        for (span in targets.getValue(TIME_SPAN)) store.put(requireNotNull(store.row(span)).edit(GONE, s, mapOf("deleted_at" to s.hlc)))\n', "",
         ":data:desktopTest", {"chronicleActivityDeleteRefused_anActivityIsNeverDeletedForGoodButIsDeletedWithItsTime"}),
        ("a span on any kind", TRIGGERS, """private val spanRules = "COALESCE((SELECT kind FROM item WHERE id = NEW.item_id) IN ('TASK', 'HABIT', 'ACTIVITY'), 1)\"""", """private val spanRules = "1\"""",
         ":data:desktopTest", {"tendrilExactlyOneOwner_aSpanHasOneOwnerOfAKindThatIsTimed"}),
        ("a span moves owner", TRIGGERS, "BEFORE UPDATE ON time_span WHEN NEW.item_id IS NOT OLD.item_id ", "BEFORE UPDATE ON time_span WHEN 0 ",
         ":data:desktopTest", {"tendrilExactlyOneOwner_aSpanHasOneOwnerOfAKindThatIsTimed"}),
        ("icons on any item", TRIGGERS, "            AND (NEW.kind = 'ACTIVITY' OR (NEW.icon IS NULL AND NEW.color IS NULL))\n", "",
         ":data:desktopTest", {"activitiesArchiveAndKeepTheirOrderAndTheirColumnsStayTheirs"}),
        ("archived on any item", TRIGGERS, "            AND (NEW.archived IS NOT NULL) = (NEW.kind = 'ACTIVITY')\n", "",
         ":data:desktopTest", {"activitiesArchiveAndKeepTheirOrderAndTheirColumnsStayTheirs"}),
        ("a task has a manual order", TRIGGERS, "            AND (NEW.sort_order IS NULL OR NEW.kind IN ('ACTIVITY', 'HABIT'))\n", "",
         ":data:desktopTest", {"activitiesArchiveAndKeepTheirOrderAndTheirColumnsStayTheirs"}),
        ("an activity has dates", TRIGGERS, "\n            AND (NEW.kind <> 'ACTIVITY' OR (NEW.start_date IS NULL AND NEW.start_time IS NULL AND NEW.due_date IS NULL AND NEW.recurrence_kind IS NULL))", "",
         ":data:desktopTest", {"activitiesArchiveAndKeepTheirOrderAndTheirColumnsStayTheirs"}),
    ],
    "08": [
        ("names compare with case", LABELKEY, "fun nameKey(name: String): String = name.trim().lowercase()", "fun nameKey(name: String): String = name.trim()",
         ":core:desktopTest", {"namesCompareIgnoringCaseAndOuterSpaces"}),
        ("names compare in any Unicode form", LABELS, "internal fun labelKey(name: String): String = nameKey(nfc(name))", "internal fun labelKey(name: String): String = nameKey(name)",
         ":data:desktopTest", {"aNameStoredInAnotherUnicodeFormStillCountsAsTheSameName"}),
        ("a new label's colour is not its name's", LABELS, "(color ?: colorForName(clean))", "(color ?: 0L)",
         ":data:desktopTest", {"namesAreUniqueIgnoringCaseAndANewLabelTakesItsColourFromItsName"}),
        ("names need not be unique", LABELS, 'require(dao.liveLabels().none { it.id != except && labelKey(it.name) == labelKey(clean) }) { "there is already a label \\"$clean\\"" }', "Unit",
         ":data:desktopTest", {"namesAreUniqueIgnoringCaseAndANewLabelTakesItsColourFromItsName"}),
        ("a dead label is edited", LABELS, "        live(id)\n        check()\n", "        check()\n",
         ":data:desktopTest", {"deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited"}),
        ("the merge keeps the one made last", LABELS, "val first = same.minOf { it.id }", "val first = same.maxOf { it.id }",
         ":data:desktopTest", {"twoLabelsOfOneNameMadeApartMergeIntoTheOneMadeFirstWithWhatCarriedThem", "aRenameOntoAnotherDevicesNameMergesTheSameWay"}),
        ("labels never merge", LABELS, "if (into.isEmpty()) return@write", "return@write",
         ":data:desktopTest", {"twoLabelsOfOneNameMadeApartMergeIntoTheOneMadeFirstWithWhatCarriedThem", "aRenameOntoAnotherDevicesNameMergesTheSameWay"}),
        ("a merged label reads as none", LABELS, "{ it.mergedInto?.let(byId::get) }", "{ null }",
         ":data:desktopTest", {"aMergeChainReadsToItsEndAndAChainEndingInADeletedLabelReadsAsNone", "somethingLabelledOnAPeerThatHadNotSeenTheMergeReadsAsTheSurvivor"}),
        ("deleting leaves what carried merged labels", LABELS, "val same = dao.allLabels().let { all -> val r = resolver(all); all.map { it.id }.filter { r(it) == id } }", "val same = listOf(id)",
         ":data:desktopTest", {"deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited"}),
        ("deleting leaves what carried it", LABELS, '            store.put(requireNotNull(store.row(member)).edit(LABELLED, s, mapOf("label_id" to null)))\n', "",
         ":data:desktopTest", {"deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited"}),
        ("a label outside its scope is set", LABELS, '        require(applies == LabelScope.ALL || applies == scope) { "label ${label.name} is not offered here" }\n', "",
         ":data:desktopTest", {"chronicleAppliesToScope_aLabelIsOfferedOnlyWhereItAppliesAndNarrowingHides"}),
        ("a habit is offered activity labels", LABELS, "if (kind == ItemKind.ACTIVITY) LabelScope.ACTIVITY else LabelScope.ALL", "LabelScope.ACTIVITY",
         ":data:desktopTest", {"chronicleAppliesToScope_aLabelIsOfferedOnlyWhereItAppliesAndNarrowingHides"}),
        ("a task is labelled", LABELS, '        require(kind == ItemKind.ACTIVITY || kind == ItemKind.HABIT) { "a ${item.kind} carries no label" }\n', "",
         ":data:desktopTest", {"chronicleOneCategoryPerRow_aSecondLabelReplacesTheFirstAndAnyKindElseCarriesNone"}),
        ("any item carries a label", TRIGGERS, "            AND (NEW.label_id IS NULL OR NEW.kind IN ('ACTIVITY', 'HABIT'))\n", "",
         ":data:desktopTest", {"chronicleOneCategoryPerRow_aSecondLabelReplacesTheFirstAndAnyKindElseCarriesNone"}),
        ("label rules dropped", TRIGGERS, "        LABEL to labelRules,\n", "",
         ":data:desktopTest", {"chronicleAppliesToScope_aLabelIsOfferedOnlyWhereItAppliesAndNarrowingHides"}),
        ("a label's total is everything's", TIMEREPO, "dao.counted(from, to, itemId, labelIds != null, labelIds.orEmpty())", "dao.counted(from, to, itemId, false, labelIds.orEmpty())",
         ":data:desktopTest", {"chronicleActivityAndCategoryTotals_40MinutesOfReadingTotal40ForLeisure"}),
        ("a label's total leaves out labels merged into it", TIMEREPO, "all.map { it.id }.filter { r(it) == id }", "listOf(id)",
         ":data:desktopTest", {"deletingASurvivorClearsWhatCarriedTheLabelsMergedIntoItAndADeadLabelIsNotEdited"}),
        ("an activity shows a merged label as stored", ACTIVITIES, "it.sortOrder, label(it.labelId))", "it.sortOrder, it.labelId)",
         ":data:desktopTest", {"somethingLabelledOnAPeerThatHadNotSeenTheMergeReadsAsTheSurvivor"}),
        ("a label reads as stored", LABELS, "suspend fun labelOf(itemId: String): String? = items.items(listOf(itemId)).singleOrNull()?.labelId.let(resolver(dao.allLabels()))",
         "suspend fun labelOf(itemId: String): String? = items.items(listOf(itemId)).singleOrNull()?.labelId",
         ":data:desktopTest", {"somethingLabelledOnAPeerThatHadNotSeenTheMergeReadsAsTheSurvivor", "aMergeWritesNothingOnWhatCarriedTheMergedLabelSoAChoiceMadeMeanwhileStands"}),
        ("triggers kept on an upgrade", OPEN, ".also(::dropTriggersBeforeUpgrade)", "",
         ":data:desktopTest", {"aVersion9DatabaseKeepsItsItemsAndTrackersWhenLabelsArrive"}),
    ],
    "09": [
        ("a restore stamps personal values anew", SETTINGS, "Group(Stamp(v.hlc, v.device), mapOf(VALUE to v.value))", "Group(clock.tick(), mapOf(VALUE to v.value))",
         ":data:desktopTest", {"anOldBackupNeverOutranksANewerPersonalValue"}),
        ("a restore writes device state", SETTINGS, "it.scope == SettingScope.DEVICE_PREF && it !== Settings.APP_LOCK", "it.scope != SettingScope.SECRET && it !== Settings.APP_LOCK",
         ":data:desktopTest", {"sharedFirstRunNotRestored_aNewPhoneAsksItsFirstRunQuestions", "mnemoFolderNotRestored_aRestoredPhoneDoesNotInheritTheFolderGrant"}),
        ("a restore turns the lock on", SETTINGS, " && it !== Settings.APP_LOCK }", " }",
         ":data:desktopTest", {"appLockIsPerDeviceAndNeverOnWithoutThisDevicesPin"}),
        ("the lock goes on without a PIN", SETTINGS, 'if (setting === Settings.APP_LOCK && value == true) require(get(Settings.APP_LOCK_PIN).isNotEmpty()) { "set this device\'s PIN before the lock" }', "Unit",
         ":data:desktopTest", {"appLockIsPerDeviceAndNeverOnWithoutThisDevicesPin"}),
        ("a backup carries device state", SETTINGS, "device = Settings.all.filter { it.scope == SettingScope.DEVICE_PREF }", "device = Settings.all.filter { it.scope != SettingScope.SECRET && it.scope != SettingScope.PERSONAL }",
         ":data:desktopTest", {"chronicleDeviceIdOwn_theDeviceIdIsNoSettingAndRidesInNoBackup"}),
        ("personal settings read from the device", SETTINGS, "SettingScope.PERSONAL -> dao.settings(listOf(settingId(setting.key))).singleOrNull()?.value", "SettingScope.PERSONAL -> dao.deviceValue(setting.key)",
         ":data:desktopTest", {"equipoisePersonalTravels_theThresholdAndContactsReachEveryDeviceAndTheRestoredPhone"}),
        ("a default is stored", SETTINGS, "if (value == setting.default) null else setting.encode(value)", "setting.encode(value)",
         ":data:desktopTest", {"aPersonalSettingChangedOnTwoDevicesKeepsTheLaterAndTheDefaultClearsIt"}),
        ("a restore pins a default", SETTINGS, "value.takeUnless { setting.decode(it) == setting.default }", "value",
         ":data:desktopTest", {"aRestoreClearsADevicePreferenceThatIsTheDefault"}),
        ("an unreadable day start is used", REGISTRY, "{ runCatching { LocalTime.parse(it) }.getOrNull() }", "{ LocalTime.parse(it) }",
         ":data:desktopTest", {"aValueThatDoesNotReadReadsAsTheDefaultAndOneOutOfRangeIsRefused"}),
        ("a zero timer limit is taken", REGISTRY, "v.toIntOrNull()?.takeIf { it >= 1 }?.hours", "v.toIntOrNull()?.takeIf { it >= 0 }?.hours",
         ":data:desktopTest", {"aValueThatDoesNotReadReadsAsTheDefaultAndOneOutOfRangeIsRefused"}),
        ("setting ids unmarked", STORES, 'internal fun settingId(key: String) = "setting:$key"', "internal fun settingId(key: String) = key",
         ":data:desktopTest", {"aPersonalSettingChangedOnTwoDevicesKeepsTheLaterAndTheDefaultClearsIt"}),
        ("the AI key syncs", REGISTRY, 'val AI_KEY = text("ai_key", SettingScope.SECRET)', 'val AI_KEY = text("ai_key", SettingScope.PERSONAL)',
         ":data:desktopTest", {"tendrilSecretNeverLeaves_theAiKeyIsInNoFolderBackupOrOtherDevice"}),
        ("the window frame syncs", REGISTRY, 'val WINDOW_FRAME = text("window_frame", SettingScope.DEVICE_STATE)', 'val WINDOW_FRAME = text("window_frame", SettingScope.PERSONAL)',
         ":data:desktopTest", {"tendrilLayoutPerDevice_aWindowFrameReachesNoOtherDevice"}),
        ("one key for two secrets", REGISTRY, 'text("llm_endpoint_key", SettingScope.SECRET)', 'text("ai_key", SettingScope.SECRET)',
         ":data:desktopTest", {"tendrilSecretNeverLeaves_theAiKeyIsInNoFolderBackupOrOtherDevice"}),
        ("totals ignore the day-start setting", TIMEREPO, "        val dayStart = personal.dayStart()\n", "        val dayStart = MIDNIGHT\n",
         ":data:desktopTest", {"theDayStartSetOnOneDeviceDecidesTheDayOnAnotherAtOnce"}),
        ("timers ignore the limit setting", TIMEREPO, "        val limit = personal.longRun()\n", "        val limit = com.factotum.core.time.LONG_RUN\n",
         ":data:desktopTest", {"theLongTimerLimitIsOneSettingForEveryDevice"}),
        ("a recovered device skips its own files", FOLDER, "(owner != device || readOwn)", "owner != device",
         ":data:desktopTest", {"aDeviceWhoseDatabaseWasRecoveredGetsItsSettingsBackFromItsOwnFiles"}),
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
