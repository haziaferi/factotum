"""T0 palette study (decision 15, Q4; owner 2026-10-06). Writes docs/screens/t0/palette.md and palette.html.

Each module takes its HUE from the identity colour of one design-lexicon entry the owner's keywords chose
(visual-craft references/lexicon). Its LIGHTNESS and CHROMA are shared by all four modules, so no module reads
louder than another on the mixed home screen (app-register-layout Step 1d B; nav-glance.md asked for at most 6
equal-lightness hues). Three shells (grounds and text) come from the keywords too. Every pairing is measured
with design-optimization's `designkit` (WCAG ratio, CIEDE2000, colour-vision simulation), never estimated.

    PYTHONUTF8=1 python tools/screens/palette_t0.py
"""
import glob
import html
import json
import math
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_MD = os.path.join(ROOT, "docs", "screens", "t0", "palette.md")
OUT_HTML = os.path.join(ROOT, "docs", "screens", "t0", "palette.html")
DK = sorted(glob.glob(os.path.expanduser("~/.claude/plugins/cache/gold-standard-local/design-optimization/*/engine/designkit_cli.py")))[-1]

# ---- the owner's keywords (★ = picked with the oblique skill) and the lexicon colour each hue comes from ----
MODULES = [
    dict(id="calendar", name="Calendar", keywords=["Swiss / International", "★ Civic / Government", "★ Ming Blue-and-White"],
         anchor=("#17488C", "Ming Dynasty Porcelain: Mohammedan cobalt"),
         why="A timetable is public wayfinding (Civic: legible under stress, never colour-only) printed in two colours (Ming: dense "
             "cobalt bands on a clean ground, so a busy day looks busy and a free day looks free). Swiss gives the visible hairline grid."),
    dict(id="routines", name="Routines", keywords=["Naturecore", "Health / Consumer Wellbeing", "★ Wabi Sabi", "★ Craft / Artisan"],
         anchor=("#697d41", "Naturecore, Mossland: moss"),
         why="Moss for growth (Naturecore); red reserved for real emergencies, values shown against a range (Health). Wabi Sabi is "
             "built on the gap, so a missed day is drawn as an honest gap, never a broken streak; Craft makes logging a practised hand, not a score."),
    dict(id="checkin", name="Check-in", keywords=["Serene / Calm", "★ Introverted-rainy", "★ Goryeo Celadon"],
         anchor=("#A2CDC5", "Goryeo Celadon: bisaek"),
         why="Serene: one thing at full contrast at a time. Introverted-rainy inverts the cheerful default: permission not to be sunny. "
             "Celadon is a colour between moods, neither happy nor sad, so the check-in never hints at a right answer."),
    dict(id="pages", name="Pages", keywords=["Editorial", "Light / Dark Academia", "★ Medieval", "★ Developer Tools"],
         anchor=("#d8c599", "Medieval, Illuminated Manuscript: gold leaf"),
         why="Editorial and Academia for reading and writing. Medieval brings rubrication and the illuminated drop cap for page titles; "
             "Developer Tools gives databases and formulas their own surface a hair off the page, as code blocks have."),
]
# Shells: ground, raised surface, text, secondary text. Light, dark, and the phone-only OLED (owner's Q10).
SHELLS = [
    dict(id="porcelain", name="Porcelain", source="Ming porcelain white and Civic Statute's dark",
         light=("#F7F7F8", "#FFFFFF", "#1B1B1B", "#5C5F66"), dark=("#121417", "#1B1E22", "#EDEFF2", "#A3A8B0")),
    dict(id="linen", name="Linen", source="Serene Chalk and Wabi Sabi's linen",
         light=("#F5F3EF", "#FCFBF9", "#35322D", "#6E685E"), dark=("#1B1917", "#25221F", "#E4DFD6", "#ABA397")),
    dict(id="rain", name="Rain", source="Introverted-rainy, its own surface and text",
         light=("#E3E5E8", "#F0F1F3", "#2D3643", "#596373"), dark=("#15181D", "#1E2228", "#DDE2E8", "#9AA3AF")),
]
OLED = ("#000000", "#0E0F11")  # ground and raised surface; text and module tones follow the shell's dark register

# Shared module lightness and chroma (OKLCH). Searched below: the lightest tone (light mode) or darkest (dark) at
# which every module tone still clears 4.5:1 on every ground, so a tone can carry a link or a label.
CHROMA, TINT = 0.11, {"light": (0.935, 0.032), "dark": (0.30, 0.045), "oled": (0.24, 0.045)}


# ---- colour maths (OKLCH -> sRGB); measurement is designkit's ----
def hex_to_oklch(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    l = 0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]
    m = 0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]
    s = 0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b2 = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, b2), math.degrees(math.atan2(b2, a)) % 360


def oklch_to_hex(L, C, H):
    """Clips chroma down until the colour is inside sRGB, so the hue and lightness are kept exactly."""
    while True:
        a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
        l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
        m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
        s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
        rgb = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
        if all(-1e-4 <= c <= 1.0001 for c in rgb) or C <= 0:
            out = [12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055 for c in (min(max(c, 0), 1) for c in rgb)]
            return "#%02X%02X%02X" % tuple(round(c * 255) for c in out)
        C -= 0.002


def rel_lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def quick_ratio(a, b):
    """Only steers the search; every reported figure is designkit's."""
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


_cache = {}


def dk(*args):
    if args not in _cache:
        res = subprocess.run(["python", DK, *args], capture_output=True, text=True)  # exits 1 when a pair fails WCAG: a verdict, not an error
        if not res.stdout.strip():
            raise RuntimeError(res.stderr)
        _cache[args] = res.stdout
    return _cache[args]


def ratio(fg, bg):
    out = dk("contrast", fg, bg)
    return float(re.search(r"ratio\s+([\d.]+):1", out).group(1)), float(re.search(r"delta-E 2000\s+([\d.]+)", out).group(1))


def cvd(h):
    m = re.search(r"deuter (#\w{6})\s+protan (#\w{6})\s+tritan (#\w{6})", dk("convert", h))
    return dict(zip(("deuter", "protan", "tritan"), m.groups()))


# ---- build ----
def tone_lightness(mode):
    """Shared lightness for the four tones in one mode: as light (light mode) or as dark (dark modes) as possible while every
    tone clears 4.5:1 on every ground of that mode."""
    hues = [hex_to_oklch(m["anchor"][0])[2] for m in MODULES]
    grounds = [s[mode if mode != "oled" else "dark"][i] for s in SHELLS for i in (0, 1)] if mode != "oled" else list(OLED)
    steps = [x / 1000 for x in range(300, 900)]
    ok = [L for L in steps if all(quick_ratio(oklch_to_hex(L, CHROMA, h), g) >= 4.6 for h in hues for g in grounds)]
    return max(ok) if mode == "light" else min(ok)


def build():
    modes = {}
    for mode in ("light", "dark", "oled"):
        L = tone_lightness(mode)
        tl, tc = TINT[mode]
        modes[mode] = dict(L=L, tones={m["id"]: dict(tone=oklch_to_hex(L, CHROMA, hex_to_oklch(m["anchor"][0])[2]),
                                                     tint=oklch_to_hex(tl, tc, hex_to_oklch(m["anchor"][0])[2])) for m in MODULES})
    return modes


def measure(modes):
    rows, worst = [], {}
    for s in SHELLS:
        for mode in ("light", "dark", "oled"):
            reg = s["dark" if mode == "oled" else mode]
            ground, raised = (OLED if mode == "oled" else reg[:2])
            text, dim = reg[2], reg[3]
            checks = [("text on ground", text, ground, 7.0), ("text on raised", text, raised, 7.0), ("secondary text on ground", dim, ground, 4.5)]
            for m in MODULES:
                t = modes[mode]["tones"][m["id"]]
                checks += [(m["name"] + " tone on ground", t["tone"], ground, 4.5), (m["name"] + " tone on raised", t["tone"], raised, 4.5),
                           ("text on " + m["name"] + " tint", text, t["tint"], 7.0)]
            for what, fg, bg, need in checks:
                r, _ = ratio(fg, bg)
                rows.append(dict(shell=s["name"], mode=mode, what=what, fg=fg, bg=bg, ratio=r, need=need, ok=r >= need))
    # module tones apart from each other: CIEDE2000, normal vision and the three simulations
    sep = []
    for mode in ("light", "dark"):
        tones = [(m["name"], modes[mode]["tones"][m["id"]]["tone"]) for m in MODULES]
        for i in range(len(tones)):
            for j in range(i + 1, len(tones)):
                (na, a), (nb, b) = tones[i], tones[j]
                d = dict(normal=ratio(a, b)[1])
                ca, cb = cvd(a), cvd(b)
                for k in ("deuter", "protan", "tritan"):
                    d[k] = ratio(ca[k], cb[k])[1]
                sep.append(dict(mode=mode, pair=na + " / " + nb, **d))
    return rows, sep


def write(modes, rows, sep):
    fails = [r for r in rows if not r["ok"]]
    out = ["# T0 palette study", "", "Generated by `tools/screens/palette_t0.py`; every ratio and distance is measured with design-optimization's `designkit`.", "",
           "## Keywords and where each hue comes from", "", "★ = picked with the oblique skill.", "",
           "| Module | Keywords | Hue from | Why |", "|---|---|---|---|"]
    out += ["| %s | %s | `%s` %s | %s |" % (m["name"], " · ".join(m["keywords"]), m["anchor"][0], m["anchor"][1], m["why"]) for m in MODULES]
    out += ["", "## Module tones (shared lightness and chroma per mode)", "", "| Module | Light tone | Light tint | Dark tone | Dark tint | OLED tint |", "|---|---|---|---|---|---|"]
    out += ["| %s | `%s` | `%s` | `%s` | `%s` | `%s` |" % (m["name"], *(modes[md]["tones"][m["id"]][k] for md, k in
            (("light", "tone"), ("light", "tint"), ("dark", "tone"), ("dark", "tint"), ("oled", "tint")))) for m in MODULES]
    out += ["", "OKLCH lightness of the tones: light %.3f, dark %.3f, OLED %.3f; chroma %.2f, clipped to sRGB where a hue cannot reach it." % (
        modes["light"]["L"], modes["dark"]["L"], modes["oled"]["L"], CHROMA), "",
        "## Shells (themes)", "", "| Shell | From | Light ground · raised · text · secondary | Dark ground · raised · text · secondary |", "|---|---|---|---|"]
    out += ["| %s | %s | %s | %s |" % (s["name"], s["source"], " · ".join("`%s`" % c for c in s["light"]), " · ".join("`%s`" % c for c in s["dark"])) for s in SHELLS]
    out += ["", "OLED (phone only) keeps a shell's dark text and tones on ground `%s`, raised `%s`." % OLED, "",
            "## Contrast", "", "%d pairings measured; %d below their floor (text 7:1, secondary text and tones 4.5:1)." % (len(rows), len(fails)), ""]
    if fails:
        out += ["| Shell | Mode | Pairing | Colours | Ratio | Floor |", "|---|---|---|---|---|---|"]
        out += ["| %s | %s | %s | `%s` on `%s` | %.2f | %.1f |" % (r["shell"], r["mode"], r["what"], r["fg"], r["bg"], r["ratio"], r["need"]) for r in fails]
    worst = min(rows, key=lambda r: r["ratio"] / r["need"])
    out += ["", "Tightest pairing: %s, %s, %s: %.2f:1 against a %.1f floor." % (worst["shell"], worst["mode"], worst["what"], worst["ratio"], worst["need"]), "",
            "## Are the four tones told apart?", "", "CIEDE2000 between module tones, with normal vision and simulated deuteranopia, protanopia and tritanopia. "
            "Below about 10 two colours start to read as the same; the module is never carried by colour alone (each bar slot and zone also has its icon and name).", "",
            "| Mode | Pair | Normal | Deuter | Protan | Tritan |", "|---|---|---|---|---|---|"]
    out += ["| %s | %s | %.1f | %.1f | %.1f | %.1f |" % (d["mode"], d["pair"], d["normal"], d["deuter"], d["protan"], d["tritan"]) for d in sep]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out, fails


def write_html(modes, sep):
    e = html.escape
    data = dict(modules=[dict(id=m["id"], name=m["name"], keywords=m["keywords"], anchor=m["anchor"], why=m["why"]) for m in MODULES],
                shells=SHELLS, oled=OLED, modes={k: v["tones"] for k, v in modes.items()},
                minsep={k: round(min(d[k] for d in sep), 1) for k in ("normal", "deuter", "protan", "tritan")})
    with open(os.path.join(os.path.dirname(OUT_HTML), "palette.template.html"), encoding="utf-8") as fh:
        page = fh.read()
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))


if __name__ == "__main__":
    modes = build()
    rows, sep = measure(modes)
    out, fails = write(modes, rows, sep)
    write_html(modes, sep)
    print("\n".join(out))
