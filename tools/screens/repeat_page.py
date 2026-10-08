"""T1.6 mockups for the owner: the three builder forms on the front, typed (off the front), and the control, drawn from
repeat_opt.py with their measures from docs/screens/t1/repeat-rank.json.

    PYTHONUTF8=1 python tools/screens/repeat_page.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import repeat_opt as R  # noqa: E402
import tier_t1 as t  # noqa: E402

BASE = {"start": "builder", "cron": "advanced", "preview": "words", "container": "sheet"}
SHOW = [
    ("freq", "Every [n] [unit ▾] (Google Calendar, Todoist, Tasks.org)", [("base", "Opens on the item's rule"), ("menu", "The unit menu"), ("month", "Monthly: by day, by weekday, last day")]),
    ("modes", "Schedule types first (MedTimer, Mnemo)", [("base", "Repeat: units as chips"), ("interval", "Interval within a day, in a window"), ("random", "Random every 2 to 4 days")]),
    ("sentence", "The rule as a sentence of tappable words", [("base", "Opens on the sentence"), ("unit", "\"week\" tapped: the unit chooser"), ("onm", "\"on day 16\" tapped, monthly")]),
    ("typed", "Typed words with preset chips (off the front)", [("base", "The field, the keyboard up")]),
]


def measures(rank, v):
    r = [x for x in rank["all"] if x["v"] == v]
    if not r:
        return ""
    r = r[0]
    return ("Actions over the 10 tasks %d · reach %.2f · clutter %.3f · covers %.0f%% · controls %d · rule in words and next dates: %s · "
            "distance from the 17 references %.2f") % (r["actions"], r["reach"], r["clutter"], 100 * r["covered"], r["controls"],
                                                       {0: "both", 1: "words only", 2: "no"}[r["unread"]], r["ref_distance"])


def main():
    with open(os.path.join(v2.OUT, "repeat-rank.json"), encoding="utf-8") as fh:
        rank = json.load(fh)
    parts = ['<h1 style="font-size:20px">T1.6 Repeat builder: the forms on the front</h1><p class="dim">Each drawn as a sheet, opening on the builder '
             '(presets as its first row), cron behind Advanced, the rule in words with its next dates. Item: Sample, Fri 16 Oct 09:00. '
             'Greys only; scores from <code>tools/screens/repeat_opt.py</code>.</p>']
    for form, title, states in SHOW:
        v = dict(BASE, form=form)
        if form == "typed":
            v["cron"] = "field"
        phones = "".join('<div><div class="cap2">%s</div>%s</div>' % (cap, R.phone(v, s, kb=(form == "typed"))) for s, cap in states)
        parts.append('<h3>%s</h3><p class="cap2" style="max-width:none">%s</p><div class="flex">%s</div>' % (title, measures(rank, v), phones))
    pv = dict(BASE, form="modes", start="presets")
    parts.append('<h3>Presets first (any form): the list, then Custom…</h3><p class="cap2" style="max-width:none">%s</p><div class="flex"><div>%s</div><div>%s</div></div>' % (
        measures(rank, pv), R.phone(pv, "presets"), R.phone(dict(BASE, form="sentence", preview="month"), "base")))
    cv = R.control()
    parts.append('<h3>Control: every section at once (loses)</h3><p class="cap2" style="max-width:none">%s</p><div class="flex"><div>%s</div></div>' % (
        measures(rank, cv), R.phone(cv, "base")))
    css = t.EXTRA + t.T12_CSS + t.T13_CSS + R.CSS + "h3{font-size:15px;margin:18px 0 6px}.cap2{font-size:12px;color:var(--dim);max-width:360px;margin:0 0 6px}.flex{display:flex;gap:12px;overflow-x:auto}"
    with open(os.path.join(v2.OUT, "repeat-options.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(kit.document("".join(parts), "light", css, False))
    print("ok")


if __name__ == "__main__":
    main()
