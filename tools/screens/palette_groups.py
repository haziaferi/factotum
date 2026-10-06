"""Module palettes for decision 15, Q4: calendar, routines and check-in, composed into groups of three.
Writes docs/screens/t0/palettes.md and docs/screens/t0/palettes.html.

Inputs
  palette-keywords.json   the owner-approved method's keyword picks (direct and oblique), per module
  palette-sources.json    every named pair of the design lexicon, extracted by lexicon_pairs.py

Owner's rules (2026-10-06)
  - grounds stay the mockups' neutrals; no pure white or black except OLED; the dark ground is CIELAB L* 5-7
  - no reds; no orange, amber, coral, salmon or peach; terracotta, rust and clay allowed; magenta, plum and
    mauve allowed; pinks in at most a third of the groups; bright colours toned down for screens
  - every palette works on light, dark and OLED; Pages keeps its mockup amber
  - eye-friendly for long reading on phone and desktop

How a lexicon pair becomes a module palette (adapted, not copied: the grounds are fixed, so only the pair's
identity colour carries over). The identity is the pair's light-register primary, else its accent, else its
secondary, else the dark register's. It keeps its OKLCH hue; then, per theme:
  accent   chroma = identity chroma, clamped to [CHROMA_FLOOR, CAP] (CAP 0.13 light, 0.11 dark: comfort);
           lightness solved for the module's CONTRAST on the ground: calendar 6.5, routines 5.0, check-in 4.5
           (all text-capable; staggered by register, and because equal contrast collapses under colour-blind
           vision; the sweep in palettes.md shows what each stagger allows)
  tint     a low-chroma container (light L 0.935, dark L 0.285, OLED L 0.22) for the module's zones and pills
  on       text on an accent fill: the theme's ink or ground, whichever reads better
Checks per palette and theme (all computed with designkit): ink on ground 7-15.8:1 (15.8 = Material's
high-emphasis white on #121212, the comfort ceiling); accent on ground >= 4.5; ink on tint >= 7; accent on
tint >= 3; on-accent >= 4.5; in sRGB gamut.

Groups: every calendar x routines x check-in triple. Feasible when, in light and dark:
  accents pairwise CIEDE2000 >= 20; >= 10 under protanopia and deuteranopia (designkit's calibrated CVD
  floor; tritanopia, about 1 in 10,000, is reported per group, not gated); every accent >= 15 from Pages'
  amber. Modules also carry labels, icons and places, so colour is never their only channel. Then non-dominated sorting over
  (harmony fit of the four hues incl. Pages, min separation, min CVD separation, chroma balance), and a
  greedy farthest-point pick of TARGET groups from the best ranks, each palette used at most MAX_USES
  times, pinks in at most a third.

    PYTHONUTF8=1 python tools/screens/palette_groups.py
"""
import glob
import html
import itertools
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T0 = os.path.join(ROOT, "docs", "screens", "t0")
ENGINE = os.environ.get("DESIGNKIT_ENGINE") or next(iter(sorted(glob.glob(os.path.join(
    os.path.expanduser("~"), "AppData", "Roaming", "Claude", "local-agent-mode-sessions", "*", "*", "rpm", "*", "engine", "designkit")))), "")
sys.path.insert(0, os.path.dirname(ENGINE))
from designkit import colorspace as cs, harmony  # noqa: E402

TARGET, MAX_USES = 24, 5
MODULES = ["calendar", "routines", "checkin"]
LABEL = {"calendar": "Calendar", "routines": "Routines", "checkin": "check-in"}

# ---- OKLCH <-> sRGB (Björn Ottosson's OKLab) --------------------------------------------------------------
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_oklch(hx):
    r, g, b = [_lin(v / 255) for v in cs.parse_hex(hx)]
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def _oklch_rgb(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklch_hex(L, C, h):
    """The colour at (L, h) with the most chroma <= C that is inside sRGB."""
    lo, hi = 0.0, C
    for _ in range(30):
        rgb = _oklch_rgb(L, hi, h)
        if all(-1e-6 <= v <= 1 + 1e-6 for v in rgb):
            break
        mid = (lo + hi) / 2
        if all(-1e-6 <= v <= 1 + 1e-6 for v in _oklch_rgb(L, mid, h)):
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-4:
            hi = lo
    rgb = _oklch_rgb(L, hi, h)
    return cs.to_hex([max(0, min(1, _gam(max(0.0, v)))) * 255 for v in rgb])


def lab_hex(Lstar, a=0.0, b=0.0):
    fy = (Lstar + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * inv(fx), 1.0 * inv(fy), 1.08883 * inv(fz)
    r = 3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z
    g = -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z
    bl = 0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z
    return cs.to_hex([max(0, min(1, _gam(max(0.0, v)))) * 255 for v in (r, g, bl)])


# ---- grounds ----------------------------------------------------------------------------------------------
# Light keeps the mockup's #F4F4F2; the mockup's white cards become #FBFBF9 (no pure white). Dark moves from
# #17181A (L* 8.2) to L* 6, keeping its slight cool tint; OLED is black with near-black cards.
GROUND = {
    "light": {"bg": "#F4F4F2", "zone": "#FBFBF9", "zone2": "#EBEBE7", "ink": "#1C1C1A", "dim": "#6B6B66"},
    "dark": {"bg": lab_hex(6.0, 0, -1.2), "zone": lab_hex(10.5, 0, -1.4), "zone2": lab_hex(15.0, 0, -1.6), "ink": "#E6E5E1", "dim": "#9C9A94"},
    "oled": {"bg": "#000000", "zone": lab_hex(5.0, 0, -1.0), "zone2": lab_hex(9.5, 0, -1.2), "ink": "#DCDBD7", "dim": "#93918B"},
}
THEMES = list(GROUND)
INK_BAND = (7.0, 15.8)
# Pages keeps the mockups' colours exactly (owner, 2026-10-06): home-workshop.html's --L/--Lt/--Ct at hue 75, chroma 0.12.
# The mockups have no OLED theme, so OLED reuses dark's.
PAGES = {"light": oklch_hex(0.55, 0.12, 75), "dark": oklch_hex(0.78, 0.12, 75), "oled": oklch_hex(0.78, 0.12, 75)}
PAGES_TINT = {"light": oklch_hex(0.94, 0.035, 75), "dark": oklch_hex(0.33, 0.05, 75), "oled": oklch_hex(0.33, 0.05, 75)}
CAP = {"light": 0.13, "dark": 0.11, "oled": 0.11}
# Accent contrast per module, staggered by register (app-register-layout: calendar is the firmest module,
# check-in the most ambient). Equal contrast means equal luminance, and equal-luminance hues collapse under
# colour-blind vision (median CVD separation 2.3 at 5.0 / 5.0 / 5.0); the stagger buys that separation.
# Chroma floor: the lexicon's most muted identities are lifted to it so modules stay apart. Both are
# chosen by the sweep in sweep() and reported in palettes.md.
CONTRAST = {"calendar": 6.5, "routines": 5.0, "checkin": 4.5}
CHROMA_FLOOR = 0.06
# Warm (earthy, sand) identities: lower caps, so a rust stays clay when lightened for dark and its tint reads
# beige, not peach (both excluded by the owner).
EARTHY_ACCENT = {"light": 0.072, "dark": 0.07, "oled": 0.07}
EARTHY_TINT = {"light": 0.015, "dark": 0.02, "oled": 0.02}
TINT = {"light": (0.935, 0.35, 0.035), "dark": (0.285, 0.40, 0.045), "oled": (0.22, 0.40, 0.045)}


def ratio(a, b):
    return cs.contrast_ratio(a, b)


# ---- hue rules --------------------------------------------------------------------------------------------
def hue_class(L, C, h, adapted=False):
    """allowed | pink | earthy | neutral, or forbidden:<why>. Applied to the identity colour, and with
    adapted=True to each theme's accent: there lightness is set by the contrast target (dark accents are all
    light), so chroma alone decides whether a warm hue reads clay or coral, sand or amber."""
    if C < 0.03:
        return "neutral"
    if adapted:
        if (h >= 345 or h < 20) and C >= 0.12:
            return "forbidden:red"
        if 20 <= h < 60 and C > 0.075:
            return "forbidden:coral or red-orange"
        if 60 <= h < 105 and C >= 0.065:
            return "forbidden:amber or gold"
        return "allowed"
    if h >= 332 or h < 20:  # 332: Dusty Bloom (339) and Rosewood (335) read pink; Le Printemps' lilac (324) does not
        if L >= 0.62:
            return "pink"
        if h >= 345 or h < 20:
            return "forbidden:red" if C >= 0.10 else "plum"
        return "plum"
    if h < 60:
        if L <= 0.62 and C <= 0.13:
            return "earthy"
        return "forbidden:red-orange, coral or peach"
    if h < 105:
        return "sand" if C < 0.05 else "forbidden:orange, amber or gold"
    return "allowed"


# ---- palettes ---------------------------------------------------------------------------------------------
def identity(pair):
    for reg in ("light", "dark"):
        roles = pair.get(reg, {})
        for role in ("primary", "accent", "secondary"):
            if role in roles:
                return roles[role]
    return None


def solve_accent(h, C, theme, target=5.0):
    """Lightness giving `target`:1 against the ground, on the side away from it."""
    bg = GROUND[theme]["bg"]
    dark_side = theme == "light"
    lo, hi = (0.15, 0.75) if dark_side else (0.45, 0.97)
    for _ in range(40):
        mid = (lo + hi) / 2
        r = ratio(oklch_hex(mid, C, h), bg)
        if dark_side:
            lo, hi = (mid, hi) if r > target else (lo, mid)
        else:
            lo, hi = (lo, mid) if r > target else (mid, hi)
    return oklch_hex(lo if dark_side else hi, C, h)


def build(module, pick, pair_name, hx, character=""):
    L, C, h = hex_to_oklch(hx)
    cls = hue_class(L, C, h)
    pal = {"id": "%s|%s|%s" % (module, pick["entry"], pair_name), "module": module, "entry": pick["entry"], "pair": pair_name,
           "how": pick["how"], "move": pick.get("move", ""), "why": pick["why"], "source": hx, "character": character,
           "class": cls, "hue": round(h, 1), "themes": {}, "checks": {}}
    for t in THEMES:
        g = GROUND[t]
        warm = cls in ("earthy", "sand")  # lightened for dark, rust turns coral: keep it clay
        ca = max(CHROMA_FLOOR, min(C, CAP[t], EARTHY_ACCENT[t] if warm else 1))
        acc = solve_accent(h, ca, t, CONTRAST[module]) if t != "oled" else pal["themes"]["dark"]["accent"]
        tl, k, cmax = TINT[t]
        tint = oklch_hex(tl, min(C * k, EARTHY_TINT[t] if warm else cmax), h)
        on = max((g["ink"], g["bg"]), key=lambda x: ratio(x, acc))
        pal["themes"][t] = {"accent": acc, "tint": tint, "on": on}
        pal["checks"][t] = {"ink/ground": ratio(g["ink"], g["bg"]), "accent/ground": ratio(acc, g["bg"]),
                            "ink/tint": ratio(g["ink"], tint), "accent/tint": ratio(acc, tint), "on/accent": ratio(on, acc)}
    pal["adapted"] = {t: hue_class(*hex_to_oklch(pal["themes"][t]["accent"]), adapted=True) for t in THEMES}
    if any(v.startswith("forbidden") for v in pal["adapted"].values()):
        pal["class"] = "forbidden once adapted (" + ", ".join(sorted({v[10:] for v in pal["adapted"].values() if v.startswith("forbidden")})) + ")"
    floors = {"accent/ground": 4.5, "ink/tint": 7.0, "accent/tint": 3.0, "on/accent": 4.5}
    pal["passes"] = all(c[k] >= v for c in pal["checks"].values() for k, v in floors.items()) and \
        all(INK_BAND[0] <= c["ink/ground"] <= INK_BAND[1] for c in pal["checks"].values())
    return pal


def palettes():
    keys = json.load(open(os.path.join(T0, "palette-keywords.json"), encoding="utf-8"))
    src = {e["entry"]: e for e in json.load(open(os.path.join(T0, "palette-sources.json"), encoding="utf-8"))["entries"]}
    out, rejected = {m: [] for m in MODULES}, []
    for m in MODULES:
        for pick in keys["modules"][m]["picks"]:
            items = []
            if "cited" in pick:
                items.append((pick["cited"]["name"], identity(pick["cited"]), "cited from the entry's own text"))
            for name in pick.get("pairs", []):
                pair = next(p for p in src[pick["entry"]]["pairs"] if p["name"] == name)
                items.append((name, identity(pair), pair.get("character", "")))
            for name, hx, character in items:
                p = build(m, pick, name, hx, character)
                (rejected if p["class"].startswith("forbidden") or not p["passes"] else out[m]).append(p)
    return out, rejected


# ---- groups -----------------------------------------------------------------------------------------------
def de(a, b):
    return cs.delta_e_hex(a, b)


def group_metrics(trip):
    m = {"sep": 1e9, "cvd": 1e9, "tritan": 1e9, "pages": 1e9}
    for t in ("light", "dark"):
        acc = [p["themes"][t]["accent"] for p in trip]
        for a, b in itertools.combinations(acc, 2):
            m["sep"] = min(m["sep"], de(a, b))
            for kind in ("protanopia", "deuteranopia"):
                m["cvd"] = min(m["cvd"], de(cs.simulate_cvd(a, kind), cs.simulate_cvd(b, kind)))
            m["tritan"] = min(m["tritan"], de(cs.simulate_cvd(a, "tritanopia"), cs.simulate_cvd(b, "tritanopia")))
        m["pages"] = min([m["pages"]] + [de(a, PAGES[t]) for a in acc])
    hues = [cs.hex_to_hsl(p["themes"]["light"]["accent"])[0] for p in trip] + [cs.hex_to_hsl(PAGES["light"])[0]]
    m["template"], m["harmony"], _ = harmony.best_template(hues)
    chroma = [hex_to_oklch(p["themes"]["light"]["accent"])[1] for p in trip]
    m["balance"] = max(chroma) - min(chroma)
    m["pinks"] = sum(p["class"] == "pink" for p in trip)
    return m


def feasible(m):
    return m["sep"] >= 20 and m["cvd"] >= 10 and m["pages"] >= 15


def ranks(cands):
    """Non-dominated sorting: higher harmony, sep, protan/deutan and tritan separation; lower balance."""
    keyf = lambda c: (c["m"]["harmony"], c["m"]["sep"], c["m"]["cvd"], c["m"]["tritan"], -c["m"]["balance"])
    left, rank = list(cands), 1
    while left:
        front = [c for c in left if not any(all(x >= y for x, y in zip(keyf(o), keyf(c))) and keyf(o) != keyf(c) for o in left)]
        for c in front:
            c["rank"] = rank
        left = [c for c in left if c not in front]
        rank += 1


def gdist(a, b):
    return sum(de(x["themes"]["light"]["accent"], y["themes"]["light"]["accent"]) for x, y in zip(a["trip"], b["trip"]))


def select(cands):
    cands.sort(key=lambda c: (c["rank"], -c["m"]["harmony"], -c["m"]["sep"]))
    chosen, uses, pinks = [], {}, 0

    def take(c):
        nonlocal pinks
        chosen.append(c)
        pinks += c["m"]["pinks"] > 0
        for p in c["trip"]:
            uses[p["id"]] = uses.get(p["id"], 0) + 1

    # Coverage first: every keyword (module, entry) with a feasible group gets its best one, so each of the
    # owner-approved picks is seen at least once. Pinks are capped against the target here.
    for key in sorted({(p["module"], p["entry"]) for c in cands for p in c["trip"]}):
        if any((p["module"], p["entry"]) == key for c in chosen for p in c["trip"]):
            continue
        ok = [c for c in cands if c not in chosen and any((p["module"], p["entry"]) == key for p in c["trip"])
              and all(uses.get(p["id"], 0) < MAX_USES for p in c["trip"]) and (c["m"]["pinks"] == 0 or pinks < TARGET // 3)]
        if ok:
            near_best = [c for c in ok if c["rank"] <= ok[0]["rank"] + 1]
            take(max(near_best, key=lambda c: min((gdist(c, s) for s in chosen), default=0)) if chosen else ok[0])
    pool_rank = 1
    while len(chosen) < TARGET:
        pool = [c for c in cands if c["rank"] <= pool_rank and c not in chosen
                and all(uses.get(p["id"], 0) < MAX_USES for p in c["trip"])
                and (c["m"]["pinks"] == 0 or pinks < TARGET // 3)]
        if not pool:
            if pool_rank > max(c["rank"] for c in cands):
                break
            pool_rank += 1
            continue
        best = pool[0] if not chosen else max(pool, key=lambda c: (min(gdist(c, s) for s in chosen), -c["rank"]))
        take(best)
        if len(pool) < 3:
            pool_rank += 1
    # pinks in at most a third of the groups actually shown: drop the weakest pink groups if short of TARGET
    while sum(c["m"]["pinks"] > 0 for c in chosen) * 3 > len(chosen):
        chosen.remove(max((c for c in chosen if c["m"]["pinks"]), key=lambda c: (c["rank"], -c["m"]["harmony"])))
    return chosen


# ---- output -----------------------------------------------------------------------------------------------
e = html.escape


def write_md(pals, rejected, cands, chosen):
    n_total = math.prod(len(pals[m]) for m in MODULES)
    out = ["# Module palettes", "", "Generated by `tools/screens/palette_groups.py`; its docstring states every rule and threshold.", "",
           "Grounds: light %s, dark %s (L* 6), OLED %s. Pages keeps its mockup amber (%s light, %s dark)." % (
               GROUND["light"]["bg"], GROUND["dark"]["bg"], GROUND["oled"]["bg"], PAGES["light"], PAGES["dark"]), "",
           "## Palettes per module", ""]
    for m in MODULES:
        out += ["### %s (%d)" % (LABEL[m], len(pals[m])), "", "| Keyword · pair | How | Class | Light accent | Dark accent | Accent/ground L·D·O | Ink/tint min |", "|---|---|---|---|---|---|---|"]
        for p in pals[m]:
            c = p["checks"]
            out.append("| %s · %s | %s | %s | %s | %s | %.1f · %.1f · %.1f | %.1f |" % (
                p["entry"], p["pair"], p["how"] + (" (%s)" % p["move"] if p["move"] else ""), p["class"], p["themes"]["light"]["accent"],
                p["themes"]["dark"]["accent"], c["light"]["accent/ground"], c["dark"]["accent/ground"], c["oled"]["accent/ground"],
                min(c[t]["ink/tint"] for t in THEMES)))
        out.append("")
    out += ["## Left out", ""] + ["- %s · %s (%s): %s" % (p["entry"], p["pair"], LABEL[p["module"]], p["class"] if p["class"].startswith("forbidden") else "fails a check") for p in rejected]
    shown = {(p["module"], p["entry"]) for c in chosen for p in c["trip"]}
    missing = sorted({(p["module"], p["entry"]) for m in MODULES for p in pals[m]} - shown)
    out += ["", "## Keywords in no group", ""] + (["- %s: %s (no feasible group: too close to another module or to Pages)" % (LABEL[m], n) for m, n in missing] or ["None."])
    out += ["", "## Groups", "", "%d triples; %d feasible (separation, colour vision, distance from Pages); %d chosen." % (n_total, len(cands), len(chosen)), "",
            "| # | Calendar | Routines | check-in | Harmony | Min ΔE | Min ΔE protan/deutan | Min ΔE tritan | From Pages | Chroma spread |", "|---|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(chosen, 1):
        t, m = c["trip"], c["m"]
        out.append("| %d | %s · %s | %s · %s | %s · %s | %s %.2f | %.1f | %.1f | %.1f | %.1f | %.3f |" % (
            i, t[0]["entry"], t[0]["pair"], t[1]["entry"], t[1]["pair"], t[2]["entry"], t[2]["pair"], m["template"], m["harmony"], m["sep"], m["cvd"], m["tritan"], m["pages"], m["balance"]))
    out += ["", "## Why the contrast is staggered", "",
            "Feasible groups for each accent contrast (calendar / routines / check-in) and chroma floor. Equal contrast means equal luminance, which colour-blind vision cannot separate.", "",
            "| Contrast | Floor 0.04 | Floor 0.06 | Floor 0.07 |", "|---|---|---|---|"]
    out += ["| %s | %s |" % (" / ".join("%g" % x for x in con), " | ".join(str(n) for n in row)) for con, row in sweep()]
    with open(os.path.join(T0, "palettes.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out


CSS = """
:root{color-scheme:light}
:root,[data-theme=light]{%(light)s}
[data-theme=dark]{%(dark)s}
[data-theme=oled]{%(oled)s}
*{box-sizing:border-box}body{margin:0;padding:20px 16px 48px;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}
h1{font-size:21px;margin:0 0 4px}h2{font-size:16px;margin:0}p{max-width:90ch}.dim{color:var(--dim)}
.sw{display:flex;gap:6px;margin:12px 0}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
.sw button.on{background:var(--ink);color:var(--bg)}
.grp{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start;background:var(--zone);border-radius:16px;padding:14px;margin:14px 0}
.info{flex:1 1 380px;min-width:0}.mods{display:grid;gap:8px;margin-top:8px}
.mod{display:grid;grid-template-columns:110px 1fr;gap:10px;align-items:center}
.chips{display:flex;gap:6px}.chip{width:54px;height:40px;border-radius:10px;display:grid;place-items:center;font-size:11px;font-weight:600}
.kw{font-size:12.5px}.kw small{display:block;color:var(--dim);font-size:11.5px}
.ob{font-size:10.5px;padding:1px 6px;border-radius:999px;background:var(--zone2);color:var(--dim);margin-left:4px}
.figs{font-size:11.5px;color:var(--dim);margin-top:8px}
/* mini home */
.ph{width:260px;height:470px;border-radius:18px;background:var(--bg);overflow:hidden;display:flex;flex-direction:column;flex:none;box-shadow:0 0 0 1px var(--zone2);font-size:11px}
.ph .hd{height:36px;display:flex;align-items:center;padding:0 10px;font-weight:600;font-size:12.5px;box-shadow:inset 3px 0 0 var(--cal-a)}
.ph .bd{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:6px;overflow:hidden}
.z{background:var(--zone);border-radius:9px;padding:5px 7px}.z h4{margin:0 0 2px;font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim);display:flex;gap:4px;align-items:center}
.dot{width:6px;height:6px;border-radius:50%%}.row{display:flex;align-items:center;gap:6px;padding:3px 0}.row .t{flex:1}
.ck{width:11px;height:11px;border-radius:50%%;border:1.4px solid var(--dim)}.sq{width:11px;height:11px;border-radius:3px}
.pill{border-radius:999px;padding:1px 8px;font-size:10px}
.cap{background:var(--zone2);border-radius:9px;padding:6px 8px;color:var(--dim)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:6px}.tile{border-radius:9px;padding:7px 8px;min-height:40px}
.timer{align-self:flex-start;border-radius:999px;padding:2px 8px;display:flex;gap:5px;align-items:center}
.bar{height:44px;display:flex;background:var(--zone2)}.bar div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:9px;color:var(--dim);gap:1px}
.bar i{font-style:normal;font-size:12px;padding:1px 10px;border-radius:999px}.bar .on{color:var(--ink);font-weight:600}
"""


def var_block(t):
    g = GROUND[t]
    return "--bg:%s;--zone:%s;--zone2:%s;--ink:%s;--dim:%s;--pg-a:%s;--pg-t:%s" % (
        g["bg"], g["zone"], g["zone2"], g["ink"], g["dim"], PAGES[t], PAGES_TINT[t])


def group_html(i, c):
    trip, m = c["trip"], c["m"]
    style = ";".join("--%s-%s-%s:%s" % (k, r, t, p["themes"][t][role]) for k, p in zip(("cal", "rou", "chk"), trip)
                     for t in THEMES for r, role in (("a", "accent"), ("t", "tint"), ("o", "on")))
    mods = "".join(
        '<div class="mod"><div class="chips"><span class="chip" style="background:var(--%s-a);color:var(--%s-o)">Aa</span>'
        '<span class="chip" style="background:var(--%s-t);color:var(--ink)">Aa</span></div><div class="kw"><b>%s</b>: %s · %s%s'
        '<small>%s</small></div></div>' % (k, k, k, LABEL[p["module"]], e(p["entry"]), e(p["pair"]),
                                             '<span class="ob">%s</span>' % e(p["move"]) if p["move"] else '<span class="ob">direct</span>', e(p["why"]))
        for k, p in zip(("cal", "rou", "chk"), trip))
    figs = "Harmony: %s %.2f · min ΔE %.1f · protan/deutan min ΔE %.1f · tritan %.1f · from Pages %.1f · chroma spread %.3f%s" % (
        m["template"], m["harmony"], m["sep"], m["cvd"], m["tritan"], m["pages"], m["balance"], " · contains pink" if m["pinks"] else "")
    home = ('<div class="ph"><div class="hd">Today · Mon 5 Oct</div><div class="bd">'
            '<div class="cap">+ Add… dentist tomorrow 9am</div>'
            '<div class="timer" style="background:var(--rou-t)"><span class="dot" style="background:var(--rou-a)"></span>Reading · 0:24 <b>Stop</b></div>'
            '<div class="z"><h4><span class="dot" style="background:var(--cal-a)"></span>Agenda</h4>'
            '<div class="row"><span style="color:var(--cal-a);font-weight:600">09:00</span><span class="t">Dentist</span></div>'
            '<div class="row"><span class="ck"></span><span class="t">Pay the fine</span><span class="pill" style="background:var(--cal-t)">today</span></div>'
            '<div class="row"><span style="color:var(--cal-a);font-weight:600">15:00</span><span class="t">Call the bank</span></div></div>'
            '<div class="z"><h4><span class="dot" style="background:var(--rou-a)"></span>Routines</h4>' +
            "".join('<div class="row"><span class="sq" style="border:1.4px solid var(--rou-a)"></span><span class="t">%s</span><span class="pill" style="background:var(--rou-t)">%s</span></div>' % (a, b)
                    for a, b in (("Walk", "Log"), ("Water · 3 of 8", "Log"), ("Morning routine", "Open"))) + '</div>'
            '<div class="two"><div class="tile" style="background:var(--chk-t)">How are things? <span style="color:var(--chk-a)">›</span></div>'
            '<div class="tile" style="background:var(--chk-t)">Today\'s ledger <span style="color:var(--chk-a)">›</span></div>'
            '<div class="tile" style="background:var(--pg-t)">Journal <span style="color:var(--pg-a)">›</span></div>'
            '<div class="tile" style="background:var(--zone)">Pinned pages · 4</div></div></div>'
            '<div class="bar"><div class="on"><i style="background:var(--cal-t);color:var(--cal-a)">◷</i>Today</div><div><i>▦</i>Week</div>'
            '<div><i>✱</i>Hub</div><div><i style="color:var(--rou-a)">↻</i>Routines</div><div><i style="color:var(--pg-a)">☰</i>Pages</div></div></div>')
    return '<section class="grp" style="%s"><div class="info"><h2>Group %d</h2><div class="mods">%s</div><div class="figs">%s</div></div>%s</section>' % (
        style, i, mods, figs, home)


def write_html(chosen, n_cands):
    mapping = "\n".join("[data-theme=%s] .grp{%s}" % (t, ";".join("--%s-%s:var(--%s-%s-%s)" % (k, r, k, r, t) for k in ("cal", "rou", "chk") for r in "ato"))
                        for t in THEMES)
    mapping = mapping.replace("[data-theme=light] .grp", ":root .grp,[data-theme=light] .grp", 1)
    css = CSS % {t: var_block(t) for t in THEMES} + mapping
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            "<title>Factotum module palettes</title><style>%s</style></head><body>" % css,
            "<h1>Module palettes: %d groups</h1>" % len(chosen),
            '<p class="dim">Calendar, Routines and check-in, one palette each; Pages keeps its amber. Every colour is computed by '
            "<code>tools/screens/palette_groups.py</code> from the lexicon picks in <code>palette-keywords.json</code>, and checked on all three grounds. "
            "%d groups passed the separation and colour-vision checks; these are the most harmonious, most distinct ones, chosen to differ from each other. "
            "Each module row shows its accent (filled) and its tint. The mini home applies the group.</p>" % n_cands,
            '<div class="sw"><button data-t="light" class="on">Light</button><button data-t="dark">Dark (L* 6)</button><button data-t="oled">OLED</button></div>']
    page += [group_html(i, c) for i, c in enumerate(chosen, 1)]
    page.append("<script>document.querySelectorAll('.sw button').forEach(b=>b.onclick=()=>{document.documentElement.dataset.theme=b.dataset.t;"
                "document.querySelectorAll('.sw button').forEach(x=>x.classList.toggle('on',x===b))});"
                "if(matchMedia('(prefers-color-scheme: dark)').matches)document.querySelector('.sw button[data-t=dark]').click()</script></body></html>")
    with open(os.path.join(T0, "palettes.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(page))


def sweep():
    """Feasible-group counts under other staggers and floors; restores the chosen settings."""
    saved = dict(CONTRAST), CHROMA_FLOOR
    rows = []
    try:
        for con in ((5.0, 5.0, 5.0), (6.0, 5.0, 4.5), (6.5, 5.0, 4.5), (7.0, 5.2, 4.5)):
            row = []
            for fl in (0.04, 0.06, 0.07):
                globals()["CHROMA_FLOOR"] = fl
                CONTRAST.update(zip(MODULES, con))
                pals, _ = palettes()
                row.append(sum(feasible(group_metrics(t)) for t in itertools.product(*(pals[m] for m in MODULES))))
            rows.append((con, row))
    finally:
        CONTRAST.update(saved[0])
        globals()["CHROMA_FLOOR"] = saved[1]
    return rows


def main():
    pals, rejected = palettes()
    cands = []
    for trip in itertools.product(*(pals[m] for m in MODULES)):
        m = group_metrics(trip)
        if feasible(m):
            cands.append({"trip": trip, "m": m})
    ranks(cands)
    chosen = select(cands)
    out = write_md(pals, rejected, cands, chosen)
    write_html(chosen, len(cands))
    return pals, rejected, cands, chosen, out


if __name__ == "__main__":
    if not os.path.isdir(ENGINE):
        raise SystemExit("designkit engine not found; set DESIGNKIT_ENGINE")
    pals, rejected, cands, chosen, out = main()
    print("engine:", ENGINE)
    print("\n".join(out))
