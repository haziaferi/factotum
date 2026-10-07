"""T1.4 Hub sheet (cards), unpaused and re-scored with T1.3's carry-overs (owner, 2026-10-07; decision 17).

Carry-overs applied to every option:
  1  the capture line on top is T1.3 v4's: no field box, the understood words highlighted, ⋯ beside it, one line high,
     the shorthand hint scrolling under it; the Hub's placeholder is Today's ("Add anything…")
  2  one drawn height: features are plain text on 48 px targets, nothing drawn larger than the text line
  3  text, not chips or pills
  4  no element heavier than the content: the feature names must outweigh the card headers (measured mass)
  5  unjustified empty space is measured (craftkit imgstat detail report, as capture_v3)
  6  Windows has room: its panel shows every card at once
And the measuring fix T1.3 found: a feature counts as seen only if it is drawn at its centre (hit-tested), so one
cut off by the sheet's edge is hidden; the earlier T1.4 measure counted it by its position.

Owner's requirement as a constraint: every screen visible (0 hidden) on the phone and on Windows.
  H  emphasis   designkit layout.emphasis_coherence over the measured masses, importance features > line > headers
     headers    the headers' share of the sheet's mass (lower: they label, they do not lead)
     sprawl     craftkit ui findings (colour excluded)
  U  hidden     screens not drawn (constraint), reach (mean Fitts' ID from the Hub's slot in the bar, where the thumb
                is when the sheet opens, to each screen), pinned (Pinned and recent shown: 1 better than 0)
  C  clutter (edge density, light and dark), empty (share of near-blank cells in the sheet)

    PYTHONUTF8=1 python tools/screens/hub_opt.py
"""
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
from designkit import layout as dk_layout  # noqa: E402

HUB_SLOT = (180, 712)
NAMES = [t.re_strip(f) for f in t.FEATURES]


def v4_top(pinned=True):
    """Carry-over 1: the T1.3 v4 line and its scrolling hint, then Pinned and recent."""
    sheet = L.sheet("both", "empty").replace("Add a task, event, log or journal line…", "Add anything…")
    inner = sheet[len('<div class="sheet" style="position:relative">'):-len("</div>")]
    rec = '<div class="subl">Pinned and recent</div><div class="ft" style="margin-bottom:4px">%s</div>' % "".join(t.feat(f) for f in t.RECENT) if pinned else ""
    return '<div class="grab"></div><div class="c2">%s</div>%s' % (inner, rec)


def phone(body, top=True, pinned=True):
    html = t.hub_phone(body, top=False)
    return html.replace('<div class="hubsheet">', '<div class="hubsheet">' + (v4_top(pinned) if top else ""), 1)


def cards_a():
    return "".join(t.card(*g) for g in t.HUB_GROUPS)


def card_tight(name, glyph, feats, mode):
    """Shorter cards for A (owner, 2026-10-07: would shorter cards remove the scroll?). The 48 px rows stay (the owner's
    target rule); what can go is the header's own row, the card's padding and the gaps between cards.
      tight   padding 2 px, gaps 4 px, header kept on its own row
      inline  the header flows as the first word of the card's first row, a quiet label, not a target
      column  the header in a fixed 76 px label column at the left, the features beside it
    """
    fs = "".join(t.feat(f) for f in feats)
    label = '<span class="hlab">%s %s</span>' % (glyph, t.e(name))
    if mode == "tight":
        return '<div class="card" style="padding:2px 10px;margin:0 0 4px"><h5>%s %s</h5><div class="ft">%s</div></div>' % (glyph, t.e(name), fs)
    if mode == "inline":
        return '<div class="card" style="padding:0 10px;margin:0 0 4px"><div class="ft" style="align-items:center">%s%s</div></div>' % (label, fs)
    return ('<div class="card" style="padding:0 10px;margin:0 0 4px;display:flex;align-items:flex-start"><span class="hlab" style="flex:none;width:76px;'
            'min-height:48px;display:flex;align-items:center">%s %s</span><div class="ft" style="flex:1;margin:0">%s</div></div>' % (glyph, t.e(name), fs))


def cards_b():
    return '<div class="grid2">%s</div>' % cards_a()


def cards_c():
    by = {g[0]: g for g in t.HUB_GROUPS}
    left = t.card(*by["Calendar"]) + t.card(*by["Routines"])
    right = t.card(*by["Pages"]) + t.card(*by["check-in"])
    foot = '<div class="grid2">%s%s</div>' % (t.card(*by["Review"]), t.card(*by["App"]))
    return '<div class="grid2"><div>%s</div><div>%s</div></div>%s' % (left, right, foot)


def list_x():
    rows = "".join('<div class="hh">%s</div>%s' % (t.e(n), "".join('<div class="hr" data-tap="%s">%s</div>' % (f, f) for f in fs)) for n, _, fs in t.HUB_GROUPS)
    return '<div class="hlist">%s</div>' % rows


# Without the App card (owner's question, 2026-10-08): its screens (Labels, Time blocks, Calendars, Settings, Trash,
# About) live behind the header's ⚙ (T1.1), and the Hub shows the other 21.
NOAPP = [g for g in t.HUB_GROUPS if g[0] != "App"]
NOAPP_NAMES = [t.re_strip(f) for _, _, fs in NOAPP for f in fs]


def noapp_a(tight=False):
    return "".join(card_tight(*g, "tight") if tight else t.card(*g) for g in NOAPP)


def noapp_c():
    by = {g[0]: g for g in NOAPP}
    left = t.card(*by["Calendar"]) + t.card(*by["Routines"])
    right = t.card(*by["Pages"]) + t.card(*by["check-in"])
    return '<div class="grid2"><div>%s</div><div>%s</div></div>%s' % (left, right, t.card(*by["Review"]))


DESK_NOAPP = lambda: t.hub_desk(v4_top() + '<div class="grid3">%s</div>' % "".join(t.card(*g) for g in NOAPP))
TIGHT_CSS = ".hlab{font-size:12px;font-weight:600;color:var(--dim);padding:0 8px;display:inline-flex;align-items:center;min-height:48px}"


OPTIONS = [
    ("A-tight", "One column, tighter cards (padding 2, gaps 4)", "direct", lambda: phone("".join(card_tight(*g, "tight") for g in t.HUB_GROUPS))),
    ("A-inline", "One column, header inline as the first word", "direct", lambda: phone("".join(card_tight(*g, "inline") for g in t.HUB_GROUPS))),
    ("A-column", "One column, header in a label column", "direct", lambda: phone("".join(card_tight(*g, "column") for g in t.HUB_GROUPS))),
    ("A-tight-", "One column, tighter cards, no Pinned and recent", "direct", lambda: phone("".join(card_tight(*g, "tight") for g in t.HUB_GROUPS), pinned=False)),
    ("A", "One column of cards", "direct", lambda: phone(cards_a())),
    ("B", "Two columns of cards", "direct", lambda: phone(cards_b())),
    ("C", "Cards where the bar says they live (store map)", "oblique", lambda: phone(cards_c())),
    ("B-", "Two columns, no Pinned and recent (room for every screen)", "direct", lambda: phone(cards_b(), pinned=False)),
    ("C-", "Store map, no Pinned and recent", "oblique", lambda: phone(cards_c(), pinned=False)),
    ("A0", "One column, no App card (App behind ⚙)", "direct", lambda: phone(noapp_a())),
    ("A0-tight", "One column, tighter cards, no App card", "direct", lambda: phone(noapp_a(True))),
    ("C0", "Store map, no App card (Review across the foot)", "oblique", lambda: phone(noapp_c())),
    ("X", "Control: one long list, no capture line", "control", lambda: phone(list_x(), top=False)),
]
DESK = lambda: t.hub_desk(v4_top() + '<div class="grid3">%s</div>' % "".join(t.card(*g) for g in t.HUB_GROUPS))
CSS = t.EXTRA + t.T12_CSS + t.T13_CSS + t.T14_CSS + L.CSS + TIGHT_CSS


def doc(html, theme="light", score=True):
    return kit.document(html, theme, CSS, score)


def masses(png, m, box):
    sx, sy, sw, sh = box
    crop = png.replace(".png", "-hub.png")
    Image.open(png).convert("RGB").crop((int(sx), int(sy), int(sx + sw), int(sy + sh))).save(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    hist = {}
    for v in lum:
        hist[int(v * 32)] = hist.get(int(v * 32), 0) + 1
    ground = (max(hist.items(), key=lambda kv: kv[1])[0] + 0.5) / 32.0

    def mass(b):
        x0, y0, bw, bh = int(b[0] - sx), int(b[1] - sy), int(b[2]), int(b[3])
        return sum(abs(lum[y * img.w + x] - ground) for y in range(max(0, y0), min(img.h, y0 + bh)) for x in range(max(0, x0), min(img.w, x0 + bw)))
    total = sum(abs(v - ground) for v in lum) or 1
    feats = sum(mass(x["box"]) for x in m["taps"] if x["name"] in NAMES and x.get("seen"))
    heads = sum(mass(b) for b in m["h5"])
    line = mass(m["boxes"]["line"]) if m["boxes"].get("line") else 0
    empty = imgstat._detail_report(imgstat._sobel(lum, img.w, img.h), img.w, img.h).get("empty_share", 0.0)
    return {"features": feats, "headers": heads, "line": line}, total, empty


def sprawl(html, name):
    path = os.path.join(ss.CACHE, "hub-%s.html" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc(html))
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True,
                         env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast"))
               and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


def score(oid, make):
    names = NOAPP_NAMES if oid in ("A0", "A0-tight", "C0") else NAMES  # without App, the 21 screens it is meant to show
    html = make()
    m = ss.measure(doc(html), 360, 740)
    png = ss.render(doc(html), 360, 740)
    clutter = sum(ss.edge_density(ss.render(doc(html, th), 360, 740)) for th in ("light", "dark")) / 2
    seen = {x["name"] for x in m["taps"] if x["name"] in names and x.get("seen")}
    vis = [x for x in m["taps"] if x["name"] in names and x.get("seen")]
    reach = sum(math.log2(math.hypot(HUB_SLOT[0] - x["x"], HUB_SLOT[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in vis) / max(1, len(vis))
    ms, total, empty = masses(png, m, m["boxes"]["hubsheet"])
    order = [k for k, _ in sorted(ms.items(), key=lambda kv: -kv[1])]
    emph = dk_layout.emphasis_coherence({"emphasis_primary": order[0], "emphasis_secondary": order[1], "section_order": ["features", "line", "headers"]},
                                        {"importance": ["features", "line", "headers"]})
    return {"hidden": len(names) - len(seen), "hidden_names": sorted(set(names) - seen), "reach": round(reach, 3),
            "pinned": 0 if oid.endswith("-") or oid == "X" else 1, "emphasis": emph, "order": order,
            "headers": round(ms["headers"] / total, 3), "sprawl": sprawl(html, oid), "clutter": round(clutter, 4), "empty": round(empty, 3),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if x.get("seen") and (x["w"] < 48 or x["h"] < 48)})}


AXES = {"H": (("emphasis", -1), ("headers", 1), ("sprawl", 1)), "U": (("reach", 1), ("pinned", -1)), "C": (("clutter", 1), ("empty", 1))}


def main():
    rows = []
    for oid, name, how, make in OPTIONS:
        r = dict(id=oid, name=name, how=how, **score(oid, make))
        rows.append(r)
        print(oid, {k: r[k] for k in ("hidden", "reach", "emphasis", "order", "headers", "sprawl", "clutter", "empty", "small")}, flush=True)
    dm = ss.measure(doc(DESK()), 1100, 660)
    desk_hidden = sorted(set(NAMES) - {x["name"] for x in dm["taps"] if x["name"] in NAMES and x.get("seen")})
    ok = [r for r in rows if r["hidden"] == 0 and not r["small"]]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, k, s) for k, s in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(c[i] for c in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    ctrl = next(r for r in rows if r["how"] == "control")
    out = {"rows": rows, "front": [r["id"] for r in front], "control_beaten": ctrl not in front, "desk_hidden": desk_hidden}
    with open(os.path.join(v2.OUT, "hub-opt.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    for r in rows:
        print("%s %-3s %-58s hidden %2d %s" % ("*" if r in front else " ", r["id"], r["name"][:58], r["hidden"],
                                              "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]) if "H" in r else "fails: %s" % (", ".join(r["hidden_names"][:6]) or r["small"])))
    print("Windows panel hides:", desk_hidden or "nothing", "| control beaten:", ctrl not in front)


if __name__ == "__main__":
    main()
