"""Navigation re-scored against the home the owner built (decision 15, 2026-10-06). Writes
docs/screens/t0/nav-home.md and injects the winners into docs/screens/t0/home-workshop.html.

The home puts these one tap away, from home only (not from anywhere):
  - the check-in line, the ledger tile, today's journal tile;
  - Today's top row: Day · Week · Month · Planner;
  - pinned pages, folded: open the fold, then the page (2 taps). ASSUMED: the pages opened daily are pinned.
Agenda, routines due and timers are home itself (areas today and due, as before).

Searched: the bar is Today · three slots · ⊞. Each slot is a module (it opens on its top row) or a single
screen, from the same pool as nav_score2's A++ plus Review as a module. ⊞ takes the four forms of
nav_glance (flat, cards, folders, grid). A+ is the slots Routines, check-in, Pages. Every combination is
scored with nav_score2.evaluate; `find` is nav_glance's search model with depth coding; `clutter` is
nav_glance's measured ⊞ screen (depth, light and dark).

    PYTHONUTF8=1 python tools/screens/nav_home.py
"""
import contextlib
import importlib.util
import io
import itertools
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "tools", "screens")
OUT_MD = os.path.join(ROOT, "docs", "screens", "t0", "nav-home.md")
WORKSHOP = os.path.join(ROOT, "docs", "screens", "t0", "home-workshop.html")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


n2 = _load("nav_score2")
ng = _load("nav_glance")

HOME_HUBS = [(0, 0, ["check-in", "ledger (masking)", "today's journal"]),
             (0, 0, ["calendar day/week/month", "confirm the week (planner)"]),  # Today's top row
             (1, 0, ["open a page"])]                                              # pinned pages, folded
REVIEW_ROW = ["time totals", "stability trend", "tracker detail and charts", "goals", "ledger/sensory history", "build a saved chart"]
MODULES = dict(n2.MODULE_PINS)
MODULES["Review (module)"] = dict(areas=dict(review=(1, 1)), hub=(1, 1, REVIEW_ROW))
POOL = list(MODULES) + n2.SCREEN_PINS
ROWS_VIA_ALL = [n2.ROUTINES_ROW, n2.CHECKIN_ROW, n2.PAGES_ROW, REVIEW_ROW]
SHEETS = ["flat", "cards", "folders", "grid"]


def candidate(pins, sheet, home=True):
    areas = dict(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(2, 1), checkin=(2, 1),
                 journal=(2, 1), pages=(2, 1), review=(2, 1), manage=(2, 1), system=(1, 1))
    hubs = list(HOME_HUBS) if home else [(1, 0, n2.TODAY_ROW)]
    named = ["today's agenda"]
    for p in pins:
        if p in MODULES:
            areas.update(MODULES[p]["areas"])
            hubs.append(MODULES[p]["hub"])
        else:
            hubs.append((0, 1, [p]))
            named.append(p)
    if sheet in ("flat", "cards"):
        hubs.append((1, 1, n2.LAUNCHER))
    else:
        if sheet == "folders":
            hubs.append((1, 1, sorted({s for g in ng.GROUPS for _, s in ng.top3(g)})))
        hubs += [(2, 1, row) for row in ROWS_VIA_ALL]  # ⊞ → module → its row
    return dict(areas=areas, hubs=hubs, visible=11, hub=0, start_load=2, register=0.9, named1=named)


def score(pins, sheet, glance, home=True):
    r = n2.evaluate(candidate(pins, sheet, home))
    v = ("modules", sheet, "full", "depth")
    return dict(pins=list(pins), sheet=sheet, cost=r["cost"], tail=r["tail"], reach2=r["reach2"], named1=r["named1"],
                switch=r["switch"], find=ng.find(sheet, "depth", "full"),
                clutter=(glance[v]["per"]["all-light"] + glance[v]["per"]["all-dark"]) / 2)


LOW, HIGH = ("cost", "tail", "switch", "find", "clutter"), ("reach2", "named1")


def dominates(a, b):
    return (all(a[k] <= b[k] + 1e-9 for k in LOW) and all(a[k] >= b[k] for k in HIGH)
            and (any(a[k] < b[k] - 1e-9 for k in LOW) or any(a[k] > b[k] for k in HIGH)))


def main():
    _, glance, _ = ng.main()
    rows = [score(p, s, glance) for p in itertools.combinations(POOL, 3) for s in SHEETS]
    front = [r for r in rows if not any(dominates(o, r) for o in rows if o is not r)]
    A_PLUS = ("Routines (module)", "check-in (module)", "Pages (module)")
    A_PP = tuple(n2.PIN_SEARCH["best"][0][3])
    ref = {"A+ before (thin home)": score(A_PLUS, "flat", glance, home=False),
           "A+ with this home": score(A_PLUS, "flat", glance),
           "A++ before (thin home)": score(A_PP, "flat", glance, home=False),
           "A++ pins with this home": score(A_PP, "flat", glance),
           # owner, 2026-10-07: Today · Calendar · Hub · Pages · check-in (slot 5 re-pinnable), Hub sheet as cards
           "Owner's bar (2026-10-07)": score(("Week (module)", "Pages (module)", "check-in (module)"), "cards", glance)}
    best = {s: min((r for r in rows if r["sheet"] == s), key=lambda r: (r["cost"], -r["reach2"], -r["named1"])) for s in SHEETS}
    return rows, front, ref, best


def fmt(r, name=None):
    return "| %s | %s | %.1f | %.1f | %d | %d | %.2f | %.2f | %.3f |" % (
        name or " · ".join(p.replace(" (module)", " ▣") for p in r["pins"]), r["sheet"], r["cost"], r["tail"], r["reach2"],
        r["named1"], r["switch"], r["find"], r["clutter"])


HEAD = ["| Slots (▣ = module) | ⊞ | Cost | Long tail | Reach in 2 | Named in 1 | Switch | Find in ⊞ | Clutter of ⊞ |",
        "|---|---|---|---|---|---|---|---|---|"]


def write(rows, front, ref, best):
    out = ["# Navigation against the owner's home", "", "Generated by `tools/screens/nav_home.py`; its docstring states what the home adds and what is assumed.",
           "", "%d combinations: every 3 bar slots from %d (%d modules, %d single screens) × the %d forms of ⊞. The bar is always Today · 3 slots · ⊞." % (
               len(rows), len(POOL), len(MODULES), len(n2.SCREEN_PINS), len(SHEETS)), "",
           "## What the home changes", ""] + HEAD + [fmt(r, n) for n, r in ref.items()]
    out += ["", "## Cheapest slots for each form of ⊞", ""] + HEAD + [fmt(best[s]) for s in SHEETS]
    out += ["", "## How the top slots move with the assumed penalty", "",
            "`nav_score2.NOT_ANYWHERE` is the steps added when a screen's cheapest route works from one place only (here, from home). "
            "It is assumed, not measured. The three cheapest slot sets with ⊞ flat, under three values:", ""]
    saved = n2.NOT_ANYWHERE
    try:
        for pen in (0.25, 0.5, 1.0):
            n2.NOT_ANYWHERE = pen
            top = sorted((n2.evaluate(candidate(p, "flat"))["cost"], p) for p in itertools.combinations(POOL, 3))[:3]
            out.append("- %.2f: %s" % (pen, "; ".join("%s (%.1f)" % (" · ".join(x.replace(" (module)", " ▣") for x in p), c) for c, p in top)))
    finally:
        n2.NOT_ANYWHERE = saved
    out += ["", "## Pareto front (%d of %d), cheapest 25" % (len(front), len(rows)), ""] + HEAD
    out += [fmt(r) for r in sorted(front, key=lambda r: (r["cost"], r["clutter"]))[:25]]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out


def inject(best, ref):
    """Puts the scored winners into the workshop page between its NAV_HOME markers, so no number there is typed."""
    data = {"best": {s: {k: best[s][k] for k in ("pins", "cost", "reach2", "named1", "find", "clutter")} for s in SHEETS},
            "aplus": {k: ref["A+ with this home"][k] for k in ("pins", "cost", "reach2", "named1", "find", "clutter")}}
    with open(WORKSHOP, encoding="utf-8", newline="") as fh:
        page = fh.read()
    new, n = re.subn(r"/\* NAV_HOME \*/.*?/\* END NAV_HOME \*/",
                     lambda m: "/* NAV_HOME */ const NAV_HOME = %s; /* END NAV_HOME */" % json.dumps(data, ensure_ascii=False), page, flags=re.S)
    if n != 1:
        raise SystemExit("home-workshop.html has no NAV_HOME marker")
    with open(WORKSHOP, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)


if __name__ == "__main__":
    rows, front, ref, best = main()
    print("\n".join(write(rows, front, ref, best)))
    if os.environ.get("NAV_HOME_INJECT") == "1":
        inject(best, ref)
