"""Counts the JUnit XML results under every module, and prints each failure. Clear the
test-results directories before the build, or a stale green run is counted.

    python tools/test_summary.py
"""
import glob
import os
import re

total = failed = 0
for path in sorted(glob.glob("*/build/test-results/**/*.xml", recursive=True)):
    text = open(path, encoding="utf-8").read()
    tests = int(re.search(r'<testsuite [^>]*tests="(\d+)"', text).group(1))
    total += tests
    print("%-80s %d" % (os.path.relpath(path).replace(os.sep, "/").split("test-results/")[1], tests))
    for name, message in re.findall(r'<testcase name="([^"]+)"[^>]*>\s*<(?:failure|error) message="([^"]*)', text):
        failed += 1
        print("  FAIL %s: %s" % (name, message[:400]))
print("total %d, failed %d" % (total, failed))
