"""Palette candidates, one keyword at a time (owner, 2026-10-06: "propose the keywords as single picks to then
discuss, rather than definitive solutions"). Writes docs/screens/t0/palette-candidates.html and .md.

Each keyword is shown on its own with the lexicon's own named palette pairs, unblended and unadapted, on a small
snippet of the module it was proposed for. Every hex below is copied from visual-craft's lexicon shard named beside
it, and the script refuses to run if one is not found there. Contrast is measured with designkit, not copied.

    PYTHONUTF8=1 python tools/screens/palette_candidates.py
"""
import glob
import html
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_HTML = os.path.join(ROOT, "docs", "screens", "t0", "palette-candidates.html")
OUT_MD = os.path.join(ROOT, "docs", "screens", "t0", "palette-candidates.md")
DK = sorted(glob.glob(os.path.expanduser("~/.claude/plugins/cache/*/design-optimization/*/engine/designkit_cli.py")))[-1]
LEXICON = sorted(glob.glob(os.path.expanduser(
    "~/AppData/Roaming/Claude/local-agent-mode-sessions/*/*/rpm/*/skills/visual-craft/references/lexicon")))


def reg(surface, text, primary, secondary=None, accent=None):
    return {k: v for k, v in dict(surface=surface, text=text, primary=primary, secondary=secondary, accent=accent).items() if v}


# module -> candidates: (keyword, shard, oblique?, what it would bring here, [(pair name, light, dark or None)])
CANDIDATES = {
    "Calendar": [
        ("Swiss / International", "screen-styles.md", False, "The grid as the design: hairline rules for hours and days, one colour used once.", [
            ("Pair 1 (teal with a signal-red accent; unnamed in the lexicon)", reg("#e8f0f0", "#0f1018", "#0799a9", "#80b0b2", "#cd2d20"), reg("#0e0f09", "#e8f0f0", "#65e2f7", "#6f7880", "#f83516")),
            ("Pair 2 (blue with a yellow accent; unnamed in the lexicon)", reg("#f7f7f5", "#131313", "#1D3557", "#6a8caf", "#F4D03F"), reg("#101114", "#f2f2ef", "#729eca", "#5c738a", "#F4D03F"))]),
        ("Civic / Government", "contexts.md", True, "A timetable is public wayfinding: legible under stress, never colour-only, focus rings as designed as the rest.", [
            ("Statute", reg("#FFFFFF", "#1B1B1B", "#1668B0"), reg("#121417", "#EDEFF2", "#8FC2F0")),
            ("Municipal", reg("#F7F6F3", "#1C1B19", "#245039"), reg("#131513", "#E9EAE5", "#77B894"))]),
        ("Ming Blue-and-White", "world-traditions.md", True, "Two colours only: a busy day is a dense cobalt band, a free day is clean porcelain.", [
            ("Day and night (one pair by role inversion)", reg("#F7F7F8", "#143667", "#17488C", accent="#0F3A76"), reg("#0B1E3D", "#F7F7F8", "#F7F7F8", accent="#4A78B8"))]),
    ],
    "Routines": [
        ("Naturecore", "subculture-styles.md", False, "Growth and being outdoors: routines as a living place rather than a checklist.", [
            ("Mossland", reg("#d2cea5", "#171a0b", "#697d41", "#b2c484", "#816345"), reg("#1e240c", "#d2cea5", "#99b469", "#afae80", "#e1b793")),
            ("Stone & Sage", reg("#bcbcb7", "#3d4340", "#7c8e79", "#9ab1b9", "#cebdd1"), reg("#3d4340", "#c7c7d0", "#7c8b9e", "#9ab1b9", "#cebdd1")),
            ("Forest Scholastic", reg("#fbfbfb", "#122e1a", "#085838", "#256b37", "#d6dad8"), reg("#122e1a", "#fbfbfb", "#085838", "#679c80", "#9fdbcc"))]),
        ("Health / Consumer Wellbeing", "contexts.md", False, "Warm, not clinical; red kept for real emergencies; a value shown against its range, not as a bare score.", [
            ("Daylight", reg("#FBF9F5", "#22211D", "#2C6050"), reg("#171614", "#E9E7E1", "#7CBAA2")),
            ("Linen", reg("#F7F4F0", "#26221E", "#8E4826"), reg("#1A1715", "#EAE5DF", "#D9906A"))]),
        ("Wabi Sabi", "world-traditions.md", True, "Built on the gap: a missed day drawn as an honest gap, never a broken streak.", [
            ("Clay & Umber", reg("#d4c9bf", "#3d2b1b", "#9d8766", "#b7aa97", "#a3623f"), reg("#272016", "#dddad0", "#705c3e", "#5b543c", "#a3623f")),
            ("Sun-bleached Bark", reg("#d2ccc6", "#372e25", "#9d8c7b", "#b6afa5", "#805e4d"), reg("#1d1a16", "#e4e1dd", "#64594f", "#7e7567", "#805e4d"))]),
        ("Craft / Artisan", "contexts.md", True, "Logging as a practised hand: precise, made by someone, not a game score.", [
            ("Dusty Bloom", reg("#eadad6", "#7c3b30", "#dda5cb", "#8568a9", "#ebac78"), reg("#7c3b30", "#eadad6", "#e6b7cf", "#c398a2", "#f39a6c")),
            ("Sage & Clay", reg("#e4e1df", "#1c4650", "#32625b", "#a17024", "#ac858d"), reg("#32625b", "#e4e1df", "#51bca9", "#c2a526", "#9a6371"))]),
    ],
    "Check-in": [
        ("Serene / Calm", "moods.md", False, "One thing at full contrast at a time; low internal contrast everywhere else.", [
            ("Still Water", reg("#F2F5F4", "#2B3634", "#41695F"), reg("#151A19", "#DDE5E2", "#8CBFB1")),
            ("Chalk", reg("#F5F3EF", "#35322D", "#75674F"), reg("#1B1917", "#E4DFD6", "#C0AE8E"))]),
        ("Introverted-rainy", "moods.md", True, "The inverse of the cheerful default: permission not to be sunny. Washed-out on purpose.", [
            ("Rainy register (the lexicon gives one register, no dark)", reg("#E3E5E8", "#2D3643", "#7889A1", "#9BA4B0", "#506786"), None)]),
        ("Goryeo Celadon", "world-traditions.md", True, "A colour between moods, neither happy nor sad: the screen never hints at a right answer.", [
            ("Day and night (one pair by role inversion)", reg("#F1F3F3", "#202726", "#A2CDC5", accent="#1C2120"), reg("#0e1614", "#E7EEEC", "#A2CDC5", accent="#DCEAE7"))]),
    ],
    "Pages": [
        ("Editorial / Print-derived", "screen-styles.md", False, "The page as a composition: type does the work, one ink colour.", [
            ("Fired Earth", reg("#f1eae6", "#292725", "#ac5228", "#307c8a", "#ed9228"), reg("#292725", "#f1eae6", "#db7c51", "#70b9c6", "#ead46a")),
            ("Indigo Atlas", reg("#e5efed", "#383342", "#2b2a5f", "#5f80cd", "#9a77c3"), reg("#2b2a5f", "#e5efed", "#70b9c6", "#9a77c3", "#eed881"))]),
        ("Light / Dark Academia", "subculture-styles.md", False, "Books, paper and ink; the journal as a notebook you keep.", [
            ("Marginalia", reg("#e5dade", "#1e140d", "#624a32", "#775239", "#707563"), reg("#1e140d", "#e5dade", "#b79a7d", "#a28166", "#707563")),
            ("Tallow & Tome", reg("#d8d6d3", "#1e1712", "#5e3e2c", "#876d4b", "#474634"), reg("#1e1712", "#d8d6d3", "#dfcfb7", "#b79a7d", "#6c6454"))]),
        ("Medieval", "period-styles.md", True, "Rubrication and the illuminated drop cap: a page title that opens like a manuscript.", [
            ("Illuminated Manuscript", reg("#f2e9da", "#292622", "#d8c599", accent="#ba4235"), reg("#1a1310", "#f0e1c4", "#846c40", accent="#fadf8c")),
            ("Tidal Keep", reg("#d6dad8", "#162d39", "#627f82", accent="#256a81"), reg("#162d39", "#d6dad8", "#5b6360", accent="#9b844a"))]),
        ("Developer Tools", "contexts.md", True, "Databases and formulas get their own surface a hair off the page, the way code blocks do.", [
            ("Console", reg("#FBFBFA", "#16181B", "#4B3AA6", "#F1F2F4"), reg("#101216", "#E3E6EA", "#A99AF0", "#191C21")),
            ("Terminal Warm", reg("#FAF8F4", "#1A1815", "#7A400E"), reg("#141210", "#E8E4DC", "#D89A4E"))]),
    ],
}


def verify_sources():
    """Every hex must appear in the lexicon shard it is attributed to."""
    if not LEXICON:
        raise SystemExit("visual-craft's lexicon folder was not found")
    text = {}
    for module, cands in CANDIDATES.items():
        for kw, shard, _, _, pairs in cands:
            if shard not in text:
                with open(os.path.join(LEXICON[-1], shard), encoding="utf-8") as fh:
                    text[shard] = fh.read().lower()
            for name, light, dark in pairs:
                for r in (light, dark or {}):
                    for role, hx in r.items():
                        if hx.lower() not in text[shard]:
                            raise SystemExit("%s / %s / %s: %s %s not in %s" % (module, kw, name, role, hx, shard))


def ratio(fg, bg):
    out = subprocess.run(["python", DK, "contrast", fg, bg], capture_output=True, text=True).stdout  # exit 1 = fails WCAG, still a result
    return float(re.search(r"ratio\s+([\d.]+):1", out).group(1))


def measured():
    data = {}
    for module, cands in CANDIDATES.items():
        data[module] = []
        for kw, shard, obl, note, pairs in cands:
            ps = []
            for name, light, dark in pairs:
                regs = {}
                for mode, r in (("light", light), ("dark", dark)):
                    if r:
                        regs[mode] = dict(colors=r, text=ratio(r["text"], r["surface"]), primary=ratio(r["primary"], r["surface"]))
                ps.append(dict(name=name, **regs))
            data[module].append(dict(keyword=kw, shard=shard, oblique=obl, note=note, pairs=ps))
    return data


def write(data):
    out = ["# Palette candidates, one keyword at a time", "",
           "Generated by `tools/screens/palette_candidates.py`. Each keyword is a separate candidate for discussion, shown with the lexicon's own named pairs, unblended. "
           "★ = picked with the oblique skill. Ratios are measured with designkit: text on surface, and primary on surface (below 3:1, primary is decorative only).", ""]
    for module, cands in data.items():
        out += ["## " + module, "", "| Keyword | Pair | Light: text · primary | Dark: text · primary |", "|---|---|---|---|"]
        for c in cands:
            for p in c["pairs"]:
                f = lambda m: "%.1f · %.1f" % (p[m]["text"], p[m]["primary"]) if m in p else "none in the lexicon"
                out.append("| %s%s | %s | %s | %s |" % ("★ " if c["oblique"] else "", c["keyword"], p["name"], f("light"), f("dark")))
        out.append("")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    with open(OUT_HTML.replace(".html", ".template.html"), encoding="utf-8") as fh:
        page = fh.read()
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
    return out


if __name__ == "__main__":
    verify_sources()
    print("\n".join(write(measured())))
