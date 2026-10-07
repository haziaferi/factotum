"""Capture sheet v2: one natural-language line for every module, scored on three axes (owner, 2026-10-07).

Owner's frame: no colour yet, so nothing may win on colour; targets 48 dp, but a control is never drawn larger
than the text box beside it; the keyboard's Enter may be the add button (the line needs no line breaks); the line
creates tasks, events, reminders, tracker and habit logs, journal lines, timers and time logs, check-in and ledger
entries; the screen it opens from sets the default kind; routing options (inferred kind chip, a kind row, typed
prefixes, Todoist's +, TickTick's ⋯) and the add options are scored together on harmony, ease of use and clutter.
Evidence: _screens-sources/nl-capture-research.md (gitignored) and the phone captures in _screens-sources/capture/.

Every measure comes from the render or from a design engine, not from taste:
  Harmony (H)
    heights      distinct drawn heights among the sheet's controls and chips (craftkit's "one shape decision":
                 radius-sprawl, type-sizes-sprawl); 1 is one height for everything
    over_box     controls drawn taller than the line's text box (owner's rule; a constraint, must be 0)
    emphasis     designkit layout.emphasis_coherence: do the two heaviest elements (mass measured as craftkit
                 imgstat's departure from the ground tone) match the importance order line > chips > kind > add?
    edges        distinct left edges the sheet's rows start at (one edge = aligned)
    sprawl       craftkit ui warnings + off-grid spacing notes on the sheet alone
  Ease of use (U)
    taps_fix     taps to change the kind when the guess is wrong (0 with a typed prefix)
    taps_more    taps to reach the full form (Details)
    submit_id    Fitts' ID from the keyboard's centre (where typing ends) to the submit target: the Enter key
                 (Gboard's, measured 53 x 46 dp) or the on-screen button
    hidden       what the person cannot see before adding: the kind (Nielsen's visibility of system status) and
                 any on-screen submit (the research's point 9: an on-screen button as well as the IME action)
  Clutter (C)
    clutter      edge density of the phone render (screen_score), mean of light and dark, over the inputs
    controls     tappable elements on the sheet
    sheet        the sheet's height, the tallest over the inputs

Each axis is the sum of its measures' ranks (Borda), so no hand-set weights; the front is over (H, U, C), with
the owner's rule and 48 dp targets as constraints. A control (everything at once, a big filled button) must lose.

    PYTHONUTF8=1 python tools/screens/capture_v2.py
"""
import glob
import itertools
import json
import math
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

CRAFT = sorted(glob.glob(os.path.expanduser(r"~/.claude/plugins/synced/*/creative-design-suite/engine")))[-1]
DESIGN = sorted(glob.glob(os.path.expanduser(r"~/.claude/plugins/cache/gold-standard-local/design-optimization/*/engine")))[-1]
sys.path[:0] = [CRAFT, DESIGN]
from craftkit import imgstat  # noqa: E402
from designkit import layout as dk_layout  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "docs", "screens", "t1")
KB_MID, ENTER_KEY, ENTER_W = (180, 615), (330, 712), 46

# inputs drawn and measured: the busiest parse, a tracker log, a journal line (opened from Journal: context)
INPUTS = [
    ("event", "Dentist tomorrow 9am every 6 months", "Event", ["Tue 6 Oct", "09:00", "Every 6 months"]),
    ("log", "water 2", "Log", ["Water", "2 glasses", "Now"]),
    ("journal", "slept badly, calmer after the walk", "Journal", ["Today's page"]),
]
KINDS_ROW = ["Task", "Event", "Log", "Journal", "More"]
ROUTING = {
    "chip": "inferred; the kind is the first chip, a tap changes it",
    "row": "a row of kinds above the line (Craft's mode row); the inferred one is selected",
    "prefix": "inferred, kind chip, and typed prefixes (Fantastical's leading words)",
    "plus": "Todoist: a + at the chip row's start opens kinds and fields; the kind is not shown",
    "more": "TickTick: a ⋯ at the chip row's end opens kinds, fields and the full form; the kind is not shown",
}
SPACE = {"routing": list(ROUTING), "add": ["enter", "line", "chips"], "fill": ["tonal", "ghost", "outline"], "h": [32, 36]}

CSS = """
.c2 .sheet{padding:12px 12px 8px}
.c2 .line{display:flex;align-items:center;gap:4px;min-height:48px;font-size:18px}
.c2 .line .in{flex:1;min-width:0}
.c2 .crow{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.c2 .chips{display:contents}
.c2 .tg{min-height:48px;min-width:48px;display:inline-flex;align-items:center;justify-content:center;flex:none;color:var(--ink);font-size:14px}
.c2 .vis{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:0 12px;white-space:nowrap}
.c2 .pchip .vis{background:var(--zone2);font-size:13px}
.c2 .kind .vis{background:var(--zone2);font-weight:600;font-size:13px}
.c2 .f-tonal .vis{background:var(--zone2)}
.c2 .f-ghost .vis{background:transparent}
.c2 .f-outline .vis{background:transparent;box-shadow:inset 0 0 0 1.5px var(--dim)}
.c2 .route{display:flex;gap:4px;margin:0 0 4px}
.c2 .route .tg{flex:1;min-width:0}.c2 .route .vis{width:100%;padding:0 4px;font-size:13px}
.c2 .route .on .vis{background:var(--zone2);font-weight:600}
.c2 .hint{font-size:12px;color:var(--dim);padding:2px 2px 4px}
.c2 .grow{flex:1}
"""


def control(name, label, h, fill="tonal", square=True, cls=""):
    w = "width:%dpx;padding:0;" % h if square else ""
    return '<span class="tg f-%s %s" data-tap="%s"><span class="vis" data-vis="%s" style="height:%dpx;%s">%s</span></span>' % (
        fill, cls, name, name, h, w, label)


def sheet(v, text, kind, chips, control_mode=False):
    h, fill = v["h"], v["fill"]
    # a short kind ("Log") is narrower than its 48 px target: drawn from the target's left edge, not centred in it,
    # so it lines up with the text above (a centred one sat 1 px in, which the edges measure caught)
    kind_chip = '<span class="tg kind" data-tap="Kind" style="justify-content:flex-start"><span class="vis" data-vis="kind" style="height:%dpx">%s</span></span>' % (h, kind)
    chip_html = "".join('<span class="tg pchip" data-tap="Fix %s"><span class="vis" data-vis="chip" style="height:%dpx">%s</span></span>' % (c, h, c) for c in chips)
    add = control("Add", "✓", h, "tonal" if fill == "tonal" else fill) if v["add"] != "enter" else ""
    details = control("Full form", "Details", h, "ghost", square=False)
    route, lead, tail = "", "", ""
    if v["routing"] in ("chip", "prefix"):
        lead, tail = kind_chip, details
    elif v["routing"] == "row":
        route = '<div class="route">%s</div>' % "".join(
            '<span class="tg%s" data-tap="Kind %s"><span class="vis" data-vis="seg" style="height:%dpx">%s</span></span>' % (
                " on" if k == kind else "", k, h, k) for k in KINDS_ROW)
        tail = details
    elif v["routing"] == "plus":
        lead = control("Add details", "+", h, "tonal")
    elif v["routing"] == "more":
        tail = control("More", "⋯", h, "ghost")
    if control_mode:  # everything at once, and a big filled button
        route = '<div class="route">%s</div>' % "".join('<span class="tg%s" data-tap="Kind %s"><span class="vis" data-vis="seg" style="height:%dpx">%s</span></span>' % (
            " on" if k == kind else "", k, h, k) for k in KINDS_ROW)
        lead = control("Add details", "+", h, "tonal") + kind_chip
        tail = details + control("More", "⋯", h, "ghost")
        add = '<span class="tg" data-tap="Add"><span class="vis" data-vis="add" style="height:56px;width:56px;padding:0;background:var(--ink);color:var(--bg);font-size:24px">✓</span></span>'
    on_line = add if v["add"] == "line" else ""
    on_row = add if v["add"] == "chips" or control_mode else ""
    line = '<div class="line"><span class="in">%s<span class="caret"></span></span>%s</div>' % (kit.ud(t.e(text)), on_line)
    # the trailing controls stay right-aligned for the right thumb, also when they wrap to a row of their own
    row = '<div class="crow"><div class="chips">%s%s</div><span style="margin-left:auto;display:flex;gap:6px">%s%s</span></div>' % (lead, chip_html, tail, on_row)
    hint = '<div class="hint">j journal · log · t timer · ci check-in</div>' if v["routing"] == "prefix" else ""
    return '<div class="sheet">%s%s%s%s</div>' % (route, line, row, hint)


def phone(v, item, control_mode=False):
    _, text, kind, chips = item
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s'
               '<div class="kb">keyboard</div></div>') % sheet(v, text, kind, chips, control_mode)
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, item, theme="light", score=True, control_mode=False):
    return kit.document(phone(v, item, control_mode), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


def masses(png, m):
    sx, sy, sw, sh = m["boxes"]["sheet"]
    crop = png.replace(".png", "-c2sheet.png")
    Image.open(png).convert("RGB").crop((int(sx), int(sy), int(sx + sw), int(sy + sh))).save(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    hist = {}
    for val in lum:
        hist[int(val * 32)] = hist.get(int(val * 32), 0) + 1
    ground = (max(hist.items(), key=lambda kv: kv[1])[0] + 0.5) / 32.0

    def mass(box):
        x0, y0, bw, bh = int(box[0] - sx), int(box[1] - sy), int(box[2]), int(box[3])
        return sum(abs(lum[y * img.w + x] - ground) for y in range(max(0, y0), min(img.h, y0 + bh)) for x in range(max(0, x0), min(img.w, x0 + bw)))
    taps = {}
    for x in m["taps"]:
        taps.setdefault(x["name"], []).append(x["box"])
    out = {"line": mass(m["boxes"]["line"])}
    out["chips"] = sum(mass(b) for n, bs in taps.items() if n.startswith("Fix ") for b in bs)
    out["kind"] = sum(mass(b) for n in ("Kind",) for b in taps.get(n, [])) + sum(mass(b) for n, bs in taps.items() if n.startswith("Kind ") for b in bs)
    out["add"] = sum(mass(b) for b in taps.get("Add", []))
    out["more"] = sum(mass(b) for n in ("Full form", "More", "Add details") for b in taps.get(n, []))
    return out


def craft_sprawl(v, item, control_mode):
    """craftkit ui on the sheet alone (no Today behind it): warnings plus off-grid spacing notes."""
    path = os.path.join(ss.CACHE, "c2-%s.html" % abs(hash((tuple(sorted(v.items())), item[0], control_mode))))
    body = '<div class="c2" style="width:360px">%s</div>' % sheet(v, item[1], item[2], item[3], control_mode)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(kit.document(body, "light", t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, True))
    res = subprocess.run([sys.executable, os.path.join(CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUTF8="1"))
    data = json.loads(res.stdout)
    found = data.get("findings", data.get("issues", []))
    # colour is out (no palette yet; owner: nothing wins on colour), so colour and contrast codes are not counted
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast"))
               and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


IMPORTANCE = ["line", "chips", "kind", "add", "more"]


def score(v, control_mode=False):
    per = []
    for item in INPUTS:
        d = doc(v, item, control_mode=control_mode)
        m = ss.measure(d, 360, 740)
        clutter = sum(ss.edge_density(ss.render(doc(v, item, th, control_mode=control_mode), 360, 740)) for th in ("light", "dark")) / 2
        ms = masses(ss.render(d, 360, 740), m)
        top = [k for k, _ in sorted(ms.items(), key=lambda kv: -kv[1])][:2]
        emph = dk_layout.emphasis_coherence({"emphasis_primary": top[0], "emphasis_secondary": top[1], "section_order": IMPORTANCE},
                                            {"importance": IMPORTANCE})
        box_h = m["boxes"]["linebox"][3]
        vis = m["vis"]
        sheet_taps = [x for x in m["taps"] if x["box"][1] >= m["boxes"]["sheet"][1] - 1]
        rows = [m["boxes"]["line"][0]] + [min((x[1] for x in vis if x[0] in ("chip", "kind")), default=m["boxes"]["line"][0])]
        if m["boxes"].get("route"):
            rows.append(m["boxes"]["route"][0])
        lead = [x for x in vis if x[0] in ("Add details",)]
        if lead:
            rows[1] = lead[0][1]
        add = [x for x in m["taps"] if x["name"] == "Add"]
        sub = (math.log2(math.hypot(KB_MID[0] - add[0]["x"], KB_MID[1] - add[0]["y"]) / min(add[0]["w"], add[0]["h"]) + 1) if add
               else math.log2(math.hypot(KB_MID[0] - ENTER_KEY[0], KB_MID[1] - ENTER_KEY[1]) / ENTER_W + 1))
        per.append({"heights": len({x[4] for x in vis}), "over_box": sum(1 for x in vis if x[4] > box_h), "emphasis": emph, "top": top,
                    "edges": len({round(x) for x in rows}), "sprawl": craft_sprawl(v, item, control_mode), "submit_id": sub,
                    "clutter": clutter, "controls": len(sheet_taps), "sheet": m["sheet_h"],
                    "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if (x["w"] < 48 or x["h"] < 48) and x in sheet_taps})})
    r = v["routing"]
    agg = {
        "heights": max(p["heights"] for p in per), "over_box": max(p["over_box"] for p in per),
        "emphasis": round(sum(p["emphasis"] for p in per) / len(per), 3), "edges": max(p["edges"] for p in per),
        "sprawl": max(p["sprawl"] for p in per),
        "taps_fix": 0 if r == "prefix" else (1 if r == "row" or control_mode else 2),
        "taps_more": 1 if r in ("chip", "prefix", "row") or control_mode else 2,
        "submit_id": round(sum(p["submit_id"] for p in per) / len(per), 2),
        "hidden": (0 if r in ("chip", "prefix", "row") or control_mode else 1) + (1 if v["add"] == "enter" and not control_mode else 0),
        "clutter": round(sum(p["clutter"] for p in per) / len(per), 4), "controls": max(p["controls"] for p in per),
        "sheet": max(p["sheet"] for p in per), "small": sorted({s for p in per for s in p["small"]}),
        "tops": [p["top"] for p in per],
    }
    return agg


AXES = {"H": (("heights", 1), ("over_box", 1), ("emphasis", -1), ("edges", 1), ("sprawl", 1)),
        "U": (("taps_fix", 1), ("taps_more", 1), ("submit_id", 1), ("hidden", 1)),
        "C": (("clutter", 1), ("controls", 1), ("sheet", 1))}
TOL = {"clutter": 0.002, "emphasis": 0.01, "submit_id": 0.05}


def ranks(rows, key, sign):
    vals = [sign * r[key] for r in rows]
    out = []
    for x in vals:  # average rank with ties inside tolerance
        less = sum(1 for y in vals if y < x - TOL.get(key, 1e-9))
        eq = sum(1 for y in vals if abs(y - x) <= TOL.get(key, 1e-9))
        out.append(less + (eq + 1) / 2)
    return out


def main():
    variants = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        if v["add"] == "enter" and v["fill"] != "tonal":
            continue  # no on-screen button: its fill does not exist
        variants.append(v)
    rows = []
    for v in variants:
        rows.append(dict(v=v, control=False, **score(v)))
        print(len(rows), v, {k: rows[-1][k] for k in ("emphasis", "heights", "submit_id", "clutter", "sheet")}, flush=True)
    rows.append(dict(v={"routing": "all", "add": "chips", "fill": "filled", "h": 36}, control=True, **score({"routing": "chip", "add": "chips", "fill": "tonal", "h": 36}, True)))
    ok = [r for r in rows if r["over_box"] == 0 and not r["small"]]
    for axis, parts in AXES.items():
        rk = [ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    for r in rows:
        r.setdefault("H", None)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    ctrl = rows[-1]
    beaten = ctrl not in front
    with open(os.path.join(OUT, "capture-v2.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front], "control_beaten": beaten}, fh, indent=1, ensure_ascii=False)
    print("front:", len(front), "control beaten:", beaten)
    for r in sorted(front, key=lambda r: r["H"] + r["U"] + r["C"]):
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]), {k: r[k] for k in ("emphasis", "heights", "edges", "sprawl", "taps_fix", "submit_id", "hidden", "clutter", "controls", "sheet")})
    if not beaten:
        sys.exit(2)


if __name__ == "__main__":
    main()
