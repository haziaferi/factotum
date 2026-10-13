"""Module personalities (decision 15, Q4, third slate). Writes docs/screens/t0/module-personalities.md and .html.

Owner (2026-10-06): Calendar is Composed, Routines Steady, check-in Gentle (tone 0.55, 0.45 and 0.15 on the
register model's 0 restful .. 1 urgent axis). Four levers carry each personality beyond hue: chroma, lightness
spread, the tertiary's relation to the primary, and the scale's character. Roles stay primary, secondary and
tertiary, each with a container, plus a scale. No purple primaries (purple only as a tertiary); pinks in at most a
third of the groups; at most 30 groups, better rather than more. Pages is not part of this.

What the source gives and what the personality gives. A lexicon pair (all 111 in palette-sources.json, plus
the three cited colours in palette-keywords.json) gives hues only. The personality sets everything else:
  hue band    where the primary may sit (Composed cool; Steady earth; Gentle sage, mist and blush)
  chroma      one chroma for every accent of the module, under the hue rules' caps
  contrast    primary / secondary / tertiary contrast on the ground; a wider set is a crisper spread
  container   container lightness per theme; nearer the accent is softer
  gaps        the secondary's and the tertiary's hue distance from the primary
  scale       tonal (one hue), shift (secondary hue to primary hue) or short (four soft steps)
These values are design assumptions standing for the owner's three words, not measurements; the page reports
what each lever produced, so a word that did not show up in the colours is visible.

Per palette, every (primary, secondary, tertiary) choice is enumerated: source hues first, then every 5 degrees
inside the gap. Each role must pass the hue rules once adapted, stay >= 15 from the reserved state colours and
>= 12 from the other roles in light and dark, and keep ink >= 7:1 on its container. Score: harmony template fit
0.45, source fidelity 0.35, role separation 0.20. Groups: primaries >= 20 apart and >= 10 under protan and
deutan, in light and dark; each secondary >= 10 from the other modules' primaries.

    PYTHONUTF8=1 python tools/screens/module_personality.py
"""
import html
import importlib.util
import itertools
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("mp", os.path.join(HERE, "module_palettes.py"))
mp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mp)
pg, cs, harmony = mp.pg, mp.cs, mp.harmony
T0, MODULES, THEMES, LABEL = mp.T0, mp.MODULES, mp.THEMES, mp.LABEL
ROLES = ("primary", "secondary", "tertiary")
# Attention moves from magenta 335 to 320 (owner, 2026-10-07: "you can change the attention color"). At 335 a blush
# sits 13-15 from it at check-in's contrast and no pink passed; 305-320 all let the one blush palette through and
# double the feasible groups (attention_sweep in the md). 320 keeps it reading magenta; 305 separates 1.2 more
# under protan/deutan. Attention always comes with a dot or an edge, never colour alone.
ATTENTION = (320, 0.15)
mp.STATE_SETS["ink due + magenta-violet attention"] = {"attention": ATTENTION}
mp.STATES.clear()
mp.STATES.update(mp.state_colours("ink due + magenta-violet attention"))
MAX_GROUPS, MAX_USES, PINK_SHARE = 30, 3, 1 / 3
SALMON_C = 0.05
MIN_GDIST = 20
BLUSH_PARTNER = (110, 180)  # blush with sage or mist; None turns pinks off  # a group must differ from every chosen one by more than one nudged role

PERSONA = {
    "calendar": {"word": "Composed", "tone": 0.55, "says": "cool and crisp: firm role contrast, clean pale containers, a contrasting tertiary, a long tonal scale",
                 "bands": ((185, 262),), "chroma": 0.105, "contrast": (6.5, 4.5, 3.2),
                 "container": {"light": 0.955, "dark": 0.25, "oled": 0.20}, "cchroma": 0.022,
                 "sec_gap": (15, 60), "ter_gap": (90, 180), "scale": "tonal", "steps": 5},
    "routines": {"word": "Steady", "tone": 0.45, "says": "earthy and grounded: warm-mid chroma, a wider-analogous tertiary, a scale that moves from the secondary's hue to the primary's",
                 "bands": ((38, 60), (60, 105), (105, 165)), "chroma": 0.085, "contrast": (5.0, 4.5, 3.2),
                 "container": {"light": 0.93, "dark": 0.28, "oled": 0.23}, "cchroma": 0.022,
                 "sec_gap": (20, 70), "ter_gap": (40, 95), "scale": "shift", "steps": 5},
    "checkin": {"word": "Gentle", "tone": 0.15, "says": "soft: low chroma, roles close in lightness, tinted containers near the accent, an analogous tertiary, four soft steps",
                "bands": ((120, 240), (332, 352)), "chroma": 0.06, "contrast": (4.5, 4.5, 3.2),
                "container": {"light": 0.905, "dark": 0.32, "oled": 0.27}, "cchroma": 0.034,
                "sec_gap": (15, 45), "ter_gap": (12, 42), "scale": "short", "steps": 4},
}


def gap(a, b):
    return abs((a - b + 180) % 360 - 180)


def purple(h):
    return 265 <= h <= 325


def pinkish(h):
    return h >= 332 or h < 20


def reddish(h):
    """Red and its edges, for every role: below 352 reads pink; from 352 to 38 it reads red or dusty rose at these
    chromas (#986258 at hue 31 did); terracotta starts at about 38 (#95644e, hue 45)."""
    return h >= 352 or h < 38


def chroma_for(h, theme, target):
    c = min(target, pg.CAP[theme])
    if 20 <= h < 60:
        c = min(c, pg.EARTHY_ACCENT[theme])
    elif 60 <= h < 105:
        c = min(c, 0.06)
    elif h >= 325:
        c = min(c, 0.05)  # blush, kept clear of the magenta attention colour
    return c


_ROLE = {}


def role(module, i, h):
    """One role at hue h, adapted to every theme, or None when a rule fails. Cached on a 0.5-degree grid."""
    h = round(h * 2) / 2 % 360
    key = (module, i, h)
    if key in _ROLE:
        return _ROLE[key]
    if reddish(h):
        _ROLE[key] = None
        return None
    P = PERSONA[module]
    out = {}
    for t in THEMES:
        c = chroma_for(h, t, P["chroma"] * (0.9 if i == 1 else 1))
        acc = pg.solve_accent(h, c, "dark" if t == "oled" else t, P["contrast"][i])
        if 20 <= h < 55 and pg.hex_to_oklch(acc)[0] >= 0.60 and c > SALMON_C:
            c = SALMON_C  # a clay lightened for contrast reads salmon or peach (excluded): desaturate it instead
            acc = pg.solve_accent(h, c, "dark" if t == "oled" else t, P["contrast"][i])
        cc = min(P["cchroma"] * (1.3 if t != "light" else 1), c * 0.6)
        if 20 <= h < 105:
            cc = min(cc, pg.EARTHY_TINT[t])  # a warm tint above this reads peach (palettes.md, Linen)
        cont = pg.oklch_hex(P["container"][t], cc, h)
        if (pg.hue_class(*pg.hex_to_oklch(acc), adapted=True).startswith("forbidden") or not mp.reserved_ok(acc, t)
                or pg.ratio(pg.GROUND[t]["ink"], cont) < 7 or pg.ratio(acc, pg.GROUND[t]["bg"]) < min(P["contrast"][i], 4.5) - 0.05):
            out = None
            break
        out[t] = {"accent": acc, "container": cont}
    _ROLE[key] = out and {"hue": h, "themes": out}
    return _ROLE[key]


def sources():
    """Every lexicon pair and cited colour: its chromatic hues, and which modules picked it before (keywords)."""
    keys = json.load(open(os.path.join(T0, "palette-keywords.json"), encoding="utf-8"))
    picked = {}
    for m, v in keys["modules"].items():
        for p in v["picks"]:
            for n in p.get("pairs", []) + ([p["cited"]["name"]] if "cited" in p else []):
                picked.setdefault((p["entry"], n), []).append((m, p.get("how", "")))
    out = []
    for e in json.load(open(os.path.join(T0, "palette-sources.json"), encoding="utf-8"))["entries"]:
        for pair in e["pairs"]:
            out.append((e["entry"], pair["name"], [hx for reg in ("light", "dark") for r, hx in pair.get(reg, {}).items() if r not in mp.SKIP_ROLES]))
    for m, v in keys["modules"].items():
        for p in v["picks"]:
            if "cited" in p:
                out.append((p["entry"], p["cited"]["name"], list(p["cited"]["light"].values())))
    res = []
    for entry, name, hexes in out:
        hues = []
        for hx in hexes:
            L, C, h = pg.hex_to_oklch(hx)
            if C >= 0.03 and all(gap(h, x) >= 8 for x in hues):
                hues.append(h)
        if hues:
            res.append({"entry": entry, "pair": name, "hues": hues, "picked": picked.get((entry, name), [])})
    return res


def in_bands(module, h):
    return any(lo <= h <= hi for lo, hi in PERSONA[module]["bands"])


def separation(rs):
    return min(pg.de(a["themes"][t]["accent"], b["themes"][t]["accent"]) for a, b in itertools.combinations(rs, 2) for t in ("light", "dark"))


def scale(module, pal, t):
    P = PERSONA[module]
    p, s = pal["roles"]["primary"]["themes"][t], pal["roles"]["secondary"]
    L0, C0, h0 = pg.hex_to_oklch(p["container"])
    L1, C1, h1 = pg.hex_to_oklch(p["accent"])
    n = P["steps"]
    if P["scale"] == "shift":
        hs = s["hue"]
        d = (h1 - hs + 180) % 360 - 180
        return [pg.oklch_hex(L0 + (L1 - L0) * k / (n - 1), C0 + (C1 - C0) * k / (n - 1), (hs + d * k / (n - 1)) % 360) for k in range(n)]
    ease = (lambda x: x ** 1.4) if P["scale"] == "short" else (lambda x: x)  # short: chroma arrives late, soft middle steps
    return [pg.oklch_hex(L0 + (L1 - L0) * k / (n - 1), C0 + (C1 - C0) * ease(k / (n - 1)), h1) for k in range(n)]


def best_palette(module, src):
    P = PERSONA[module]
    best = None
    for hp in [h for h in src["hues"] if in_bands(module, h) and not purple(h)]:
        rp = role(module, 0, hp)
        if not rp:
            continue

        def options(i, lo, hi, allow_purple):
            seen = []
            for h in [x for x in src["hues"] if lo <= gap(x, hp) <= hi] + [hp + s * g for g in range(lo, hi + 1, 5) for s in (1, -1)]:
                h %= 360
                if (purple(h) and not allow_purple) or any(gap(h, x) < 2 for x, _, _ in seen):
                    continue
                r = role(module, i, h)
                if r:
                    seen.append((h, r, any(gap(h, x) < 2 for x in src["hues"])))
            return seen

        sec = options(1, *P["sec_gap"], False)
        if pinkish(hp) and BLUSH_PARTNER:
            sec += options(1, *BLUSH_PARTNER, False)  # analogous to a blush is red or purple: let it pair with a contrasting hue
        for (hs, rs, fs), (ht, rt, ft) in itertools.product(sec, options(2, *P["ter_gap"], True)):
            trio = (rp, rs, rt)
            sep = separation(trio)
            if sep < 12:
                continue
            harm = harmony.best_template([cs.hex_to_hsl(r["themes"]["light"]["accent"])[0] for r in trio])
            fid = (1 + fs + ft) / 3
            score = 0.45 * harm[1] + 0.35 * fid + 0.20 * min(sep / 25, 1)
            if not best or score > best["score"]:
                best = {"score": score, "harm": harm[1], "template": harm[0], "fid": fid, "sep": sep,
                        "roles": dict(zip(ROLES, trio)), "from_source": [True, fs, ft]}
    if not best:
        return None
    pal = dict(best, module=module, entry=src["entry"], pair=src["pair"], picked=[h for m, h in src["picked"] if m == module],
               id="%s|%s|%s" % (module, src["entry"], src["pair"]))
    pal["scale"] = {t: scale(module, pal, t) for t in THEMES}
    for t in THEMES:
        st = pal["scale"][t]
        if pg.ratio(st[-1], pg.GROUND[t]["zone"]) < 3 or min(pg.de(a, b) for a, b in zip(st, st[1:])) < 5:
            return None
    pal["pink"] = pinkish(pal["roles"]["primary"]["hue"]) or pinkish(pal["roles"]["secondary"]["hue"])
    return pal


def levers(pal):
    """What the personality produced, measured on the light theme."""
    r = {k: pg.hex_to_oklch(pal["roles"][k]["themes"]["light"]["accent"]) for k in ROLES}
    cont = pg.hex_to_oklch(pal["roles"]["primary"]["themes"]["light"]["container"])
    st = pal["scale"]["light"]
    hs = [pg.hex_to_oklch(x)[2] for x in st[1:]]
    pt = min(pg.de(cs.simulate_cvd(pal["roles"]["primary"]["themes"][t]["accent"], k), cs.simulate_cvd(pal["roles"]["tertiary"]["themes"][t]["accent"], k))
             for t in ("light", "dark") for k in ("protanopia", "deuteranopia"))
    return {"chroma": sum(v[1] for v in r.values()) / 3, "spread": max(v[0] for v in r.values()) - min(v[0] for v in r.values()),
            "cont_gap": cont[0] - r["primary"][0], "ter_gap": gap(r["primary"][2], r["tertiary"][2]),
            "scale_shift": gap(hs[0], hs[-1]), "steps": len(st), "pt_cvd": pt}


def palettes():
    out = {m: [] for m in MODULES}
    for src in sources():
        for m in MODULES:
            p = best_palette(m, src)
            if p:
                out[m].append(p)
    for m in MODULES:  # near-identical palettes from different pairs: keep the better, merge provenance
        kept = []
        for p in sorted(out[m], key=lambda p: -p["score"]):
            twin = next((k for k in kept if all(pg.de(p["roles"][r]["themes"]["light"]["accent"], k["roles"][r]["themes"]["light"]["accent"]) < 6 for r in ROLES)), None)
            if twin:
                twin.setdefault("also", []).append("%s · %s" % (p["entry"], p["pair"]))
                twin["picked"] = twin["picked"] + p["picked"]
            else:
                kept.append(p)
        out[m] = kept
    return out


def pair_ok(a, b):
    m = {"sep": 1e9, "cvd": 1e9, "cross": 1e9}
    for t in ("light", "dark"):
        pa, pb = a["roles"]["primary"]["themes"][t]["accent"], b["roles"]["primary"]["themes"][t]["accent"]
        m["sep"] = min(m["sep"], pg.de(pa, pb))
        for k in ("protanopia", "deuteranopia"):
            m["cvd"] = min(m["cvd"], pg.de(cs.simulate_cvd(pa, k), cs.simulate_cvd(pb, k)))
        m["cross"] = min(m["cross"], pg.de(a["roles"]["secondary"]["themes"][t]["accent"], pb), pg.de(b["roles"]["secondary"]["themes"][t]["accent"], pa))
    return m if m["sep"] >= 20 and m["cvd"] >= 10 and m["cross"] >= 10 else None


def groups(pals):
    C, R, K = (pals[m] for m in MODULES)
    ok = {}
    for (x, X), (y, Y) in (((0, C), (1, R)), ((0, C), (2, K)), ((1, R), (2, K))):
        for i, a in enumerate(X):
            for j, b in enumerate(Y):
                m = pair_ok(a, b)
                if m:
                    ok[(x, i, y, j)] = m
    cands = []
    for i, j, k in itertools.product(range(len(C)), range(len(R)), range(len(K))):
        ms = [ok.get((0, i, 1, j)), ok.get((0, i, 2, k)), ok.get((1, j, 2, k))]
        if all(ms):
            trip = (C[i], R[j], K[k])
            sep, cvd = min(m["sep"] for m in ms), min(m["cvd"] for m in ms)
            score = sum(p["score"] for p in trip) / 3 + 0.10 * min(sep / 40, 1) + 0.10 * min(cvd / 20, 1)
            cands.append({"trip": trip, "sep": sep, "cvd": cvd, "score": score, "pink": any(p["pink"] for p in trip)})
    return cands


def gdist(a, b):
    return sum(pg.de(x["roles"][r]["themes"]["light"]["accent"], y["roles"][r]["themes"]["light"]["accent"]) for x, y in zip(a["trip"], b["trip"]) for r in ("primary", "secondary"))


def select(cands):
    """Better rather than more: from the candidates within 0.05 of the best still allowed, take the one farthest
    from those already chosen; each palette at most MAX_USES times; pinks in at most a third."""
    cands = sorted(cands, key=lambda c: -c["score"])
    chosen, uses = [], {}
    while len(chosen) < MAX_GROUPS:
        pinks = sum(c["pink"] for c in chosen)
        pool = [c for c in cands if c not in chosen and all(uses.get(p["id"], 0) < MAX_USES for p in c["trip"])
                and (not c["pink"] or pinks + 1 <= (len(chosen) + 1) * PINK_SHARE)]
        if not pool:
            break
        top = pool[0]["score"]
        pool = [c for c in pool if c["score"] >= top - 0.05]
        c = max(pool, key=lambda c: min((gdist(c, s) for s in chosen), default=0))
        if chosen and min(gdist(c, s) for s in chosen) < MIN_GDIST:
            cands.remove(c)  # too like a chosen group to add anything
            continue
        chosen.append(c)
        for p in c["trip"]:
            uses[p["id"]] = uses.get(p["id"], 0) + 1
    return chosen


# ---- roles: where each colour goes (owner's map, 2026-10-06, plus this slate's re-assessment) ---------------
# (screen, element, source, note). note: "" = owner's choice kept; "changed: ..." or "new: ..." = this slate.
ELEMENTS = [
    ("All screens", "Header stripe", "primary", ""),
    ("All screens", "Selected top-row tab", "primary container", ""),
    ("All screens", "Primary action (Save, Confirm)", "primary", ""),
    ("All screens", "Bottom-bar icons", "neutral ink", ""),
    ("All screens", "Label chips", "user", ""),
    ("Today", "Zone heading tick (Agenda, Routines due, check-in)", "that module's primary", "new: three hue groups on home help a glance (nav-glance.md: hue pop-out up to 6 groups)"),
    ("Today", "A zone's one action (Log, How are things?)", "that module's primary container", "new"),
    ("Today", "Capture, Still open, Journal, Pinned pages", "neutral (Journal on zone2)", "new: home itself belongs to no module"),
    ("Calendar", "Events and tasks in Day / Week / Month", "user", ""),
    ("Calendar", "Today's column (Week), today's cell (Month)", "primary container", "new: Month follows Week"),
    ("Calendar", "Selected day (Month)", "primary ring", "new"),
    ("Calendar", "Current-time line", "primary", ""),
    ("Calendar", "Task done tick", "state done", ""),
    ("Calendar", "Due soon / still open", "state due soon", ""),
    ("Calendar", "Clash marker", "state attention", ""),
    ("Calendar", "Planner time blocks", "secondary (container fill, accent edge)", "changed from scale: blocks are kinds of plan, not amounts, and a scale reads as more-or-less; secondary is 'the plan' in every module"),
    ("Routines", "Habit marker", "user", ""),
    ("Routines", "Log / Open / Add reading buttons", "primary container", ""),
    ("Routines", "Paused habit", "state skipped", ""),
    ("Routines", "Running timer", "user", ""),
    ("Routines", "Tracker chart lines", "user", ""),
    ("Routines", "Previous-period line (Charts)", "tertiary, dashed", "new: tertiary is 'the comparison' in every module"),
    ("Routines", "Period chips (Charts)", "primary container", "new"),
    ("Routines", "Habit heatmap", "scale", ""),
    ("Routines", "Goal line", "neutral dim", ""),
    ("Routines", "Checklist progress", "secondary", "changed from primary: progress through a plan; primary stays for what acts now"),
    ("check-in", "Selected mood / energy", "primary container + primary ring", ""),
    ("check-in", "What might help (the regulation suggestion)", "secondary container, secondary edge", "new: the plan"),
    ("check-in", "Did it help? (Helped / No change / Not now)", "neutral; the tapped one primary container", "new"),
    ("check-in", "Ledger scale cells", "scale", ""),
    ("check-in", "Sensory channel chips", "neutral surface", ""),
    ("check-in", "Steadiness, said in words", "neutral ink", "new: SPEC §3.5, no numbers or curves on the check-in screen"),
    ("check-in", "Trend line", "primary", "moved: to the Look back sheet, off the check-in screen (SPEC §3.5)"),
    ("check-in", "Comparison line", "tertiary, dashed", "moved: as the trend line"),
    ("check-in", "Burnout notice", "state attention: edge and icon only", "changed: a banner; the ledger and the screen keep their colours (register: ambient, no colour-coded alerts)"),
    ("check-in", "First-time question (what helps when low)", "secondary container on the chosen answer", "new"),
]
UNUSED = "Calendar uses neither its tertiary nor its scale on any screen; both are kept so the palette is complete if a later screen needs them."

e = html.escape


def write_md(pals, cands, chosen):
    out = ["# Module personalities", "", "Generated by `tools/screens/module_personality.py`; every rule is in its docstring.", "",
           "## The three personalities", "", "| Module | Word | Tone | What it sets |", "|---|---|---|---|"]
    out += ["| %s | %s | %.2f | %s |" % (LABEL[m], P["word"], P["tone"], P["says"]) for m, P in PERSONA.items()]
    out += ["", "## What the levers produced (mean over the chosen groups, light theme)", "",
            "| Module | Chroma | Accent lightness spread | Container above primary | Tertiary hue gap | Scale hue shift · steps | Primary vs tertiary, protan/deutan |",
            "|---|---|---|---|---|---|---|"]
    for i, m in enumerate(MODULES):
        lv = [levers(c["trip"][i]) for c in chosen] or [levers(p) for p in pals[m]]
        avg = lambda k: sum(x[k] for x in lv) / len(lv)
        out.append("| %s | %.3f | %.3f | %.3f | %.0f° | %.0f° · %d | %.1f |" % (LABEL[m], avg("chroma"), avg("spread"), avg("cont_gap"), avg("ter_gap"), avg("scale_shift"), lv[0]["steps"], avg("pt_cvd")))
    out += ["", "The protan/deutan column is why the comparison line is dashed: check-in's analogous tertiary is close to its primary by design.", "",
            "## Where each colour goes", "", "| Screen | Element | Colour | Note |", "|---|---|---|---|"]
    out += ["| %s | %s | %s | %s |" % row for row in ELEMENTS]
    out += ["", UNUSED, "", "## Attention colour", "",
            "Attention is %s / %s (light / dark), hue %d. Rerun of this slate per attention hue:" % (mp.STATES["light"]["attention"], mp.STATES["dark"]["attention"], ATTENTION[0]), "",
            "| Attention hue | Palettes C / R / c | Feasible groups | Chosen | With a pink |", "|---|---|---|---|---|"]
    out += ["| %d%s | %s | %d | %d | %d |" % (h, " (used)" if h == ATTENTION[0] else "", " / ".join(map(str, n)), f, c, k) for h, n, f, c, k in attention_sweep()]
    out += ["", "## Palettes per module", ""]
    for m in MODULES:
        out.append("%s: %d palettes from %d sources." % (LABEL[m], len(pals[m]), len(sources())))
    out += ["", "## Groups", "", "%d feasible groups; %d chosen (%d with a pink)." % (len(cands), len(chosen), sum(c["pink"] for c in chosen)), "",
            "| # | Calendar | Routines | check-in | Score | Min ΔE | Protan/deutan |", "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(chosen, 1):
        out.append("| %d | %s | %s | %s | %.3f | %.1f | %.1f |" % (i, *("%s · %s (%s %s %s)" % (p["entry"], p["pair"], *(p["roles"][r]["themes"]["light"]["accent"] for r in ROLES)) for p in c["trip"]), c["score"], c["sep"], c["cvd"]))
    with open(os.path.join(T0, "module-personalities.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out


CSS = """
:root,[data-theme=light]{%(light)s}[data-theme=dark]{%(dark)s}[data-theme=oled]{%(oled)s}
*{box-sizing:border-box}body{margin:0;padding:20px 16px 48px;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}
h1{font-size:21px;margin:0 0 4px}h2{font-size:16px;margin:22px 0 6px}p{max-width:95ch}.dim{color:var(--dim)}
.sw{display:flex;gap:6px;margin:12px 0;flex-wrap:wrap}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
.sw button.on{background:var(--ink);color:var(--bg)}
.pers{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}.pers div{background:var(--zone);border-radius:12px;padding:10px 12px;font-size:13px}
table{border-collapse:collapse;font-size:12.5px;max-width:1100px}td,th{text-align:left;padding:4px 8px;border-bottom:1px solid var(--zone2);vertical-align:top}
tr.chg td:nth-child(4){color:var(--ink)}tr.keep td:nth-child(4){color:var(--dim)}
details.g{background:var(--zone);border-radius:14px;margin:10px 0;padding:10px 12px}details.g>summary{cursor:pointer;list-style:none;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
summary::-webkit-details-marker{display:none}.gn{font-weight:700;width:30px}
.mod{display:flex;gap:6px;align-items:center;flex:1 1 300px;min-width:0}.mod b{font-size:11px;width:70px;color:var(--dim);font-weight:600}
.chips{display:flex;gap:3px;align-items:center}.c{width:22px;height:28px;border-radius:6px}.c.s{width:12px}.c.r{width:9px;border-radius:2px;height:20px}
.kw{font-size:11.5px;color:var(--dim);flex-basis:100%%;margin-left:44px}
.screens{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px}
.ph{width:250px;height:480px;border-radius:18px;background:var(--bg);overflow:hidden;display:flex;flex-direction:column;flex:none;box-shadow:0 0 0 1px var(--zone2);font-size:11px;position:relative}
.ph.tall{height:720px}.cap{font-size:11px;color:var(--dim);width:250px;margin-top:4px}
.hd{height:34px;display:flex;align-items:center;gap:6px;padding:0 10px;font-weight:600;font-size:12px;flex:none}
.bd{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:6px;overflow:hidden}
.z{background:var(--zone);border-radius:9px;padding:6px 7px}.z h4{margin:0 0 3px;font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim);display:flex;align-items:center;gap:5px}
.tick{width:3px;height:9px;border-radius:2px;display:inline-block}
.row{display:flex;align-items:center;gap:6px;padding:3px 0}.row .t{flex:1}
.pill{border-radius:999px;padding:1px 8px;font-size:10px;white-space:nowrap}.tabs{display:flex;gap:4px}.tabs span{padding:2px 8px;border-radius:999px;font-size:10px;color:var(--dim)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.wk{display:grid;grid-template-columns:repeat(5,1fr);gap:3px}.wk>div{background:var(--zone);border-radius:6px;min-height:200px;padding:3px;display:flex;flex-direction:column;gap:3px}
.wk small{font-size:9px;color:var(--dim);text-align:center}.ev{border-radius:4px;padding:2px 3px;font-size:8.5px;line-height:1.2}
.mo{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.mo div{background:var(--zone);border-radius:5px;height:44px;padding:2px 3px;font-size:8.5px;display:flex;flex-direction:column;gap:2px}
.mo .dots{display:flex;gap:2px;flex-wrap:wrap}.mo .dots i{width:5px;height:5px;border-radius:50%%}
.hours{position:relative;background:var(--zone);border-radius:9px;height:250px}.hours .h{position:absolute;left:0;right:0;border-top:1px solid var(--zone2);font-size:8px;color:var(--dim);padding-left:3px}
.blk{position:absolute;border-radius:5px;padding:2px 4px;font-size:9px}
.heat{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.heat i{height:11px;border-radius:2px}
.cells{display:flex;gap:2px}.cells i{width:16px;height:10px;border-radius:2px;background:var(--zone2)}
.pad{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;width:120px}.pad i{height:28px;border-radius:6px;background:var(--zone2)}
.mood{display:flex;gap:6px}.mood i{width:24px;height:24px;border-radius:50%%;background:var(--zone2);font-style:normal;display:flex;align-items:center;justify-content:center;font-size:12px}
svg{display:block}.bar{height:40px;display:flex;background:var(--zone2);flex:none}.bar div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:8.5px;color:var(--dim)}
.bar i{font-style:normal;font-size:11px;color:var(--ink)}.bar .on{color:var(--ink);font-weight:700}.bar .on i{background:var(--zone);border-radius:999px;padding:0 9px}
.bar .hub i{width:26px;height:26px;border-radius:50%%;background:var(--zone);display:flex;align-items:center;justify-content:center}
.sheet{position:absolute;left:0;right:0;bottom:0;background:var(--zone);border-radius:16px 16px 0 0;padding:10px;box-shadow:0 -1px 0 var(--zone2)}
.scrim{position:absolute;inset:0;background:color-mix(in srgb,var(--ink) 18%%,transparent)}
.u{visibility:hidden}body.grey .u{visibility:visible;background:var(--zone2)!important;border-color:var(--dim)!important;color:var(--dim)!important;stroke:var(--dim)!important;outline:1px dashed var(--dim);outline-offset:-1px}
body.grey svg .u{outline:none;stroke-dasharray:1 2}
"""


def var_block(t):
    g = pg.GROUND[t]
    return "--bg:%s;--zone:%s;--zone2:%s;--ink:%s;--dim:%s;--att:%s;--pg:%s;--pgt:%s" % (
        g["bg"], g["zone"], g["zone2"], g["ink"], g["dim"], mp.STATES[t]["attention"], pg.PAGES[t], pg.PAGES_TINT[t])


NAMES = ["%s%s" % (k, s) for k in "abc" for s in ("p", "pc", "s", "sc", "t", "tc", "q0", "q1", "q2", "q3", "q4")]


def pal_vars(k, p):
    out = []
    for t in THEMES:
        for r, sh in zip(ROLES, "pst"):
            out.append("--%s%s-%s:%s;--%s%sc-%s:%s" % (k, sh, t, p["roles"][r]["themes"][t]["accent"], k, sh, t, p["roles"][r]["themes"][t]["container"]))
        st = p["scale"][t] + [p["scale"][t][-1]] * (5 - len(p["scale"][t]))
        out += ["--%sq%d-%s:%s" % (k, i, t, x) for i, x in enumerate(st)]
    return ";".join(out)


def mapping():
    return "\n".join("%s{%s}" % (":root details.g,[data-theme=light] details.g" if t == "light" else "[data-theme=%s] details.g" % t,
                                  ";".join("--%s:var(--%s-%s)" % (n, n, t) for n in NAMES)) for t in THEMES)


def bar(on):
    items = [("Today", "◷"), ("Week", "▦"), ("Hub", "✳"), ("Routines", "↻"), ("Pages", "☰")]
    return '<div class="bar">%s</div>' % "".join(
        '<div class="%s"><i>%s</i>%s</div>' % ("on" if n == on else ("hub" if n == "Hub" else ""), ic, n) for n, ic in items)


def phone(title, body, on, stripe=None, tall=False, cap="", extra=""):
    hd = '<div class="hd"%s>%s</div>' % (' style="box-shadow:inset 0 -2px 0 var(--%s)"' % stripe if stripe else "", title)
    return '<div><div class="ph%s">%s<div class="bd">%s</div>%s%s</div><div class="cap">%s</div></div>' % (
        " tall" if tall else "", hd, body, bar(on) if on is not None else "", extra, cap)


def tabs(sel, names, k):
    return '<div class="tabs">%s</div>' % "".join(
        '<span%s>%s</span>' % (' style="background:var(--%spc);color:var(--ink)"' % k if n == sel else "", n) for n in names)


def zh(label, k=None):
    return '<h4>%s%s</h4>' % ('<i class="tick" style="background:var(--%sp)"></i>' % k if k else "", label)


def screens():
    """Twelve screens. Elements whose colour the user chooses carry class u: hidden by default, grey on demand."""
    U = lambda w="8px", h="8px", r="3px": '<i class="u" style="display:inline-block;width:%s;height:%s;border-radius:%s;background:var(--zone2)"></i>' % (w, h, r)
    today = phone("Today · Tue 6 Oct", (
        '<div class="z row" style="color:var(--dim)"><span class="t">Add anything…</span><span>＋</span></div>'
        '<div class="z">' + zh("Running") + '<div class="row">' + U() + '<span class="t">Reading</span><span>0:24</span><span class="dim">■</span></div></div>'
        '<div class="z">' + zh("Still open") + '<div class="row"><span style="width:9px;height:9px;border:1.4px solid var(--ink);border-radius:2px"></span><span class="t">School form · due 18:00</span></div></div>'
        '<div class="z">' + zh("Agenda", "a") + '<div class="row"><span class="dim">09:00</span>' + U("3px", "12px", "2px") + '<span class="t">Dentist</span></div>'
        '<div style="height:0;border-top:1.6px solid var(--ap);margin:1px 0"></div>'
        '<div class="row"><span class="dim">15:00</span>' + U("3px", "12px", "2px") + '<span class="t">Bank</span></div></div>'
        '<div class="z">' + zh("Routines due", "b") + '<div class="row">' + U() + '<span class="t">Walk</span><span class="pill" style="background:var(--bpc)">Log</span></div>'
        '<div class="row">' + U() + '<span class="t">Water · 3 glasses today</span><span class="pill" style="background:var(--bpc)">Log</span></div></div>'
        '<div class="cols"><div class="z">' + zh("check-in", "c") + '<span class="pill" style="background:var(--cpc)">How are things?</span></div>'
        '<div class="z">' + zh("Ledger", "c") + '<div class="cells">' + "".join('<i style="background:var(--cq%d)"></i>' % v for v in (2, 1, 3)) + '</div></div></div>'
        '<div class="cols"><div class="z" style="background:var(--zone2)">' + zh("Journal") + 'Tuesday</div><div class="z">' + zh("Pinned") + '▸ 3 pages</div></div>'
        '<div class="row dim">✓ Done today · 3</div>'), "Today", cap="Today: home belongs to no module; each zone carries its module's tick and action colour.")
    day = phone("Tue 6 Oct", (tabs("Day", ("Day", "Week", "Month", "Planner"), "a") +
        '<div class="hours">' + "".join('<div class="h" style="top:%dpx">%02d</div>' % ((h - 8) * 36, h) for h in range(8, 15)) +
        '<div class="blk u" style="top:36px;left:26px;right:60px;height:30px;border-left:3px solid var(--zone2)">Dentist</div>'
        '<div class="blk" style="top:72px;left:26px;right:8px;height:66px;background:var(--asc);border-left:3px solid var(--as)">Focus · planned</div>'
        '<div class="blk u" style="top:150px;left:26px;right:90px;height:30px">Call</div><div class="blk u" style="top:160px;left:120px;right:8px;height:30px">Gym</div>'
        '<span style="position:absolute;top:150px;right:4px;color:var(--att);font-size:10px">●</span>'
        '<div style="position:absolute;top:128px;left:20px;right:0;border-top:1.8px solid var(--ap)"><i style="position:absolute;left:-4px;top:-4.5px;width:7px;height:7px;border-radius:50%;background:var(--ap)"></i></div>'
        '<div class="blk" style="top:210px;left:26px;right:8px;border:1.4px solid var(--ink)">Due 13:30 · School form</div></div>'
        '<div class="row"><span>✓</span><span class="t dim">Bins out</span><span class="pill" style="background:var(--ap);color:var(--bg)">＋ New</span></div>'), "Week", stripe="ap",
        cap="Day: user colours hidden; the planned block is secondary, the now line primary, the clash attention.")
    wk_days = [("Mon", '<span class="ev u">09 Dentist</span><span class="ev" style="background:var(--asc);box-shadow:inset 2px 0 0 var(--as)">Focus</span>'),
               ("Tue", '<span class="ev u">Bins</span><span class="ev" style="border:1px solid var(--ink)">Due · form</span>'),
               ("Wed", '<span class="ev u">10 Call</span><span class="ev u">10 Gym</span><span style="color:var(--att);font-size:9px">● clash</span>'),
               ("Thu", '<span class="ev" style="background:var(--asc);box-shadow:inset 2px 0 0 var(--as)">Admin</span>'),
               ("Fri", '<span class="ev u">Trip</span>')]
    week = phone("Week · 5–11 Oct", tabs("Week", ("Day", "Week", "Month", "Planner"), "a") + '<div class="wk">' + "".join(
        '<div%s><small>%s</small>%s</div>' % (' style="background:var(--apc)"' if d == "Tue" else "", d, ev) for d, ev in wk_days) + '</div>', "Week", stripe="ap",
        cap="Week: today's column is the primary container.")
    cells = []
    for d in range(1, 36):
        n = d - 3
        style = ' style="background:var(--apc)"' if n == 6 else (' style="box-shadow:inset 0 0 0 1.6px var(--ap)"' if n == 9 else "")
        dots = "".join('<i class="u"></i>' for _ in range(n % 3)) + ('<i style="background:var(--as);border-radius:1px;width:8px;height:3px"></i>' if n in (5, 8, 12, 19) else "")
        cells.append('<div%s>%s<span class="dots">%s</span></div>' % (style, n if 1 <= n <= 31 else "", dots if 1 <= n <= 31 else ""))
    month = phone("October", tabs("Month", ("Day", "Week", "Month", "Planner"), "a") + '<div class="mo">' + "".join(
        '<small class="dim" style="text-align:center;font-size:8px">%s</small>' % w for w in "MTWTFSS") + "".join(cells) + '</div>'
        '<div class="z"><div class="row"><span class="t">Fri 9 · 2 events</span><span class="dim">›</span></div></div>', "Week", stripe="ap",
        cap="Month: today filled, the selected day ringed; a short secondary bar marks days with planned blocks.")
    plan_cols = [("Mon", ["Focus", "u"]), ("Tue", ["u", "Admin"]), ("Wed", ["Focus", "u", "u"]), ("Thu", ["Admin"]), ("Fri", ["u", "Focus"])]
    planner = phone("Planner · this week", tabs("Planner", ("Day", "Week", "Month", "Planner"), "a") + '<div class="wk">' + "".join(
        '<div><small>%s</small>%s</div>' % (d, "".join('<span class="ev u">habit</span>' if b == "u" else
                                                         '<span class="ev" style="background:var(--asc);box-shadow:inset 2px 0 0 var(--as);min-height:34px">%s</span>' % b for b in bs))
        for d, bs in plan_cols) + '</div>'
        '<div class="z">' + zh("Not placed") + '<div class="row"><span class="pill" style="background:var(--zone2)">Stretch</span><span class="pill" style="background:var(--zone2)">Read</span></div>'
        '<div class="row"><span style="color:var(--att)">●</span><span class="t">Wed: Focus overlaps Call</span><span class="pill" style="background:var(--ap);color:var(--bg)">Confirm</span></div></div>', "Week", stripe="ap",
        cap="Planner: blocks secondary; placed habits keep their own colours.")
    habits = phone("Routines", (tabs("Habits", ("Habits", "Trackers", "Charts"), "b") +
        '<div class="z">' + zh("Due today") + "".join(
            '<div class="row">%s<span class="t">%s</span>%s</div>' % s for s in [
                ('<span>✓</span>', 'Vitamins', '<span class="dim">done</span>'),
                (U("11px", "11px"), 'Walk', '<span class="pill" style="background:var(--bpc)">Log</span>'),
                (U("11px", "11px"), 'Water · 3 glasses today', '<span class="pill" style="background:var(--bpc)">Log</span>'),
                ('<span style="width:11px;height:11px;border:1.4px dashed var(--dim);border-radius:3px"></span>', '<span class="dim">Read · paused</span>', '<span class="dim">–</span>')]) + '</div>'
        '<div class="z">' + zh("Morning checklist") + '<div class="row"><span class="t">3 of 5</span></div><div style="height:6px;border-radius:3px;background:var(--bsc)"><div style="width:60%;height:100%;border-radius:3px;background:var(--bs)"></div></div></div>'
        '<div class="z">' + zh("Running") + '<div class="row">' + U() + '<span class="t">Stretch</span><span>0:08</span></div></div>'
        '<div class="z">' + zh("Walk · last 4 weeks") + '<div class="heat">' + "".join('<i style="background:var(--bq%d)"></i>' % v for v in [0, 2, 3, 1, 4, 4, 2, 3, 0, 1, 4, 3, 2, 4, 1, 3, 4, 2, 0, 3, 4, 4, 3, 2, 1, 4, 3, 4]) + '</div></div>'
        '<div class="row"><span class="t"></span><span class="pill" style="background:var(--bp);color:var(--bg)">＋ New habit</span></div>'), "Routines", stripe="bp",
        cap="Habits: checklist progress secondary; the heatmap is the scale.")
    spark = lambda d: '<svg viewBox="0 0 60 16" width="60" height="16"><path class="u" d="%s" fill="none" stroke="var(--zone2)" stroke-width="1.4"/></svg>' % d
    trackers = phone("Routines", (tabs("Trackers", ("Habits", "Trackers", "Charts"), "b") +
        '<div class="z">' + "".join('<div class="row"><span class="t">%s<br><span class="dim">%s</span></span>%s</div>' % (n, v, spark(d)) for n, v, d in [
            ("Sleep", "7 h 10 · today", "M0,10 L15,8 L30,11 L45,5 L60,6"), ("Weight", "71.2 · Sun", "M0,6 L15,7 L30,7 L45,8 L60,9"), ("Water", "1.4 l · now", "M0,12 L15,9 L30,10 L45,6 L60,4")]) + '</div>'
        '<div class="z">' + zh("Sleep · 4 weeks") + '<svg viewBox="0 0 130 50" width="100%" height="60"><line x1="0" x2="130" y1="16" y2="16" stroke="var(--dim)" stroke-dasharray="2 2"/>'
        '<path class="u" d="M0,30 L20,24 L40,28 L60,18 L80,20 L100,12 L130,16" fill="none" stroke="var(--zone2)" stroke-width="1.6"/><text x="2" y="12" font-size="6" fill="var(--dim)">goal</text></svg></div>'
        '<div class="row"><span class="t"></span><span class="pill" style="background:var(--bpc)">Add reading</span></div>'), "Routines", stripe="bp",
        cap="Trackers: lines are the user's; the goal line neutral dim.")
    charts = phone("Routines", (tabs("Charts", ("Habits", "Trackers", "Charts"), "b") +
        '<div class="row">' + "".join('<span class="pill" style="%s">%s</span>' % ("background:var(--bpc)" if p == "Month" else "background:var(--zone2)", p) for p in ("Week", "Month", "Year")) + '</div>'
        '<div class="z">' + zh("Energy and sleep · October") + '<svg viewBox="0 0 130 60" width="100%" height="72">'
        '<path d="M0,40 L20,34 L40,38 L60,30 L80,33 L100,26 L130,28" fill="none" stroke="var(--bt)" stroke-width="1.3" stroke-dasharray="3 2"/>'
        '<path class="u" d="M0,36 L20,28 L40,30 L60,20 L80,24 L100,16 L130,18" fill="none" stroke="var(--zone2)" stroke-width="1.7"/>'
        '<text x="2" y="58" font-size="6" fill="var(--bt)">- - September</text></svg></div>'
        '<div class="z">' + zh("Walk · days this year") + '<div class="heat">' + "".join('<i style="background:var(--bq%d);height:8px"></i>' % ((i * 7) % 5) for i in range(35)) + '</div></div>'
        '<div class="row"><span class="t"></span><span class="pill" style="background:var(--bp);color:var(--bg)">＋ New chart</span></div>'), "Routines", stripe="bp",
        cap="Charts: the previous period is the tertiary, dashed; the period chip is the primary container.")
    ledger = "".join('<div class="row"><span class="t">%s</span><span class="cells">%s</span><span class="dim" style="width:46px;text-align:right">%s</span></div>' % (
        n, "".join('<i style="background:var(--cq%d)"></i>' % (k + 1 if k < v else 0) for k in range(levels)), word)
        for n, levels, v, word in (("Masking", 4, 3, "most"), ("Demand", 4, 2, "some"), ("Recovery", 3, 1, "a little")))
    checkin = phone("check-in", (
        '<div class="row"><span class="pill" style="background:var(--zone2)">About: now ▾</span></div>'
        '<div class="z">' + zh("How are things right now?") + '<div class="mood">' + "".join(
            '<i style="%s">%s</i>' % ("background:var(--cpc);box-shadow:0 0 0 1.6px var(--cp)" if i == 2 else "", f) for i, f in enumerate("◔◑◕●○")) + '</div>'
        '<div class="row" style="align-items:flex-start;margin-top:5px"><div class="pad">' + "".join(
            '<i%s></i>' % (' style="background:var(--cpc);box-shadow:0 0 0 1.6px var(--cp)"' if i == 6 else "") for i in range(9)) + '</div>'
        '<span class="dim" style="font-size:9px">↑ energy<br>→ pleasant</span></div>'
        '<div class="row" style="color:var(--dim)"><span class="t">Add a note…</span><span class="pill" style="background:var(--cp);color:var(--bg)">Save</span></div></div>'
        '<div class="z" style="background:var(--csc);box-shadow:inset 3px 0 0 var(--cs)">' + zh("What might help") + 'Something to bring your energy up?'
        '<div class="row" style="flex-wrap:wrap">' + "".join('<span class="pill" style="background:var(--zone)">%s</span>' % t for t in ("Walk outside", "Music", "Cold water")) + '</div>'
        '<div class="row dim">Mixed: you asked to choose. <span class="pill" style="background:var(--zone);color:var(--ink)">Up</span><span class="pill" style="background:var(--zone);color:var(--ink)">Down</span></div></div>'
        '<div class="z">' + zh("Did the walk help?") + '<div class="row">' + "".join(
            '<span class="pill" style="background:var(--%s)">%s</span>' % ("cpc" if o == "Helped" else "zone2", o) for o in ("Helped", "No change", "Not now")) + '</div>'
        '<div class="dim" style="font-size:9.5px">Asked once: here after a tool, or in one line at the next open.</div></div>'
        '<div class="z">' + zh("Today's ledger") + ledger + '</div>'
        '<div class="z">' + zh("Sensory") + '<div class="row" style="flex-wrap:wrap">' + "".join(
            '<span class="pill" style="background:var(--zone2)">%s</span>' % s for s in ("Sound · loud", "Light", "Touch", "Crowds")) + '</div></div>'
        '<div class="z">' + zh("Lately") + 'Steadier than the last fortnight.<div class="row"><span class="t"></span><span style="text-decoration:underline">Look back ›</span></div></div>'
        '<div class="dim" style="font-size:9.5px;padding:0 4px">No numbers, averages or curves here (SPEC §3.5). Mixed mode and the notice threshold live in Settings.</div>'), None, stripe="cp", tall=True,
        cap="check-in, the whole screen: check-in, regulation (suggestion, Mixed ask, outcome tap), ledger, sensory log, steadiness in words. Reached from Hub, home and the widget.")
    burnout = phone("check-in", (
        '<div class="z" style="box-shadow:inset 3px 0 0 var(--att)"><div class="row" style="align-items:flex-start"><span style="color:var(--att)">●</span>'
        '<span class="t">Your load has stayed high for a while. A notice, not a diagnosis.</span></div>'
        '<div class="row"><span class="t"></span><span class="pill" style="background:var(--csc);box-shadow:inset 0 0 0 1px var(--cs)">What helps</span><span class="pill" style="background:var(--zone2)">Later</span></div></div>'
        '<div class="z">' + zh("How are things right now?") + '<div class="mood">' + "".join('<i>%s</i>' % f for f in "◔◑◕●○") + '</div></div>'
        '<div class="z">' + zh("Today's ledger") + ledger + '</div>'), None, stripe="cp",
        cap="Burnout notice, a triggered state: one banner, attention on its edge and dot only; everything else keeps its colours.")
    look = phone("check-in", (
        '<div class="z dim" style="height:120px">(check-in screen)</div>'), None, stripe="cp", extra=(
        '<div class="scrim"></div><div class="sheet">' + zh("Look back · 8 weeks") +
        '<svg viewBox="0 0 130 50" width="100%" height="70"><path d="M0,32 C20,24 30,34 50,26 S80,16 100,22 S120,26 130,22" fill="none" stroke="var(--cp)" stroke-width="1.8"/>'
        '<path d="M0,36 C25,34 40,38 60,34 S100,30 130,32" fill="none" stroke="var(--ct)" stroke-width="1.2" stroke-dasharray="3 2"/></svg>'
        '<div class="row"><span class="t">Steadier than the last fortnight.</span></div><div class="row dim" style="font-size:9.5px">— this fortnight · - - the one before</div></div>'),
        cap="Look back (to decide): the trend and comparison lines, on a sheet of their own, since SPEC §3.5 keeps curves off the check-in screen.")
    first = phone("check-in", '<div class="z dim" style="height:120px">(check-in screen)</div>', None, stripe="cp", extra=(
        '<div class="scrim"></div><div class="sheet">' + zh("Once, the first time") + 'When you have a low moment, what usually helps?'
        '<div class="row" style="flex-wrap:wrap;margin-top:4px">' + "".join('<span class="pill" style="background:var(--%s)">%s</span>' % ("csc" if o == "Mixed: ask me" else "zone2", o)
                                                                       for o in ("More energy", "Less energy", "Mixed: ask me")) + '</div></div>'),
        cap="First check-in only: Equipoise's one onboarding question.")
    return today + day + week + month + planner + habits + trackers + charts + checkin + burnout + look + first


def group_html(i, c):
    style = ";".join(pal_vars(k, p) for k, p in zip("abc", c["trip"]))
    mods = "".join(
        '<div class="mod"><b>%s<br>%s</b><span class="chips">%s<span style="width:4px"></span>%s<span style="width:4px"></span>%s</span></div>' % (
            LABEL[p["module"]], PERSONA[p["module"]]["word"],
            "".join('<i class="c" style="background:var(--%s%s)"></i>' % (k, s) for s in "pst"),
            "".join('<i class="c s" style="background:var(--%s%sc)"></i>' % (k, s) for s in "ps"),
            "".join('<i class="c r" style="background:var(--%sq%d)"></i>' % (k, q) for q in range(PERSONA[p["module"]]["steps"])))
        for k, p in zip("abc", c["trip"]))
    kws = " · ".join("%s: %s, %s%s" % (LABEL[p["module"]], e(p["entry"]), e(p["pair"]), " (picked: %s)" % e(", ".join(sorted(set(p["picked"])))) if p["picked"] else "") for p in c["trip"])
    figs = "score %.3f · min ΔE %.1f · protan/deutan %.1f%s" % (c["score"], c["sep"], c["cvd"], " · pink" if c["pink"] else "")
    return '<details class="g" style="%s"><summary><span class="gn">%d</span>%s<span class="kw">%s<br>%s</span></summary><div class="screens"></div></details>' % (style, i, mods, kws, figs)


def write_html(chosen, n_cands):
    css = CSS % {t: var_block(t) for t in THEMES} + mapping()
    pers = "".join('<div><b>%s · %s</b> <span class="dim">tone %.2f</span><br>%s</div>' % (LABEL[m], P["word"], P["tone"], e(P["says"])) for m, P in PERSONA.items())
    rows = "".join('<tr class="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % ("chg" if n else "keep", e(s), e(el), e(src), e(n) or "your choice")
                   for s, el, src, n in ELEMENTS)
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            "<title>Module personalities</title><style>%s</style></head><body>" % css,
            "<h1>Module personalities: %d groups</h1>" % len(chosen),
            '<p class="dim">Each palette takes only its hues from a lexicon pair; chroma, lightness spread, the tertiary\'s distance and the scale come from the module\'s personality. '
            "%d groups passed every check; these %d are the best, kept apart from each other. Open a group to see it on twelve screens. Pages is not part of this.</p>" % (n_cands, len(chosen)),
            '<div class="pers">%s</div>' % pers,
            '<div class="sw"><button data-t="light" class="on">Light</button><button data-t="dark">Dark (L* 6)</button><button data-t="oled">OLED</button>'
            '<button id="grey">User colours: hidden</button><button id="all">Open all</button></div>',
            '<details><summary><b>Where each colour goes</b> <span class="dim">(your map; changed and new rows say why)</span></summary><table><tr><th>Screen</th><th>Element</th><th>Colour</th><th>Note</th></tr>%s</table><p class="dim">%s</p></details>' % (rows, e(UNUSED))]
    page += [group_html(i, c) for i, c in enumerate(chosen, 1)]
    page.append('<template id="scr">%s</template>' % screens())
    page.append("<script>const T=document.getElementById('scr');"
                "document.querySelectorAll('details.g').forEach(d=>d.addEventListener('toggle',()=>{const s=d.querySelector('.screens');if(d.open&&!s.childElementCount)s.append(T.content.cloneNode(true))}));"
                "document.querySelectorAll('.sw button[data-t]').forEach(b=>b.onclick=()=>{document.documentElement.dataset.theme=b.dataset.t;"
                "document.querySelectorAll('.sw button[data-t]').forEach(x=>x.classList.toggle('on',x===b))});"
                "const g=document.getElementById('grey');g.onclick=()=>{const on=document.body.classList.toggle('grey');g.textContent='User colours: '+(on?'grey placeholders':'hidden')};"
                "document.getElementById('all').onclick=()=>{const ds=[...document.querySelectorAll('details.g')],o=!ds.every(d=>d.open);ds.forEach(d=>d.open=o)};"
                "const q=location.hash.slice(1),tb=q&&document.querySelector('.sw button[data-t='+q+']');if(tb)tb.click();else if(matchMedia('(prefers-color-scheme: dark)').matches)document.querySelector('.sw button[data-t=dark]').click();"
                "document.querySelector('details.g').open=true</script></body></html>")
    with open(os.path.join(T0, "module-personalities.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(page))


def attention_sweep(hues=(335, 320, 305, 290)):
    saved = dict(mp.STATES)
    rows = []
    try:
        for h in hues:
            mp.STATE_SETS["sweep"] = {"attention": (h, ATTENTION[1])}
            mp.STATES.clear()
            mp.STATES.update(mp.state_colours("sweep"))
            _ROLE.clear()
            pals = palettes()
            cands = groups(pals)
            ch = select(cands)
            rows.append((h, [len(pals[m]) for m in MODULES], len(cands), len(ch), sum(c["pink"] for c in ch)))
    finally:
        mp.STATES.clear()
        mp.STATES.update(saved)
        _ROLE.clear()
    return rows


def main():
    pals = palettes()
    cands = groups(pals)
    chosen = select(cands)
    out = write_md(pals, cands, chosen)
    write_html(chosen, len(cands))
    return out


if __name__ == "__main__":
    print("\n".join(main()))
