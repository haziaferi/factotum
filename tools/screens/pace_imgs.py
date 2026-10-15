r"""The drawings for the Paced timer trial page, as webp data URIs: T3b.4e's best options and its control, and T3b.4b's places.

Drawn through one kept-open headless browser (~/.claude/tools/headless_browser.py), never a cold launch per image.
Writes docs/screens/t3/pace-imgs.json (gitignored): {"sheets": [{"v", "src"}], "places": [{"place", "elsewhere", "srcs"}]}.
"""
import base64
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "tools"))
import headless_browser as hb  # noqa: E402
from PIL import Image  # noqa: E402

import t3_opt as M  # noqa: E402

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-pace")
SHOW = 8   # T3b.4e's best options drawn


def webp(html, name):
    png = os.path.join(CACHE, name + ".png")
    hb.screenshot(html, png, 360, 740)
    buf = io.BytesIO()
    Image.open(png).convert("RGB").save(buf, "WEBP", quality=80)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def key(v):
    return "-".join(str(v[k]) for k in sorted(v) if k != "control")


def main():
    os.makedirs(CACHE, exist_ok=True)
    rows, ok, _ = M.T.ranked("pace5")
    best = sorted((r for r in ok if not r["v"].get("control")), key=lambda r: r["total"])[:SHOW]
    typed = min((r for r in ok if r["v"].get("pauses") == "sentence" and r["v"].get("time") == "typed"), key=lambda r: r["total"])
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in best + ([typed] if typed not in best else []) + [ctl]:
        sheets.append({"v": r["v"], "src": webp(M.T.DRAW["pace5"](r["v"])[0], "p5-" + key(r["v"]))})
        print(key(r["v"]))
    places = []   # T3b.4b: each place running, then Today while it runs
    for v in [dict(place=p, elsewhere=e) for p in M.PPLACE_SPACE["place"] for e in M.PPLACE_SPACE["elsewhere"]] + [{"place": "bdt", "elsewhere": "none", "control": True}]:
        srcs = [webp(html, "pp-%s-%s-%d" % (v["place"], v["elsewhere"], i)) for i, html in enumerate(M.T.DRAW["paceplace"](v))]
        places.append({"place": v["place"], "elsewhere": v["elsewhere"], "srcs": srcs})
    with open(os.path.join(M.T.OUT, "pace-imgs.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"sheets": sheets, "places": places}, fh)


if __name__ == "__main__":
    main()
