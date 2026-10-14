r"""The 18 Paced timer sheets (T3b.4, mode x place) and Break Down Timer as webp data URIs, for the try page.

Drawn through one kept-open headless browser (~/.claude/tools/headless_browser.py), never a cold launch per image.
Writes docs/screens/t3/pace-imgs.json: [{"mode", "place", "src"}].
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


def main():
    os.makedirs(CACHE, exist_ok=True)
    out = []
    opts = [dict(mode=m, place=p) for m in M.PACE_SPACE["mode"] for p in M.PACE_SPACE["place"]]
    opts.append({"mode": "bdt", "place": "bdt", "control": True})
    for v in opts:
        html = M.pdoc(M.pace_phone(v))
        png = os.path.join(CACHE, "%s-%s.png" % (v["mode"], v["place"]))
        hb.screenshot(html, png, 360, 740)
        buf = io.BytesIO()
        Image.open(png).convert("RGB").save(buf, "WEBP", quality=80)
        out.append({"mode": v["mode"], "place": v["place"], "src": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")})
        print(v["mode"], v["place"], len(buf.getvalue()))
    places = []   # T3b.4b: each place running, then Today while it runs
    for v in [dict(place=p, elsewhere=e) for p in M.PPLACE_SPACE["place"] for e in M.PPLACE_SPACE["elsewhere"]] + [{"place": "bdt", "elsewhere": "none", "control": True}]:
        srcs = []
        for i, html in enumerate(M.T.DRAW["paceplace"](v)):
            png = os.path.join(CACHE, "pp-%s-%s-%d.png" % (v["place"], v["elsewhere"], i))
            hb.screenshot(html, png, 360, 740)
            buf = io.BytesIO()
            Image.open(png).convert("RGB").save(buf, "WEBP", quality=80)
            srcs.append("data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii"))
        places.append({"place": v["place"], "elsewhere": v["elsewhere"], "srcs": srcs})
    with open(os.path.join(M.T.OUT, "pace-imgs.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"sheets": out, "places": places}, fh)


if __name__ == "__main__":
    main()
