"""Drives an Android app over adb for the screens survey (docs/screens-workflow-prompt.md, step 1).
Screenshots go to the gitignored _screens-sources/<app>/; nothing here reads the owner's data,
so only use it on debug builds that start empty.

    python tools/screens/adb_walk.py launch <package>
    python tools/screens/adb_walk.py shot <app> <name>        # PNG into _screens-sources/<app>/<name>.png
    python tools/screens/adb_walk.py texts                    # visible texts and content descriptions, with centres
    python tools/screens/adb_walk.py tap "<text>" [nth]       # tap the nth element whose text or description equals <text>
    python tools/screens/adb_walk.py type "<text>"
    python tools/screens/adb_walk.py key BACK|ENTER|HOME
    python tools/screens/adb_walk.py top                      # the resumed activity
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

DEVICE = os.environ.get("ADB_SERIAL", "8ad59cbb")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def adb(*args, binary=False):
    out = subprocess.run(["adb", "-s", DEVICE, *args], capture_output=True, check=True)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def nodes():
    adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
    root = ET.fromstring(adb("shell", "cat", "/sdcard/window.xml"))
    for n in root.iter("node"):
        label = n.get("text") or n.get("content-desc") or ""
        x0, y0, x1, y1 = map(int, re.findall(r"\d+", n.get("bounds")))
        yield label, ((x0 + x1) // 2, (y0 + y1) // 2), n


def main(cmd, *args):
    if cmd == "launch":
        adb("shell", "monkey", "-p", args[0], "-c", "android.intent.category.LAUNCHER", "1")
    elif cmd == "shot":
        folder = os.path.join(ROOT, "_screens-sources", args[0])
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, args[1] + ".png")
        with open(path, "wb") as fh:
            fh.write(adb("exec-out", "screencap", "-p", binary=True))
        print(path)
    elif cmd == "texts":
        for label, (x, y), _ in nodes():
            if label.strip():
                print("%4d,%4d  %s" % (x, y, label.replace("\n", " ")[:80]))
    elif cmd == "tap":
        nth = int(args[1]) if len(args) > 1 else 0
        hits = [c for label, c, _ in nodes() if label == args[0]]
        if len(hits) <= nth:
            sys.exit("no element %r (found %d)" % (args[0], len(hits)))
        adb("shell", "input", "tap", str(hits[nth][0]), str(hits[nth][1]))
    elif cmd == "type":
        adb("shell", "input", "text", args[0].replace(" ", "%s"))
    elif cmd == "key":
        adb("shell", "input", "keyevent", "KEYCODE_" + args[0])
    elif cmd == "top":
        print(re.search(r"mResumedActivity: .*", adb("shell", "dumpsys", "activity", "activities")).group(0))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:]) if len(sys.argv) > 1 else sys.exit(__doc__)
