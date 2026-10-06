"""Full module palettes (decision 15, Q4, second slate): one palette for each of Calendar, Routines and
check-in, used across all of that module's screens; groups of three compatible palettes. Pages is not part
of this. Writes docs/screens/t0/module-palettes.md and docs/screens/t0/module-palettes.html.

Owner (2026-10-06): roles are primary, secondary and tertiary, a container for each, and chart colours;
grounds stay neutral. States are one shared set, whose colours appear nowhere else (states.md: due soon
ochre, attention magenta; done and skipped in ink). Item colours on charts come from the guided picker
(series.md), so a module's chart colours are its single-series colour and a sequential scale. Up to 50
groups. Purples and indigos read as a generic choice: tertiary freely, primary or secondary in a few groups
only. No reds; no orange, amber, coral, salmon or peach; pinks in at most a third of the groups.

Roles from a lexicon pair. Its chromatic roles are taken in the lexicon's order (primary, secondary,
accent, highlight...), skipping forbidden hues, reserved state colours and near-duplicates (dE < 15). Missing
roles are filled by exact enumeration: every position of designkit's harmony templates around the primary,
scored with designkit's own template fit and separation. (designkit's --pin search fails on a collapsed
dimension, "range must be increasing"; the enumeration needs neither.)

Per theme, every role is re-solved on the fixed grounds:
  primary    the module's contrast (calendar 6.5, routines 5.0, check-in 4.5; palettes.md's sweep)
  secondary  4.5:1 (text-capable)
  tertiary   3.2:1 (graphical marks, WCAG 1.4.11)
  container  per role: low chroma, ink on it >= 7:1
  scale      5 steps in the primary's hue, container to primary, each step a lighter-to-darker move
Checks: palette_groups.py's (ink band, accent and container contrast, on-accent), the owner's hue rules on
every adapted role, dE >= 15 from both reserved state colours, roles >= 12 apart, scale monotone with its
last step >= 3:1 on the card.

Groups: primaries >= 20 apart and >= 10 under protan and deutan, in light and dark; each secondary >= 10 from
the other modules' primaries. Ranked by harmony, separation and colour-vision separation; picked by coverage
(every placeable pick at least once) then farthest-point diversity; each palette at most MAX_USES times.

    PYTHONUTF8=1 python tools/screens/module_palettes.py
"""
import html
import importlib.util
import itertools
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T0 = os.path.join(ROOT, "docs", "screens", "t0")
spec = importlib.util.spec_from_file_location("pg", os.path.join(HERE, "palette_groups.py"))
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)
cs, harmony = pg.cs, pg.harmony

MODULES, THEMES, LABEL = pg.MODULES, pg.THEMES, pg.LABEL
TARGET, MAX_USES, PURPLE_GROUPS, PINK_SHARE = 50, 4, 5, 1 / 3  # owner: purple-led "in a few groups"; pinks <= a third
ROLE_CONTRAST = {"secondary": 4.5, "tertiary": 3.2}
CONTAINER = {"light": 0.93, "dark": 0.28, "oled": 0.22}
# Candidate state sets: (name, {state: (hue, chroma)}); a state not listed is drawn in ink and reserves no hue.
# STATE_SETS are compared end to end by state_sweep() (feasible and chosen groups); STATE_SET is the one used.
STATE_SETS = {
    "ochre due + magenta attention": {"due soon": (85, 0.11), "attention": (335, 0.15)},
    "ink due + magenta attention": {"attention": (335, 0.15)},
    "ink due + orange attention": {"attention": (45, 0.15)},
    "ink due + violet attention": {"attention": (305, 0.15)},
    "olive due + magenta attention": {"due soon": (105, 0.10), "attention": (335, 0.15)},
    "slate due + orange attention": {"due soon": (250, 0.06), "attention": (45, 0.15)},
}
STATE_SET = os.environ.get("FACTOTUM_STATE_SET", "ink due + magenta attention")  # most groups under the owner's caps (relax_sweep)


def state_colours(name):
    return {t: {s: pg.solve_accent(h, C, t if t != "oled" else "dark", 4.5) for s, (h, C) in STATE_SETS[name].items()} for t in THEMES}


STATES = state_colours(STATE_SET)
SKIP_ROLES = ("surface", "text", "bg", "mid", "muted", "surface-alt", "text-dim")


def is_purple(hx):
    L, C, h = pg.hex_to_oklch(hx)
    return C >= 0.04 and 265 <= h <= 325


def adapt(h, C, theme, target, warm):
    ca = max(0.05, min(C, pg.CAP[theme], pg.EARTHY_ACCENT[theme] if warm else 1))
    if theme == "oled":
        theme_for = "dark"
    else:
        theme_for = theme
    return pg.solve_accent(h, ca, theme_for, target)


def reserved_ok(hx, theme):
    return all(pg.de(hx, s) >= 15 for s in STATES[theme].values())


def lexicon_roles(pair):
    out = []
    for reg in ("light", "dark"):
        for role, hx in pair.get(reg, {}).items():
            if role in SKIP_ROLES:
                continue
            L, C, h = pg.hex_to_oklch(hx)
            if C < 0.03 or pg.hue_class(L, C, h).startswith("forbidden"):
                continue
            if any(pg.de(hx, o) < 15 for o in out):
                continue
            out.append(hx)
    return out


def template_candidates(primary_hx):
    """Every harmony-template position around the primary (designkit's eight templates), plus a lighter and
    a deeper tonal step of the primary itself, so tonal palettes can stay tonal."""
    L, C, h0 = pg.hex_to_oklch(primary_hx)
    offsets = sorted({o for t in harmony.TEMPLATES.values() for o in t["offsets"] if o} | {-30.0, 30.0, -15.0, 15.0})
    cands = [pg.oklch_hex(min(max(L, 0.45), 0.7), max(0.05, C * 0.9), (h0 + o) % 360) for o in offsets]
    cands += [pg.oklch_hex(0.80, max(0.04, C * 0.6), h0), pg.oklch_hex(0.35, max(0.05, C), h0)]
    return cands


def role_ok(hx, target, accepted, module):
    """A source colour can take a role if, adapted for every theme at the role's contrast, it is allowed by the
    owner's hue rules, clear of the reserved state colours, and >= 15 from the roles already taken."""
    L, C, h = pg.hex_to_oklch(hx)
    if C < 0.03 or pg.hue_class(L, C, h).startswith("forbidden"):
        return None
    warm = pg.hue_class(L, C, h) in ("earthy", "sand")
    per = {t: adapt(h, C, t, target, warm) for t in THEMES}
    for t, acc in per.items():
        if pg.hue_class(*pg.hex_to_oklch(acc), adapted=True).startswith("forbidden") or not reserved_ok(acc, t):
            return None
    if any(pg.de(per["light"], a["light"]) < 15 or pg.de(per["dark"], a["dark"]) < 15 for a in accepted):
        return None
    return per


def choose_roles(module, src):
    """Primary is the lexicon's identity colour and must pass. Secondary and tertiary take the lexicon's next
    colours that pass; a slot left empty is filled from the template candidates, best harmony fit first."""
    targets = (pg.CONTRAST[module], ROLE_CONTRAST["secondary"], ROLE_CONTRAST["tertiary"])
    first = role_ok(src[0], targets[0], [], module)
    if first is None:
        return None, 0
    chosen, adapted, filled = [src[0]], [first], 0
    for hx in src[1:]:
        if len(chosen) == 3:
            break
        per = role_ok(hx, targets[len(chosen)], adapted, module)
        if per:
            chosen.append(hx)
            adapted.append(per)
    while len(chosen) < 3:
        options = []
        for hx in template_candidates(src[0]):
            if is_purple(hx) and len(chosen) == 1:
                continue  # purple stays tertiary unless the lexicon itself leads with it
            per = role_ok(hx, targets[len(chosen)], adapted, module)
            if per:
                fit = harmony.best_template([cs.hex_to_hsl(x)[0] for x in chosen + [hx]])[1]
                options.append((fit, min(pg.de(per["light"], a["light"]) for a in adapted), hx, per))
        if not options:
            return None, filled
        fit, sep, hx, per = max(options)
        chosen.append(hx)
        adapted.append(per)
        filled += 1
    return chosen, filled


def build(module, pick, pair_name, pair):
    src = lexicon_roles(pair) if pair else [pick["cited"]["light"][k] for k in pick["cited"]["light"]]
    if not src:
        return None
    ident, n_filled = choose_roles(module, src)
    if ident is None:
        return {"problems": ["primary or a role could not pass the rules"], "id": pick["entry"]}
    filled = [None] * n_filled
    pal = {"id": "%s|%s|%s" % (module, pick["entry"], pair_name), "module": module, "entry": pick["entry"], "pair": pair_name,
           "how": pick["how"], "move": pick.get("move", ""), "why": pick["why"], "set": pick.get("set", "first"),
           "source": ident, "filled": len(filled), "roles": {}, "problems": []}
    for role, hx, target in zip(("primary", "secondary", "tertiary"), ident,
                                (pg.CONTRAST[module], ROLE_CONTRAST["secondary"], ROLE_CONTRAST["tertiary"])):
        L, C, h = pg.hex_to_oklch(hx)
        warm = pg.hue_class(L, C, h) in ("earthy", "sand")
        per = {}
        for t in THEMES:
            acc = adapt(h, C, t, target, warm)
            cont = pg.oklch_hex(CONTAINER[t], min(C * 0.35, pg.EARTHY_TINT[t] if warm else 0.035), h)
            per[t] = {"accent": acc, "container": cont}
            g = pg.GROUND[t]
            cls = pg.hue_class(*pg.hex_to_oklch(acc), adapted=True)
            if cls.startswith("forbidden"):
                pal["problems"].append("%s %s %s" % (role, t, cls))
            if not reserved_ok(acc, t):
                pal["problems"].append("%s %s near a state colour" % (role, t))
            if pg.ratio(acc, g["bg"]) < min(target, 4.5) - 0.05 or pg.ratio(g["ink"], cont) < 7:
                pal["problems"].append("%s %s contrast" % (role, t))
        pal["roles"][role] = {"hue": round(h, 1), "class": pg.hue_class(L, C, h), "purple": is_purple(hx), "themes": per}
    for a, b in itertools.combinations(("primary", "secondary", "tertiary"), 2):
        if pg.de(pal["roles"][a]["themes"]["light"]["accent"], pal["roles"][b]["themes"]["light"]["accent"]) < 12:
            pal["problems"].append("%s and %s too close" % (a, b))
    # the sequential scale: container -> primary in the primary's hue
    p = pal["roles"]["primary"]
    pal["scale"] = {}
    for t in THEMES:
        L0, C0, h = pg.hex_to_oklch(p["themes"][t]["container"])
        L1, C1, _ = pg.hex_to_oklch(p["themes"][t]["accent"])
        steps = [pg.oklch_hex(L0 + (L1 - L0) * k / 4, C0 + (C1 - C0) * k / 4, h) for k in range(5)]
        pal["scale"][t] = steps
        if pg.ratio(steps[-1], pg.GROUND[t]["zone"]) < 3:
            pal["problems"].append("scale %s end under 3:1" % t)
    pal["pink"] = any(r["class"] == "pink" or pg.hue_class(*pg.hex_to_oklch(r["themes"]["light"]["accent"])) == "pink"
                      for k, r in pal["roles"].items() if k != "tertiary")  # a pink tertiary is pink in moderation
    pal["purple_lead"] = pal["roles"]["primary"]["purple"] or pal["roles"]["secondary"]["purple"]
    return pal


def palettes():
    keys = json.load(open(os.path.join(T0, "palette-keywords.json"), encoding="utf-8"))
    src = {e["entry"]: e for e in json.load(open(os.path.join(T0, "palette-sources.json"), encoding="utf-8"))["entries"]}
    out, rejected = {m: [] for m in MODULES}, []
    for m in MODULES:
        for pick in keys["modules"][m]["picks"]:
            items = [(pick["cited"]["name"], None)] if "cited" in pick else []
            items += [(n, next(p for p in src[pick["entry"]]["pairs"] if p["name"] == n)) for n in pick.get("pairs", [])]
            for name, pair in items:
                p = build(m, pick, name, pair)
                if p is None:
                    rejected.append((m, pick["entry"], name, "no usable colour"))
                elif p["problems"]:
                    rejected.append((m, pick["entry"], name, "; ".join(sorted(set(p["problems"])))))
                else:
                    out[m].append(p)
    return out, rejected


def metrics(trip):
    m = {"sep": 1e9, "cvd": 1e9, "tritan": 1e9, "cross": 1e9}
    for t in ("light", "dark"):
        prim = [p["roles"]["primary"]["themes"][t]["accent"] for p in trip]
        for a, b in itertools.combinations(prim, 2):
            m["sep"] = min(m["sep"], pg.de(a, b))
            for kind in ("protanopia", "deuteranopia"):
                m["cvd"] = min(m["cvd"], pg.de(cs.simulate_cvd(a, kind), cs.simulate_cvd(b, kind)))
            m["tritan"] = min(m["tritan"], pg.de(cs.simulate_cvd(a, "tritanopia"), cs.simulate_cvd(b, "tritanopia")))
        for i, p in enumerate(trip):
            sec = p["roles"]["secondary"]["themes"][t]["accent"]
            m["cross"] = min([m["cross"]] + [pg.de(sec, x) for j, x in enumerate(prim) if j != i])
    m["template"], m["harmony"], _ = harmony.best_template([cs.hex_to_hsl(p["roles"]["primary"]["themes"]["light"]["accent"])[0] for p in trip])
    m["pink"] = any(p["pink"] for p in trip)
    m["purple"] = any(p["purple_lead"] for p in trip)
    return m


def feasible(m):
    return m["sep"] >= 20 and m["cvd"] >= 10 and m["cross"] >= 10


def rank(cands):
    key = lambda c: (c["m"]["harmony"], c["m"]["sep"], c["m"]["cvd"], c["m"]["tritan"])
    left, r = list(cands), 1
    while left:
        front = [c for c in left if not any(all(x >= y for x, y in zip(key(o), key(c))) and key(o) != key(c) for o in left)]
        for c in front:
            c["rank"] = r
        left = [c for c in left if c not in front]
        r += 1


def gdist(a, b):
    return sum(pg.de(x["roles"][r]["themes"]["light"]["accent"], y["roles"][r]["themes"]["light"]["accent"])
               for x, y in zip(a["trip"], b["trip"]) for r in ("primary", "secondary"))


def select(cands):
    cands.sort(key=lambda c: (c["rank"], -c["m"]["harmony"], -c["m"]["sep"]))
    chosen, uses = [], {}
    counts = {"pink": 0, "purple": 0}

    def allowed(c):
        return (c not in chosen and all(uses.get(p["id"], 0) < MAX_USES for p in c["trip"])
                and (not c["m"]["pink"] or counts["pink"] < int(TARGET * PINK_SHARE)) and (not c["m"]["purple"] or counts["purple"] < PURPLE_GROUPS))

    def take(c):
        chosen.append(c)
        counts["pink"] += c["m"]["pink"]
        counts["purple"] += c["m"]["purple"]
        for p in c["trip"]:
            uses[p["id"]] = uses.get(p["id"], 0) + 1

    for key in sorted({(p["module"], p["entry"]) for c in cands for p in c["trip"]}):
        if any((p["module"], p["entry"]) == key for c in chosen for p in c["trip"]):
            continue
        ok = [c for c in cands if allowed(c) and any((p["module"], p["entry"]) == key for p in c["trip"])]
        if ok:
            near = [c for c in ok if c["rank"] <= ok[0]["rank"] + 1]
            take(max(near, key=lambda c: min((gdist(c, s) for s in chosen), default=0)))
    while len(chosen) < TARGET:
        pool = [c for c in cands if allowed(c)]
        if not pool:
            break
        best_rank = min(c["rank"] for c in pool)
        pool = [c for c in pool if c["rank"] <= best_rank + 2]
        take(max(pool, key=lambda c: min(gdist(c, s) for s in chosen)))
    while sum(c["m"]["pink"] for c in chosen) > len(chosen) * PINK_SHARE:
        chosen.remove(max((c for c in chosen if c["m"]["pink"]), key=lambda c: c["rank"]))
    return chosen


# ---- output -----------------------------------------------------------------------------------------------
e = html.escape
ROLES = ("primary", "secondary", "tertiary")


def write_md(pals, rejected, cands, chosen):
    out = ["# Module palettes (full)", "", "Generated by `tools/screens/module_palettes.py`; every rule is in its docstring.", "",
           "State set: **%s**. Reserved (light / dark): %s. States not listed are drawn in ink and reserve nothing." % (STATE_SET, "; ".join(
               "%s %s / %s" % (s, STATES["light"][s], STATES["dark"][s]) for s in STATES["light"])), "",
           "## Palettes per module", ""]
    for m in MODULES:
        out += ["### %s (%d)" % (LABEL[m], len(pals[m])), "", "| Keyword · pair | How | Primary | Secondary | Tertiary | Filled by search |", "|---|---|---|---|---|---|"]
        for p in pals[m]:
            out.append("| %s · %s | %s%s | %s | %s | %s | %d |" % (p["entry"], p["pair"], p["how"], " (%s)" % p["move"] if p["move"] else "",
                       *(p["roles"][r]["themes"]["light"]["accent"] for r in ROLES), p["filled"]))
        out.append("")
    out += ["## Left out", ""] + ["- %s · %s · %s: %s" % (LABEL[m], en, n, why) for m, en, n, why in rejected]
    shown = {(p["module"], p["entry"]) for c in chosen for p in c["trip"]}
    missing = sorted({(p["module"], p["entry"]) for m in MODULES for p in pals[m]} - shown)
    out += ["", "## Picks in no group", ""] + (["- %s: %s" % (LABEL[m], n) for m, n in missing] or ["None."])
    out += ["", "## Groups", "", "%d triples; %d feasible; %d chosen (%d with a pink, %d led by a purple)." % (
        len(pals["calendar"]) * len(pals["routines"]) * len(pals["checkin"]), len(cands), len(chosen),
        sum(c["m"]["pink"] for c in chosen), sum(c["m"]["purple"] for c in chosen)), "",
            "| # | Calendar | Routines | check-in | Harmony | Min ΔE | Protan/deutan | Tritan |", "|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(chosen, 1):
        t, m = c["trip"], c["m"]
        out.append("| %d | %s · %s | %s · %s | %s · %s | %s %.2f | %.1f | %.1f | %.1f |" % (
            i, t[0]["entry"], t[0]["pair"], t[1]["entry"], t[1]["pair"], t[2]["entry"], t[2]["pair"], m["template"], m["harmony"], m["sep"], m["cvd"], m["tritan"]))
    out += ["", "## How many groups the rules allow", "",
            "Groups chosen (up to %d) for each candidate state set and each relaxation of the caps. Most feasible groups contain a pink- or purple-led "
            "palette, because the calm lexicon picks that differ from blue, green and teal are mostly pinks, mauves and lavenders." % TARGET, "",
            "| State set | Feasible | purple ≤5, pink ≤⅓ (owner) | purple ≤10, pink ≤⅓ | purple ≤5, pink ≤½ | purple ≤10, pink ≤½ | no purple cap, pink ≤½ |",
            "|---|---|---|---|---|---|---|"]
    out += ["| %s%s | %d | %s |" % (n, " (used)" if n == STATE_SET else "", f, " | ".join(str(x) for x in r)) for n, f, r in relax_sweep()]
    with open(os.path.join(T0, "module-palettes.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out


CSS = """
:root,[data-theme=light]{%(light)s}[data-theme=dark]{%(dark)s}[data-theme=oled]{%(oled)s}
*{box-sizing:border-box}body{margin:0;padding:20px 16px 48px;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}
h1{font-size:21px;margin:0 0 4px}p{max-width:95ch}.dim{color:var(--dim)}code{font-size:12.5px}
.sw{display:flex;gap:6px;margin:12px 0;flex-wrap:wrap}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
.sw button.on{background:var(--ink);color:var(--bg)}
.states{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0 16px;font-size:12.5px}
.st{display:flex;align-items:center;gap:6px;background:var(--zone);border-radius:999px;padding:4px 10px}
details{background:var(--zone);border-radius:14px;margin:10px 0;padding:10px 12px}summary{cursor:pointer;list-style:none;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
summary::-webkit-details-marker{display:none}.gn{font-weight:700;width:30px}
.mod{display:flex;gap:6px;align-items:center;flex:1 1 300px;min-width:0}.mod b{font-size:11px;width:62px;color:var(--dim);font-weight:600}
.chips{display:flex;gap:3px}.c{width:22px;height:28px;border-radius:6px}.c.s{width:12px}.c.r{width:9px;border-radius:2px;height:20px}
.kw{font-size:11.5px;color:var(--dim);flex-basis:100%%;margin-left:44px}
.screens{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px}
.ph{width:250px;height:470px;border-radius:18px;background:var(--bg);overflow:hidden;display:flex;flex-direction:column;flex:none;box-shadow:0 0 0 1px var(--zone2);font-size:11px}
.hd{height:34px;display:flex;align-items:center;gap:6px;padding:0 10px;font-weight:600;font-size:12px}
.bd{flex:1;padding:4px 8px;display:flex;flex-direction:column;gap:6px;overflow:hidden}
.z{background:var(--zone);border-radius:9px;padding:6px 7px}.z h4{margin:0 0 3px;font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}
.row{display:flex;align-items:center;gap:6px;padding:3px 0}.row .t{flex:1}
.pill{border-radius:999px;padding:1px 8px;font-size:10px}.tabs{display:flex;gap:4px}.tabs span{padding:2px 8px;border-radius:999px;font-size:10px;color:var(--dim)}
.wk{display:grid;grid-template-columns:repeat(5,1fr);gap:3px}.wk div{background:var(--zone);border-radius:6px;min-height:150px;padding:3px;display:flex;flex-direction:column;gap:3px}
.wk small{font-size:9px;color:var(--dim);text-align:center}.ev{border-radius:4px;padding:2px 3px;font-size:8.5px;line-height:1.2}
.heat{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}.heat i{height:11px;border-radius:2px}
svg{display:block}.bar{height:40px;display:flex;background:var(--zone2)}.bar div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:8.5px;color:var(--dim)}
.bar i{font-style:normal;font-size:11px;color:var(--ink)}.bar .on{color:var(--ink);font-weight:600}
"""


_SERIES = []


def series_colours():
    """The guided picker's first three suggestions (series_contest.fixed_list: farthest-first from its space)."""
    if not _SERIES:
        sp = importlib.util.spec_from_file_location("sc", os.path.join(HERE, "series_contest.py"))
        sc = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(sc)
        _SERIES.extend(sc.fixed_list(3))
    return _SERIES


def var_block(t):
    g = pg.GROUND[t]
    series = ";".join("--s%d:%s" % (i, c["light" if t == "light" else "dark"]) for i, c in enumerate(series_colours()))
    return "--bg:%s;--zone:%s;--zone2:%s;--ink:%s;--dim:%s;--due:%s;--att:%s;%s" % (g["bg"], g["zone"], g["zone2"], g["ink"], g["dim"], STATES[t].get("due soon", g["ink"]), STATES[t]["attention"], series)


def pal_vars(k, p):
    out = []
    for t in THEMES:
        for r, short in zip(ROLES, "pst"):
            out.append("--%s%s-%s:%s;--%s%sc-%s:%s" % (k, short, t, p["roles"][r]["themes"][t]["accent"], k, short, t, p["roles"][r]["themes"][t]["container"]))
        out += ["--%sq%d-%s:%s" % (k, i, t, x) for i, x in enumerate(p["scale"][t])]
    return ";".join(out)


def mapping():
    names = ["%s%s" % (k, s) for k in ("a", "b", "c") for s in ("p", "pc", "s", "sc", "t", "tc", "q0", "q1", "q2", "q3", "q4")]
    css = []
    for t in THEMES:
        sel = (":root details,[data-theme=light] details" if t == "light" else "[data-theme=%s] details" % t)
        css.append("%s{%s}" % (sel, ";".join("--%s:var(--%s-%s)" % (n, n, t) for n in names)))
    return "\n".join(css)


BAR = '<div class="bar"><div%s><i>◷</i>Today</div><div%s><i>▦</i>Week</div><div><i>✱</i>Hub</div><div%s><i>↻</i>Routines</div><div><i>☰</i>Pages</div></div>'


def screens():
    """Three screens per group: Calendar week (a), Routines with a chart (b), check-in (c). Item colours on the
    chart come from the guided picker (series.md), labelled directly."""
    week = ('<div class="ph"><div class="hd" style="box-shadow:inset 3px 0 0 var(--ap)">Week · 5–11 Oct</div><div class="bd">'
            '<div class="tabs"><span>Day</span><span style="background:var(--apc);color:var(--ink)">Week</span><span>Month</span><span>Planner</span></div>'
            '<div class="wk">' + "".join(
                '<div><small>%s</small>%s</div>' % (d, ev) for d, ev in [
                    ("Mon", '<span class="ev" style="background:var(--apc);box-shadow:inset 2px 0 0 var(--ap)">09:00 Dentist</span><span class="ev" style="background:var(--asc);box-shadow:inset 2px 0 0 var(--as)">15:00 Bank</span>'),
                    ("Tue", '<span class="ev" style="background:var(--atc);box-shadow:inset 2px 0 0 var(--at)">Bins</span>'),
                    ("Wed", '<span class="ev" style="background:var(--apc);box-shadow:inset 2px 0 0 var(--ap)">10:00 Call</span>'),
                    ("Thu", '<span class="ev" style="background:var(--asc);box-shadow:inset 2px 0 0 var(--as)">Gym</span><span class="ev" style="border:1px solid var(--due);color:var(--due)">Due: form</span>'),
                    ("Fri", '<span class="ev" style="background:var(--apc);box-shadow:inset 2px 0 0 var(--ap)">Trip</span>')]) + '</div>'
            '<div class="z"><h4>Planner · this week</h4><div class="row"><span class="t">Habits placed</span><span class="pill" style="background:var(--ap);color:var(--bg)">Confirm</span></div>'
            '<div class="row"><span style="color:var(--att)">●</span><span class="t">Clash: Gym and Call</span></div></div></div>' + BAR % (' class="on"', "", "") + '</div>')
    # Item colours: the guided picker's first three suggestions (series.md), as CSS variables per theme.
    lines = [("Sleep", "var(--s0)", "M0,26 L20,22 L40,26 L60,16 L80,14 L100,6"), ("Energy", "var(--s1)", "M0,40 L20,36 L40,44 L60,34 L80,36 L100,40"),
             ("Water", "var(--s2)", "M0,30 L20,32 L40,24 L60,26 L80,24 L100,23")]
    chart = ('<svg viewBox="0 0 130 52" width="100%%" height="62">%s</svg>' % "".join(
        '<path d="%s" fill="none" stroke="%s" stroke-width="1.6"/><text x="103" y="%s" font-size="6.5" fill="%s">%s</text>' % (d, col, d.split()[-1].split(",")[1], col, n)
        for n, col, d in lines))
    rout = ('<div class="ph"><div class="hd" style="box-shadow:inset 3px 0 0 var(--bp)">Routines</div><div class="bd">'
            '<div class="tabs"><span style="background:var(--bpc);color:var(--ink)">Habits</span><span>Trackers</span><span>Charts</span></div>'
            '<div class="z"><h4>Due today</h4>' + "".join(
                '<div class="row"><span style="width:11px;height:11px;border-radius:3px;%s"></span><span class="t">%s</span><span class="pill" style="background:var(--%s)">%s</span></div>' % s
                for s in [("background:var(--ink)", "Vitamins · done", "zone2", "✓"), ("border:1.4px solid var(--bp)", "Walk", "bpc", "Log"),
                          ("border:1.4px solid var(--bs)", "Water · 3 of 8", "bsc", "Log"), ("border:1.4px solid var(--bt)", "Stretch", "btc", "Open"),
                          ("border:1.4px dashed var(--dim)", "Read · paused", "zone2", "–")]) + '</div>'
            '<div class="z"><h4>Trackers · labelled</h4>' + chart + '</div>'
            '<div class="z"><h4>Walk · last 4 weeks</h4><div class="heat">' + "".join(
                '<i style="background:var(--bq%d)"></i>' % v for v in [0, 2, 3, 1, 4, 4, 2, 3, 0, 1, 4, 3, 2, 4, 1, 3, 4, 2, 0, 3, 4, 4, 3, 2, 1, 4, 3, 4]) + '</div></div>'
            '</div>' + BAR % ("", "", ' class="on"') + '</div>')
    chk = ('<div class="ph"><div class="hd" style="box-shadow:inset 3px 0 0 var(--cp)">check-in</div><div class="bd">'
           '<div class="z" style="background:var(--cpc)"><h4>How are things right now?</h4><div class="row"><span class="pill" style="background:var(--bg)">Mood</span>'
           '<span class="pill" style="background:var(--bg)">Energy</span><span class="t"></span><span class="pill" style="background:var(--cp);color:var(--bg)">Save</span></div></div>'
           '<div class="z"><h4>Ledger · today</h4>' + "".join(
               '<div class="row"><span class="t">%s</span><span style="display:flex;gap:2px">%s</span></div>' % (n, "".join(
                   '<i style="width:12px;height:9px;border-radius:2px;background:var(--cq%d)"></i>' % (k if k <= v else 0) for k in range(1, 5)))
               for n, v in (("Masking", 3), ("Effort", 2), ("Recovery", 4))) + '</div>'
           '<div class="z"><h4>Sensory</h4><div class="row">' + "".join(
               '<span class="pill" style="background:var(--%s)">%s</span>' % (c, n) for c, n in (("csc", "Sound"), ("ctc", "Light"), ("csc", "Touch"))) + '</div></div>'
           '<div class="z"><h4>How things have felt</h4><svg viewBox="0 0 130 40" width="100%" height="48"><path d="M0,28 C20,20 30,30 50,22 S80,12 100,18 S120,24 130,20" fill="none" stroke="var(--cp)" stroke-width="1.8"/>'
           '<path d="M0,32 C25,30 40,34 60,30 S100,26 130,28" fill="none" stroke="var(--ct)" stroke-width="1.2" stroke-dasharray="3 2"/></svg>'
           '<div class="row" style="color:var(--dim)">Steadier than last week</div></div>'
           '</div>' + BAR % ("", "", "") + '</div>')
    return week + rout + chk


def group_html(i, c):
    trip, m = c["trip"], c["m"]
    style = ";".join(pal_vars(k, p) for k, p in zip("abc", trip))
    mods = "".join(
        '<div class="mod"><b>%s</b><span class="chips">%s<span style="width:4px"></span>%s<span style="width:4px"></span>%s</span></div>' % (
            LABEL[p["module"]],
            "".join('<i class="c" style="background:var(--%s%s)"></i>' % (k, s) for s in "pst"),
            "".join('<i class="c s" style="background:var(--%s%sc)"></i>' % (k, s) for s in "pst"),
            "".join('<i class="c r" style="background:var(--%sq%d)"></i>' % (k, q) for q in range(5)))
        for k, p in zip("abc", trip))
    kws = " · ".join("%s: %s, %s%s" % (LABEL[p["module"]], e(p["entry"]), e(p["pair"]), " (%s)" % e(p["move"]) if p["move"] else "") for p in trip)
    figs = "%s %.2f · min ΔE %.1f · protan/deutan %.1f · tritan %.1f%s%s" % (m["template"], m["harmony"], m["sep"], m["cvd"], m["tritan"],
                                                                         " · pink" if m["pink"] else "", " · purple-led" if m["purple"] else "")
    return ('<details style="%s"><summary><span class="gn">%d</span>%s<span class="kw">%s<br>%s</span></summary><div class="screens">%s</div></details>' % (
        style, i, mods, kws, figs, screens()))


def write_html(chosen, n_cands):
    css = CSS % {t: var_block(t) for t in THEMES} + mapping()
    st = ('<div class="states"><b>Shared states:</b><span class="st">✓ Done (ink)</span><span class="st" style="color:var(--dim)">– Skipped (dim)</span>'
          '<span class="st" style="color:var(--due);box-shadow:inset 0 0 0 1px var(--due)">Due soon</span><span class="st" style="color:var(--att);box-shadow:inset 0 0 0 1px var(--att)">● Attention</span></div>')
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            "<title>Factotum module palettes</title><style>%s</style></head><body>" % css,
            "<h1>Module palettes: %d groups</h1>" % len(chosen),
            '<p class="dim">Each row is one group: Calendar, Routines and check-in, each with primary, secondary and tertiary (large chips), '
            "their containers (narrow chips) and the five-step chart scale. Open a row to see the palettes on a Calendar week, a Routines screen with "
            "a chart and a heatmap, and check-in with the ledger and the trend. Chart lines for trackers use colours from the guided picker (series.md), "
            "labelled directly, not the module palette. %d groups passed every check; these are chosen for harmony, separation and variety. "
            "Pages is not part of this.</p>" % n_cands,
            '<div class="sw"><button data-t="light" class="on">Light</button><button data-t="dark">Dark (L* 6)</button><button data-t="oled">OLED</button>'
            '<button id="all">Open all</button></div>', st]
    page += [group_html(i, c) for i, c in enumerate(chosen, 1)]
    page.append("<script>document.querySelectorAll('.sw button[data-t]').forEach(b=>b.onclick=()=>{document.documentElement.dataset.theme=b.dataset.t;"
                "document.querySelectorAll('.sw button[data-t]').forEach(x=>x.classList.toggle('on',x===b))});"
                "document.getElementById('all').onclick=()=>{const o=![...document.querySelectorAll('details')].every(d=>d.open);document.querySelectorAll('details').forEach(d=>d.open=o)};"
                "if(matchMedia('(prefers-color-scheme: dark)').matches)document.querySelector('.sw button[data-t=dark]').click()</script></body></html>")
    with open(os.path.join(T0, "module-palettes.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(page))


def relax_sweep():
    """Groups chosen under each state set and each relaxation of the owner's caps: the trade-off, measured."""
    global PURPLE_GROUPS, PINK_SHARE
    saved = (dict(STATES), PURPLE_GROUPS, PINK_SHARE)
    rows = []
    try:
        for name in STATE_SETS:
            STATES.clear()
            STATES.update(state_colours(name))
            pals, _ = palettes()
            cands = [{"trip": t, "m": m} for t in itertools.product(*(pals[x] for x in MODULES)) for m in [metrics(t)] if feasible(m)]
            if cands:
                rank(cands)
            row = []
            for purple, pink in ((5, 1 / 3), (10, 1 / 3), (5, 1 / 2), (10, 1 / 2), (50, 1 / 2)):
                PURPLE_GROUPS, PINK_SHARE = purple, pink
                row.append(len(select([dict(c) for c in cands])) if cands else 0)
            rows.append((name, len(cands), row))
    finally:
        STATES.clear()
        STATES.update(saved[0])
        PURPLE_GROUPS, PINK_SHARE = saved[1], saved[2]
    return rows


def main():
    pals, rejected = palettes()
    cands = []
    for trip in itertools.product(*(pals[m] for m in MODULES)):
        m = metrics(trip)
        if feasible(m):
            cands.append({"trip": trip, "m": m})
    rank(cands)
    chosen = select(cands)
    out = write_md(pals, rejected, cands, chosen)
    write_html(chosen, len(cands))
    return out


if __name__ == "__main__":
    print("\n".join(main()))
