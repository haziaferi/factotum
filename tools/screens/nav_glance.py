"""Glanceability of the phone navigation (owner, 2026-10-05: A+ and A++ "fill the screen with options,
good for clarity of choice, difficult to parse at a glance"; can colour and depth help; can A+ be
combined with P7). Writes docs/screens/t0/nav-glance.md and docs/screens/t0/nav-glance.html.

Every combination of four levers is built as real mockup screens, rendered headless at 360x740 and
measured, then scored for steps with nav_score2's model:

  bar     modules (A+) | pins (A++, enumerated default) | min (Today · Modules · capture: P7's grid as a tab)
  sheet   flat (A+ as mocked: tiles under text headings) | cards (each module a card, every screen)
          | folders (P7 inside ⊞: a card per module, its 3 most used screens + the module) | grid (P7: module tiles only)
  row     full | top3 (3 + More) | hide (full on arrival, hidden once the content scrolls) | none (title menu ▾)
  coding  plain | hue (one hue per module) | depth (hue + tonal surfaces instead of rules, inactive items receded)

Objectives (phone):
  cost, tail, reach2, named1      nav_score2's step model, unchanged
  start_nav     navigation elements on the start screen
  primary       of those, how many are drawn at full contrast
  find          expected items inspected to find a uniformly chosen feature in ⊞ (search model below)
  clutter       MEASURED: edge density of the rendered start, module and ⊞ screens (Mack & Oliva 2004), mean

Search model for `find` (an assumption, stated in the output): a target's group is found by reading
headings one by one, (G+1)/2, unless each group is a filled region in its own hue and G <= 6, when the
group is picked at a glance, 1 (colour pop-out needs area and a small set: Treisman & Gelade 1980,
Healey 1996). Inside a group, items are read one by one, (n+1)/2. Hue on text headings alone is not
counted as pop-out.

    PYTHONUTF8=1 python tools/screens/nav_glance.py
"""
import concurrent.futures
import contextlib
import hashlib
import html
import importlib.util
import io
import itertools
import json
import os
import subprocess
import tempfile

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "tools", "screens")
OUT_MD = os.path.join(ROOT, "docs", "screens", "t0", "nav-glance.md")
OUT_HTML = os.path.join(ROOT, "docs", "screens", "t0", "nav-glance.html")
CACHE = os.path.join(ROOT, "_screens-sources", "glance-renders")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


n2 = _load("nav_score2")
fa = _load("frames_all")
e = html.escape

# ---- the content every variant draws ----------------------------------------------------------------
# ⊞ groups: (module, glyph, [(tile, nav_score2 screen)]). Same tiles as frames_all's LAUNCHER_SHEET.
GROUPS = [
    ("Today", "◷", [("Day", "calendar day/week/month"), ("Week", "calendar day/week/month"), ("Month", "calendar day/week/month"),
                    ("Planner", "confirm the week (planner)")]),
    ("Routines", "↻", [("Habits", "manage habits"), ("Trackers", "manage trackers"), ("Activities", "manage activities"),
                       ("Checklists", "manage checklists"), ("Charts", "tracker detail and charts"), ("Goals", "goals")]),
    ("check-in", "◎", [("check-in", "check-in"), ("Ledger", "ledger (masking)"), ("Sensory", "sensory log"), ("Trend", "stability trend")]),
    ("Pages", "☰", [("Journal", "today's journal"), ("Tree", "open a page"), ("Templates", "templates"), ("Road Map", "Road Map")]),
    ("App", "⚙", [("Labels", "labels"), ("Time blocks", "time blocks"), ("Calendars", "calendar links"), ("Settings", "settings"),
                  ("Trash", "trash"), ("About", "about")]),
]
WEIGHT = {s[0]: s[1] for s in n2.SCREENS}
# Areas each module's tile opens (folders and grid make a module itself a ⊞ target).
MODULE_AREAS = {"Today": ["calendar"], "Routines": ["manage", "review", "due"], "check-in": ["checkin"],
                "Pages": ["pages", "journal"], "App": ["system"]}
HUE = {"Today": 250, "Week": 250, "Routines": 150, "check-in": 300, "Pages": 75, "App": None, "Ledger": 300, "Modules": None, "All": None}
TODAY_ROW = ["Agenda", "Day", "Week", "Month", "Planner"]
ROUTINES_ROW = ["Habits", "Trackers", "Activities", "Checklists", "Charts", "Goals"]


def top3(group):
    """The three most used tiles of a group, by weekly weight; drawn order breaks ties."""
    tiles = group[2]
    return sorted(tiles, key=lambda t: (-WEIGHT[t[1]], tiles.index(t)))[:3]


# ---- the levers -------------------------------------------------------------------------------------
BARS = {"modules": [("◷", "Today"), ("↻", "Routines"), ("◎", "check-in"), ("☰", "Pages"), ("⊞", "All")],
        "pins": [("◷", "Today"), ("☰", "Pages"), ("▦", "Week"), ("◇", "Ledger"), ("⊞", "All")],
        "min": [("◷", "Today"), ("⊞", "Modules"), ("+", "Capture")]}
SHEETS = ["flat", "cards", "folders", "grid"]
ROWS = ["full", "top3", "hide", "none"]
CODINGS = ["plain", "hue", "depth"]


def nav_candidate(bar, sheet, row):
    """A nav_score2 candidate for one lever setting. Row and sheet change hubs and area costs only."""
    if bar == "modules":
        base = dict(n2.PHONE["A+. Modules + top rows + ⊞"])
        rows = [(1, 0, n2.TODAY_ROW), (1, 1, n2.ROUTINES_ROW), (1, 1, n2.CHECKIN_ROW), (1, 1, n2.PAGES_ROW)]
    elif bar == "pins":
        base = dict(n2.PHONE["A++. Today · 3 pins · ⊞"])
        pinned = [h for h in base["hubs"] if h[0] == 0]  # a single screen pinned to the bar: no row involved
        rows = [h for h in base["hubs"] if h[0] > 0 and h[2] is not n2.LAUNCHER] + [(1, 0, n2.TODAY_ROW)]
    else:
        base = dict(note="", areas=dict(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(2, 1), checkin=(2, 1),
                                        journal=(2, 1), pages=(2, 1), review=(2, 1), manage=(2, 1), system=(2, 1)),
                    visible=6, start_load=2, register=0.9, named1=["today's agenda", "capture"])
        rows = [(1, 0, n2.TODAY_ROW), (2, 1, n2.ROUTINES_ROW), (2, 1, n2.CHECKIN_ROW), (2, 1, n2.PAGES_ROW)]
    if bar != "pins":
        pinned = []
    areas = dict(base["areas"])
    on_bar = {"modules": ["Today", "Routines", "check-in", "Pages"], "pins": ["Today", "Pages"], "min": ["Today"]}[bar]
    sheet_cost = 1  # ⊞ is one tap from anywhere: a sheet (modules, pins) or a tab (min)
    hubs = list(pinned)
    # rows not reachable from the bar open from ⊞ when ⊞ shows modules (folders, grid, and the headings of flat/cards)
    for cost, anywhere, names in rows:
        if row == "full":
            hubs.append((cost, anywhere, names))
        elif row == "top3":
            ranked = sorted(names, key=lambda n: -WEIGHT[n])
            hubs += [(cost, anywhere, ranked[:3]), (cost + 1, anywhere, ranked[3:])]
        elif row == "hide":
            hubs.append((cost, 0, names))  # a flick back up first, so not from anywhere
        else:
            hubs.append((cost + 1, anywhere, names))  # title menu ▾, then the screen
    if bar != "min":
        for module, mod_areas in MODULE_AREAS.items():
            if module not in on_bar or sheet in ("folders", "grid"):
                for a in mod_areas:
                    if areas[a] is None or areas[a][0] + (0 if areas[a][1] else 0.5) > sheet_cost + 1:
                        areas[a] = (sheet_cost + 1, 1)
    if sheet in ("flat", "cards"):
        hubs.append((sheet_cost, 1, n2.LAUNCHER))
    elif sheet == "folders":
        hubs.append((sheet_cost, 1, sorted({s for g in GROUPS for _, s in top3(g)})))
    cand = dict(base, areas=areas, hubs=hubs)
    cand["hub"] = {"flat": 24, "cards": 24, "folders": 5 * 4, "grid": 5}[sheet]
    return cand


# ---- the glance model -------------------------------------------------------------------------------
def row_visible(row, names):
    return {"full": len(names), "top3": 4, "hide": len(names), "none": 0}[row]


def start_nav(bar, row):
    return len(BARS[bar]) + row_visible(row, TODAY_ROW) + 2 + (1 if row == "none" else 0)


def primary(bar, row, coding):
    n = start_nav(bar, row)
    if coding != "depth":
        return n
    # depth: the active bar item, the ⊞/capture accent and the active row chip stay at full contrast
    return 2 + (1 if row != "none" else 0)


def find(sheet, coding, row):
    groups = [len(g[2]) for g in GROUPS]
    G = len(groups)
    pop = coding != "plain" and sheet in ("cards", "folders", "grid") and G <= 6
    pick = 1 if pop else (G + 1) / 2
    total, count = 0.0, 0
    for g in GROUPS:
        n = len(g[2])
        shown = {t for t, _ in top3(g)}
        for i, (tile, _) in enumerate(g[2]):
            if sheet in ("flat", "cards"):
                within = (n + 1) / 2
            elif sheet == "folders":
                within = 2 if tile in shown else 4 + row_search(row, n)  # 3 shortcuts + the module, then its row
            else:
                within = 1 + row_search(row, n)
            total += pick + within
            count += 1
    return total / count


def sibling(row):
    """Mean taps from one screen of a module to a sibling screen (Routines' six, uniformly), mid-content."""
    n = len(ROUTINES_ROW)
    return {"full": 1.0, "hide": 1.5, "top3": (3 / n) * 1 + ((n - 3) / n) * 2, "none": 2.0}[row]


def row_search(row, n):
    """Items read in a module's row to find one of its n screens, the target chosen uniformly."""
    if row == "top3":  # in the 3 shown: (3+1)/2; else all 3, More, then the rest one by one
        return 3 / n * 2 + (n - 3) / n * (4 + (n - 3 + 1) / 2)
    return {"full": (n + 1) / 2, "hide": (n + 1) / 2, "none": 1 + (n + 1) / 2}[row]


# ---- rendering --------------------------------------------------------------------------------------
def hvars(h):
    """A module's hue as CSS variables. Lightness comes from the theme (THEME_CSS), so tints work in light and dark."""
    return "--h:%d;--c:%d" % (h or 0, 0 if h is None else 1)


# --g/--mod: the module's strong tone; --gt/--modt: its tint. Every module gets the same lightness and chroma, so
# none reads louder than another (app-register-layout Step 1d B). The hues are placeholders: the palette is Q4.
THEME_CSS = """:root{--L:.55;--Lt:.94;--Ct:.035}
:root[data-theme=dark]{--L:.78;--Lt:.33;--Ct:.05}
.phone,.card{--g:oklch(var(--L) calc(.12*var(--c)) var(--h));--gt:oklch(var(--Lt) calc(var(--Ct)*var(--c)) var(--h))}
.phone{--mod:var(--g);--modt:var(--gt)}"""


CODING_CSS = {
    "plain": "",
    "hue": """.bar div.on i{color:var(--mod)}.bar div.on{box-shadow:inset 0 3px 0 var(--mod)}.tabs .on{background:var(--modt);border-color:var(--mod)}
.hdr{box-shadow:inset 4px 0 0 var(--mod)}.card{background:var(--gt)!important;border-color:var(--g)!important}.card .gh,.tile i{color:var(--g)}""",
    "depth": """.hdr{border-bottom:0;background:var(--bg);box-shadow:inset 4px 0 0 var(--mod)}.zone{border:0;background:var(--zone)}.it{border-top:0;padding:6px 0}
.list div{border-top:0}.bar{border-top:0;background:var(--zone2)}.bar div{opacity:.55}.bar div.on{opacity:1}.bar div.on i{background:var(--modt);color:var(--mod);border-radius:999px;padding:2px 18px}
.tabs span{border-color:transparent;color:var(--dim)}.tabs .on{background:var(--modt);color:var(--fg)}.btn{border:0}.ic{border:0}
.card{border:0!important;background:var(--gt)!important}.card .gh,.tile i{color:var(--g)}.card .tiles span{border:0;background:var(--bg)}
.drawer{border:0!important;box-shadow:0 -8px 28px rgba(0,0,0,.18)}.tiles span{border:0}""",
}
BASE_CSS = fa.CSS + """
body{padding:0;margin:0}.phone{border:0;border-radius:0}.card{border:1px solid var(--line);border-radius:12px;padding:6px 8px;margin:6px 0;background:var(--zone)}
.card .gh{font-size:12px;font-weight:600;display:flex}.card .gh span{margin-left:auto;color:var(--dim);font-weight:400}
.folders{display:grid;grid-template-columns:1fr 1fr;gap:8px}.folders .card{margin:0;min-height:96px}
.tgrid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:6px}.tile{border-radius:14px;height:84px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:12px}
.tile i{font-style:normal;font-size:22px}"""


def bar_html(bar, on):
    return fa.bar(BARS[bar], on)


def row_html(row, names):
    if row == "none":
        return ""
    shown = names if row in ("full", "hide") else names[:3] + ["More ▾"]
    return fa.TOPROW(shown)


def title(row, text):
    return text + (" ▾" if row == "none" else "")


def sheet_html(sheet):
    nl = '<div class="nl">Dentist tomorrow 9am every 6 months</div><div class="grp">Pinned and recent</div><div class="tiles">%s</div>' % "".join(
        "<span>%s</span>" % t for t in ["Journal", "Ledger", "Trackers", "Week"])

    def gvars(m):
        return hvars(HUE.get(m))

    if sheet == "flat":
        body = "".join('<div class="grp">%s</div><div class="tiles">%s</div>' % (e(m), "".join("<span>%s</span>" % e(t) for t, _ in ts))
                       for m, _, ts in GROUPS)
    elif sheet == "cards":
        body = "".join('<div class="card" style="%s"><div class="gh">%s %s<span>›</span></div><div class="tiles">%s</div></div>' % (
            gvars(m), g, e(m), "".join("<span>%s</span>" % e(t) for t, _ in ts)) for m, g, ts in GROUPS)
    elif sheet == "folders":
        body = '<div class="folders">%s</div>' % "".join(
            '<div class="card" style="%s"><div class="gh">%s %s<span>%d ›</span></div><div class="tiles">%s</div></div>' % (
                gvars(m), g, e(m), len(ts), "".join("<span>%s</span>" % e(t) for t, _ in top3((m, g, ts)))) for m, g, ts in GROUPS)
    else:
        body = '<div class="tgrid">%s</div>' % "".join(
            '<div class="tile card" style="%s"><i>%s</i>%s</div>' % (gvars(m), g, e(m)) for m, g, _ in GROUPS)
    return nl + body


def surfaces(bar, sheet, row):
    """(name, module, html body) for the three screens measured."""
    agenda = fa.zone("Agenda", fa.AGENDA[:3]) + fa.zone("Routines", fa.ROUTINES[:4])
    start = fa.phone(fa.hdr(title(row, "Today · Mon 5 Oct")), row_html(row, TODAY_ROW) + agenda, bar_html(bar, "Today"))
    module_on = {"modules": "Routines", "pins": "", "min": "Modules"}[bar]
    module = fa.phone(fa.hdr(title(row, "Routines"), "‹" if bar != "modules" else ""), row_html(row, ROUTINES_ROW) + fa.listpage(
        ["Walk · every day", "Water · 8 a day in blocks", "Gym · Mon Wed Fri", "Read · rolling, every 2 days", "+ New habit"]),
        bar_html(bar, module_on))
    if bar == "min":
        all_ = fa.phone(fa.hdr("Modules"), sheet_html(sheet), bar_html(bar, "Modules"))
    else:
        all_ = fa.phone(fa.hdr(title(row, "Today · Mon 5 Oct")), fa.zone("Agenda", fa.AGENDA[:2]), bar_html(bar, "All"),
                        overlay='<div class="drawer bottom tall">%s</div>' % sheet_html(sheet))
    return [("start", "Today", start), ("module", "Routines", module), ("all", "App", all_)]


def page(body, module, coding, theme):
    body = body.replace('<div class="phone">', '<div class="phone" style="%s">' % hvars(HUE.get(module)), 1)
    return ('<!doctype html><html data-theme="%s"><head><meta charset="utf-8"><style>%s\n%s\n%s</style></head><body>%s</body></html>' % (
        theme, BASE_CSS, THEME_CSS, CODING_CSS[coding], body))


def render(doc):
    """Renders one page headless at 360x740 (cached by content) and returns its PNG path."""
    key = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:20]
    png = os.path.join(CACHE, key + ".png")
    if os.path.exists(png):
        return png
    src = os.path.join(CACHE, key + ".html")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=360,740", "--user-data-dir=" + prof, "--screenshot=" + png, "file:///" + src.replace("\\", "/")],
                       capture_output=True, timeout=120)
    if not os.path.exists(png):
        raise RuntimeError("render failed: " + src)
    return png


def edge_density(png, threshold=40):
    """Share of pixels on an edge: grey image, edge filter, threshold out of 255."""
    im = Image.open(png).convert("L").filter(ImageFilter.FIND_EDGES)
    hist = im.histogram()
    return sum(hist[threshold:]) / float(im.size[0] * im.size[1])


# ---- run --------------------------------------------------------------------------------------------
def main():
    os.makedirs(CACHE, exist_ok=True)
    variants = list(itertools.product(BARS, SHEETS, ROWS, CODINGS))
    docs = {}
    for v in variants:
        bar, sheet, row, coding = v
        docs[v] = [(name + "-" + theme, page(body, module, coding, theme)) for name, module, body in surfaces(bar, sheet, row)
                   for theme in ("light", "dark")]
    unique = sorted({d for ds in docs.values() for _, d in ds})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        pngs = dict(zip(unique, pool.map(render, unique)))
    dens = {d: edge_density(p) for d, p in pngs.items()}

    rows = {}
    for v in variants:
        bar, sheet, row, coding = v
        r = n2.evaluate(nav_candidate(bar, sheet, row))
        per = {name: dens[d] for name, d in docs[v]}
        rows[v] = dict(cost=r["cost"], tail=r["tail"], reach2=r["reach2"], named1=r["named1"], switch=r["switch"],
                       sibling=sibling(row), start_nav=start_nav(bar, row), primary=primary(bar, row, coding), find=find(sheet, coding, row),
                       clutter=sum(per.values()) / len(per), per=per, png={name: pngs[d] for name, d in docs[v]},
                       docs=dict(docs[v]))
    low = ("cost", "tail", "sibling", "start_nav", "primary", "find", "clutter")
    high = ("reach2", "named1")

    def dom(a, b):
        return (all(a[k] <= b[k] + 1e-9 for k in low) and all(a[k] >= b[k] for k in high)
                and (any(a[k] < b[k] - 1e-9 for k in low) or any(a[k] > b[k] for k in high)))

    front = [v for v in variants if not any(dom(rows[o], rows[v]) for o in variants if o != v)]
    return variants, rows, front


def label(v):
    return " · ".join(v)


def write(variants, rows, front):
    ref = {"A+ as mocked": ("modules", "flat", "full", "plain"), "A++ as mocked": ("pins", "flat", "full", "plain")}
    cols = "| Variant (bar · sheet · row · coding) | Cost | Long tail | Reach in 2 | Named in 1 | Sibling | Start nav | Full contrast | Find in ⊞ | Clutter |"
    fmt = "| %s | %.0f | %.1f | %d | %d | %.1f | %d | %d | %.2f | %.3f |"
    line = lambda v: fmt % (label(v), rows[v]["cost"], rows[v]["tail"], rows[v]["reach2"], rows[v]["named1"], rows[v]["sibling"], rows[v]["start_nav"],
                            rows[v]["primary"], rows[v]["find"], rows[v]["clutter"])
    out = ["# Navigation at a glance", "", "Generated by `tools/screens/nav_glance.py` (its docstring states the model).", "",
           "%d variants: every combination of bar (%s), ⊞ form (%s), top row (%s) and coding (%s). Each was drawn as three phone screens, "
           "start, a module and ⊞, then rendered headless at 360×740. **Clutter** is measured: the share of edge pixels, averaged over the "
           "three. **Find in ⊞** is a search model: the items you inspect to find a feature. **Full contrast** counts the navigation "
           "elements drawn at full strength on the start screen. Step costs come from `nav_score2`." % (
               len(variants), ", ".join(BARS), ", ".join(SHEETS), ", ".join(ROWS), ", ".join(CODINGS)), "",
           "## The two as mocked", "", cols, "|---|---|---|---|---|---|---|---|---|---|"]
    out += [line(v) for v in ref.values()]
    out += ["", "## Pareto front (%d of %d)" % (len(front), len(variants)), "", cols, "|---|---|---|---|---|---|---|---|---|---|"]
    out += [line(v) for v in sorted(front, key=lambda v: (rows[v]["cost"], rows[v]["clutter"]))]
    # one lever at a time, against A+ as mocked
    out += ["", "## Each lever alone, from A+ as mocked", "", cols, "|---|---|---|---|---|---|---|---|---|---|"]
    base = ref["A+ as mocked"]
    for i, opts in enumerate([list(BARS), SHEETS, ROWS, CODINGS]):
        for o in opts:
            v = tuple(o if j == i else base[j] for j in range(4))
            if v != base:
                out.append(line(v))
    out += ["", "## Is the clutter ranking an artefact of the edge threshold?", ""]
    for t in THRESHOLDS:
        c = {v: sum(edge_density(p, t) for p in rows[v]["png"].values()) / len(rows[v]["png"]) for v in variants}
        worst_depth = max(c[v] for v in variants if v[3] == "depth")
        best_other = min(c[v] for v in variants if v[3] != "depth")
        same = [v[:3] for v in variants if v[3] == "depth"]
        wins = sum(1 for s in same if c[s + ("depth",)] < min(c[s + ("plain",)], c[s + ("hue",)]))
        out.append("- Threshold %d/255: with the same bar, ⊞ and row, depth is less cluttered than both plain and hue in %d of %d. "
                   "Across structures, the most cluttered depth variant measures %.3f and the least cluttered plain or hue one %.3f." % (
                       t, wins, len(same), worst_depth, best_other))
    out += ["", "## The shortlist, mocked", "", "`nav-glance.html` draws these, in light and dark:", "", cols, "|---|---|---|---|---|---|---|---|---|---|"]
    out += [line(v).replace("| " + label(v), "| %s: %s" % (n, label(v)), 1) for n, v in SHORTLIST.items()]
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return out


THRESHOLDS = (20, 40, 80, 120)
SHORTLIST = {
    "A+ as mocked": ("modules", "flat", "full", "plain"),
    "A+ with depth": ("modules", "flat", "full", "depth"),
    "A+ × P7, coloured cards": ("modules", "cards", "full", "depth"),
    "A+ × P7, folders": ("modules", "folders", "top3", "depth"),
    "A+ × P7, module grid": ("modules", "grid", "full", "depth"),
    "A++ with coloured cards": ("pins", "cards", "full", "depth"),
    "P7 as a tab": ("min", "grid", "full", "depth"),
}


def write_html(rows):
    """The shortlist as live mockups: each screen is its own measured page, in an iframe, light or dark."""
    css = fa.CSS + """.shot{display:flex;gap:14px;overflow-x:auto;padding-bottom:6px}iframe{width:362px;height:742px;border:1px solid var(--line);border-radius:22px;flex:none;background:var(--bg)}
.tog{border:1px solid var(--line);border-radius:999px;padding:4px 12px;background:var(--zone);color:var(--fg);cursor:pointer}
body.dark .light,body:not(.dark) .dark{display:none}"""
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             "<title>Factotum navigation glance</title><style>%s</style></head><body>" % css,
             "<h1>Navigation at a glance</h1>",
             '<p class="dim">The shortlist from <code>nav-glance.md</code>. Each frame is exactly the page that was rendered and measured. '
             "Hues are placeholders, one per module at equal lightness and chroma; the palette itself is Q4. The data is invented.</p>",
             '<p><button class="tog" onclick="theme(!document.body.classList.contains(\'dark\'))">Light / dark</button></p>']
    for name, v in SHORTLIST.items():
        r = rows[v]
        parts.append("<h2>%s <small>%s</small></h2>" % (e(name), e(label(v))))
        parts.append('<p class="dim">Weekly steps %.0f · reach in 2: %d · sibling %.1f · navigation on start %d, at full contrast %d · '
                     "find in ⊞ %.2f · clutter %.3f</p>" % (r["cost"], r["reach2"], r["sibling"], r["start_nav"], r["primary"], r["find"], r["clutter"]))
        for theme in ("light", "dark"):
            parts.append('<div class="shot %s">%s</div>' % (theme, "".join(
                '<iframe scrolling="no" title="%s" srcdoc="%s"></iframe>' % (e(s), e(r["docs"][s + "-" + theme], quote=True)) for s in ("start", "module", "all"))))
    parts.append("<script>function theme(d){document.body.classList.toggle('dark',d);document.documentElement.dataset.theme=d?'dark':'light'}"
                 "theme(matchMedia('(prefers-color-scheme: dark)').matches)</script></body></html>")
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts))


if __name__ == "__main__":
    variants, rows, front = main()
    out = write(variants, rows, front)
    write_html(rows)
    print("\n".join(out[-(len(SHORTLIST) + 12):]))
    with open(os.path.join(CACHE, "rows.json"), "w", encoding="utf-8") as fh:
        json.dump({label(v): {k: r[k] for k in r if k not in ("png", "docs")} for v, r in rows.items()}, fh, indent=1)
