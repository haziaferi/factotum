"""Where the shorthand legend sits (owner, 2026-10-07): five options scored against the approved capture sheet
(no chips, highlighted parse, the kind in the hint's place, ⋯ beside the line; decision 17).

  scroll    the hint line holds all 14 shorthands and scrolls sideways
  context   empty: the kinds; once a kind's shorthand is typed, the small line shows that kind's field markers
  menu      ⋯ › Shorthands opens the full table over the sheet
  ask       a "?" at the hint's end opens the full table over the sheet
  settings  a reference page in Settings (Help › Shorthands); the hint keeps its five kinds
  control   all 14 always on, in three hint lines (it should lose on clutter)

States drawn: the empty line (at rest), "ev dentist tomorrow 9am" (a kind's shorthand typed) and, for menu and ask,
the table open. Measures (render and DOM, as capture_v2):
  U  rest      shorthands readable on the sheet at rest, of 14 (higher is better)
     typed     shorthands readable once a kind's shorthand is typed (higher is better)
     reach     taps (or swipes) to see all 14: scroll swipes, menu 2, ask 1, settings 3 (and capture closes)
     leaves    consulting the legend closes the capture sheet and the typed line (settings)
  C  sheet     the sheet's height at rest; clutter (edge density); controls on the sheet; covered (share of
     the screen the open table hides)
  H  heights, edges and sprawl (craftkit ui) of the sheet at rest
Each axis is a sum of ranks; the front is over (H, U, C).

    PYTHONUTF8=1 python tools/screens/legend_opt.py
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

KINDS = [("j", "journal"), ("lg", "log"), ("t", "timer"), ("ck", "check-in"), ("td", "task"), ("ev", "event"), ("rm", "reminder"), ("ld", "ledger")]
FIELDS = [("#", "label"), ("!", "reminder"), ("@", "calendar"), ("^", "page"), ("~", "duration"), ("*", "repeat")]
EVENT_FIELDS = ["#", "!", "@", "^", "*"]  # an event's markers (no duration: its time says it)
VARIANTS = ["scroll", "context", "menu", "ask", "settings", "control"]
H = 32
CSS = v2.CSS + """
.c2 .hl{background:var(--zone2);border-radius:4px;padding:0 2px}
/* owner, 2026-10-07: ⋯ stays level with the first line when the text wraps; the text keeps its own rectangle */
.c2 .line{align-items:flex-start}.c2 .line .in{padding:13px 0 0;line-height:22px}
.c2 .ph{color:var(--dim)}
.c2 .hint{font-size:12px;color:var(--dim);padding:2px 2px 4px;white-space:nowrap}
.c2 .hint.scroll{overflow-x:auto;overflow-y:hidden;scrollbar-width:none}
.c2 .hint.wrap{white-space:normal}
.c2 .hintrow{display:flex;align-items:center}.c2 .hintrow .hint{flex:1;min-width:0;overflow:hidden}
.legend{position:absolute;left:0;right:0;bottom:100%;background:var(--zone);border-radius:16px 16px 0 0;box-shadow:0 -8px 24px rgba(0,0,0,.14);padding:10px 14px}
.legend .g{display:grid;grid-template-columns:1fr 1fr;column-gap:12px}
.legend .r{min-height:28px;display:flex;align-items:center;gap:8px;font-size:13px}.legend b{min-width:22px;font-weight:600}
.legend h5{margin:4px 0;font-size:12px;color:var(--dim);font-weight:600}
"""


def item(tok, name):
    return '<span class="lgi">%s %s</span>' % (tok, name)


def legend_table():
    rows = lambda xs: "".join('<div class="r lgi"><b>%s</b>%s</div>' % (a, b) for a, b in xs)
    return ('<div class="legend"><h5>Start a line with</h5><div class="g">%s</div><h5>Anywhere in the line</h5><div class="g">%s</div></div>' % (rows(KINDS), rows(FIELDS)))


def sheet(variant, state):
    more = v2.control("More", "⋯", H, "ghost")
    if state in ("empty", "open"):
        inner = '<span class="ph">Add a task, event, log or journal line…</span>'
    else:
        inner = kit.ud('<span class="hl">ev</span> dentist <span class="hl">tomorrow 9am</span>' + (
            ' with the new hygienist <span class="hl">*every</span> 6 months' if state == "wrapped" else "")) + '<span class="caret"></span>'
    line = '<div class="line"><span class="in">%s</span>%s</div>' % (inner, more)
    kinds = " · ".join(item(a, b) for a, b in KINDS)
    every = kinds + " · " + " · ".join(item(a, b) for a, b in FIELDS)
    five = " · ".join(item(a, b) for a, b in KINDS[:5])
    if variant == "control":
        hint = '<div class="hint wrap">%s</div>' % every
    elif state in ("empty", "open"):
        if variant in ("scroll", "both"):  # both (owner, 2026-10-07): scrolling while empty, the kind's markers once typed
            hint = '<div class="hint scroll">%s</div>' % every
        elif variant == "ask":
            hint = '<div class="hintrow"><div class="hint">%s</div>%s</div>' % (" · ".join(item(a, b) for a, b in KINDS[:4]), v2.control("Shorthands", "?", H, "ghost"))
        else:
            hint = '<div class="hint">%s</div>' % five
    else:  # typed (or wrapped) with a kind's shorthand: the kind takes the hint's place (approved)
        if variant in ("context", "both"):
            hint = '<div class="hint">Event · %s</div>' % " · ".join(item(a, b) for a, b in FIELDS if a in EVENT_FIELDS)
        else:
            hint = '<div class="hint">Event</div>'
    return '<div class="sheet" style="position:relative">%s%s%s</div>' % (line, hint, legend_table() if state == "open" else "")


def phone(variant, state):
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s'
               '<div class="kb">keyboard</div></div>') % sheet(variant, state)
    return today[:-len("</div>")] + overlay + "</div>"


def doc(variant, state, theme="light", score=True):
    return kit.document(phone(variant, state), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


def sprawl(variant):
    path = os.path.join(ss.CACHE, "legend-%s.html" % variant)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc(variant, "empty"))
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast"))
               and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


def score(variant):
    rest = ss.measure(doc(variant, "empty"), 360, 740)
    typed = ss.measure(doc(variant, "typed"), 360, 740)
    clutter = sum(ss.edge_density(ss.render(doc(variant, "empty", th), 360, 740)) for th in ("light", "dark")) / 2
    sheet_taps = [x for x in rest["taps"] if x["box"][1] >= rest["boxes"]["sheet"][1] - 1]
    covered, open_seen = 0.0, 0
    if variant in ("menu", "ask"):  # the table open over the sheet: the share of the screen it hides, measured
        op = ss.measure(doc(variant, "open"), 360, 740)
        lg = op["boxes"].get("legend")
        covered = round(lg[2] * lg[3] / (360 * 740), 3) if lg else 0.0
        open_seen = sum(op["lgi"])
    # swipes to bring every item into view on a scrolling hint: its full width over the visible width
    reach = {"scroll": None, "both": None, "context": 99, "menu": 2, "ask": 1, "settings": 3, "control": 0}[variant]
    if variant in ("scroll", "both"):
        visible = sum(rest["lgi"])
        reach = math.ceil(14 / max(1, visible)) - 1
    return {"rest": sum(rest["lgi"]), "typed": sum(typed["lgi"]), "reach": reach, "leaves": 1 if variant == "settings" else 0,
            "open_seen": open_seen, "sheet": rest["sheet_h"], "clutter": round(clutter, 4), "controls": len(sheet_taps), "covered": covered,
            "heights": max(1, len({x[4] for x in rest["vis"]})), "edges": 1, "sprawl": sprawl(variant),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in sheet_taps if x["w"] < 48 or x["h"] < 48}),
            "min_text": rest["min_text"]}


AXES = {"H": (("heights", 1), ("edges", 1), ("sprawl", 1)),
        "U": (("rest", -1), ("typed", -1), ("reach", 1), ("leaves", 1)),
        "C": (("sheet", 1), ("clutter", 1), ("controls", 1), ("covered", 1))}


def main():
    rows = []
    for vname in VARIANTS:
        r = dict(v=vname, control=vname == "control", **score(vname))
        rows.append(r)
        print(vname, {k: r[k] for k in ("rest", "typed", "reach", "leaves", "sheet", "clutter", "controls", "covered", "sprawl", "small")}, flush=True)
    ok = [r for r in rows if not r["small"]]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    ctrl = rows[-1]
    with open(os.path.join(v2.OUT, "legend-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [r["v"] for r in front], "control_beaten": ctrl not in front}, fh, indent=1, ensure_ascii=False)
    for r in sorted(ok, key=lambda r: r["H"] + r["U"] + r["C"]):
        print("%s %-9s H %4.1f U %4.1f C %4.1f" % ("*" if r in front else " ", r["v"], r["H"], r["U"], r["C"]))
    print("control beaten:", ctrl not in front)


if __name__ == "__main__":
    main()
