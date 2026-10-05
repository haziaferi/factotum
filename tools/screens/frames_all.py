"""Writes docs/screens/t0/frames-all.html: every navigation candidate of nav_score2.py as a structure
mockup (owner, 2026-10-05: "make a mockup of all of them"). One sample dataset and one set of parts,
so candidates differ only in navigation. Each block shows the candidate's measured row and the step
cost of a few long-tail screens, both computed by nav_score2.evaluate, never typed here.

    python tools/screens/frames_all.py
"""
import contextlib
import html
import importlib.util
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "frames-all.html")
spec = importlib.util.spec_from_file_location("n2", os.path.join(ROOT, "tools", "screens", "nav_score2.py"))
n2 = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(n2)

TAIL = ["manage habits", "tracker detail and charts", "templates", "labels", "time blocks", "trash", "settings"]
e = html.escape

# ---- parts --------------------------------------------------------------------------------------
def hdr(title, left="", right="⌕ ◐"):
    l = '<span class="ic">%s</span>' % left if left else ""
    r = "".join('<span class="ic">%s</span>' % g for g in right.split())
    return '<div class="hdr">%s<b>%s</b>%s</div>' % (l, e(title), r)

def zone(title, rows, link=""):
    lk = '<span class="lk">%s ›</span>' % e(link) if link else ""
    return '<div class="zone"><h4>%s%s</h4>%s</div>' % (e(title), lk, "".join(rows))

def it(text, small="", lead="", btn=""):
    ld = '<span class="ck"></span>' if lead == "ck" else ('<span class="tm">%s</span>' % lead if lead else "")
    sm = " <small>%s</small>" % e(small) if small else ""
    b = '<span class="btn">%s</span>' % e(btn) if btn else ""
    return '<div class="it">%s<span class="t">%s%s</span>%s</div>' % (ld, e(text), sm, b)

AGENDA = [it("Dentist", "event", "09:00"), it("Pay the fine", "due today", "ck"), it("Call the bank", "reminder", "15:00"),
          it("Return library books", "", "ck")]
ROUTINES = [it("Walk", "", "", "Log"), it("Water", "3 of 8 · next block 14:00", "", "Log"),
            it("Morning routine", "checklist 3/5", "", "Open"), it("Reading", "timer · 0:24 running", "", "Stop"),
            it("Sleep", "reading due", "", "Add")]

def bar(items, on, plus=None):
    cells = []
    for i, (glyph, label) in enumerate(items):
        if plus is not None and i == plus:
            cells.append('<div class="plus"><i>+</i></div>')
        cls = ' class="on"' if label == on else ""
        cells.append('<div%s><i>%s</i>%s</div>' % (cls, glyph, e(label)))
    if plus is not None and plus >= len(items):
        cells.append('<div class="plus"><i>+</i></div>')
    return '<div class="bar">%s</div>' % "".join(cells)

def phone(inner_hdr, body, bottom="", overlay="", fab=False):
    f = '<div class="fab">+</div>' if fab else ""
    ov = '<div class="scrim"></div>%s' % overlay if overlay else ""
    return '<div class="phone">%s<div class="body">%s</div>%s%s%s</div>' % (inner_hdr, body, f, bottom, ov)

def drawer(entries, side="left"):
    rows = "".join('<div%s>%s</div>' % (' class="grp"' if x.startswith("§") else "", e(x.lstrip("§"))) for x in entries)
    return '<div class="drawer %s">%s</div>' % (side, rows)

def listpage(entries):
    return '<div class="zone list">%s</div>' % "".join(
        '<div%s>%s</div>' % (' class="grp"' if x.startswith("§") else "", e(x.lstrip("§"))) for x in entries)

def tree():
    return listpage(["§Pinned", "Today", "Journal · Mon 5 Oct", "§Pages", "Garden plan", "   Beds (canvas)",
                     "   Seeds (database)", "Reading list (database)", "Trip", "§Modules", "Week", "Routines", "check-in",
                     "Review"])

G_BAR = [("◷", "Today"), ("▦", "Week"), ("☰", "Library"), ("↗", "Review")]
A_BAR = [("◷", "Today"), ("↻", "Routines"), ("◎", "check-in"), ("☰", "Pages"), ("⊞", "All")]
PIN_BAR = [("◷", "Today"), ("☰", "Pages"), ("▦", "Week"), ("◇", "Ledger"), ("⊞", "All")]


def TOPROW(names):
    return '<div class="tabs">%s</div>' % "".join(
        '<span%s>%s</span>' % (' class="on"' if i == 0 else "", e(n)) for i, n in enumerate(names))


LAUNCHER_SHEET = ('<div class="drawer bottom tall"><div class="nl">Dentist tomorrow 9am every 6 months</div>'
                  '<div class="grp">Pinned and recent</div><div class="tiles">%s</div>%s</div>') % (
    "".join('<span>%s</span>' % e(t) for t in ["Journal", "Ledger", "Trackers", "Week"]),
    "".join('<div class="grp">%s</div><div class="tiles">%s</div>' % (e(g), "".join('<span>%s</span>' % e(t) for t in ts)) for g, ts in [
        ("Today", ["Day", "Week", "Month", "Planner"]),
        ("Routines", ["Habits", "Trackers", "Activities", "Checklists", "Charts", "Goals"]),
        ("check-in", ["check-in", "Ledger", "Sensory", "Trend"]),
        ("Pages", ["Journal", "Tree", "Templates", "Road Map"]),
        ("App", ["Labels", "Time blocks", "Calendars", "Settings", "Trash", "About"])]))
ALL_PLACES = ["§Places", "Today", "Week", "Library", "Review", "§Routines", "Habits", "Trackers", "Activities",
              "Checklists", "§check-in", "check-in", "Ledger", "Sensory", "§System", "Labels", "Templates", "Road Map",
              "Trash", "Settings"]

# ---- the candidates' screens ----------------------------------------------------------------------
SCREENS = {
    "B. Today hub": [
        ("Start: four zones", phone(hdr("Today · Mon 5 Oct"), zone("Agenda", AGENDA[:2]) + zone("Routines", ROUTINES[:2]) +
            zone("Journal", [it("Today's page", "2 lines", "", "Open")]) + zone("check-in", [it("How are things right now?", "", "", "check-in")]),
            bar([("◷", "Today"), ("▦", "Calendar"), ("☰", "Pages"), ("↗", "Review")], "Today"), fab=True)),
        ("The account menu holds the system screens; there is no place to manage routines (search only)",
         phone(hdr("Today · Mon 5 Oct"), zone("Agenda", AGENDA[:2]), bar([("◷", "Today"), ("▦", "Calendar"), ("☰", "Pages"), ("↗", "Review")], "Today"),
               overlay=drawer(["§Account", "Settings", "Labels", "Trash", "Backup", "Sync folder", "About"], "right"))),
    ],
    "G (as mocked)": [
        ("Start: agenda + routines", phone(hdr("Today · Mon 5 Oct"), zone("Agenda", AGENDA) + zone("Routines", ROUTINES), bar(G_BAR, "Today", plus=2))),
        ("Review is the weekly hub; managing routines has no path (search only)",
         phone(hdr("Review · this week"), listpage(["§This week", "Time totals", "Trackers and charts", "Habits", "Goals",
               "How things have felt", "Ledger and sensory history", "Saved charts"]), bar(G_BAR, "Review", plus=2))),
    ],
    "G+ (manage from Today)": [
        ("Start: as G, with 'All routines' at the head of the routines zone", phone(hdr("Today · Mon 5 Oct"),
            zone("Agenda", AGENDA) + zone("Routines", ROUTINES, "All routines"), bar(G_BAR, "Today", plus=2))),
        ("All routines: the manager, one tap from Today", phone(hdr("All routines", "‹"),
            '<div class="tabs"><span class="on">Habits</span><span>Trackers</span><span>Activities</span><span>Checklists</span></div>' +
            listpage(["Walk · every day", "Water · 8 a day in blocks", "Gym · Mon Wed Fri", "Read · rolling, every 2 days", "+ New habit"]),
            bar(G_BAR, "Today", plus=2))),
    ],
    "P6. Bar + drawer": [
        ("Start: G's bar, plus ☰ in the header", phone(hdr("Today · Mon 5 Oct", "☰"), zone("Agenda", AGENDA) + zone("Routines", ROUTINES), bar(G_BAR, "Today", plus=2))),
        ("The drawer lists every place", phone(hdr("Today · Mon 5 Oct", "☰"), zone("Agenda", AGENDA), bar(G_BAR, "Today", plus=2), overlay=drawer(ALL_PLACES))),
    ],
    "P5. Bar + Browse hub": [
        ("Start: the fifth slot is Browse instead of Review", phone(hdr("Today · Mon 5 Oct"), zone("Agenda", AGENDA) + zone("Routines", ROUTINES),
            bar([("◷", "Today"), ("▦", "Week"), ("☰", "Library"), ("⋯", "Browse")], "Today", plus=2))),
        ("Browse: every other place on one page", phone(hdr("Browse"), listpage(["§Look back", "Review", "§Routines", "Habits", "Trackers",
            "Activities", "Checklists", "§check-in", "History", "§Organise", "Labels", "Templates", "Road Map", "§App", "Trash", "Settings"]),
            bar([("◷", "Today"), ("▦", "Week"), ("☰", "Library"), ("⋯", "Browse")], "Browse", plus=2))),
    ],
    "A. Module tabs": [
        ("Start: today's agenda only", phone(hdr("Today · Mon 5 Oct"), zone("Agenda", AGENDA),
            bar([("◷", "Today"), ("↻", "Routines"), ("◎", "check-in"), ("☰", "Pages"), ("⋯", "More")], "Today"), fab=True)),
        ("Routines tab: what's due, the manager and the charts in one module", phone(hdr("Routines"),
            zone("Due today", ROUTINES[:3]) + listpage(["§Manage", "Habits", "Trackers", "Activities", "Checklists", "§Look back", "Charts and goals"]),
            bar([("◷", "Today"), ("↻", "Routines"), ("◎", "check-in"), ("☰", "Pages"), ("⋯", "More")], "Routines"))),
    ],
    "P4. Drawer only": [
        ("Start: Today with ☰ and a + button, no bar", phone(hdr("Today · Mon 5 Oct", "☰"), zone("Agenda", AGENDA) + zone("Routines", ROUTINES), fab=True)),
        ("The drawer is all the navigation", phone(hdr("Today · Mon 5 Oct", "☰"), zone("Agenda", AGENDA), overlay=drawer(ALL_PLACES))),
    ],
    "P7. Home grid": [
        ("Start: a grid of modules", phone(hdr("Factotum"), '<div class="grid">%s</div>' % "".join(
            '<div><i>%s</i>%s</div>' % (g, e(t)) for g, t in [("◷", "Today"), ("▦", "Week"), ("↻", "Routines"), ("◎", "check-in"),
            ("✎", "Journal"), ("☰", "Pages"), ("↗", "Review"), ("#", "Labels"), ("⧉", "Templates"), ("⚙", "Settings")]), fab=True)),
        ("Each module is one tap, but switching goes back through the grid", phone(hdr("Routines", "‹"), zone("Due today", ROUTINES[:3]) +
            listpage(["§Manage", "Habits", "Trackers", "Activities", "Checklists"]))),
    ],
    "A+. Modules + top rows + ⊞": [
        ("Start: Today, with its own top row (Agenda · Day · Week · Month · Planner)", phone(hdr("Today · Mon 5 Oct"),
            TOPROW(["Agenda", "Day", "Week", "Month", "Planner"]) + zone("Agenda", AGENDA[:3]) + zone("Routines", ROUTINES[:4]),
            bar(A_BAR, "Today"))),
        ("⊞ from anywhere: the capture line, pinned and recent, then every feature by name", phone(hdr("Today · Mon 5 Oct"),
            zone("Agenda", AGENDA[:2]), bar(A_BAR, "All"), overlay=LAUNCHER_SHEET)),
        ("A module opens on its own screens: Routines → Habits · Trackers · Activities · Checklists · Charts", phone(hdr("Routines"),
            TOPROW(["Habits", "Trackers", "Activities", "Checklists", "Charts"]) +
            listpage(["Walk · every day", "Water · 8 a day in blocks", "Gym · Mon Wed Fri", "Read · rolling, every 2 days", "+ New habit"]),
            bar(A_BAR, "Routines"))),
    ],
    "A++. Today · 3 pins · ⊞": [
        ("Start: Today and ⊞ fixed; the three middle slots are pinned (default found by enumeration)", phone(hdr("Today · Mon 5 Oct"),
            TOPROW(["Agenda", "Day", "Week", "Month", "Planner"]) + zone("Agenda", AGENDA[:3]) + zone("Routines", ROUTINES[:4]),
            bar(PIN_BAR, "Today"))),
        ("Pin to the bar: a module (opens with its top row) or a single screen", phone(hdr("Pin to the bar", "‹"),
            zone("Slots", [it("1 · Pages", "module"), it("2 · Week", "module"), it("3 · Ledger", "screen")]) +
            listpage(["§Modules", "Routines", "check-in", "Pages", "Week", "§Screens", "Journal", "Ledger", "Habits", "Trackers", "Charts",
                      "§Pages", "Pin a page from the tree…"]), bar(PIN_BAR, "All"))),
    ],
    "P8. Search first (tree)": [
        ("Start: the tree, Today pinned; the bar is Search, Capture, Menu", phone(hdr("Factotum"), tree(),
            bar([("⌕", "Search"), ("+", "Capture"), ("≡", "Menu")], ""))),
        ("The menu holds the actions", phone(hdr("Factotum"), tree(), bar([("⌕", "Search"), ("+", "Capture"), ("≡", "Menu")], "Menu"),
            overlay=drawer(["§Actions", "Today's journal", "check-in", "Ledger", "Sensory", "This week", "Review", "Settings"], "bottom"))),
    ],
}


def desk(rail_html, title, cols, wide=False):
    return ('<div class="desk">%s<div class="main"><div class="hdr"><b>%s</b><span class="srch">⌕ Search everything <span class="kbd">Ctrl+K</span></span></div>'
            '<div class="cols">%s</div></div></div>') % (rail_html, e(title), cols)

RAIL = ('<div class="rail"><div class="on"><i>◷</i>Today<br><span class="kbd">Ctrl+1</span></div><div><i>▦</i>Week<br><span class="kbd">Ctrl+2</span></div>'
        '<div><i>☰</i>Library<br><span class="kbd">Ctrl+3</span></div><div><i>↗</i>Review<br><span class="kbd">Ctrl+4</span></div>'
        '<div><i>+</i>New<br><span class="kbd">Ctrl+N</span></div><div class="sp"></div><div><i>◐</i>Account</div></div>')
SIDEBAR = '<div class="side">%s</div>' % "".join(
    '<div%s>%s</div>' % (' class="grp"' if x.startswith("§") else (' class="on"' if x == "Today" else ""), e(x.lstrip("§"))) for x in
    ["+ New  (Ctrl+N)", "Today", "§Week", "Day", "Week", "Month", "Planner", "§Routines", "Habits", "Trackers", "Activities", "Checklists",
     "§check-in", "check-in", "Ledger", "Sensory", "§Library", "Journal", "Pages", "Templates", "Road Map", "§Review", "This week",
     "Charts and goals", "§", "Trash", "Settings"])
TODAY_COLS = zone("Agenda", AGENDA) + zone("Routines", ROUTINES, "All routines")
RAIL3 = ('<div class="rail">%s<div class="sp"></div><div><i>⊞</i>All</div><div><i>◐</i>Account</div></div>' % "".join(
    '<div%s><i>%s</i>%s<br><span class="kbd">Ctrl+%d</span></div>' % (' class="on"' if t == "Routines" else "", g, t, i + 1)
    for i, (g, t) in enumerate([("◷", "Today"), ("▦", "Week"), ("↻", "Routines"), ("◎", "check-in"), ("☰", "Pages"), ("↗", "Review")])))
PANEL3 = '<div class="side panel">%s</div>' % "".join(
    '<div%s>%s</div>' % (' class="grp"' if x.startswith("§") else (' class="on"' if x == "Habits" else ""), e(x.lstrip("§")))
    for x in ["§Routines", "Habits", "Trackers", "Activities", "Checklists", "Charts", "Goals", "§", "+ New habit"])
HABITS_COLS = listpage(["Walk · every day", "Water · 8 a day in blocks", "Gym · Mon Wed Fri", "Read · rolling, every 2 days"]) + zone(
    "Walk", [it("Repeats", "every day"), it("Tracker", "yes / no"), it("Reminder", "08:00"), it("Label", "health")])
WIN = {
    "W1. Rail mirrors G+": desk(RAIL, "Today · Mon 5 Oct", TODAY_COLS),
    "W2. Full sidebar": desk(SIDEBAR, "Today · Mon 5 Oct", TODAY_COLS),
    "W3. Module rail + bounded panel": desk(RAIL3 + PANEL3, "Routines · Habits", HABITS_COLS),
}

# ---- page ---------------------------------------------------------------------------------------
CSS = """
:root{--bg:#f4f4f2;--fg:#1c1c1a;--dim:#6b6b66;--line:#cfcfca;--zone:#fff;--zone2:#ebebe7;--hi:#d9d9d4;--bar:#fafaf8;--scrim:rgba(0,0,0,.28)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#17181a;--fg:#e6e5e1;--dim:#9c9a94;--line:#3a3b3f;--zone:#202125;--zone2:#2a2b30;--hi:#34353a;--bar:#1d1e21;--scrim:rgba(0,0,0,.5)}}
:root[data-theme=dark]{--bg:#17181a;--fg:#e6e5e1;--dim:#9c9a94;--line:#3a3b3f;--zone:#202125;--zone2:#2a2b30;--hi:#34353a;--bar:#1d1e21;--scrim:rgba(0,0,0,.5)}
*{box-sizing:border-box}body{margin:0;padding:24px 16px 48px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}
h1{font-size:21px;margin:0 0 4px}h2{font-size:17px;margin:40px 0 4px}p,li{max-width:90ch}.dim,small{color:var(--dim)}
nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}nav.toc a{border:1px solid var(--line);border-radius:999px;padding:3px 10px;color:var(--fg);text-decoration:none;font-size:13px}
.row{display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}.wrap{overflow-x:auto;padding-bottom:6px}
.cap{font-size:12px;color:var(--dim);margin:6px 0 0;max-width:360px}
.phone{position:relative;width:360px;height:740px;border:1px solid var(--line);border-radius:22px;background:var(--bg);display:flex;flex-direction:column;overflow:hidden;flex:none}
.hdr{height:52px;display:flex;align-items:center;gap:8px;padding:0 12px;border-bottom:1px solid var(--line);background:var(--bar);flex:none}
.hdr b{flex:1;font-size:16px}.ic{width:28px;height:28px;border:1px solid var(--line);border-radius:6px;display:grid;place-items:center;font-size:13px;color:var(--dim)}
.body{flex:1;overflow:hidden;padding:10px;display:flex;flex-direction:column;gap:10px}
.zone{background:var(--zone);border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.zone h4{margin:0 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--dim);display:flex}.lk{margin-left:auto;text-transform:none;letter-spacing:0;color:var(--fg)}
.it{display:flex;align-items:center;gap:8px;padding:7px 0;border-top:1px solid var(--line)}.zone .it:first-of-type{border-top:0}
.ck{width:18px;height:18px;border:1.5px solid var(--dim);border-radius:50%;flex:none}.tm{width:46px;color:var(--dim);font-size:12px;flex:none}
.it span.t{flex:1}.btn{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;background:var(--zone2)}
.list div{padding:7px 2px;border-top:1px solid var(--line);white-space:pre}.list div:first-child{border-top:0}.list .grp,.drawer .grp,.side .grp{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--dim);border-top:0;padding-top:10px}
.bar{height:62px;display:flex;border-top:1px solid var(--line);background:var(--bar);flex:none}
.bar div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:11px;color:var(--dim);gap:2px}
.bar div i{font-style:normal;font-size:16px}.bar div.on{color:var(--fg);font-weight:600}
.bar div.plus i{width:44px;height:44px;border-radius:50%;border:1.5px solid var(--fg);display:grid;place-items:center;font-size:22px;color:var(--fg)}
.fab{position:absolute;right:16px;bottom:78px;width:52px;height:52px;border-radius:16px;border:1.5px solid var(--fg);background:var(--zone);display:grid;place-items:center;font-size:24px}
.phone .fab:last-child{bottom:16px}
.scrim{position:absolute;inset:0;background:var(--scrim)}
.drawer{position:absolute;top:0;bottom:0;width:250px;background:var(--zone);border-right:1px solid var(--line);padding:12px;overflow:hidden}.drawer.left{left:0}
.drawer.right{right:0;left:auto;top:52px;bottom:auto;border:1px solid var(--line);border-radius:10px;margin:4px}
.drawer.bottom{left:0;right:0;width:auto;top:auto;bottom:62px;border-radius:16px 16px 0 0;border:1px solid var(--line)}
.drawer div{padding:6px 2px}.drawer.tall{top:70px;overflow:hidden}
.nl{border:1.5px solid var(--fg);border-radius:10px;padding:8px 10px;font-size:14px;margin-bottom:4px}
.tiles{display:flex;flex-wrap:wrap;gap:5px;padding:2px 0 4px!important}.tiles span{border:1px solid var(--line);border-radius:8px;padding:5px 8px;font-size:12px;background:var(--zone2)}
.tabs{flex-wrap:nowrap;overflow-x:auto;flex:none;scrollbar-width:none}.side.panel{width:170px;background:var(--zone)}
.tabs{display:flex;gap:6px}.tabs span{border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12px}.tabs .on{background:var(--hi);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.grid div{background:var(--zone);border:1px solid var(--line);border-radius:12px;height:92px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:12px;gap:4px}.grid i{font-style:normal;font-size:20px}
.desk{width:1100px;height:640px;border:1px solid var(--line);border-radius:10px;display:flex;overflow:hidden;background:var(--bg);flex:none}
.rail{width:76px;border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:10px 0;gap:6px;background:var(--bar)}
.rail div{width:62px;padding:6px 0;border-radius:8px;text-align:center;font-size:11px;color:var(--dim)}.rail div i{display:block;font-style:normal;font-size:16px}.rail div.on{background:var(--hi);color:var(--fg);font-weight:600}.rail .sp{flex:1}
.side{width:200px;border-right:1px solid var(--line);padding:8px 10px;background:var(--bar);overflow:hidden;font-size:13px}.side div{padding:3px 6px;border-radius:6px}.side .on{background:var(--hi);font-weight:600}
.main{flex:1;display:flex;flex-direction:column;min-width:0}.cols{flex:1;display:grid;grid-template-columns:1.3fr 1fr;gap:12px;padding:12px;align-content:start}
.srch{border:1px solid var(--line);border-radius:6px;padding:4px 10px;width:300px;color:var(--dim)}.kbd{font:11px ui-monospace,monospace;border:1px solid var(--line);border-radius:4px;padding:0 4px;color:var(--dim)}
table{border-collapse:collapse;font-size:13px;margin:6px 0 10px}td,th{border-top:1px solid var(--line);padding:4px 8px;text-align:left}th{color:var(--dim);font-weight:600}
.front{display:inline-block;border:1px solid var(--fg);border-radius:999px;padding:0 8px;font-size:12px;margin-left:6px}
"""


def score_table(cand):
    r = n2.evaluate(cand)
    by_name = {s[0]: s for s in n2.SCREENS}
    tail = []
    for name in TAIL:
        _, _, _, area, depth = by_name[name]
        n, _, only_search = n2.steps_for(cand, name, area, depth)
        steps = "search only" if only_search else str(n)
        tail.append("<td>%s</td>" % steps)
    head = ("<table><tr><th>Cost</th><th>Long tail</th><th>Max depth</th><th>Search only</th><th>Reach in 2</th><th>Named in 1</th>"
            "<th>Switch</th><th>Visible</th><th>Largest list</th><th>Start load</th><th>Register</th></tr><tr><td>%.0f</td><td>%.1f</td><td>%d</td>"
            "<td>%d</td><td>%d/%d</td><td>%d</td><td>%.2f</td><td>%d</td><td>%d</td><td>%d</td><td>%.2f</td></tr></table>") % (
        r["cost"], r["tail"], r["max_depth"], len(r["search_only"]), r["reach2"], len(n2.SCREENS), r["named1"], r["switch"],
        r["visible"], r["hub"], r["start_load"], r["register"])
    tails = "<table><tr>%s</tr><tr>%s</tr></table>" % ("".join("<th>%s</th>" % e(t) for t in TAIL), "".join(tail))
    return head + '<p class="dim" style="margin:0">Steps to some long-tail screens:</p>' + tails


def front_of(cands):
    rows = {n: n2.evaluate(c) for n, c in cands.items()}
    return {n for n, r in rows.items() if not any(n2.dominates(o, r) for m, o in rows.items() if m != n)}


def main():
    pf, wf = front_of(n2.PHONE), front_of(n2.WINDOWS)
    order = sorted(n2.PHONE, key=lambda n: n2.evaluate(n2.PHONE[n])["cost"])
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>Factotum navigation mockups</title><style>%s</style></head><body>' % CSS,
             '<h1>Factotum navigation: every candidate</h1>',
             '<p class="dim">These are structure mockups for decision 15, Q2. They show where things live and how many steps they cost, not how they look. '
             'Greys, the system font and the glyphs are placeholders, because the palette, type, icons and wording are still to be scored. '
             'Every candidate uses the same invented sample data. The numbers come from <code>tools/screens/nav_score2.py</code>, '
             '"front" marks the Pareto front, and the candidates are ordered by total weekly cost.</p>',
             '<nav class="toc">%s</nav>' % "".join('<a href="#c%d">%s</a>' % (i, e(n.split(" (")[0])) for i, n in enumerate(order + list(n2.WINDOWS)))]
    for i, name in enumerate(order):
        cand = n2.PHONE[name]
        parts.append('<h2 id="c%d">Phone: %s%s</h2><p>%s</p>' % (i, e(name), '<span class="front">front</span>' if name in pf else "", e(cand["note"])))
        parts.append(score_table(cand))
        parts.append('<div class="wrap"><div class="row">%s</div></div>' % "".join(
            '<div>%s<p class="cap">%s</p></div>' % (ph, e(cap)) for cap, ph in SCREENS[name]))
    for j, (name, cand) in enumerate(n2.WINDOWS.items()):
        parts.append('<h2 id="c%d">Windows: %s%s</h2><p>%s</p>' % (len(order) + j, e(name), '<span class="front">front</span>' if name in wf else "", e(cand["note"])))
        parts.append(score_table(cand))
        parts.append('<div class="wrap">%s</div>' % WIN[name])
    parts.append("""<h2>What these mockups leave out</h2><ul>
<li><b>Look:</b> the palette, type, shapes, density and icons (Q4–Q8). Every grey, size and glyph is a placeholder.</li>
<li><b>Wording:</b> registers are per cluster and set in their tiers (Q9). The words here are placeholders, except "Label", "Log" and "check-in".</li>
<li><b>Prompts that arrive:</b> alarms, clashes, the outcome question, the timer question, burnout.</li>
<li><b>Other screens:</b> the editors, the [+] sheet (shown in <code>frame.html</code>), search results, widgets, the tray, empty states, and anything behind a second tap other than what is drawn.</li>
<li><b>The on-device LLM</b> is not placed in any candidate.</li>
<li><b>The source screenshots</b> are on <code>frame.html</code>, so they are not repeated here.</li>
</ul></body></html>""")
    assert set(n2.PIN_SEARCH["best"][0][3]) == {"Pages (module)", "Week (module)", "ledger (masking)"}, "A++ mockup pins differ from the enumerated best: %s" % (n2.PIN_SEARCH["best"][0][3],)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts))
    print(OUT, "| phone front:", sorted(pf), "| windows front:", sorted(wf))


if __name__ == "__main__":
    main()
