#!/usr/bin/env bash
# SPEC:R61, R196, R197: the device tests, on one device named by its adb serial, never on every
# device attached (Gradle's connected tasks run on all of them, phones included).
#   tools/device/run.sh emulator-5554
set -u
SERIAL="${1:?give the adb serial of the device to test on}"
cd "$(dirname "$0")/../.."
SDK="${ANDROID_HOME:-$LOCALAPPDATA/Android/Sdk}"
adb() { "$SDK/platform-tools/adb" -s "$SERIAL" "$@"; }
PKG=com.hazia.factotum.data.test
RUNNER="$PKG/androidx.test.runner.AndroidJUnitRunner"

./gradlew --offline :data:assembleAndroidDeviceTest > build-logs/device-assemble.log 2>&1 || { echo "BUILD FAILED: build-logs/device-assemble.log"; exit 1; }
adb install -r -t data/build/outputs/apk/androidTest/data-androidTest.apk > /dev/null || exit 1
echo "device: $(adb shell getprop ro.product.model | tr -d '\r'), API $(adb shell getprop ro.build.version.sdk | tr -d '\r')"
adb logcat -c

run() { adb shell am instrument -w -r "$@" "$RUNNER" | tr -d '\r'; }
status=0
# R196 and R197: every test that runs in one pass.
out=$(run -e class com.hazia.factotum.data.TriggersOnDeviceTest,com.hazia.factotum.data.search.SearchIndexOnDeviceTest)
echo "$out" | grep -E "^INSTRUMENTATION_CODE|^OK|^FAILURES|^Tests run|INSTRUMENTATION_STATUS: test=|INSTRUMENTATION_STATUS: stack=" | grep -v "INSTRUMENTATION_STATUS: test=" || true
echo "$out" | grep -q "^OK (" || status=1

# R61: each step its own run; a force-stop ends the first one's process.
T=com.hazia.factotum.data.ForceStopOnDeviceTest
run -e r61 arm -e class "$T#armThenFinish" | grep -E "^OK|FAILURES" ; sleep 2
c=$(run -e r61 read-finished -e class "$T#theNextStartReadsWhatHappened"); echo "$c" | grep -E "^OK|FAILURES|stack=" | head -5
echo "$c" | grep -q "^OK (" || status=1
run -e r61 arm-and-stop -e class "$T#armThenForceStop" | grep -E "^OK|FAILURES|Process crashed|INSTRUMENTATION_RESULT: shortMsg" ; sleep 2
s=$(run -e r61 read-stopped -e class "$T#theNextStartReadsWhatHappened"); echo "$s" | grep -E "^OK|FAILURES|stack=" | head -5
echo "$s" | grep -q "^OK (" || status=1

echo "--- reported"
adb logcat -d -s FactotumDevice:I | grep -v "^---------" | sed 's/^.*FactotumDevice: //'
exit $status
