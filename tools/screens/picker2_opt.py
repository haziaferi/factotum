"""T1.5 v2 (owner, 2026-10-08): "An entire calendar picker should be opened by the user rather than appear unprompted.
The natural language input has as few clicks to make as possible on purpose."

So the line sets the date and time by typing (no taps); the picker is a fallback the person asks for:
  menu      tapping a highlighted date opens a short menu: Today, Tomorrow, This weekend, Next week, No date,
            "Pick a date…", "Time…" (Microsoft To Do's pattern)
  calendar  the month grid, only on "Pick a date…"
  time      the time entry and the event's end, only on "Time…" (or a tapped highlighted time)
Variables: where the menu opens (a pop-over by the word, in the keyboard's place, a small sheet), where the calendar
and time open (a sheet, a page, the keyboard's place), the time entry (picker_opt's five), the event's end (duration
presets or an end time). Day load stays on (15 of the 18 on picker_opt's front carried it).

Tasks, as fixes after typing: "make it tomorrow"; "make it Fri 16 Oct" (not a preset); "add 14:30"; "an event at
15:00 for 1 h"; "no date". Each starts with a tap on the highlighted date (or time). Measured as picker_opt: taps,
keystrokes and drags apart, reach, every needed control drawn in its own view (the owner's rule), the line hidden or
not, and per view clutter, coverage and controls; harmony from the hardest view.

    PYTHONUTF8=1 python tools/screens/picker2_opt.py
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

SPACE = {"menu": ["popover", "keyboard", "sheet"], "detail": ["sheet", "page", "keyboard"], "entry": P.ENTRIES, "end": ["duration", "endtime"]}
MENU_ROWS = P.PRESETS + ["Pick a date…", "Time…"]
CSS = P.CSS + """
.pk .mrow{min-height:48px;display:flex;align-items:center;justify-content:space-between;font-size:14px;padding:0 4px}
.pk .mrow .wd2{font-size:12px;color:var(--dim)}
"""
WEEKDAY = {"Today": "Mon", "Tomorrow": "Tue", "This weekend": "Sat", "Next week": "Mon"}


def menu_html():
    rows = "".join('<div class="mrow" data-tap="Menu %s"><span>%s</span><span class="wd2">%s</span></div>' % (r, r, WEEKDAY.get(r, "")) for r in MENU_ROWS)
    return rows


def view_html(v, view):
    if view == "menu":
        return menu_html()
    if view == "calendar":
        return '<div class="row">%s</div>' % P.btn("Back to menu", "‹ Date") + P.month(True)
    return '<div class="row">%s</div>' % P.btn("Back to menu", "‹ Date") + P.time_entry(v["entry"]) + P.end_part(v)


def phone(v, view):
    c = v["menu"] if view == "menu" else v["detail"]
    cls = {"keyboard": "pk", "sheet": "pk sheet", "popover": "pk pop", "page": "pk page"}[c]
    style = ' style="height:290px"' if c == "keyboard" else (' style="max-height:704px"' if c == "sheet" else "")
    if c == "popover":
        style = ' style="left:12px;right:auto;width:240px"'
    pk = '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, view_html(v, view))
    if c == "page":
        return kit.phone(kit.header("Date" if view == "calendar" else "Time", (("✓", "Done"),), ("‹", "Back")),
                         '<div class="c2" style="position:relative;height:100%%">%s</div>' % pk, "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    if c == "keyboard":
        overlay = '<div class="sheet c2" style="position:relative">%s</div>%s' % (P.line_html(), pk)
    elif c == "popover":
        overlay = '<div class="sheet c2" style="position:relative">%s%s</div><div class="kb" style="height:250px">keyboard</div>' % (pk, P.line_html())
    else:
        overlay = '<div class="c2">%s</div>' % pk
    overlay = '<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s</div>' % overlay
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, view, theme="light", score=True):
    return kit.document(phone(v, view), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


def tasks(v):
    """(view, targets tapped, keystrokes, drags) per step; each task opens with the tap on the highlighted word."""
    e, end = v["entry"], v["end"]
    t1430 = {"blocks": (["Other time"], 4, 0), "typed": (["Time field"], 4, 0), "cron": (["Time field"], 4, 0), "wheel": ([], 0, 2), "dial": (["Hour 2"], 0, 1)}[e]
    t15 = {"blocks": (["Block Afternoon"], 0, 0), "typed": (["Time field"], 2, 0), "cron": (["Time field"], 2, 0), "wheel": ([], 0, 1), "dial": (["Hour 3"], 0, 0)}[e]
    end1h = (["Lasts 1 h"], 0, 0) if end == "duration" else t15
    return [
        [("line", ["Date word"], 0, 0), ("menu", ["Menu Tomorrow"], 0, 0)],
        [("line", ["Date word"], 0, 0), ("menu", ["Menu Pick a date…"], 0, 0), ("calendar", ["Day 16"], 0, 0)],
        [("line", ["Date word"], 0, 0), ("menu", ["Menu Time…"], 0, 0), ("time", t1430[0], t1430[1], t1430[2])],
        [("line", ["Date word"], 0, 0), ("menu", ["Menu Time…"], 0, 0), ("time", t15[0] + end1h[0], t15[1] + end1h[1], t15[2] + end1h[2])],
        [("line", ["Date word"], 0, 0), ("menu", ["Menu No date"], 0, 0)],
    ]


def score(v):
    per = {}
    for view in ("menu", "calendar", "time"):
        d = doc(v, view)
        m = ss.measure(d, 360, 740)
        clutter = sum(ss.edge_density(ss.render(doc(v, view, th), 360, 740)) for th in ("light", "dark")) / 2
        pk = m["boxes"].get("picker")
        c = v["menu"] if view == "menu" else v["detail"]
        per[view] = {"m": m, "taps": {x["name"]: x for x in m["taps"]}, "clutter": clutter,
                     "covered": 1.0 if c == "page" else round(min(1.0, (pk[3] if pk else 0) / 740), 3),
                     "controls": len([x for x in m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen")]),
                     "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen") and (x["w"] < 48 or x["h"] < 48)})}
    tk, ids, unseen = [0, 0, 0], [], set()
    for task in tasks(v):
        for view, names, keys, drags in task:
            tk[0] += len(names); tk[1] += keys; tk[2] += drags
            if view == "line":
                continue  # the highlighted word on the approved line (T1.3), already scored there
            needed = names + (["Hour wheel", "Minute wheel"] if drags and v["entry"] == "wheel" else [])
            for n in needed:
                x = per[view]["taps"].get(n)
                if not x or not x.get("seen"):
                    unseen.add("%s: %s" % (view, n))
                    continue
                if n in names:
                    ids.append(math.log2(math.hypot(P.THUMB[0] - x["x"], P.THUMB[1] - x["y"]) / min(x["w"], x["h"]) + 1))
    return {"taps": tk[0], "keys": tk[1], "drags": tk[2], "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": len(unseen), "unseen_names": sorted(unseen),
            "line": (0 if v["menu"] in ("keyboard", "popover") else 1) + (0 if v["detail"] == "keyboard" else 1),
            "heights": max(max(1, len({x[4] for x in p["m"]["vis"]})) for p in per.values()),
            "clutter": round(sum(p["clutter"] for p in per.values()) / 3, 4), "covered": max(p["covered"] for p in per.values()),
            "menu_covered": per["menu"]["covered"], "controls": max(p["controls"] for p in per.values()),
            "small": sorted({s for p in per.values() for s in p["small"]})}


AXES = {"H": (("heights", 1),),
        "U": (("taps", 1), ("keys", 1), ("drags", 1), ("reach", 1), ("line", 1)),
        "C": (("clutter", 1), ("covered", 1), ("menu_covered", 1), ("controls", 1))}


def main():
    rows = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        r = dict(v=v, **score(v))
        rows.append(r)
        print(len(rows), v, {k: r[k] for k in ("taps", "keys", "drags", "unseen", "menu_covered", "covered", "small")}, flush=True)
    ok = [r for r in rows if not r["small"] and r["unseen"] == 0]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    with open(os.path.join(v2.OUT, "picker2-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front]}, fh, indent=1, ensure_ascii=False)
    print("pass the rule:", len(ok), "of", len(rows), "front:", len(front))
    for r in sorted(front, key=lambda r: r["H"] + r["U"] + r["C"]):
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]), {k: r[k] for k in ("taps", "keys", "drags", "reach", "line", "clutter", "covered", "menu_covered")})


if __name__ == "__main__":
    main()
