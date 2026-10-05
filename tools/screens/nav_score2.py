"""Navigation re-scoring with every sought screen (owner, 2026-10-05: "compare 5 with the number of
screens"). Writes docs/screens/t0/nav-scores-2.md.

Model. Every screen has a home AREA and a depth inside it. A candidate says what reaching each
area costs and whether that cost holds from anywhere; a screen costs area cost + its depth. An area a
candidate has no path to is 'search only' (it costs search + 1, and is counted). This keeps every
cost derived from a few stated choices instead of ~40 hand-typed numbers.

Weights per week: the owner's cadences (several a day 35, daily 7, weekly 1, when noticed 2).
Assumed, not set by the owner: occasional editing and management = 1 (as weekly); setup and system
screens = 0.25. They are stated in the output.

Objectives, phone and Windows separately:
  cost        sum of weight x (steps + 0.5 when not reachable from anywhere)
  tail        the same, over screens of weight <= 1 only (the long tail)
  max_depth   the deepest screen
  search_only screens with no browsable path
  visible     navigation entries always on screen
  hub         the largest single list of navigation entries (a bar, a drawer, a Browse page, a menu)
  register    1 = no default surface mixes modules of different tone (app-register-layout Step 1d)

    python tools/screens/nav_score2.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "nav-scores-2.md")

# (screen, weekly weight, weight source, area, depth inside the area)
SCREENS = [
    ("capture", 35, "owner", "capture", 0), ("tick a task", 35, "owner", "today", 1), ("search", 35, "owner", "search", 0),
    ("today's agenda", 7, "owner", "today", 0), ("calendar day/week/month", 7, "owner", "calendar", 0),
    ("Log a habit", 7, "owner", "due", 1), ("start/stop a timer", 7, "owner", "due", 1),
    ("tracker reading", 7, "owner", "due", 1), ("tick a checklist", 7, "owner", "due", 1),
    ("ledger (masking)", 7, "owner", "checkin", 1), ("today's journal", 7, "owner", "journal", 0),
    ("open a page", 7, "owner", "pages", 1), ("database view", 7, "owner", "pages", 1), ("canvas", 7, "owner", "pages", 1),
    ("check-in", 2, "owner", "checkin", 1), ("sensory log", 2, "owner", "checkin", 1),
    ("confirm the week (planner)", 1, "owner", "calendar", 1), ("time totals", 1, "owner", "review", 0),
    ("stability trend", 1, "owner", "review", 0), ("tracker detail and charts", 1, "owner", "review", 1),
    ("goals", 1, "owner", "review", 1), ("ledger/sensory history", 1, "owner", "review", 1),
    ("edit an item", 1, "assumed", "today", 1), ("edit one occurrence", 1, "assumed", "calendar", 2),
    ("past journal days", 1, "assumed", "journal", 1), ("manage habits", 1, "assumed", "manage", 0),
    ("manage trackers", 1, "assumed", "manage", 1), ("manage activities", 1, "assumed", "manage", 1),
    ("manage checklists", 1, "assumed", "manage", 1), ("build a saved chart", 1, "assumed", "review", 1),
    ("templates", 1, "assumed", "pages", 1), ("Road Map", 1, "assumed", "pages", 1),
    ("page History", 0.25, "assumed", "pages", 2), ("labels", 0.25, "assumed", "system", 2),
    ("time blocks", 0.25, "assumed", "system", 2), ("calendar links", 0.25, "assumed", "system", 2),
    ("settings", 0.25, "assumed", "system", 1), ("sync folder", 0.25, "assumed", "system", 2),
    ("trash", 0.25, "assumed", "system", 1), ("backup", 0.25, "assumed", "system", 2),
    ("app lock", 0.25, "assumed", "system", 2), ("about", 0.25, "assumed", "system", 1),
]

AREAS = ["capture", "search", "today", "due", "calendar", "checkin", "journal", "pages", "review", "manage", "system"]

# area -> (cost to reach, from anywhere?); None = no browsable path (search only).
def A(**kw):
    return kw

PHONE = {
    "G (as mocked)": dict(note="Bar: Today · Week · [+] · Library · Review; account menu in the header. No place to manage routines.",
        areas=A(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(1, 1), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(1, 1), manage=None, system=(1, 1)),
        visible=7, hub=9, start_load=2, register=0.9),
    "G+ (manage from Today)": dict(note="G, with 'All routines' at the head of Today's routines zone.",
        areas=A(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(1, 1), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(1, 1), manage=(1, 0), system=(1, 1)),
        visible=7, hub=9, start_load=2, register=0.9),
    "A. Module tabs": dict(note="Bar: Today · Habits & tracking (due + manage + charts) · check-in · Pages · More (system).",
        areas=A(capture=(1, 0), search=(1, 1), today=(0, 0), due=(1, 1), calendar=(1, 0), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(1, 1), manage=(1, 1), system=(1, 1)),
        visible=6, hub=8, start_load=1, register=1.0),
    "B. Today hub": dict(note="Bar: Today · Calendar · Pages · Review; Today carries journal and check-in cards. No manage place.",
        areas=A(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(1, 1), checkin=(0, 0), journal=(1, 0),
                pages=(1, 1), review=(1, 1), manage=None, system=(1, 1)),
        visible=6, hub=8, start_load=4, register=0.7),
    "P4. Drawer only": dict(note="Tasks.org: Today is the start (agenda + routines); a drawer lists every place (~12).",
        areas=A(capture=(1, 0), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(2, 1), checkin=(2, 1), journal=(2, 1),
                pages=(2, 1), review=(2, 1), manage=(2, 1), system=(2, 1)),
        visible=3, hub=12, start_load=2, register=0.9),
    "P5. Bar + Browse hub": dict(note="Todoist: Today · Week · [+] · Library · Browse; Browse lists Review, Routines, check-in history, Labels, Templates, Road Map, Trash, Settings.",
        areas=A(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(1, 1), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(2, 1), manage=(2, 1), system=(2, 1)),
        visible=7, hub=10, start_load=2, register=0.9),
    "P6. Bar + drawer": dict(note="G's bar, plus a drawer (header ☰) listing every place incl. Routines, Labels, Templates, Trash, Settings.",
        areas=A(capture=(1, 1), search=(1, 1), today=(0, 0), due=(0, 0), calendar=(1, 1), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(1, 1), manage=(2, 1), system=(2, 1)),
        visible=8, hub=12, start_load=2, register=0.9),
    "P7. Home grid": dict(note="Start = a grid of ~10 module tiles; each module one tap; back to the grid to switch.",
        areas=A(capture=(1, 0), search=(1, 1), today=(1, 0), due=(1, 0), calendar=(1, 0), checkin=(1, 0), journal=(1, 0),
                pages=(1, 0), review=(1, 0), manage=(1, 0), system=(1, 0)),
        visible=12, hub=10, start_load=10, register=1.0),
    "P8. Search first (tree)": dict(note="Obsidian/Notion: Search · Capture · Menu; the tree is the start, Today pinned.",
        areas=A(capture=(1, 1), search=(1, 1), today=(1, 0), due=(1, 0), calendar=(2, 0), checkin=(2, 1), journal=(2, 1),
                pages=(1, 0), review=(2, 0), manage=(2, 0), system=(2, 1)),
        visible=3, hub=11, start_load=1, register=1.0),
}

WINDOWS = {
    "W1. Rail mirrors G+": dict(note="Rail: Today · Week · Library · Review · New (Ctrl+1-4, Ctrl+N), Ctrl+K, system-wide quick add; manage from Today; account menu.",
        areas=A(capture=(1, 1), search=(1, 1), today=(1, 1), due=(1, 1), calendar=(1, 1), checkin=(1, 1), journal=(2, 1),
                pages=(1, 1), review=(1, 1), manage=(2, 1), system=(1, 1)),
        visible=7, hub=9, start_load=2, register=0.9),
    "W2. Full sidebar": dict(note="Sidebar groups named like the phone's places, every sub-view one click: Today; Week (Day, Week, Month, Planner); Routines (Habits, Trackers, Activities, Checklists); check-in (check-in, Ledger, Sensory); Library (Journal, tree, Templates, Road Map); Review; footer Settings, Trash. Ctrl+K, system-wide quick add.",
        areas=A(capture=(1, 1), search=(1, 1), today=(1, 1), due=(1, 1), calendar=(1, 1), checkin=(0, 1), journal=(1, 1),
                pages=(1, 1), review=(1, 1), manage=(0, 1), system=(0, 1)),
        visible=22, hub=22, start_load=2, register=0.9),
}
# W2's area costs of 0 for checkin/manage/system: their sub-views are themselves sidebar entries, so
# a screen's 'depth inside the area' is the one click (check-in, Habits, Settings...).


MANAGE = ["manage habits", "manage trackers", "manage activities", "manage checklists"]
SYSTEM_LIST = ["labels", "trash", "settings", "about"]
# Screens a candidate's hub lists as entries of their own (a drawer, a Browse page, a module tab, the
# account menu): (hub cost, from anywhere, names). Such a screen costs hub + 1, as its mockup draws it.
HUBS = {
    "G (as mocked)": (1, 1, SYSTEM_LIST), "G+ (manage from Today)": (1, 1, SYSTEM_LIST), "B. Today hub": (1, 1, SYSTEM_LIST),
    "A. Module tabs": (1, 1, MANAGE), "P7. Home grid": (1, 0, MANAGE),
    "P6. Bar + drawer": (1, 1, MANAGE + SYSTEM_LIST + ["templates", "Road Map", "ledger (masking)", "sensory log"]),
    "P4. Drawer only": (1, 1, MANAGE + SYSTEM_LIST + ["templates", "Road Map", "ledger (masking)", "sensory log"]),
    "P5. Bar + Browse hub": (1, 1, MANAGE + SYSTEM_LIST + ["templates", "Road Map", "ledger/sensory history"]),
}
for _name, _hub in HUBS.items():
    PHONE[_name]["hub_direct"] = _hub


def steps_for(cand, name, area, depth):
    """(steps, from anywhere, search only?) for one screen in one candidate."""
    hub_cost, hub_any, direct = cand.get("hub_direct", (0, 0, []))
    path = cand["areas"][area]
    if name in direct:
        return hub_cost + 1, bool(hub_any), False
    if path is None:
        return cand["areas"]["search"][0] + 1, True, True
    return path[0] + depth, bool(path[1]), False


def evaluate(cand):
    total = tail = 0.0
    depths, search_only = [], []
    for name, w, _, area, depth in SCREENS:
        steps, anywhere, only_search = steps_for(cand, name, area, depth)
        if only_search:
            search_only.append(name)
        steps = max(steps, 0)
        exp = steps + (0 if anywhere else 0.5)
        total += w * exp
        if w <= 1:
            tail += w * exp
        depths.append((steps, name))
    return {"cost": total, "tail": tail, "max_depth": max(depths)[0], "deepest": max(depths)[1],
            "search_only": search_only, "visible": cand["visible"], "hub": cand["hub"],
            "start_load": cand["start_load"], "register": cand["register"]}


LOW = ("cost", "tail", "max_depth", "visible", "hub", "start_load")


def dominates(a, b):
    sa, sb = len(a["search_only"]), len(b["search_only"])
    no_worse = all(a[k] <= b[k] for k in LOW) and sa <= sb and a["register"] >= b["register"]
    better = any(a[k] < b[k] for k in LOW) or sa < sb or a["register"] > b["register"]
    return no_worse and better


def table(cands, title):
    rows = {n: evaluate(c) for n, c in cands.items()}
    for n, r in rows.items():
        r["by"] = [m for m, o in rows.items() if m != n and dominates(o, r)]
    out = ["## " + title, "",
           "| Candidate | Cost (all) | Long tail | Max depth | Search only | Visible | Largest hub | Start load | Register | Dominated by |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in sorted(rows.items(), key=lambda kv: kv[1]["cost"]):
        out.append("| %s | %.0f | %.1f | %d (%s) | %d | %d | %d | %d | %.2f | %s |" % (
            n, r["cost"], r["tail"], r["max_depth"], r["deepest"], len(r["search_only"]), r["visible"], r["hub"],
            r["start_load"], r["register"], ", ".join(m.split(" ")[0] for m in r["by"]) or "**front**"))
    out += [""] + ["- **%s**: %s%s" % (n, c["note"], (" Search only: " + ", ".join(rows[n]["search_only"]) + ".") if rows[n]["search_only"] else "")
                   for n, c in cands.items()] + [""]
    return out, rows


lines = ["# Navigation, re-scored with every screen",
         "",
         "Generated by `tools/screens/nav_score2.py`. It answers the owner's question of 2026-10-05: five bar slots against about 40 screens.",
         "",
         "**What is scored**",
         "",
         "- Every one of the %d sought screens has a home area and a depth inside it. A candidate states only what reaching each area costs, so every screen's cost is derived." % len(SCREENS),
         "- An area a candidate never reaches is **search only**: it costs a search plus one step, and it is counted.",
         "- **Cost** is Σ weight × steps, with half a step added when a screen is not reachable from anywhere.",
         "- **Long tail** is the same sum over the screens weighing 1 or less a week.",
         "- **Largest hub** is the longest single list of entries: a bar, a drawer, a Browse page or a menu.",
         "",
         "**Weights per week**",
         "",
         "- The owner's: 35 for several a day, 7 for daily, 2 for when noticed, 1 for weekly.",
         "- **Assumed**, not set by the owner: occasional editing and management count as 1, setup and system screens as 0.25.",
         "",
         "Phone and Windows are scored separately: the five-slot limit binds only the phone.",
         ""]
pl, prow = table(PHONE, "Phone")
wl, wrow = table(WINDOWS, "Windows")
lines += pl + wl
lines += ["## Screens and their areas", "", "| Screen | Weight | Area | Depth in area |", "|---|---|---|---|"]
lines += ["| %s | %s (%s) | %s | %d |" % (n, w, src, a, d) for n, w, src, a, d in SCREENS]
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(pl[:len(PHONE) + 4]))
print("\n".join(wl[:len(WINDOWS) + 4]))
