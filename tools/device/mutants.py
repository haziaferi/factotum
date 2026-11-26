"""SPEC:R196, R197: the device tests' fail-before check. Each mutant breaks one install the tests
claim to check, the tests run on one device, and the mutant counts as killed only if every test
named for it fails; the file is restored whatever happens. A control run with no mutant must pass.

    python tools/device/mutants.py emulator-5554
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SDK = os.environ.get("ANDROID_HOME") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk")
ADB = os.path.join(SDK, "platform-tools", "adb")
PKG = "com.hazia.factotum.data.test"
CLASSES = "com.hazia.factotum.data.TriggersOnDeviceTest,com.hazia.factotum.data.search.SearchIndexOnDeviceTest"
TRIGGERS = "data/src/commonMain/kotlin/com/hazia/factotum/data/SchemaTriggers.kt"

MUTANTS = [
    ("the rule and outbox triggers are not installed", TRIGGERS, "        statements.forEach(connection::execSQL)\n", "",
     {"everyTriggerTheOpenMakesIsThere", "aRuleTriggerRefusesARowThatBreaksItsRules", "aSpanStaysOnItsOwner", "aRawWriteReachesTheOutboxAndTheIndex"}),
    ("the search triggers are not installed", TRIGGERS, "        searchTriggers.forEach(connection::execSQL)\n", "",
     {"everyTriggerTheOpenMakesIsThere", "aRawWriteReachesTheOutboxAndTheIndex", "accentsAndCaseFoldAndTheIndexFollowsEveryWrite"}),
    ("a delete leaves its index entry", "data/src/commonMain/kotlin/com/hazia/factotum/data/search/SearchIndex.kt",
     '"CREATE TRIGGER ${s.table}_search_update AFTER UPDATE OF ${s.watched.joinToString(", ")} ON ${s.table} BEGIN ${s.remove("OLD")} ${s.add()} END"',
     '"CREATE TRIGGER ${s.table}_search_update AFTER UPDATE OF ${s.watched.joinToString(", ")} ON ${s.table} WHEN NEW.deleted_at IS NULL BEGIN ${s.remove("OLD")} ${s.add()} END"',
     {"accentsAndCaseFoldAndTheIndexFollowsEveryWrite"}),
    # Made once when the file is made, not on every open: a fresh database still has them all.
    ("the triggers are made only with the file", TRIGGERS,
     "    override fun onCreate(connection: SQLiteConnection) = seedBlocks(connection)\n\n"
     "    override fun onOpen(connection: SQLiteConnection) {\n        statements.forEach(connection::execSQL)\n",
     "    override fun onCreate(connection: SQLiteConnection) { seedBlocks(connection); statements.forEach(connection::execSQL) }\n\n"
     "    override fun onOpen(connection: SQLiteConnection) {\n",
     {"theNextOpenMakesADroppedTriggerAgain"}),
]


def device_failures(serial):
    """Builds and installs the device tests, runs them, and returns (ran, failed test names)."""
    gradle = os.path.join(ROOT, "gradlew.bat" if os.name == "nt" else "gradlew")
    os.makedirs(os.path.join(ROOT, "build-logs"), exist_ok=True)
    with open(os.path.join(ROOT, "build-logs", "device-mutant-build.log"), "w") as log:
        if subprocess.call([gradle, ":data:assembleAndroidDeviceTest"], cwd=ROOT, stdout=log, stderr=log) != 0:
            return 0, {"<build failed>"}
    apk = os.path.join(ROOT, "data", "build", "outputs", "apk", "androidTest", "data-androidTest.apk")
    subprocess.check_call([ADB, "-s", serial, "install", "-r", "-t", apk], stdout=subprocess.DEVNULL)
    out = subprocess.run([ADB, "-s", serial, "shell", "am", "instrument", "-w", "-r", "-e", "class", CLASSES,
                          PKG + "/androidx.test.runner.AndroidJUnitRunner"], capture_output=True, text=True).stdout
    ran, failed, test = 0, set(), None
    for line in out.replace("\r", "").splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: test="):
            test = line.split("=", 1)[1]
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = int(line.split(": ", 1)[1])
            if code in (0, -2, -3, -4):
                ran += 1
            if code == -2:
                failed.add(test)
    return ran, failed


def main(serial):
    survived = 0
    for name, path, before, after, expected in MUTANTS:
        full = os.path.join(ROOT, path)
        with open(full, encoding="utf-8", newline="") as f:
            original = f.read()
        assert original.count(before) == 1, "%s: pattern found %d times" % (name, original.count(before))
        try:
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(original.replace(before, after))
            ran, failed = device_failures(serial)
        finally:
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(original)
        killed = expected <= failed
        survived += not killed
        print("%-48s %s ran=%d failed: %s" % (name, "killed" if killed else "SURVIVED", ran, ", ".join(sorted(failed)) or "none"))
    ran, failed = device_failures(serial)
    print("%-48s %s ran=%d failed: %s" % ("control", "ok" if not failed and ran else "FAILED", ran, ", ".join(sorted(failed)) or "none"))
    subprocess.call([ADB, "-s", serial, "uninstall", PKG], stdout=subprocess.DEVNULL)
    return 1 if survived or failed or not ran else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
