"""Visual weight of the capture sheet's elements, measured on the render (owner, 2026-10-07: a big black ✓ "creates a
huge imbalance between the elements on the sheet"; the reach-only search could not see it).

Measures, on the light render's sheet region, with craftkit's own definitions (creative-design-suite imgstat):
  mass        departure of each pixel's luminance from the sheet's ground tone (imgstat._balance_report), summed per
              element box: the typed line, the chips, ✓ and ▤
  add_share   ✓'s share of the sheet's mass. The typed text is the content and should outweigh the button that
              submits it; ✓ must still read as the action (its glyph >= 4.5:1, screen_score's `faint`)
  add_vs_line ✓'s mass over the typed line's (<= 1 keeps the text first)
  focal       where edge energy concentrates (imgstat._focal_report), and whether it lands on the typed line or on ✓
  balance     share of mass left of centre (imgstat)
plus thumb travel (Fitts' ID from Enter, as tier_t1) and taps under 48 dp.

    PYTHONUTF8=1 python tools/screens/sheet_weight.py
"""
import glob
import itertools
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

ENGINE = sorted(glob.glob(os.path.expanduser(r"~/.claude/plugins/synced/*/creative-design-suite/engine")))[-1]
sys.path.insert(0, ENGINE)
from craftkit import imgstat  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "screens", "t1")
SPACE = {"place": ["line", "chips"], "add_style": list(t.ADD_STYLES), "add": [48, 56], "form_glyph": ["▤", "⤢", "Details"]}
FONT = {"line": 16, "chips": 18}


def doc(v, theme="light", score=True):
    return kit.document(t.cap_phone_v(v["place"], FONT[v["place"]], v["add"], add_style=v["add_style"], form_glyph=v["form_glyph"]),
                        theme, t.EXTRA + t.T12_CSS + t.T13_CSS, score)


def mass_in(lum, w, box, ground, ox, oy):
    x0, y0, bw, bh = box
    x0, y0 = int(x0 - ox), int(y0 - oy)
    tot = 0.0
    for y in range(max(0, y0), min(len(lum) // w, y0 + int(bh))):
        row = y * w
        for x in range(max(0, x0), min(w, x0 + int(bw))):
            tot += abs(lum[row + x] - ground)
    return tot


def score(v):
    d = doc(v)
    m = ss.measure(d, 360, 740)
    png = ss.render(d, 360, 740)
    sx, sy, sw, sh = m["boxes"]["sheet"]
    crop = os.path.join(ss.CACHE, os.path.basename(png).replace(".png", "-sheet.png"))
    Image.open(png).convert("RGB").crop((int(sx), int(sy), int(sx + sw), int(sy + sh))).save(crop)
    rep = imgstat.analyse(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    hist = {}
    for val in lum:
        hist[int(val * 32)] = hist.get(int(val * 32), 0) + 1
    ground = (max(hist.items(), key=lambda kv: kv[1])[0] + 0.5) / 32.0
    total = sum(abs(val - ground) for val in lum) or 1
    taps = {x["name"]: x for x in m["taps"]}
    mass = {"line": mass_in(lum, img.w, m["boxes"]["line"], ground, sx, sy), "chips": mass_in(lum, img.w, m["boxes"]["chips"], ground, sx, sy),
            "add": mass_in(lum, img.w, taps["Add"]["box"], ground, sx, sy), "form": mass_in(lum, img.w, taps["Full form"]["box"], ground, sx, sy)}
    fx, fy = rep["focal"]["fraction"]
    fpx = (sx + fx * sw, sy + fy * sh)

    def dist(box):
        x0, y0, bw, bh = box
        return math.hypot(fpx[0] - (x0 + bw / 2), fpx[1] - (y0 + bh / 2))
    focal_on = min((("line", dist(m["boxes"]["line"])), ("chips", dist(m["boxes"]["chips"])), ("add", dist(taps["Add"]["box"]))), key=lambda kv: kv[1])[0]
    a = taps["Add"]
    fitts = math.log2(math.hypot(t.ENTER_KEY[0] - a["x"], t.ENTER_KEY[1] - a["y"]) / min(a["w"], a["h"]) + 1)
    return {"v": v, "add_share": round(mass["add"] / total, 3), "add_vs_line": round(mass["add"] / (mass["line"] or 1), 2),
            "form_share": round(mass["form"] / total, 3), "focal_on": focal_on, "balance_left": rep["balance"]["horizontal"],
            "fitts_add": round(fitts, 2), "faint": [x for x in m["taps"] if x["contrast"] < 4.5 and x["name"] in ("Add", "Full form")] and
            sorted("%s %.1f" % (x["name"], x["contrast"]) for x in m["taps"] if x["contrast"] < 4.5 and x["name"] in ("Add", "Full form")) or [],
            "small": sorted("%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if x["w"] < 48 or x["h"] < 48), "sheet_h": m["sheet_h"]}


def main():
    rows = [score(dict(zip(SPACE, c))) for c in itertools.product(*SPACE.values())]
    with open(os.path.join(OUT, "sheet-weight.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    for r in sorted(rows, key=lambda r: (r["v"]["place"], r["add_vs_line"])):
        v = r["v"]
        print("%-5s %-7s %2d %-7s  add/sheet %.3f  add/line %.2f  form %.3f  focal %-5s  left %.2f  ID %.2f  sheet %d  %s %s" % (
            v["place"], v["add_style"], v["add"], v["form_glyph"], r["add_share"], r["add_vs_line"], r["form_share"], r["focal_on"],
            r["balance_left"], r["fitts_add"], r["sheet_h"], ",".join(r["faint"]), ",".join(r["small"])))
    return rows


if __name__ == "__main__":
    main()
