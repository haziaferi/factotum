"""Capture sheet (T1.3 A′): sizes and the placement of ✓ (Add) and ▤ (Full form), searched exhaustively
(owner, 2026-10-07: free = ✓/▤ placement and sizes; chips stay under the line; balanced, so a Pareto front;
right thumb, with a mirror setting). Writes docs/screens/t1/capture-opt.md and capture-opt.json.

Model, in dp on a 360 x 740 phone with a 250 dp keyboard (its top at y 490). The sheet sits on the keyboard.
Text wraps by width; chips pack into rows. All of it is computed from the variables below, then the chosen
layouts are rendered and re-measured with screen_score (tier_t1 draws them), so the model is checked against the
page it describes.

Objectives
  fitts_add     Fitts' index of difficulty log2(D/W + 1) from the keyboard's Enter key (330, 712), where the right
                thumb rests after typing, to ✓. Lower is easier (MacKenzie 1992's Shannon form).
  fitts_chips   the same, mean over the chips, from the keyboard's centre (180, 615)
  fitts_form    the same to ▤ (secondary)
  sheet         sheet height above the keyboard (less hides less of Today)
  spacing       the smallest gap between ✓'s target and any other target, keyboard included (more is safer)
  text          the line's font size (more is easier to read, 18 at most)
  lines         lines the sample text wraps to (fewer reads as one thought)
Assumptions, stated: glyph width 0.52 em for the system sans; chip text 13 px; the sample is the decision-17 one.

    PYTHONUTF8=1 python tools/screens/capture_opt.py
"""
import itertools
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t1")
W, H, KB = 360, 740, 250
KTOP = H - KB
ENTER = (330, 712)
KB_MID = (180, 615)
REST = ENTER
# Frames for the sensitivity check: the assumed 360 dp phone, and the owner's phone as measured over adb
# (1080 x 2340 px at 450 dpi = 384 x 832 dp; Gboard's top at 497 dp, its Enter key centred at 355, 751).
FRAMES = {
    "model 360": {"W": 360, "KTOP": 490, "ENTER": (330, 712), "KB_MID": (180, 615)},
    "phone 384": {"W": 384, "KTOP": 497, "ENTER": (355, 751), "KB_MID": (192, 640)},
}
PAD_X, PAD_TOP, PAD_BOT = 12, 16, 8
SAMPLE = "Dentist tomorrow 9am every 6 months"
CHIPS = ["Tue 6 Oct", "09:00", "Every 6 months", "Event"]
EM = 0.52

PLACEMENTS = {
    "line": "✓ and ▤ at the right of the line (as approved)",
    "chips": "✓ and ▤ at the right of the chip row (Todoist, TickTick)",
    "row": "an action row above the keyboard: ▤ left, ✓ right",
    "split": "▤ at the right of the line, ✓ at the right of the chip row",
}
SPACE = {"place": list(PLACEMENTS), "font": [15, 16, 17, 18], "line_h": [48, 52, 56], "chip_h": [32, 34, 36],
         "add": [48, 52, 56], "gap": [4, 8, 12]}


def text_lines(font, width):
    per_line = max(1, int(width / (font * EM)))
    words, lines, cur = SAMPLE.split(), 1, 0
    for w in words:
        need = len(w) + (1 if cur else 0)
        if cur + need > per_line:
            lines, cur = lines + 1, len(w)
        else:
            cur += need
    return lines


def chip_rows(width, reserve):
    rows, x = 1, 0
    for c in CHIPS:
        cw = len(c) * 13 * EM + 24
        if x and x + 6 + cw > width - reserve:
            rows, x = rows + 1, cw
        else:
            x = x + (6 if x else 0) + cw
    return rows


def fitts(src, centre, width):
    d = math.hypot(src[0] - centre[0], src[1] - centre[1])
    return math.log2(d / width + 1)


def layout(v):
    inner = W - 2 * PAD_X
    form_w, add_w = 48, v["add"]
    line_res = form_w + add_w + 8 if v["place"] == "line" else (form_w + 4 if v["place"] == "split" else 0)
    chip_res = form_w + add_w + 8 if v["place"] == "chips" else (add_w + 4 if v["place"] == "split" else 0)
    lines = text_lines(v["font"], inner - line_res)
    line_h = max(v["line_h"], lines * v["font"] * 1.35 + 14, add_w if v["place"] == "line" else 0)
    rows = chip_rows(inner, chip_res)
    chips_h = rows * 48
    if v["place"] in ("chips", "split"):
        chips_h = max(chips_h, add_w)
    action_h = max(48, add_w) if v["place"] == "row" else 0
    sheet = PAD_TOP + line_h + v["gap"] + chips_h + (v["gap"] + action_h if action_h else 0) + PAD_BOT
    top = KTOP - sheet
    line_y = top + PAD_TOP + line_h / 2
    chips_top = top + PAD_TOP + line_h + v["gap"]
    if v["place"] == "line":
        add_c, form_c = (W - PAD_X - add_w / 2, line_y), (W - PAD_X - add_w - 4 - 24, line_y)
    elif v["place"] == "chips":
        y = chips_top + chips_h - max(48, add_w) / 2
        add_c, form_c = (W - PAD_X - add_w / 2, y), (W - PAD_X - add_w - 4 - 24, y)
    elif v["place"] == "split":
        add_c = (W - PAD_X - add_w / 2, chips_top + chips_h - max(48, add_w) / 2)
        form_c = (W - PAD_X - 24, line_y)
    else:
        y = KTOP - PAD_BOT - action_h / 2
        add_c, form_c = (W - PAD_X - add_w / 2, y), (PAD_X + 24, y)
    # chip centres, row by row
    centres, x, row = [], PAD_X, 0
    for c in CHIPS:
        cw = len(c) * 13 * EM + 24
        if x > PAD_X and x + cw > W - PAD_X - chip_res:
            row, x = row + 1, PAD_X
        centres.append((x + cw / 2, chips_top + row * 48 + 24, cw))
        x += cw + 6
    # spacing: ✓'s target box against ▤, the nearest chip and the keyboard top
    ax0, ay0 = add_c[0] - add_w / 2, add_c[1] - max(48, add_w) / 2
    ax1, ay1 = ax0 + add_w, ay0 + max(48, add_w)

    def gap(bx0, by0, bx1, by1):
        dx = max(bx0 - ax1, ax0 - bx1, 0)
        dy = max(by0 - ay1, ay0 - by1, 0)
        return math.hypot(dx, dy)
    gaps = [gap(form_c[0] - 24, form_c[1] - 24, form_c[0] + 24, form_c[1] + 24), KTOP - ay1]
    gaps += [gap(cx - cw / 2, cy - 24, cx + cw / 2, cy + 24) for cx, cy, cw in centres]
    return {
        "fitts_add": fitts(REST, add_c, add_w), "fitts_form": fitts(REST, form_c, 48),
        "fitts_chips": sum(fitts(KB_MID, (cx, cy), cw) for cx, cy, cw in centres) / len(centres),
        "sheet": sheet, "spacing": min(gaps), "text": v["font"], "lines": lines,
    }


LOW = ("fitts_add", "fitts_chips", "fitts_form", "sheet", "lines")
HIGH = ("spacing", "text")


def dominates(a, b):
    ge = all(a[k] <= b[k] + 1e-9 for k in LOW) and all(a[k] >= b[k] - 1e-9 for k in HIGH)
    gt = any(a[k] < b[k] - 1e-9 for k in LOW) or any(a[k] > b[k] + 1e-9 for k in HIGH)
    return ge and gt


def main(write=True):
    keys = list(SPACE)
    cands = []
    for combo in itertools.product(*SPACE.values()):
        v = dict(zip(keys, combo))
        cands.append({"v": v, "m": layout(v)})
    front = [c for c in cands if not any(dominates(o["m"], c["m"]) for o in cands if o is not c)]
    # balanced representatives: per placement, the front member nearest the ideal point (normalised)
    rng = {k: (min(c["m"][k] for c in front), max(c["m"][k] for c in front)) for k in LOW + HIGH}

    def norm_dist(c):
        s = 0
        for k in LOW:
            lo, hi = rng[k]
            s += ((c["m"][k] - lo) / (hi - lo or 1)) ** 2
        for k in HIGH:
            lo, hi = rng[k]
            s += ((hi - c["m"][k]) / (hi - lo or 1)) ** 2
        return math.sqrt(s)
    picks = {}
    for p in PLACEMENTS:
        own = [c for c in front if c["v"]["place"] == p]
        if own:
            picks[p] = min(own, key=norm_dist)
    current = next(c for c in cands if c["v"] == {"place": "line", "font": 16, "line_h": 48, "chip_h": 34, "add": 48, "gap": 4})
    knee = min(front, key=norm_dist)
    out = {"count": len(cands), "front": len(front), "knee": knee, "picks": picks, "current": current,
           "front_by_place": {p: sum(c["v"]["place"] == p for c in front) for p in PLACEMENTS}}
    if write:
        with open(os.path.join(OUT, "capture-opt.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(out, references=reference_rows()), fh, indent=1, ensure_ascii=False)
    return out


# Reference apps' add sheets, measured on the owner's phone (adb_walk.py geometry; placeholder accounts, sample line
# typed and cleared, nothing saved; captures in the gitignored _screens-sources/capture/). Add target: x, y, w, h in dp.
# sheet: dp above the keyboard; None = a full screen. lines: how the sample wrapped (None = not typed or no parse).
REFERENCES = [
    {"app": "Todoist", "place": "chips", "add": (316, 424, 44, 48), "sheet": 153, "lines": 1, "parses": True},
    {"app": "TickTick", "place": "row", "add": (330, 457, 40, 30), "sheet": 130, "lines": 1, "parses": True},
    {"app": "Microsoft To Do", "place": "line", "add": (327, 398, 42, 44), "sheet": 104, "lines": 2, "parses": True},
    {"app": "Google Tasks", "place": "row", "add": (280, 440, 88, 48), "sheet": 113, "lines": 1, "parses": False},
    {"app": "Any.do", "place": "top", "add": (332, 38, 41, 41), "sheet": None, "lines": None, "parses": True},
    {"app": "Keep", "place": "top", "add": (0, 32, 56, 56), "sheet": None, "lines": 1, "parses": False},
    {"app": "Tasks.org", "place": "top", "add": (4, 36, 48, 48), "sheet": None, "lines": 1, "parses": False},
]


def set_frame(name, rest):
    g = globals()
    g.update(FRAMES[name])
    g["REST"] = g[rest]


def reference_rows():
    """Fitts' ID to each app's add target from the phone frame's Enter key and keyboard centre (smaller-of width,
    MacKenzie and Buxton 1992), so the apps and our layouts share one frame."""
    f = FRAMES["phone 384"]
    out = []
    for r in REFERENCES:
        x, y, w, h = r["add"]
        c, size = (x + w / 2, y + h / 2), min(w, h)
        out.append(dict(r, id_enter=round(fitts(f["ENTER"], c, size), 2), id_mid=round(fitts(f["KB_MID"], c, size), 2),
                        small=size < 48))
    return out


def sensitivity():
    """Re-runs the search in each frame with the thumb resting on Enter or on the keyboard's centre, and reports each
    placement's pick: a pick that holds across all four is not an artefact of the assumed phone or thumb."""
    rows = []
    for frame in FRAMES:
        for rest in ("ENTER", "KB_MID"):
            set_frame(frame, rest)
            o = main(write=False)
            rows.append({"frame": frame, "rest": rest, "knee": o["knee"], "picks": o["picks"],
                         "current": o["current"], "front_by_place": o["front_by_place"]})
    set_frame("model 360", "ENTER")
    return rows


def fmt(c):
    v, m = c["v"], c["m"]
    return "| %s | %d px | %d | %d | %d | %d | %.2f | %.2f | %.2f | %.0f | %.0f | %d |" % (
        v["place"], v["font"], v["line_h"], v["chip_h"], v["add"], v["gap"], m["fitts_add"], m["fitts_chips"], m["fitts_form"],
        m["sheet"], m["spacing"], m["lines"])


if __name__ == "__main__":
    o = main()
    head = ["| Placement | Text | Line h | Chip h | ✓ size | Gap | ID to ✓ | ID to chips | ID to ▤ | Sheet dp | Spacing at ✓ | Lines |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    md = ["# Capture sheet: sizes and placement, enumerated", "", "Generated by `tools/screens/capture_opt.py` (its docstring states the model).", "",
          "%d layouts; %d on the Pareto front. Front members per placement: %s." % (
              o["count"], o["front"], ", ".join("%s %d" % kv for kv in o["front_by_place"].items())), "",
          "## As approved (A′)", ""] + head + [fmt(o["current"])] + ["", "## Balanced pick per placement (nearest the ideal point)", ""] + head + \
         [fmt(c) for c in o["picks"].values()] + ["", "Knee of the whole front: " + fmt(o["knee"])]
    md += ["", "## Reference apps, measured on the owner's phone (384 x 832 dp)", "",
           "| App | Add sits | Add target dp | ID from Enter | ID from keyboard centre | Sheet dp | Parses | Under 48 |", "|---|---|---|---|---|---|---|---|"]
    for r in reference_rows():
        md.append("| %s | %s | %dx%d | %.2f | %.2f | %s | %s | %s |" % (r["app"], r["place"], r["add"][2], r["add"][3], r["id_enter"], r["id_mid"],
                  r["sheet"] if r["sheet"] else "full screen", "yes" if r["parses"] else "no", "yes" if r["small"] else ""))
    md += ["", "## Sensitivity: frame x thumb rest", "", "Each placement's balanced pick, re-searched in each frame. ID to ✓ / sheet dp / lines.", "",
           "| Frame | Thumb rests on | Knee | line | chips | row | split | A′ as approved |", "|---|---|---|---|---|---|---|---|"]
    for r in sensitivity():
        cell = lambda c: "%s %dpx ✓%d: %.2f / %.0f / %d" % (c["v"]["place"], c["v"]["font"], c["v"]["add"], c["m"]["fitts_add"], c["m"]["sheet"], c["m"]["lines"]) if c else "none on front"
        md.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (r["frame"], "Enter" if r["rest"] == "ENTER" else "keyboard centre", cell(r["knee"]),
                  *[cell(r["picks"].get(p)) for p in PLACEMENTS], cell(r["current"])))
    with open(os.path.join(OUT, "capture-opt.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
