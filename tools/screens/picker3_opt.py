"""T1.5 v3 (owner, 2026-10-08): the line sets dates and times by typing; a typed date is never asked again (tapping its
highlight opens no picker, only "Keep as text", as every highlight does). The picker is for choosing a day by looking at the month: it opens from ⋯ › Date beside the
line, or from the full page's Date row, and opens straight on the calendar, with no presets.

Variables: steps (one view: month, time and end together; two: a day tapped, then the time view), container (a
sheet, a page, the keyboard's place; the pop-over failed the visibility rule in v2), the time entry (picker_opt's
five), the event's end (duration presets or an end time). Day load on (picker_opt's front).
Tasks, all opened the same way (⋯ › Date, 2 taps, not counted): "Fri 16"; "Fri 16 at 14:30"; "an event Fri 16 at
15:00 for 1 h"; "the 3rd of next month". Each ends with Done. Measured as picker_opt, with the owner's rule that
everything a task needs is drawn in its own view.

    PYTHONUTF8=1 python tools/screens/picker3_opt.py
"""
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import picker_opt as P  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

SPACE = {"steps": ["one", "two"], "container": ["sheet", "page", "keyboard"], "entry": P.ENTRIES + ["dialtyped"], "end": ["duration", "endtime"]}


def done_row(back=False):
    return '<div class="row" style="justify-content:space-between">%s%s</div>' % (P.btn("Back to month", "‹ Fri 16") if back else "<span></span>", P.btn("Done", "Done"))


def view_html(v, view):
    if v["steps"] == "one":
        return P.month(True) + P.time_entry(v["entry"]) + P.end_part(v) + done_row()
    if view == 1:
        return P.month(True) + done_row()  # a day tap with no time wanted: Done; with a time, the time view follows
    return done_row(back=True) + P.time_entry(v["entry"]) + P.end_part(v)


def phone(v, view=1):
    c = v["container"]
    cls = {"keyboard": "pk", "sheet": "pk sheet", "page": "pk page"}[c]
    style = ' style="height:290px"' if c == "keyboard" else (' style="max-height:704px"' if c == "sheet" else "")
    pk = '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, view_html(v, view))
    if c == "page":
        return kit.phone(kit.header("Date", (), ("‹", "Back")), '<div class="c2" style="position:relative;height:100%%">%s</div>' % pk, "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="sheet c2" style="position:relative">%s</div>%s' % (P.line_html(), pk)) if c == "keyboard" else '<div class="c2">%s</div>' % pk
    overlay = '<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s</div>' % overlay
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, view=1, theme="light", score=True):
    return kit.document(phone(v, view), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + P.CSS, score)


def tasks(v):
    """(view, targets, keys, drags) per step."""
    e, end, two = v["entry"], v["end"], v["steps"] == "two"
    # a wheel moves one value per step (owner, 2026-10-08: "scrolling a wheel one hour and one minute at a time"):
    # from 09:00, 14:30 is 5 hour steps and 6 five-minute steps, 15:00 is 6; the first count (one drag a wheel)
    # flattered the wheels
    # dialtyped: the person takes the quicker of its two (the dial here; a suggestion chip for 09:00)
    t1430 = {"blocks": (["Other time"], 4, 0), "typed": (["Time field"], 4, 0), "cron": (["Time field"], 4, 0), "wheel": ([], 0, 11), "dial": (["Hour 2"], 0, 1),
             "dialtyped": (["Hour 2"], 0, 1)}[e]
    t15 = {"blocks": (["Block Afternoon"], 0, 0), "typed": (["Time field"], 2, 0), "cron": (["Time field"], 2, 0), "wheel": ([], 0, 6), "dial": (["Hour 3"], 0, 0),
           "dialtyped": (["Hour 3"], 0, 0)}[e]
    end1h = (["Lasts 1 h"], 0, 0) if end == "duration" else t15
    tv = 2 if two else 1  # the view the time lives in
    # two steps: tapping a day with a time wanted opens the time view (the day tap is the step); without a time, Done
    return [
        [(1, ["Day 16", "Done"], 0, 0)],
        [(1, ["Day 16"], 0, 0), (tv, t1430[0] + ["Done"], t1430[1], t1430[2])],
        [(1, ["Day 16"], 0, 0), (tv, t15[0] + end1h[0] + ["Done"], t15[1] + end1h[1], t15[2] + end1h[2])],
        [(1, ["Next month", "Day 3", "Done"], 0, 0)],
    ]


def score(v):
    views = [1, 2] if v["steps"] == "two" else [1]
    per = {}
    for view in views:
        d = doc(v, view)
        m = ss.measure(d, 360, 740)
        clutter = sum(ss.edge_density(ss.render(doc(v, view, th), 360, 740)) for th in ("light", "dark")) / 2
        pk = m["boxes"].get("picker")
        inpk = [x for x in m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen")]
        per[view] = {"m": m, "taps": {x["name"]: x for x in m["taps"]}, "clutter": clutter,
                     "covered": 1.0 if v["container"] == "page" else round(min(1.0, (pk[3] if pk else 0) / 740), 3), "controls": len(inpk),
                     "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in inpk if x["w"] < 48 or x["h"] < 48})}
    tk, ids, unseen = [0, 0, 0], [], set()
    for task in tasks(v):
        for view, names, keys, drags in task:
            tk[0] += len(names); tk[1] += keys; tk[2] += drags
            needed = names + (["Hour wheel", "Minute wheel"] if drags and v["entry"] == "wheel" else [])
            for n in needed:
                x = per[view]["taps"].get(n)
                if not x or not x.get("seen"):
                    unseen.add("%d: %s" % (view, n))
                    continue
                if n in names:
                    ids.append(math.log2(math.hypot(P.THUMB[0] - x["x"], P.THUMB[1] - x["y"]) / min(x["w"], x["h"]) + 1))
    return {"taps": tk[0], "keys": tk[1], "drags": tk[2], "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": len(unseen), "unseen_names": sorted(unseen),
            "line": 0 if v["container"] == "keyboard" else 1, "heights": max(max(1, len({x[4] for x in p["m"]["vis"]})) for p in per.values()),
            "clutter": round(sum(p["clutter"] for p in per.values()) / len(per), 4), "covered": max(p["covered"] for p in per.values()),
            "controls": max(p["controls"] for p in per.values()), "small": sorted({s for p in per.values() for s in p["small"]})}


AXES = {"H": (("heights", 1),), "U": (("taps", 1), ("keys", 1), ("drags", 1), ("reach", 1), ("line", 1)),
        "C": (("clutter", 1), ("covered", 1), ("controls", 1))}


def main():
    rows = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        r = dict(v=v, **score(v))
        rows.append(r)
        print(len(rows), v, {k: r[k] for k in ("taps", "keys", "drags", "unseen", "covered", "small")}, flush=True)
    ok = [r for r in rows if not r["small"] and r["unseen"] == 0]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    with open(os.path.join(v2.OUT, "picker3-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front]}, fh, indent=1, ensure_ascii=False)
    print("pass the rule:", len(ok), "of", len(rows), "front:", len(front))
    for r in sorted(front, key=lambda r: r["H"] + r["U"] + r["C"]):
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]), {k: r[k] for k in ("taps", "keys", "drags", "reach", "line", "clutter", "covered", "controls")})


if __name__ == "__main__":
    main()
