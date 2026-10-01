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
        ("the clock is not saved with a write", REPO, "                sync.saveClock(clock)\n", "",
         ":data:desktopTest", {"eachWriteSavesTheClockWithIt"}),
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
