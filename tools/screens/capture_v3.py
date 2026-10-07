"""Capture sheet v3 (owner, 2026-10-07): the prefix variant, its hint shown only while the line is empty, with
  tail     ⋯ in place of Details (opens the full form, kind and templates) | a row of small icons in its place
           (TickTick's tool row) | the icons and ⋯
  display  the parse as chips under the line | the parsed words underlined in the line | highlighted in the line
           (Todoist, Microsoft To Do); with underline or highlight there is no chip row, only the kind chip and tail
  add      Enter (the IME action) | Enter and a ✓ at the row's end
Scored on capture_v2's axes and measures, plus, from the owner's concern about "unjustified empty space":
  empty    the share of the sheet's grid cells with almost no detail (craftkit imgstat _detail_report, empty_share)
  unshown  parsed values the sheet does not show resolved (underline and highlight mark "tomorrow" but not
           "Tue 6 Oct", nor a log's unit or tracker): what the person cannot check before adding
Inputs: capture_v2's three, plus the empty line (where the prefix hint shows).

    PYTHONUTF8=1 python tools/screens/capture_v3.py
"""
import itertools
import json
import math
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
from craftkit import imgstat  # noqa: E402  (path set by capture_v2)

# the words each input's parse rests on, and how many resolved values chips show that marks in the text do not
MARKS = {"event": ["tomorrow 9am", "every 6 months"], "log": ["water", "2"], "journal": []}
RESOLVED = {"event": 2, "log": 2, "journal": 1}  # Tue 6 Oct + 09:00; Water as a tracker + glasses; Today's page
EMPTY = ("empty", "", "Task", [])
INPUTS = v2.INPUTS + [EMPTY]
SPACE = {"tail": ["more", "icons", "icons+more"], "display": ["chips", "underline", "highlight"], "add": ["enter", "chips"]}
ICONS = [("Date", "▦"), ("Repeat", "↻"), ("Reminder", "◔"), ("Label", "#")]
H, FILL = 32, "ghost"  # drawn height and ✓ fill: tied on every measure in v2
CSS = v2.CSS + """
.c2 .ul{text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:3px}
.c2 .hl{background:var(--zone2);border-radius:4px;padding:0 2px}
.c2 .ph{color:var(--dim)}
"""


def marked(text, key, display):
    out = t.e(text)
    for w in MARKS.get(key, []):
        out = out.replace(w, '<span class="%s">%s</span>' % ("ul" if display == "underline" else "hl", w), 1)
    return out


def sheet(v, item, control_mode=False):
    key, text, kind, chips = item
    ctl = v2.control
    kind_chip = ('<span class="tg kind" data-tap="Kind" style="justify-content:flex-start"><span class="vis" data-vis="kind" style="height:%dpx">%s</span></span>' % (H, kind))
    km = v.get("kind", "chip")  # capture_v4: how the kind shows (owner, 2026-10-07: is the chip needed?)
    caption_row = ""
    if km == "inline":  # the kind as hint-sized text at the row's start, still a 48 px target
        kind_chip = '<span class="tg" data-tap="Kind" style="justify-content:flex-start"><span class="kcap" style="font-size:12px;color:var(--dim)">%s</span></span>' % kind
    elif km == "row":  # the kind as a hint-sized line where the hint sits; changed by prefix or ⋯ › Kind
        kind_chip, caption_row = "", '<div class="hint">%s</div>' % kind
    elif km == "none":
        kind_chip = ""
    shown_chips = chips if v["display"] == "chips" else []
    chip_html = "".join('<span class="tg pchip" data-tap="Fix %s"><span class="vis" data-vis="chip" style="height:%dpx">%s</span></span>' % (c, H, c) for c in shown_chips)
    icons = "".join(ctl(n, g, H, "ghost") for n, g in ICONS) if v["tail"] in ("icons", "icons+more") else ""
    more = ctl("More", "⋯", H, "ghost") if v["tail"] in ("more", "icons+more") else ""
    add = ctl("Add", "✓", H, FILL) if v["add"] == "chips" else ""
    if control_mode:
        add = '<span class="tg" data-tap="Add"><span class="vis" data-vis="add" style="height:56px;width:56px;padding:0;background:var(--ink);color:var(--bg);font-size:24px">✓</span></span>'
        icons = "".join(ctl(n, g, H, "ghost") for n, g in ICONS)
        more = ctl("More", "⋯", H, "ghost") + ctl("Full form", "Details", H, "ghost", square=False)
    if key == "empty":
        inner = '<span class="ph">Add a task, event, log or journal line…</span>'
    else:
        body = t.e(text) if v["display"] == "chips" else marked(text, key, v["display"])
        inner = kit.ud(body) + '<span class="caret"></span>'
    line = '<div class="line"><span class="in">%s</span></div>' % inner
    row = '<div class="crow"><div class="chips">%s%s</div><span style="margin-left:auto;display:flex;gap:6px">%s%s%s</span></div>' % (
        kind_chip, chip_html, icons, more, add)
    hint = '<div class="hint">j journal · log · t timer · ci check-in</div>' if key == "empty" else (caption_row if not control_mode else "")
    return '<div class="sheet">%s%s%s</div>' % (line, row, hint)


def phone(v, item, control_mode=False):
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s'
               '<div class="kb">keyboard</div></div>') % sheet(v, item, control_mode)
    return today[:-len("</div>")] + overlay + "</div>"


def doc(v, item, theme="light", score=True, control_mode=False):
    return kit.document(phone(v, item, control_mode), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


def empty_share(png, m):
    sx, sy, sw, sh = m["boxes"]["sheet"]
    crop = png.replace(".png", "-c3sheet.png")
    Image.open(png).convert("RGB").crop((int(sx), int(sy), int(sx + sw), int(sy + sh))).save(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    return imgstat._detail_report(imgstat._sobel(lum, img.w, img.h), img.w, img.h).get("empty_share", 0.0)


def score(v, control_mode=False):
    # reuse capture_v2.score's measuring by swapping its document builder for this module's
    saved = v2.doc, v2.INPUTS
    v2.doc = lambda vv, item, theme="light", score=True, control_mode=False: doc(vv, item, theme, score, control_mode)
    v2.INPUTS = v2.INPUTS  # the three typed inputs; the empty one is measured below
    v2_sheet = v2.sheet
    v2.sheet = lambda vv, text, kind, chips, cm=False: sheet(vv, next(i for i in INPUTS if i[1] == text), cm)
    try:
        agg = v2.score(dict(v, routing="prefix", h=H, fill=FILL), control_mode)
    finally:
        v2.doc, v2.INPUTS = saved
        v2.sheet = v2_sheet
    empties, heights = [], []
    for item in INPUTS:
        d = doc(v, item, control_mode=control_mode)
        m = ss.measure(d, 360, 740)
        empties.append(empty_share(ss.render(d, 360, 740), m))
        heights.append(m["sheet_h"])
    agg["empty"] = round(sum(empties) / len(empties), 3)
    agg["sheet"] = max(heights[:-1])  # typed inputs: the empty line's hint is the same in every variant
    agg["sheet_empty"] = heights[-1]
    agg["sheet_typed_min"] = min(heights[:-1])
    agg["unshown"] = 0 if v["display"] == "chips" or control_mode else sum(RESOLVED.values())
    agg["taps_fix"] = 0  # prefixes
    agg["taps_more"] = 1 if v["tail"] != "icons" else 2  # the icons open single fields; the full form sits in their long press / ⋯
    agg["hidden"] = (1 if v["add"] == "enter" and not control_mode else 0)
    return agg


AXES = {"H": (("heights", 1), ("over_box", 1), ("emphasis", -1), ("edges", 1), ("sprawl", 1)),
        "U": (("taps_more", 1), ("submit_id", 1), ("hidden", 1), ("unshown", 1)),
        "C": (("clutter", 1), ("controls", 1), ("sheet", 1), ("empty", 1))}


def main():
    rows = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        rows.append(dict(v=v, control=False, **score(v)))
        print(len(rows), v, {k: rows[-1][k] for k in ("emphasis", "sheet", "empty", "controls", "clutter", "unshown")}, flush=True)
    rows.append(dict(v={"tail": "all", "display": "chips", "add": "big"}, control=True, **score({"tail": "icons+more", "display": "chips", "add": "chips"}, True)))
    ok = [r for r in rows if r["over_box"] == 0 and not r["small"]]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    beaten = rows[-1] not in front
    with open(os.path.join(v2.OUT, "capture-v3.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front], "control_beaten": beaten}, fh, indent=1, ensure_ascii=False)
    print("front:", len(front), "control beaten:", beaten)
    for r in front:
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]))
    if not beaten:
        sys.exit(2)


if __name__ == "__main__":
    main()
