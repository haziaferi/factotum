"""T1.5 Date and time picker (owner, 2026-10-08; decision 17): presets first (Today, Tomorrow, This weekend, Next week,
No date), then a month grid and the time; typing a date works (the capture line). Owner's answers:
  time entry  score: the planner's time blocks as presets, a typed field with suggestions, scroll wheels, a clock dial,
              and cron with its calculator (cron lives in both pickers; here, a typed field that also takes a cron
              expression and reads it back with its next three dates)
  week start  and 12/24-hour clock: follow the system (drawn Monday, 24-hour, as this phone's Italian region)
  event end   score both: duration presets, and an end time picked like the start
  day load    score with and without (a quiet dot under days that hold items)
  container   score all: replaces the keyboard (Todoist, TickTick), a sheet over the screen, a pop-over by the date
              word (Microsoft To Do), a full page (the full form)
References, captured on the owner's phone (gitignored): Todoist and TickTick (dial in a dialog), Google Tasks (a
dialog), Microsoft To Do (a pop-over of presets), Any.do (preset chips).

Measures, all from the render or counted from the design, never timed with assumed constants:
  H  heights (distinct drawn heights of controls), edges (distinct left edges of the sections), sprawl (craftkit ui),
     heavy (the largest single element's share of the picker's visual mass, imgstat departure from ground)
  U  ops     taps + keystrokes + drags over the task set below, by the design's own steps
     reach   mean Fitts' ID from the thumb's rest (bottom centre) to the targets those tasks use
     unseen  targets the tasks need that are not drawn on screen (cut off or scrolled away; hit-tested)
     line    the typed line hidden while picking (1) or still visible (0)
     load    busy days not shown (1) or shown (0)
  C  clutter (edge density), covered (share of the screen the picker hides), controls (targets drawn)
Task set: "tomorrow 09:00"; "Fri 14:30"; "next Monday, all day"; "an event, today 15:00 for 1 h"; "09:00 every weekday".
The repeat task without cron goes through T1.6's repeat builder, counted as 2 taps (its common choices come first,
decision 17): an assumption until T1.6 is drawn, and the same for every option.

    PYTHONUTF8=1 python tools/screens/picker_opt.py
"""
import itertools
import json
import math
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import legend_opt as L  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
from craftkit import imgstat  # noqa: E402

THUMB = (180, 700)
CONTAINERS = ["keyboard", "sheet", "popover", "page"]
ENTRIES = ["blocks", "typed", "wheel", "dial", "cron"]
SPACE = {"container": CONTAINERS, "entry": ENTRIES, "load": [False, True], "end": ["duration", "endtime"], "steps": ["one", "two"]}
PRESETS = ["Today", "Tomorrow", "This weekend", "Next week", "No date"]
BLOCKS = [("Morning", "08:00"), ("Midday", "12:00"), ("Afternoon", "15:00"), ("Evening", "19:00")]  # placeholder blocks (planner defaults)
BUSY = {8, 9, 12, 15, 21}
CSS = L.CSS + """
.pk{background:var(--zone);padding:2px 12px 4px;overflow:hidden}
.pk .sec{font-size:12px;color:var(--dim);font-weight:600;min-width:44px;display:inline-flex;align-items:center;min-height:48px}
.pk .row{display:flex;flex-wrap:wrap;gap:0 6px;min-height:48px;align-items:center}
.pk .grid{display:grid;grid-template-columns:repeat(7,1fr);margin:0 -12px}  /* full width: 7 x 48 px needs 336 */
.pk .wd{font-size:11px;color:var(--dim);text-align:center;padding:0}
.pk .day{min-height:48px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:14px}
.pk .day.sel b{background:var(--zone2);border-radius:999px;width:32px;height:32px;display:grid;place-items:center;font-weight:600}
.pk .day b{font-weight:400;width:32px;height:32px;display:grid;place-items:center}
.pk .dot{width:4px;height:4px;border-radius:50%;background:var(--dim);margin-top:1px}
.pk .mh{display:flex;align-items:center;justify-content:space-between;min-height:48px;font-size:14px;font-weight:600}
.pk .field{flex:1;min-height:48px;display:flex;align-items:center;padding:0 12px;border-radius:10px;box-shadow:inset 0 0 0 1px var(--zone2);font-size:15px}
.pk .wheels{display:flex;justify-content:center;gap:24px}.pk .wheel{width:64px;text-align:center;font-size:15px}
.pk .wheel div{height:48px;display:grid;place-items:center;color:var(--dim)}.pk .wheel .on{color:var(--ink);font-weight:600;box-shadow:inset 0 1px 0 var(--zone2),inset 0 -1px 0 var(--zone2)}
.pk .dial{width:232px;height:232px;border-radius:50%;background:var(--zone2);position:relative;margin:4px auto}
.pk .dial span{position:absolute;width:48px;height:48px;display:grid;place-items:center;font-size:13px;transform:translate(-50%,-50%)}
.pk .hhmm{font-size:28px;text-align:center;font-weight:300;min-height:48px;display:grid;place-items:center}
.pk .calc{font-size:12px;color:var(--dim);padding:2px 0 4px;line-height:18px}
.pk.page{position:absolute;inset:56px 0 0 0;overflow:hidden}
.pk.pop{position:absolute;left:12px;right:12px;bottom:100%;margin-bottom:6px;border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,.22);max-height:520px}
.pk.sheet{border-radius:20px 20px 0 0;box-shadow:0 -8px 24px rgba(0,0,0,.14)}
"""


def btn(name, label, square=False):
    return v2.control(name, label, 32, "ghost", square=square)


def chip(name, label):
    return v2.control(name, label, 32, "tonal", square=False)  # sized to its words (a square overflowed them)


def month(load):
    days = '<div class="grid">%s%s%s</div>' % (
        "".join('<div class="wd">%s</div>' % d for d in "MTWTFSS"), "<div></div>" * 3,
        "".join('<div class="day%s" data-tap="Day %d"><b>%d</b>%s</div>' % (" sel" if d == 9 else "", d, d, '<i class="dot"></i>' if load and d in BUSY else "")
                for d in range(1, 32)))
    return '<div class="mh"><span>October 2026</span><span>%s%s</span></div>%s' % (btn("Prev month", "‹", True), btn("Next month", "›", True), days)


def time_entry(entry, label="Time"):
    if entry == "blocks":
        return '<div class="row"><span class="sec">%s</span>%s%s</div>' % (label, "".join(chip("Block %s" % n, "%s %s" % (n, h)) for n, h in BLOCKS), btn("Other time", "Other…"))
    if entry in ("typed", "cron"):
        out = '<div class="row"><span class="sec">%s</span><span class="field" data-tap="Time field">9</span>%s%s</div>' % (
            label, chip("Suggest 09:00", "09:00"), chip("Suggest 21:00", "21:00"))
        if entry == "cron":
            out += '<div class="calc">Also takes cron: <b>0 9 * * 1-5</b> reads "09:00, Monday to Friday", next Thu 8, Fri 9, Mon 12 Oct</div>'
        return out
    if entry == "dialtyped":  # owner, 2026-10-08: the typed field with its suggestions and the dial, one view; the keyboard only on the field
        spots = "".join('<span data-tap="Hour %d" style="left:%.0fpx;top:%.0fpx">%d</span>' % (
            h, 116 + 92 * math.sin(math.radians(h * 30)), 116 - 92 * math.cos(math.radians(h * 30)), h) for h in range(12))
        return ('<div class="row"><span class="sec">%s</span><span class="field" data-tap="Time field">09:00</span>%s%s</div><div class="dial">%s</div>' % (
            label, chip("Suggest 09:00", "09:00"), chip("Suggest 21:00", "21:00"), spots))
    if entry == "wheel":
        col = lambda name, vals, on: '<div class="wheel" data-tap="%s">%s</div>' % (name, "".join('<div%s>%s</div>' % (' class="on"' if v == on else "", v) for v in vals))
        return '<div class="row"><span class="sec">%s</span><div class="wheels" style="flex:1">%s%s</div></div>' % (label, col("Hour wheel", ["08", "09", "10"], "09"), col("Minute wheel", ["55", "00", "05"], "00"))
    # dial: Material's, hours on a ring
    spots = "".join('<span data-tap="Hour %d" style="left:%.0fpx;top:%.0fpx">%d</span>' % (
        h, 116 + 92 * math.sin(math.radians(h * 30)), 116 - 92 * math.cos(math.radians(h * 30)), h) for h in range(12))
    return '<div class="row"><span class="sec">%s</span><span class="hhmm" style="flex:1">09:00</span></div><div class="dial">%s</div>' % (label, spots)


def end_part(v):
    if v["end"] == "duration":
        return '<div class="row"><span class="sec">Ends</span>%s</div>' % "".join(chip("Lasts %s" % d, d) for d in ("30 min", "1 h", "2 h", "All day"))
    # an end time needs its own way to say "all day" (TickTick: a switch beside it), or that task would cost nothing
    return time_entry(v["entry"] if v["entry"] != "cron" else "typed", "Ends") + '<div class="row">%s</div>' % chip("Lasts All day", "All day")


def picker(v, control=False, view=1):
    presets = '<div class="row">%s</div>' % "".join(chip("Preset %s" % p, p) for p in PRESETS)
    body = presets + month(v["load"]) + time_entry(v["entry"]) + end_part(v)
    if v.get("steps") == "two":  # the date first, the time on its own view (Todoist, TickTick)
        body = (presets + month(v["load"]) + '<div class="row">%s</div>' % btn("Add time", "Add time ›") if view == 1 else
                '<div class="row">%s</div>' % btn("Back to date", "‹ Tue 9 Oct") + time_entry(v["entry"]) + end_part(v))
    if control:  # everything at once: every time entry and both ends
        body = presets + month(True) + "".join(time_entry(e) for e in ("blocks", "typed", "wheel", "dial")) + end_part(dict(v, end="duration")) + end_part(dict(v, end="endtime", entry="dial"))
    cls = {"keyboard": "pk", "sheet": "pk sheet", "popover": "pk pop", "page": "pk page"}[v["container"]]
    style = ' style="height:290px"' if v["container"] == "keyboard" else (' style="max-height:704px"' if v["container"] == "sheet" else "")
    return '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, body)


def line_html():
    return ('<div class="line"><span class="in">%s<span class="caret"></span></span>%s</div><div class="hint">Event · # label · ! reminder · @ calendar · ^ page · * repeat</div>' % (
        kit.ud('<span class="hl">ev</span> dentist <span class="hl">tomorrow</span>'), v2.control("More", "⋯", 32, "ghost")))


def phone(v, control=False, view=1):
    c = v["container"]
    if c == "page":
        return kit.phone(kit.header("Date and time", (("✓", "Done"),), ("‹", "Back")), '<div class="c2" style="position:relative;height:100%%">%s</div>' % picker(v, control, view), "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    if c == "keyboard":  # the picker takes the keyboard's place; the line stays above it
        overlay = '<div class="sheet c2" style="position:relative">%s</div>%s' % (line_html(), picker(v, control, view))
    elif c == "popover":  # anchored on the line, above it, keyboard kept
        overlay = '<div class="sheet c2" style="position:relative">%s%s</div><div class="kb" style="height:250px">keyboard</div>' % (picker(v, control, view), line_html())
    else:  # a sheet over the screen: the line goes behind it
        overlay = '<div class="c2">%s</div>' % picker(v, control, view)
    overlay = '<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s</div>' % overlay
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, theme="light", score=True, control=False, view=1):
    return kit.document(phone(v, control, view), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


# the steps each task takes, by design: (targets tapped, keystrokes, drags)
def steps(v):
    e, end = v["entry"], v["end"]
    time_09 = {"blocks": (["Other time", "Suggest 09:00"], 1, 0), "typed": (["Time field", "Suggest 09:00"], 1, 0), "cron": (["Time field", "Suggest 09:00"], 1, 0),
               "wheel": ([], 0, 1), "dial": (["Hour 9"], 0, 0)}[e]
    time_1430 = {"blocks": (["Other time"], 4, 0), "typed": (["Time field"], 4, 0), "cron": (["Time field"], 4, 0), "wheel": ([], 0, 2), "dial": (["Hour 2"], 0, 1)}[e]
    time_15 = {"blocks": (["Block Afternoon"], 0, 0), "typed": (["Time field"], 2, 0), "cron": (["Time field"], 2, 0), "wheel": ([], 0, 1), "dial": (["Hour 3"], 0, 0)}[e]
    end_1h = (["Lasts 1 h"], 0, 0) if end == "duration" else time_15  # an end time costs a second time entry
    tasks = [
        (["Preset Tomorrow"] + time_09[0], time_09[1], time_09[2]),
        (["Day 9"] + time_1430[0], time_1430[1], time_1430[2]),
        (["Preset Next week"], 0, 0),  # a date with no time is a whole-day item (SPEC R94): no all-day tap
        (["Preset Today"] + time_15[0] + end_1h[0], time_15[1] + end_1h[1], time_15[2] + end_1h[2]),
        (["Time field"], 11, 0) if e == "cron" else (["Repeat (T1.6)", "Every weekday (T1.6)"] + time_09[0], time_09[1], time_09[2]),
    ]
    if v.get("steps") == "two":  # every task that sets a time opens the time view first
        tasks = [(names[:1] + (["Add time"] if (names[1:] or keys or drags) and not names[0] == "Time field" else []) + names[1:], keys, drags)
                 if names[0] != "Time field" else (["Add time"] + names, keys, drags) for names, keys, drags in tasks]
    return tasks


def masses(png, m):
    pk = m["boxes"].get("picker")
    sx, sy, sw, sh = pk
    crop = png.replace(".png", "-pk-%d.png" % os.getpid())  # per process: parallel workers crop the same render
    Image.open(png).convert("RGB").crop((int(sx), int(max(0, sy)), int(sx + sw), int(min(740, sy + sh)))).save(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    hist = {}
    for x in lum:
        hist[int(x * 32)] = hist.get(int(x * 32), 0) + 1
    ground = (max(hist.items(), key=lambda kv: kv[1])[0] + 0.5) / 32.0
    total = sum(abs(x - ground) for x in lum) or 1
    heavy = 0.0
    for tp in m["taps"]:
        if not tp.get("seen"):
            continue
        x0, y0, bw, bh = int(tp["box"][0] - sx), int(tp["box"][1] - max(0, sy)), int(tp["box"][2]), int(tp["box"][3])
        ms = sum(abs(lum[y * img.w + x] - ground) for y in range(max(0, y0), min(img.h, y0 + bh)) for x in range(max(0, x0), min(img.w, x0 + bw)))
        heavy = max(heavy, ms / total)
    return round(heavy, 3)


def sprawl(v, control, view=1):
    path = os.path.join(ss.CACHE, "pk-%s-%s-%d-%s-%s-%d-%d.html" % (v["container"], v["entry"], v["load"], v["end"], v.get("steps", "one"), control, view))
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(doc(v, control=control, view=view))
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast"))
               and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


def score(v, control=False):
    """Two steps are measured on both views: a control counts as seen if its own view draws it; clutter is their mean,
    coverage and controls their larger, and the harder view sets heights, sprawl and the heaviest element."""
    views = [1, 2] if v.get("steps") == "two" and not control else [1]
    per = []
    for view in views:
        d = doc(v, control=control, view=view)
        m = ss.measure(d, 360, 740)
        png = ss.render(d, 360, 740)
        clutter = sum(ss.edge_density(ss.render(doc(v, th, control=control, view=view), 360, 740)) for th in ("light", "dark")) / 2
        pk = m["boxes"].get("picker")
        pk_taps = [x for x in m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen")]
        per.append({"m": m, "clutter": clutter, "pk": pk, "pk_taps": pk_taps, "heavy": masses(png, m), "sprawl": sprawl(v, control, view)})
    taps = {}
    for p in per:
        for x in p["m"]["taps"]:
            if x.get("seen") or x["name"] not in taps:
                taps[x["name"]] = x
    ops, ids, unseen_needed = 0, [], set()
    tk = [0, 0, 0]
    for names, keys, drags in steps(v):
        ops += len(names) + keys + drags
        tk[0] += len(names); tk[1] += keys; tk[2] += drags
        # a drag needs its wheel on screen as much as a tap needs its target (wheels were left out of this check at first)
        needed = names + (["Hour wheel", "Minute wheel"] if drags and v["entry"] == "wheel" else [])
        for n in needed:
            x = taps.get(n)
            if n.endswith("(T1.6)"):
                continue
            if not x or not x.get("seen"):
                unseen_needed.add(n)
                continue
            if n in names:
                ids.append(math.log2(math.hypot(THUMB[0] - x["x"], THUMB[1] - x["y"]) / min(x["w"], x["h"]) + 1))
    cover = lambda p: round(min(1.0, (p["pk"][3] if p["pk"] else 0) / 740), 3) if v["container"] != "page" else 1.0
    return {"ops": ops, "taps": tk[0], "keys": tk[1], "drags": tk[2], "reach": round(sum(ids) / max(1, len(ids)), 3),
            "unseen": len(unseen_needed), "unseen_names": sorted(unseen_needed),
            "line": 0 if v["container"] in ("keyboard", "popover") else 1, "load": 0 if (v["load"] or control) else 1,
            "heights": max(max(1, len({x[4] for x in p["m"]["vis"]})) for p in per), "edges": 1,
            "sprawl": max(p["sprawl"] for p in per), "heavy": max(p["heavy"] for p in per),
            "clutter": round(sum(p["clutter"] for p in per) / len(per), 4), "covered": max(cover(p) for p in per),
            "controls": max(len(p["pk_taps"]) for p in per),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for p in per for x in p["pk_taps"] if x["w"] < 48 or x["h"] < 48})}


AXES = {"H": (("heights", 1), ("sprawl", 1), ("heavy", 1)),
        "U": (("taps", 1), ("keys", 1), ("drags", 1), ("reach", 1), ("line", 1), ("load", 1)),  # taps, keys, drags apart
        "C": (("clutter", 1), ("covered", 1), ("controls", 1))}


def main():
    rows = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        r = dict(v=v, control=False, **score(v))
        rows.append(r)
        print(len(rows), v, {k: r[k] for k in ("ops", "reach", "unseen", "heavy", "clutter", "covered", "controls", "small")}, flush=True)
    ctrl = dict(v={"container": "sheet", "entry": "all", "load": True, "end": "both"}, control=True,
                **score({"container": "sheet", "entry": "typed", "load": True, "end": "duration", "steps": "one"}, True))
    rows.append(ctrl)
    # owner, 2026-10-08: everything a task needs must be visible (as the Hub): a cut-off control is a constraint
    ok = [r for r in rows if not r["small"] and (r["unseen"] == 0 or r["control"])]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    with open(os.path.join(v2.OUT, "picker-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front], "control_beaten": ctrl not in front}, fh, indent=1, ensure_ascii=False)
    print("front", len(front), "control beaten", ctrl not in front)
    for r in sorted(front, key=lambda r: r["H"] + r["U"] + r["C"]):
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]), {k: r[k] for k in ("ops", "reach", "unseen", "line", "heavy", "clutter", "covered")})
    if ctrl in front:
        sys.exit(2)


if __name__ == "__main__":
    main()
