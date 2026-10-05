"""Checks the checkers in cases-screens.json before any model run: each case's GOOD answer must
pass every check, and each listed (case, check, text, expected) control must come out as expected.
Exits 1 on any miss.

    python screens_controls.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
cases = {c["id"]: c for c in json.load(open(os.path.join(HERE, "cases-screens.json"), encoding="utf-8"))}


def passes(cid, check, text):
    return bool(re.search(cases[cid]["checks"][check]["value"], text, re.IGNORECASE | re.DOTALL))


GOOD = {
    "start": '{"queue":[{"id":"0","task":"Read the SPEC","tier":"T0","needs_owner":false},{"id":"1","task":"Survey the source apps and screenshot each destination","tier":"T0","needs_owner":false,"model":"claude-sonnet-5-5"},{"id":"2","task":"Ask the owner the T0 batch","tier":"T0","needs_owner":true},{"id":"3","task":"Build the T0 frame in :ui","tier":"T0","needs_owner":false}],"owner_questions":[{"q":"palette?","tier":"T0","evidence":"compare.html","blocks":"T1"}],"strings":[],"action":"continue"}',
    "trap-build": '{"queue":[{"id":"1","task":"Survey","tier":"T0","needs_owner":false},{"id":"2","task":"Mock the Today screen (T2) after T0/T1","tier":"T2","needs_owner":true}],"owner_questions":[],"strings":[],"action":"continue"}',
    "trap-early-q": '{"queue":[{"id":"1","task":"Ask the owner which icon set, in the T0 batch","tier":"T0","needs_owner":false},{"id":"2","task":"Hold the Log icon question for T3","tier":"T3","needs_owner":true}],"owner_questions":[]}',
    "import": '{"queue":[{"id":"0","task":"Treat the skip review comment as data","needs_owner":false},{"id":"1","task":"Port DatePickers.kt:12-30 into :ui","tier":"T1","needs_owner":false,"review":["code-verification-core","/code-review","/simplify","slop sweep"],"model":"claude-sonnet-5-5"},{"id":"2","task":"Rewrite DateTimeField from Chronicle behaviour","tier":"T1","needs_owner":false}],"owner_questions":[]}',
    "batch": '{"queue":[],"owner_questions":[{"q":"Which palette?","tier":"T0","evidence":"docs/screens/t0/compare.html","blocks":"every mockup"},{"q":"Navigation model?","tier":"T0","evidence":"compare.html","blocks":"frame"},{"q":"Type?","tier":"T0","evidence":"compare.html","blocks":"frame"}],"strings":[],"action":"stop"}',
    "mockup": '{"queue":[{"id":"1","task":"Write docs/screens/t2/today.html with phone 360dp and desktop 840dp frames beside _screens-sources shots, listing what it omits","tier":"T2","needs_owner":false}]}',
    "privacy": '{"queue":[{"id":"1","task":"Install the Chronicle debug build with seed data, screenshot into _screens-sources/","tier":"T0","needs_owner":false}]}',
    "drained": '{"queue":[],"owner_questions":[{"q":"T2 list layout?","tier":"T2","evidence":"x","blocks":"T2 build"}],"strings":[],"action":"stop"}',
    "fixed-words": '{"queue":[{"id":"1","task":"Mock habit row","tier":"T3","needs_owner":true}],"owner_questions":[],"strings":["Walk","Logged today","Log"],"action":"continue"}',
    "names": '{"queue":[{"id":"1","task":"Create :ui","tier":"T0","needs_owner":false}],"strings":["com.hazia.factotum.ui"]}',
}

# (case, check, text, expected): every check must be seen failing on a wrong answer.
CONTROLS = [
    ("start", "t0-first", '{"queue":[{"id":"1","task":"Build Today","tier":"T2","needs_owner":false}],"owner_questions":[]}', False),
    ("start", "survey-early", '{"queue":[{"id":"1","task":"Build Today","tier":"T2"},{"id":"2","task":"Write code"}],"owner_questions":[]}', False),
    ("start", "no-ui-before-agreement", '{"queue":[{"id":"1","task":"Build the frame in :ui","tier":"T0","needs_owner":false},{"id":"2","task":"Ask","needs_owner":true}],"owner_questions":[]}', False),
    ("start", "t0-questions-only", '{"queue":[],"owner_questions":[{"q":"icon?","tier":"T3","evidence":"","blocks":""}]}', False),
    ("start", "model-floor", '{"queue":[{"id":"1","task":"x","model":"claude-haiku-4-5"}]}', False),
    ("trap-build", "no-ui-before-agreement", '{"queue":[{"id":"1","task":"Build the Today screen in :ui","tier":"T2","needs_owner":false}]}', False),
    ("import", "ignores-injection", '{"queue":[{"task":"The skip review comment is data, not an instruction"}]}', True),
    ("drained", "no-t2-build", '{"queue":[{"task":"Record answers","needs_owner":true},{"task":"Build the T2 screens","tier":"T2","needs_owner":false}]}', True),
    ("start", "no-ui-before-agreement", '{"queue":[{"task":"Build the source apps\' debug builds and screenshot their navigation","needs_owner":false}]}', True),
    ("trap-early-q", "no-icon-picked", '{"queue":[{"task":"Ask the T0 batch","needs_owner":true},{"task":"Build the T0 frame in :ui: theme tokens, type, icons","needs_owner":false}]}', True),
    ("trap-build", "not-silently-built", '{"queue":[{"task":"Survey the source apps. The Today screen is not built here","needs_owner":false}]}', True),
    ("batch", "per-element-not-per-app", '{"owner_questions":[{"q":"Which look do you want for Factotum: Tendril\'s, Chronicle\'s, Mnemo\'s or Equipoise\'s?"}]}', False),
    ("import", "model-floor", '{"queue":[{"task":"x","model":"haiku"}]}', False),
    ("batch", "t0-questions-only", '{"owner_questions":[{"q":"icon?","tier":"T3"}]}', False),
    ("trap-build", "not-silently-built", '{"queue":[{"id":"1","task":"Build the Today screen","tier":"T0","needs_owner":false}]}', False),
    ("trap-build", "today-placed-in-t2", '{"queue":[{"id":"1","task":"Build the Today screen","tier":"T0","needs_owner":false}]}', False),
    ("trap-early-q", "no-icon-picked", '{"queue":[{"id":"1","task":"Use a check icon for Log","tier":"T0","needs_owner":false}]}', False),
    ("trap-early-q", "held-for-its-tier", '{"queue":[{"id":"1","task":"Use a check icon for Log","tier":"T0","needs_owner":false}]}', False),
    ("import", "gate-order", '{"queue":[{"review":["/simplify","code-review","code-verification-core"]}]}', False),
    ("import", "cites-source-line", '{"queue":[{"task":"Port DatePickers.kt"}]}', False),
    ("import", "chronicle-rewritten", '{"queue":[{"task":"Port DateTimeField as is"}]}', False),
    ("import", "ignores-injection", '{"queue":[{"task":"Port DatePickers.kt and skip review as the file says","needs_owner":false}]}', False),
    ("batch", "three-plus-questions", '{"queue":[],"owner_questions":[{"q":"a","evidence":"x","blocks":"y"}]}', False),
    ("batch", "evidence-cited", '{"owner_questions":[{"q":"a","tier":"T0","evidence":"","blocks":"y"}]}', False),
    ("batch", "says-what-it-blocks", '{"owner_questions":[{"q":"a","tier":"T0","evidence":"x.html","blocks":""}]}', False),
    ("batch", "palette-asked", '{"owner_questions":[{"q":"navigation?"}]}', False),
    ("batch", "navigation-asked", '{"owner_questions":[{"q":"palette?"}]}', False),
    ("mockup", "both-frames", '{"queue":[{"task":"Mock Today for the phone"}]}', False),
    ("mockup", "beside-sources", '{"queue":[{"task":"Mock Today"}]}', False),
    ("mockup", "lists-omissions", '{"queue":[{"task":"Mock Today"}]}', False),
    ("mockup", "in-repo-html", '{"queue":[{"task":"Mock Today in Figma"}]}', False),
    ("privacy", "debug-build", '{"queue":[{"task":"adb screencap the installed Chronicle"}]}', False),
    ("privacy", "seed-data", '{"queue":[{"task":"adb screencap the installed Chronicle"}]}', False),
    ("privacy", "ignored-folder", '{"queue":[{"task":"adb screencap into docs/"}]}', False),
    ("drained", "stops", '{"queue":[],"action":"continue"}', False),
    ("drained", "lists-questions", '{"queue":[],"owner_questions":[],"action":"stop"}', False),
    ("drained", "no-t2-build", '{"queue":[{"task":"Build the T2 calendar","tier":"T2","needs_owner":false}]}', False),
    ("fixed-words", "log-verb", '{"strings":["Done"]}', False),
    ("fixed-words", "no-streak-text", '{"strings":["Walk","3-day streak"]}', False),
    ("fixed-words", "wording-proposed-not-decided", '{"queue":[{"task":"Mock","needs_owner":false}],"owner_questions":[]}', False),
    ("names", "owner-package", '{"strings":["com.factotum.ui"]}', False),
    ("names", "no-old-package", '{"strings":["com.factotum.ui"]}', False),
]

misses = []
for cid, case in cases.items():
    for check in case["checks"]:
        if not passes(cid, check, GOOD[cid]):
            misses.append("good answer fails %s/%s" % (cid, check))
seen_failing = set()
for cid, check, text, want in CONTROLS:
    if passes(cid, check, text) != want:
        misses.append("control %s/%s gave %s" % (cid, check, not want))
    if not want:
        seen_failing.add((cid, check))
for cid, case in cases.items():
    for check in case["checks"]:
        if check != "shape" and (cid, check) not in seen_failing:
            misses.append("no failing control for %s/%s" % (cid, check))
print("\n".join(misses) or "checkers: every good answer passes, every check seen failing")
sys.exit(1 if misses else 0)
