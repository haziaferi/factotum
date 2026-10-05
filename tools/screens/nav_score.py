"""Scores Factotum navigation candidates (decision 15, Q2) and writes docs/screens/t0/nav-scores.md.

Each candidate is a table: for every sought job (jobs.md), the steps it costs on the phone and on
Windows from the start screen, and whether that cost holds from anywhere. The costs follow from the
candidate's stated layout; they are claims to check against its mockup later, the same way
reference.json was measured.

Objectives (no weights needed for the Pareto front):
  cost_phone, cost_windows  sum over jobs of weekly weight x expected steps, where a job not reachable
                            from anywhere costs half a step more (half the time one is elsewhere)
  fixed                     navigation entries always shown (bar/rail + header actions)
  start_load                independent zones on the start screen (what the default surface carries)
  register                  1 = no default surface mixes modules of different tone; lower = mixed,
                            per app-register-layout Step 1d (allowed as zones, but a cost)
Weekly weights are the owner's (2026-10-05): several a day 35, daily 7, weekly 1, when noticed 2.
Rare jobs (settings) are 0.25, an assumption the owner did not set; it barely moves any total.

    python tools/screens/nav_score.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "nav-scores.md")

# job: (weekly weight, cadence label, jobs.md group)
JOBS = {
    "capture":   (35, "several a day", "J1"),
    "tick_task": (35, "several a day", "J4"),
    "search":    (35, "several a day", "J8"),
    "today":     (7, "daily", "J2"),
    "calendar":  (7, "daily", "J2"),
    "habit_log": (7, "daily", "J4"),
    "timer":     (7, "daily", "J4"),
    "reading":   (7, "daily", "J4"),
    "checklist": (7, "daily", "J4"),
    "ledger":    (7, "daily", "J5"),
    "journal":   (7, "daily", "J7"),
    "pages":     (7, "daily (owner)", "J7/J8"),
    "checkin":   (2, "when noticed", "J5"),
    "sensory":   (2, "when noticed", "J5"),
    "plan_week": (1, "weekly", "J6"),
    "lookback":  (1, "weekly (owner)", "J9"),
    "settings":  (0.25, "rare (assumed)", "J10"),
}

# A cost is (phone, windows, anywhere); anywhere=True means the same cost from every screen.
def c(phone, windows=None, anywhere=False):
    return (phone, phone if windows is None else windows, anywhere)

CANDIDATES = {
    "A. Module tabs": {
        "layout": "Bar/rail: Today · Habits & tracking · Check-in · Pages · More. Search icon in every header (Ctrl+K on Windows); capture FAB on Today, a global quick-add hotkey on Windows.",
        "fixed": 6, "start_load": 1, "register": 1.0,
        "costs": dict(capture=c(1, 1, False), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1),
                      habit_log=c(2), timer=c(2), reading=c(2), checklist=c(2), ledger=c(2), journal=c(2),
                      pages=c(1, 1, True), checkin=c(1, 1, True), sensory=c(2), plan_week=c(2), lookback=c(2),
                      settings=c(2)),
    },
    "B. Today hub": {
        "layout": "Start = Today hub in zones: agenda, routines due (habits, readings, checklists, timers), the journal card, a check-in prompt. Bar: Today · Calendar · Pages · Review. Capture FAB everywhere; search in every header.",
        "fixed": 6, "start_load": 4, "register": 0.7,
        "costs": dict(capture=c(1, 1, True), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1, 1, True),
                      habit_log=c(1), timer=c(1), reading=c(1), checklist=c(1), ledger=c(1), journal=c(1),
                      pages=c(1, 1, True), checkin=c(1), sensory=c(2), plan_week=c(2), lookback=c(1, 1, True),
                      settings=c(2)),
    },
    "C. Time + cadence": {
        "layout": "Bar: Today · Week · Journal & pages · Review. Today = agenda + routines due. A global + offers capture and check-in (with ledger and sensory inside the check-in). Journal & pages opens on today's journal.",
        "fixed": 6, "start_load": 2, "register": 0.85,
        "costs": dict(capture=c(1, 1, True), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1, 1, True),
                      habit_log=c(1), timer=c(2), reading=c(2), checklist=c(1), ledger=c(3, 3, True),
                      journal=c(1, 1, True), pages=c(2), checkin=c(2, 2, True), sensory=c(3, 3, True),
                      plan_week=c(1, 1, True), lookback=c(1, 1, True), settings=c(2)),
    },
    "D. Action bar + tree": {
        "layout": "Bar: Search · Capture · Menu (Obsidian/Notion). Start = the tree; modules and pages are tree entries, Today pinned first; the menu holds the daily actions.",
        "fixed": 11, "start_load": 1, "register": 1.0,
        "costs": dict(capture=c(1, 1, True), tick_task=c(2), search=c(1, 1, True), today=c(1), calendar=c(2),
                      habit_log=c(2), timer=c(2), reading=c(2), checklist=c(2), ledger=c(2), journal=c(2, 2, True),
                      pages=c(1), checkin=c(2, 2, True), sensory=c(2, 2, True), plan_week=c(2), lookback=c(2),
                      settings=c(2, 2, True)),
    },
    "E. Tendril (control)": {
        "layout": "Tendril as it ships: Pages · Calendar · Tasks & Habits · Road Map · Settings; Ctrl+K and a quick-add window on Windows only.",
        "fixed": 5, "start_load": 1, "register": 1.0,
        "costs": dict(capture=c(2, 1, False), tick_task=c(2), search=c(2, 1, False), today=c(1), calendar=c(1),
                      habit_log=c(2), timer=c(2), reading=c(3), checklist=c(3), ledger=c(3), journal=c(2, 1, False),
                      pages=c(0), checkin=c(3), sensory=c(3), plan_week=c(2), lookback=c(3), settings=c(1, 1, True)),
    },
    "F. Hybrid: time bar + smart + (journal first)": {
        "layout": "Phone bar: Today · Week · [+] · Library · Review; Windows rail the same with Ctrl+1..4, Ctrl+K search and a system-wide quick-add hotkey. Today = agenda + routines due, all logged in place. [+] = one natural-language line with chips (task/event/reminder, note, reading, timer, check-in, sensory, ledger). Library opens on today's journal, the page tree one tap below. Search in every header.",
        "fixed": 6, "start_load": 2, "register": 0.9,
        "costs": dict(capture=c(1, 1, True), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1, 1, True),
                      habit_log=c(1), timer=c(1), reading=c(1), checklist=c(1), ledger=c(2, 2, True),
                      journal=c(1, 1, True), pages=c(2), checkin=c(2, 2, True), sensory=c(2, 2, True),
                      plan_week=c(1, 1, True), lookback=c(1, 1, True), settings=c(2)),
    },
    "G. Hybrid: time bar + smart + (tree first)": {
        "layout": "As F, but Library opens on the page tree with today's journal pinned first.",
        "fixed": 6, "start_load": 2, "register": 0.9,
        "costs": dict(capture=c(1, 1, True), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1, 1, True),
                      habit_log=c(1), timer=c(1), reading=c(1), checklist=c(1), ledger=c(2, 2, True),
                      journal=c(2, 2, True), pages=c(1, 1, True), checkin=c(2, 2, True), sensory=c(2, 2, True),
                      plan_week=c(1, 1, True), lookback=c(1, 1, True), settings=c(2)),
    },
    "H. Hybrid: hub zones + time bar + smart +": {
        "layout": "As F, but Today also carries the journal card and a check-in prompt, as zones (B's hub on F's frame).",
        "fixed": 6, "start_load": 4, "register": 0.7,
        "costs": dict(capture=c(1, 1, True), tick_task=c(1), search=c(1, 1, True), today=c(0), calendar=c(1, 1, True),
                      habit_log=c(1), timer=c(1), reading=c(1), checklist=c(1), ledger=c(1), journal=c(1),
                      pages=c(2), checkin=c(1), sensory=c(2, 2, True), plan_week=c(1, 1, True),
                      lookback=c(1, 1, True), settings=c(2)),
    },
}


def weekly_cost(costs, device):
    total = 0.0
    for job, (weight, _, _) in JOBS.items():
        phone, windows, anywhere = costs[job]
        steps = phone if device == "phone" else windows
        total += weight * (steps + (0 if anywhere else 0.5))
    return total


def score(name, cand):
    return {"name": name, "cost_phone": weekly_cost(cand["costs"], "phone"),
            "cost_windows": weekly_cost(cand["costs"], "windows"),
            "fixed": cand["fixed"], "start_load": cand["start_load"], "register": cand["register"]}


def dominates(a, b):
    """a is no worse on every objective and better on one (lower costs/fixed/load, higher register)."""
    keys_low = ("cost_phone", "cost_windows", "fixed", "start_load")
    no_worse = all(a[k] <= b[k] for k in keys_low) and a["register"] >= b["register"]
    better = any(a[k] < b[k] for k in keys_low) or a["register"] > b["register"]
    return no_worse and better


scores = [score(n, cd) for n, cd in CANDIDATES.items()]
for s in scores:
    s["dominated_by"] = [o["name"] for o in scores if dominates(o, s)]
front = [s for s in scores if not s["dominated_by"]]

lines = ["# Navigation candidates, scored",
         "",
         "Generated by `tools/screens/nav_score.py`. The inputs are:",
         "",
         "- the owner's cadences (`jobs.md`);",
         "- the reference survey (`reference.md`);",
         "- each candidate's per-job costs, listed below so every one can be challenged.",
         "",
         "**How each objective is computed**",
         "",
         "- **Weekly cost** is Σ weight × steps over the sought jobs, with half a step added when a job is not reachable from anywhere. Lower is better.",
         "- **Fixed** is the number of navigation entries always on screen.",
         "- **Start load** is the number of zones on the start screen.",
         "- **Register** is 1 when no default surface mixes modules of different tone. Lower is worse.",
         "",
         "Weights per week: 35 for several a day, 7 for daily, 2 for when noticed, 1 for weekly. Rare jobs are 0.25, an assumption.",
         "",
         "| Candidate | Weekly cost, phone | Weekly cost, Windows | Fixed | Start load | Register | Dominated by |",
         "|---|---|---|---|---|---|---|"]
for s in sorted(scores, key=lambda s: s["cost_phone"]):
    lines.append("| %s | %.0f | %.0f | %d | %d | %.2f | %s |" % (
        s["name"], s["cost_phone"], s["cost_windows"], s["fixed"], s["start_load"], s["register"],
        ", ".join(n.split(".")[0] for n in s["dominated_by"]) or "**on the front**"))
lines += ["", "**Pareto front:** %s." % ", ".join(s["name"] for s in front), ""]
lines += ["## The candidates and their per-job costs", "",
          "Costs are phone/Windows steps; **\\*** means the same cost from anywhere.", "",
          "| Job | Weekly weight | " + " | ".join(n.split(".")[0] for n in CANDIDATES) + " |",
          "|---|---|" + "|".join("---" for _ in CANDIDATES) + "|"]
for job, (weight, label, group) in JOBS.items():
    cells = []
    for cand in CANDIDATES.values():
        phone, windows, anywhere = cand["costs"][job]
        cells.append(("%d" % phone if phone == windows else "%d/%d" % (phone, windows)) + ("*" if anywhere else ""))
    lines.append("| %s (%s) | %s, %s | %s |" % (job, group, weight, label, " | ".join(cells)))
lines += ["", "**Layouts:**", ""]
lines += ["- **%s**: %s" % (n, cd["layout"]) for n, cd in CANDIDATES.items()]
lines.append("")
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines))
print("\n".join(lines[14:14 + len(scores) + 4]))
