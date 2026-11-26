#!/usr/bin/env bash
# SPEC:R61, R196, R197: the device tests, on one device named by its adb serial, never on every
# device attached (Gradle's connected tasks run on all of them, phones included).
#   tools/device/run.sh emulator-5554
# It leaves the device as it found it: the test app is uninstalled at the end, and the device's
# own log is read, not cleared.
set -u
export MSYS_NO_PATHCONV=1  # Git Bash on Windows must pass device paths and arguments as written
SERIAL="${1:?give the adb serial of the device to test on}"
cd "$(dirname "$0")/../.."
SDK="${ANDROID_HOME:-${LOCALAPPDATA:-}/Android/Sdk}"
ADB="$SDK/platform-tools/adb"
[ -x "$ADB" ] || [ -x "$ADB.exe" ] || ADB="$(command -v adb)" || { echo "no adb: set ANDROID_HOME"; exit 1; }
adb() { "$ADB" -s "$SERIAL" "$@"; }
PKG=com.hazia.factotum.data.test
RUNNER="$PKG/androidx.test.runner.AndroidJUnitRunner"
mkdir -p build-logs

./gradlew :data:assembleAndroidDeviceTest > build-logs/device-assemble.log 2>&1 || { echo "BUILD FAILED: build-logs/device-assemble.log"; exit 1; }
adb install -r -t data/build/outputs/apk/androidTest/data-androidTest.apk > /dev/null || exit 1
# The test app goes when the run ends, however it ends, with any alarm a stopped run left set.
trap 'adb uninstall "$PKG" > /dev/null 2>&1' EXIT
echo "device: $(adb shell getprop ro.product.model | tr -d '\r'), API $(adb shell getprop ro.build.version.sdk | tr -d '\r')"
# Only this run's lines are read back.
SINCE="$(adb shell date "'+%m-%d %H:%M:%S.000'" | tr -d '\r')"
reported() { adb logcat -d -T "$SINCE" -s FactotumDevice:I | tr -d '\r' | grep -v "^---------" | sed 's/^.*FactotumDevice: //'; }

run() { adb shell am instrument -w -r "$@" "$RUNNER" | tr -d '\r'; }
status=0
# A test whose assumption failed counts as OK in the summary: a step that ran is checked by the line it reports.
expect() { reported | grep -q "^$1" || { echo "MISSING: no '$1' line, so that step did not run"; status=1; }; }

# R196 and R197: every test that runs in one pass.
out=$(run -e class com.hazia.factotum.data.TriggersOnDeviceTest,com.hazia.factotum.data.search.SearchIndexOnDeviceTest)
echo "$out" | grep -E "^OK|^FAILURES|^Tests run|INSTRUMENTATION_STATUS: stack=" || true
echo "$out" | grep -q "^OK (" || status=1
expect "R196 triggers="
expect "R197 sqlite="

# R61: each step its own run; a force-stop ends the process it stops.
T=com.hazia.factotum.data.ForceStopOnDeviceTest
step() { local r; r=$(run -e r61 "$1" -e class "$T#$2"); echo "$1: $(echo "$r" | grep -E "^OK|^FAILURES|shortMsg" | head -1)"; [ "$3" = check ] && { echo "$r" | grep -q "^OK (" || { echo "$r" | grep "stack=" | head -3; status=1; }; }; }
step arm armThenFinish check; sleep 2
step read-finished theNextStartReadsWhatHappened check; expect "R61 read-finished:"
step arm armThenFinish check; sleep 2
adb shell am force-stop "$PKG"; sleep 2
step read-stopped-idle theNextStartReadsWhatHappened check; expect "R61 read-stopped-idle:"
step arm-and-stop armThenForceStop crash; sleep 2
step read-stopped theNextStartReadsWhatHappened check; expect "R61 read-stopped:"

echo "--- reported"
reported
exit $status
