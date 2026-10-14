"""T3 habits, trackers, time, goals, charts and checklists (decision 19), scored as T2 was, a control per part.

    python tools/screens/t3_opt.py habits                 score a part (docs/screens/t3/t3-<part>.json)
    python tools/screens/t3_opt.py page_html scores       t3-options.html, t3-scores.html (fails if a control wins)

Parts:
  pace     T3b.4 the Paced timer sheet, re-compared with Break Down Timer (owner, 2026-10-14)
  measure3 T3b.1d the Measuring list, trackers and activities as one (owner, 2026-10-14), the full space at 12 and 40 items
  acts     T3b.2 the Activities list, taps first: running timers, a past session, Same as last (Chronicle's Last used)
  measure2 T3b.1c the Measuring list with scroll counted, at 12 and 30 items (owner, 2026-10-13): compact rows, folding labels, most used first
  measure  T3b.1b the Measuring list, taps first (owner, 2026-10-13): merged with activities or apart, a control per kind
  trackers T3b.1 the Trackers list: layout, what a row says, what Log does, grouping (owner, 2026-10-13)
  habits2  T3a.1c the Habits list: the optional name, every if as a header (owner, 2026-10-13)
  premise  T3a.2d what the premise box opens (owner, 2026-10-13; axes chosen by the owner)
  hsheet   T3a.2c the New habit sheet, scored from docs/screens/t3/habit-prototype.html (owner, 2026-10-13)
  addsent  T3a.2b adding a habit as an open sentence (owner, 2026-10-13)
  routines T3a.1b the Habits list with routines (owner, 2026-10-13): the preview, how the sequence shows
  addhabit T3a.2 adding a habit (owner, 2026-10-13: score in place against a sheet)
  basics   T3a.1 Habits as Daily basics (owner, 2026-10-13): layout, the energy filter, its mark, done today
  habits   T3.1 the Habits list (Hub › Routines › Habits): how presence shows, grouping, where Log sits, and how a
           counted habit's amount reads

Reuses t2_opt's page helpers (doc, header, desk_doc, the probes) and toast_opt's machinery (Pareto rank sums, the
control gate, the options and scores pages). Phone 360x740 and Windows 1100x660, measured in headless Edge.
References: docs/screens/t3/t3-references.json (Loop Habit Tracker, Tendril), normalised into t3-refs.json here.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import t2_opt as M2  # noqa: E402  (sets toast_opt's globals for T2; reset below for T3)
import toast_opt as T  # noqa: E402

e = kit.e
THUMB = T.THUMB
doc, header, desk_doc, key_of, small_of, seen_count, dclutter = M2.doc, M2.header, M2.desk_doc, M2.key_of, M2.small_of, M2.seen_count, M2.dclutter

# ==== Part habits: T3.1 the Habits list ========================================================================================
"""
  The sample: Tue 13 Oct 2026 (the day of the captures), six placeholder habits. Presence follows SPEC §3.6: the days
  this month, the last date and the usual time, withheld below 3 days; no streaks.
  presence  none (as Tendril's list), count ("9 days in Oct"), last ("Last Sat · usually 07:30"), dots (a dot per day
            of the month so far, filled when logged; an empty dot is a day not logged), count_last (both lines' facts
            on one line)
  group     blocks (under the time block each sits in, as Tendril; Any time last; paused at the foot), flat (manual order)
  log       row (Log, or + for a count, at the row's right, as T1's Today rows), cells (Loop: the last 4 days as cells,
            today's tapped), page (the row opens the habit's page, Log there, then ‹: 3)
  amount    plain ("3 glasses today": Tendril's rule, never a fraction), fraction ("3 of 8", T1's approved Today row)
  Measured: actions and reach to Log the first habit; presence shown (the share of habits whose presence a row states;
  withheld rows excepted) and the marks read for it (a count or a date is 1, dots are one each); guilt marks (marks of
  a day not logged: empty dots of past days, crosses; and a fraction below its number, which reads as a shortfall);
  rows seen, titles cut, clutter, Windows' clutter; whether Log sits where Today's rows have it (T1.2).
  Control: Loop-like with streaks and a score: "streak 4" and "62%" on every row, the last 4 days as ticks and crosses (48 dp cells, as Loop's), flat.
"""
HABITS_SPACE = {"presence": ["none", "count", "last", "dots", "count_last"], "group": ["blocks", "flat"],
                "log": ["row", "cells", "page"], "amount": ["plain", "fraction"]}
TODAY_N = 13   # Tue 13 Oct
# (title, glyph, block, kind, logged days of October so far, last, usual, amount today, number, unit, paused)
HABITS = [
    ("Walk", "↻", "Morning", "yes", {1, 2, 4, 5, 6, 8, 9, 10, 12}, "Mon", "07:30", None, None, None, False),
    ("Meditate", "↻", "Morning", "yes", {3, 7, 11}, "Sun", None, None, None, None, False),
    ("Stretch", "↻", "Midday", "yes", {2, 5, 9, 12, 13}, "today", "12:30", None, None, None, False),
    ("Water", "↻", "Any time", "number", {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}, "today", None, 3, 8, "glasses", False),
    ("Read", "↻", "Evening", "number", {1, 4, 6, 9, 11}, "Sun", "21:00", 0, 20, "pages", False),
    ("Floss", "↻", "Night", "yes", {1, 2}, "2 Oct", None, None, None, None, True),
]
BLOCKS = ["Morning", "Midday", "Afternoon", "Evening", "Night", "Any time"]
BLOCK_TIME = {"Morning": "06:30–09:00", "Midday": "09:00–13:00", "Afternoon": "13:00–18:00", "Evening": "18:00–21:30", "Night": "21:30–23:30", "Any time": ""}

CSS = """
.hrow{display:flex;align-items:center;gap:10px;min-height:56px;border-bottom:1px solid var(--zone2);padding:4px 0}
.hrow .g{width:20px;flex:none;text-align:center;color:var(--dim)}
.hrow .t{flex:1;min-width:0;font-size:15px}.hrow .t .nm{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hrow .sub{display:block;font-size:13px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hrow .logb{flex:none;min-width:56px;min-height:48px;border-radius:24px;box-shadow:inset 0 0 0 1.5px var(--dim);display:grid;place-items:center;font-size:14px;font-weight:600}
.dots{display:flex;gap:3px;margin-top:4px}.dots i{width:7px;height:7px;border-radius:50%;box-shadow:inset 0 0 0 1px var(--dim)}.dots i.on{background:var(--ink);box-shadow:none}
.cells{display:flex;flex:none}.cells span{width:48px;min-height:48px;display:grid;place-items:center;font-size:15px;color:var(--dim)}
.cells span.on{color:var(--ink);font-weight:700}
.chead{display:flex;justify-content:flex-end;font-size:11px;color:var(--dim)}.chead span{width:48px;text-align:center}
.paused .t{opacity:.6}
"""


def hdoc(html, theme="light"):
    return doc(html, theme, CSS)


def presence_html(h, v):
    title, g, block, kind, days, last, usual, amt, num, unit, paused = h
    n = len(days)
    if paused:
        return "Paused"
    p = v["presence"]
    parts = []
    if kind == "number":
        parts.append(("%d of %d" % (amt, num)) if v["amount"] == "fraction" else ("%d %s today" % (amt, unit)))
    if p == "none":
        return " · ".join(parts)
    withheld = n < 3
    cnt = "" if withheld else "%d days in Oct" % n
    lst = "Last %s" % last + (" · usually %s" % usual if (usual and not withheld) else "")
    if p == "count":
        parts.append(cnt)
    elif p == "last":
        parts.append(lst)
    elif p == "count_last":
        parts += [cnt, "last %s" % last]
    return " · ".join(x for x in parts if x)


def dots_html(h):
    days = h[4]
    return '<span class="dots" data-dots="1">%s</span>' % "".join(
        '<i class="%s" data-day="%d"></i>' % ("on" if d in days else ("" if d < TODAY_N else "today"), d) for d in range(1, TODAY_N + 1))


def log_html(h, v):
    if v["log"] == "row" and not h[10]:
        return '<span class="logb" data-tap="Log %s">%s</span>' % (h[0], "+" if h[3] == "number" else "Log")
    if v["log"] == "cells" and not h[10]:
        return '<span class="cells">%s</span>' % "".join(
            '<span class="%s" data-tap="%s" data-cell="%s">%s</span>' % (
                "on" if d in h[4] else "", "Log %s" % h[0] if d == TODAY_N else "Cell %s %d" % (h[0], d), "miss" if (d not in h[4] and d < TODAY_N) else "",
                ("✓" if d in h[4] else "·") if h[3] == "yes" else ("%d" % (h[7] if d == TODAY_N else (h[8] if d in h[4] else 0))))
            for d in range(TODAY_N, TODAY_N - 4, -1))
    return ""


def hrow(h, v):
    sub = presence_html(h, v)
    dots = dots_html(h) if (v["presence"] == "dots" and not h[10]) else ""
    return '<div class="hrow%s" data-tap="Open habit" data-habit="%s"><span class="g">%s</span><span class="t"><span class="nm">%s</span>%s%s</span>%s</div>' % (
        " paused" if h[10] else "", h[0], h[1], kit.ud(e(h[0])), '<span class="sub">%s</span>' % e(sub) if sub else "", dots, log_html(h, v))


def control_row(h):
    streak = {"Walk": 1, "Meditate": 0, "Stretch": 2, "Water": 13, "Read": 0, "Floss": 0}[h[0]]
    pct = round(100 * len(h[4]) / TODAY_N)
    cells = "".join('<span class="%s" data-cell="%s" %s>%s</span>' % ("on" if d in h[4] else "", "" if d in h[4] else "miss",
                    'data-tap="Log %s"' % h[0] if d == TODAY_N else "", "✓" if d in h[4] else "×") for d in range(TODAY_N, TODAY_N - 4, -1))
    return ('<div class="hrow" data-tap="Open habit" data-habit="%s"><span class="t"><span class="nm">%s</span><span class="sub">streak %d · %d%%</span></span>'
            '<span class="cells" style="font-size:12px">%s</span></div>') % (h[0], kit.ud(e(h[0])), streak, pct, cells.replace('width:40px', ''))


def habits_body(v):
    if v.get("control"):
        rows = "".join(control_row(h) for h in HABITS)
        return '<div class="zone">%s</div>' % rows
    head = ""
    if v["log"] == "cells":
        head = '<div class="chead">%s</div>' % "".join("<span>%s</span>" % x for x in ("Tue 13", "Mon 12", "Sun 11", "Sat 10"))
    live = [h for h in HABITS if not h[10]]
    paused = [h for h in HABITS if h[10]]
    if v["group"] == "flat":
        body = "".join(hrow(h, v) for h in live)
    else:
        body = ""
        for b in BLOCKS:
            part = [h for h in live if h[2] == b]
            if part:
                body += '<div class="dayh">%s%s</div>' % (b, (" · " + BLOCK_TIME[b]) if BLOCK_TIME[b] else "") + "".join(hrow(h, v) for h in part)
    body += '<div class="dayh">Paused</div>' + "".join(hrow(h, v) for h in paused)
    return '<div class="zone">%s%s</div>' % (head, body)


def habits_phone(v):
    return kit.phone(kit.header("Habits", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New habit…</span></div>' + habits_body(v), kit.bar("Hub"))


def habits_desk(v, theme="light"):
    inner = habits_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Habits", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme, CSS)


HAB_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var o={dots:0,emptypast:0,miss:0};"
          "document.querySelectorAll('.dots i').forEach(function(i){var r=i.getBoundingClientRect();if(r.bottom>vb)return;o.dots++;"
          "if(!i.classList.contains('on')&&!i.classList.contains('today'))o.emptypast++});"
          "document.querySelectorAll('[data-judge],[data-cell=\"miss\"]').forEach(function(c){var r=c.getBoundingClientRect();if(r.bottom<=vb&&r.height)o.miss++});"
          "var cut=0;document.querySelectorAll('.hrow .nm,.hrow .sub').forEach(function(s){var r=s.getBoundingClientRect();if(r.bottom<=vb&&s.scrollWidth>s.clientWidth+1)cut++});o.cut=cut;return o})()")


def score_habits(v):
    ctl = v.get("control")
    d = hdoc(habits_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-hab-%s" % key_of(v), HAB_JS)
    first = tp.get("Log Walk")
    if ctl or v["log"] in ("row", "cells"):
        log_actions, reach = 1, T.fitts(THUMB, first)
    else:   # page: open the habit, Log there, back
        log_actions, reach = 3, T.fitts(THUMB, tp["Open habit"])
    live = [h for h in HABITS if not h[10]]
    if ctl:
        shown, marks, fraction = 1.0, 3, 0   # a streak, a percentage and seven days per row
    else:
        p = v["presence"]
        stated = [h for h in live if len(h[4]) >= 3 or p in ("last", "dots", "count_last")]
        shown = 0.0 if p == "none" else round(len(stated) / len(live), 3)
        marks = {"none": 0, "count": 1, "last": 1, "dots": TODAY_N, "count_last": 2}[p]
        fraction = sum(1 for h in live if h[3] == "number" and v["amount"] == "fraction" and h[7] < h[8])
    guilt = pr["emptypast"] + pr["miss"] + fraction + (len(live) if ctl else 0)   # the control's streaks and scores rank every row
    return {"log_actions": log_actions, "reach_log": round(reach, 3), "presence_shown": shown, "presence_marks": marks, "guilt_marks": guilt,
            "rows_seen": seen_count(tp, "Open habit"), "cut": pr["cut"], "like_today": 0 if (not ctl and v["log"] == "row") else 1,
            "small": small_of(tp, {"Log %s" % h[0] for h in HABITS}),
            "clutter": T.clutter_of(lambda th: hdoc(habits_phone(v), th)), "desk_clutter": dclutter(lambda th: habits_desk(v, th))}


# ==== Part basics: T3a.1 the Habits list, as Daily basics (owner, 2026-10-13) ====================================================
"""
  Rescored on the owner's definition: habits are very basic daily yes/no things that are easy to forget (make the bed,
  brush teeth, wash the face, shower), held as if-then cues, with the least judgment possible; a clear reference on a
  low day. The first scoring (t3-habits-v1.json) asked how presence shows; here no history is on the list at all.
  Fixed in every option: yes/no only; T1's own Log button at the row's right (owner: "the same as the Today's page");
  the cue is the habit's block (order) and its written cue (wording) (owner's answer c); each habit has an energy level
  (low, mid, high), and a filter shows only what can be handled now: High (the default) shows all, Mid shows low and
  mid, Low shows low (owner, 2026-10-13); it resets to High when the personal day starts, and is one setting for the
  person on every device (PERSONAL). The cue (the "if") sits above the habit's title (owner, 2026-10-13).
  layout  blocks (under the block's name; the cue is the row's second line), flow (one list in the day's order, the cue as
          the second line, no headers), sentence (under the block's name; the row reads "After breakfast, brush teeth")
  filter  chips (Low · Mid · High under the header: 1 tap), switch (one "Low energy only" switch: 1 tap, low only), menu
          (✎ › Energy: 2 actions)
  mark    none, dots (●○○ for low, ●●○ mid, ●●● high at the row's end, before Log), word ("low" in the second line)
  done    fold (a Logged habit folds into "Done today · n", as Today's rows do, decision 15), stay (ticked, in place)
  Measured: judgment marks (anything that reads as history or a miss: streaks, scores, crosses, counts); the share of
  rows whose cue shows; day order (pairs of rows out of the day's order); words read per row; actions and reach to show
  only low-energy habits, and whether the filter can say Mid; reach to Log; likeness to Today's rows (Log, the fold);
  rows seen, titles cut; clutter, Windows' clutter.
  Control: the leading design (blocks, chips, no mark, fold) with history added: "streak 3 · 62%" on every row. The
  first control (a Loop-like list: alphabetical, no cue, no filter, ticks and crosses) reached the front on Calm alone,
  having no cue lines and no filter row to draw; this one isolates the one thing the owner's rule forbids.
"""
BASICS_SPACE = {"layout": ["blocks", "flow", "sentence"], "filter": ["chips", "switch", "menu"], "mark": ["none", "dots", "word"], "done": ["fold", "stay"]}
# (title, cue, block, energy, logged today)
BASICS = [
    ("Make the bed", "After waking", "Morning", "low", True),
    ("Take meds", "With breakfast", "Morning", "low", False),
    ("Brush teeth", "After breakfast", "Morning", "low", False),
    ("Shower", "After the walk", "Morning", "mid", False),
    ("Tidy the desk", "After lunch", "Midday", "mid", False),
    ("Put a wash on", "When I get home", "Afternoon", "high", False),
    ("Wash face", "Before bed", "Night", "low", False),
    ("Floss", "After brushing", "Night", "low", False),
]
BLOCK_ORDER = ["Morning", "Midday", "Afternoon", "Evening", "Night"]
DOTS = {"low": "●○○", "mid": "●●○", "high": "●●●"}

BASICS_CSS = """
.bsub{display:block;font-size:13px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row .t .nm{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.edots{flex:none;font-size:11px;letter-spacing:1px;color:var(--dim);width:34px;text-align:right}
.fchips{display:flex;gap:6px;flex:none;overflow:hidden}
.fchips span.on{background:var(--zone2);color:var(--ink);font-weight:600;box-shadow:none}
.fchips span{min-height:48px;min-width:48px;justify-content:center;display:flex;align-items:center;padding:0 14px;border-radius:999px;font-size:14px;box-shadow:inset 0 0 0 1px var(--zone2);color:var(--dim)}
.eswitch{display:flex;align-items:center;justify-content:space-between;min-height:48px;padding:0 4px;font-size:15px;flex:none}
.eswitch b{width:44px;height:26px;border-radius:13px;background:var(--zone2);display:block;position:relative}
.eswitch b:after{content:"";position:absolute;left:3px;top:3px;width:20px;height:20px;border-radius:50%;background:var(--bg)}
.row.ticked .nm{text-decoration:line-through;color:var(--dim)}
.cgrid{display:flex;flex:none}.cgrid span{width:48px;min-height:48px;display:grid;place-items:center;font-size:15px;color:var(--dim)}
"""


def bdoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS)


def basics_row(h, v):
    title, cue, block, energy, logged = h
    if v["layout"] == "sentence":
        name, sub = "%s, %s" % (cue, title[0].lower() + title[1:]), ""
    else:
        name, sub = title, cue
    if v["mark"] == "word":
        sub = (sub + " · " if sub else "") + energy
    if v.get("history"):   # the control: a streak and a share of days on every row
        sub += ' · <span data-judge="1">streak %d</span> · <span data-judge="1">%d%%</span>' % (len(title) % 5, 40 + (len(title) * 7) % 55)
    mark = '<span class="edots">%s</span>' % DOTS[energy] if v["mark"] == "dots" else ""
    act = '<span class="act" data-tap="Log %s"><span>Log</span></span>' % title if not logged else ""
    subh = '<span class="bsub">%s</span>' % (sub if v.get("history") else e(sub)) if sub else ""
    # the cue (the "if") sits above the habit (owner, 2026-10-13)
    return '<div class="row%s" data-tap="Open habit" data-cue="%s" data-block="%s"><span class="tm kind">↻</span><span class="t">%s<span class="nm">%s</span></span>%s%s</div>' % (
        " ticked" if (logged and v["done"] == "stay") else "", e(cue), block, subh, kit.ud(e(name)), mark, act)


def basics_body(v):
    if v.get("control"):   # the leading design with history added: what the owner's rule forbids, and nothing else
        v = dict(v, layout="blocks", filter="chips", mark="none", done="fold", history=True)
    top = ""
    if v["filter"] == "chips":
        top = '<div class="fchips">%s</div>' % "".join('<span class="%s" data-tap="Energy %s">%s</span>' % ("on" if x == "High" else "", x, x) for x in ("Low", "Mid", "High"))
    elif v["filter"] == "switch":
        top = '<div class="eswitch" data-tap="Energy Low">Low energy only<b></b></div>'
    live = [h for h in BASICS if not (h[4] and v["done"] == "fold")]
    folded = [h for h in BASICS if h[4] and v["done"] == "fold"]
    order = sorted(live, key=lambda h: BLOCK_ORDER.index(h[2]))
    if v["layout"] == "flow":
        body = "".join(basics_row(h, v) for h in order)
    else:
        body, last = "", None
        for h in order:
            if h[2] != last:
                body += '<div class="dayh">%s</div>' % h[2]
                last = h[2]
            body += basics_row(h, v)
    if folded:
        body += '<div class="fold" data-tap="Done today"><span class="t">Done today · %d</span>▸</div>' % len(folded)
    return top + '<div class="zone">%s</div>' % body


def basics_phone(v):
    return kit.phone(kit.header("Habits", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New habit…</span></div>' + basics_body(v), kit.bar("Hub"))


def basics_desk(v, theme="light"):
    inner = basics_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Habits", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme, CSS + BASICS_CSS)


BASICS_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var rows=[],cut=0,miss=0;"
             "document.querySelectorAll('[data-tap=\"Open habit\"]').forEach(function(r){var b=r.getBoundingClientRect();if(!b.height||b.bottom>vb)return;"
             "var t=r.querySelector('.t');rows.push({cue:r.dataset.cue,block:r.dataset.block,text:t?t.innerText:'',cueshown:r.dataset.cue&&t&&t.innerText.indexOf(r.dataset.cue)>=0?1:0});"
             "r.querySelectorAll('.nm,.bsub').forEach(function(s){if(s.scrollWidth>s.clientWidth+1)cut++})});"
             "document.querySelectorAll('[data-judge],[data-cell=\"miss\"]').forEach(function(c){var b=c.getBoundingClientRect();if(b.height&&b.bottom<=vb)miss++});"
             "return {rows:rows,cut:cut,miss:miss}})()")


def score_basics(v):
    ctl = v.get("control")
    d = bdoc(basics_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-basics-%s" % key_of(v), BASICS_JS)
    rows = pr["rows"]
    words = sum(len(r["text"].split()) for r in rows) / max(1, len(rows))
    blocks = [BLOCK_ORDER.index(r["block"]) for r in rows]
    pairs = [(a, b) for i, a in enumerate(blocks) for b in blocks[i + 1:]]
    disorder = sum(1 for a, b in pairs if a > b) / max(1, len(pairs))
    first_log = next((x for x in tp.all if x["name"].startswith("Log ") and x.get("seen")), None)
    vv = dict(v, filter="chips") if ctl else v   # the control carries the leading design's chips
    judgment = pr["miss"]   # marks of history on screen: streaks, shares of days, crosses
    f_actions = {"chips": 1, "switch": 1, "menu": 2}[vv["filter"]]
    f_reach = T.fitts(THUMB, tp["Energy Low"] if "Energy Low" in tp else tp["Edit"])
    f_mid = 1 if vv["filter"] in ("chips", "menu") else 0
    return {"judgment_marks": judgment, "cue_shown": round(sum(r["cueshown"] for r in rows) / max(1, len(rows)), 3), "disorder": round(disorder, 3),
            "words_per_row": round(words, 2), "filter_actions": f_actions, "reach_filter": round(f_reach, 3), "filter_says_mid": f_mid,
            "reach_log": round(T.fitts(THUMB, first_log), 3) if first_log else 9,
            "like_today": 0 if (ctl or v["done"] == "fold") else 1, "rows_seen": len(rows), "cut": pr["cut"],
            "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Log ", "Energy "))}),
            "clutter": T.clutter_of(lambda th: bdoc(basics_phone(v), th)), "desk_clutter": dclutter(lambda th: basics_desk(v, th))}


# ==== Part addhabit: T3a.2 adding a habit (owner, 2026-10-13: score both forms) ===================================================
"""
  The fields, in the owner's order of things: the habit's name; If (its cue, shown above it in the list); Block (its
  order); Energy (Low, Mid, High); Repeat (Every day, or chosen days); Reminder (Off; at the block's start or at a set
  time); Label; Notes. Habits are yes/no, so there is no amount.
  form   inplace (the T1.3 capture line takes the name; the new row then grows in place in the list with its fields,
         each change kept as made, as an item's page does, T2), sheet (a dedicated sheet over the list with every field
         and Cancel and Add, as Tendril's Add habit; leaving without Add loses it)
  cue    text (a free text field, "If…"), suggest (anchors as chips under the field: After waking, After breakfast, After
         lunch, When I get home, Before bed; and Write your own)
  block  chips (Morning, Midday, Afternoon, Evening, Night), from_cue (a chosen anchor sets the block, shown on the Block
         line and changeable; a written cue leaves it to a tap)
  Walked: adding "Brush teeth", after breakfast, Morning, Low energy, every day: taps (typing excluded), the times the
  keyboard opens, reach to each target in order (Fitts from the thumb), fields seen without scrolling, the list's rows
  still seen (context), lost on leaving, likeness to an item's page; clutter, Windows' clutter.
  Control: Tendril's sheet as it is, cue last: the name, Schedule (Since last check-in, On the calendar), Every 1 day,
  Where (six block chips and At a set time), Counts something, Area, a Note, and the cue as a last free text field,
  Cancel and Add at the foot.
"""
ADD_SPACE = {"form": ["inplace", "sheet"], "cue": ["text", "suggest"], "block": ["chips", "from_cue"]}
ANCHORS = [("After waking", "Morning"), ("After breakfast", "Morning"), ("After lunch", "Midday"), ("When I get home", "Afternoon"), ("Before bed", "Night")]

ADD_CSS = """
.achips{display:flex;flex-wrap:wrap;gap:6px;padding:4px 0 8px 40px}
.achips span{min-height:40px;min-width:48px;justify-content:center;padding:0 12px;border-radius:999px;box-shadow:inset 0 0 0 1px var(--zone2);display:flex;align-items:center;font-size:13px;color:var(--ink)}
.achips span.on{background:var(--zone2);font-weight:600;box-shadow:none}
.achips.tall span{min-height:48px}
.xp .achips span{box-shadow:inset 0 0 0 1px var(--dim)}
.asheet .amid{flex:1;min-height:0;overflow:hidden}
.fld .v small{display:block;color:var(--dim);font-size:12px}
.asheet{position:absolute;left:0;right:0;bottom:0;top:96px;background:var(--bg);border-radius:20px 20px 0 0;box-shadow:0 -6px 24px rgba(0,0,0,.18);padding:8px 14px;overflow:hidden;z-index:30;display:flex;flex-direction:column}
.asheet .afoot{display:flex;justify-content:flex-end;gap:8px;margin-top:auto;padding:8px 0}
.asheet .afoot span{min-height:48px;min-width:72px;display:grid;place-items:center;font-weight:600;font-size:15px;border-radius:24px}
.asheet .afoot span.add{background:var(--ink);color:var(--bg)}
.atitle{font-size:20px;font-weight:600;padding:6px 4px 8px;border-bottom:1px solid var(--zone2)}
"""


def adoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + ADD_CSS)


def add_fields(v):
    """The fields of a new habit, after "Brush teeth" is in: If, Block, Energy, Repeat, Reminder, Label, Notes."""
    out = []
    if v["cue"] == "suggest":
        out.append('<div class="fld" data-tap="F If"><i>?</i><span class="v">If…<small>Choose or write when it comes</small></span></div>')
        out.append('<div class="achips tall">%s</div>' % "".join('<span data-tap="Cue %s">%s</span>' % (a, a) for a, _ in ANCHORS[:4]) + "")
        out[-1] = out[-1][:-len("</div>")] + '<span data-tap="Cue own">Write your own…</span></div>'
    else:
        out.append('<div class="fld" data-tap="Cue own"><i>?</i><span class="v" style="color:var(--dim)">If… (After breakfast)</span></div>')
    if v["block"] == "chips":
        out.append('<div class="fld"><i>◷</i><span class="v">Block</span></div><div class="achips tall">%s</div>' % "".join(
            '<span data-tap="Block %s">%s</span>' % (b, b) for b in BLOCK_ORDER))
    else:
        out.append('<div class="fld" data-tap="Block"><i>◷</i><span class="v">Block<small>Set by the If, or tap to choose</small></span></div>')
    out.append('<div class="fld"><i>◔</i><span class="v">Energy</span></div><div class="achips tall">%s</div>' % "".join(
        '<span data-tap="Energy %s">%s</span>' % (x, x) for x in ("Low", "Mid", "High")))
    out.append('<div class="fld" data-tap="F Repeat"><i>↻</i><span class="v">Every day</span></div>')
    out.append('<div class="fld unset" data-tap="F Reminder"><i>◴</i><span class="v">No reminder</span></div>')
    out.append('<div class="fld unset" data-tap="F Label"><i>●</i><span class="v">Add a label</span></div>')
    out.append('<div class="fld unset" data-tap="F Notes"><i>¶</i><span class="v">Add notes</span></div>')
    return "".join(out)


def addhabit_phone(v):
    base = basics_phone({"layout": "blocks", "filter": "chips", "mark": "none", "done": "fold"})
    if v.get("control"):
        form = ('<div class="asheet"><div class="atitle" data-tap="Title">Brush teeth</div><div class="amid">'
                '<div class="fld"><i></i><span class="v">Schedule</span></div><div class="achips tall"><span class="on">Since last check-in</span><span>On the calendar</span></div>'
                '<div class="fld"><i></i><span class="v">Every 1 · day · week · month</span></div>'
                '<div class="fld"><i></i><span class="v">Where</span></div><div class="achips tall">%s<span>At a set time…</span></div>'
                '<div class="fld"><i></i><span class="v">Counts something</span></div><div class="fld"><i></i><span class="v">Area</span></div>'
                '<div class="fld"><i></i><span class="v">Note · Optional</span></div><div class="fld" data-tap="Cue own"><i></i><span class="v">If…</span></div></div>'
                '<div class="afoot"><span data-tap="Cancel">Cancel</span><span class="add" data-tap="Add">Add</span></div></div>') % "".join(
                    '<span data-tap="Block %s">%s</span>' % (b, b) for b in ["Any time"] + BLOCK_ORDER)
        return base[:-len("</div>")] + form + "</div>"
    if v["form"] == "sheet":
        form = '<div class="asheet"><div class="atitle" data-tap="Title">Brush teeth</div><div class="amid">%s</div><div class="afoot"><span data-tap="Cancel">Cancel</span><span class="add" data-tap="Add">Add</span></div></div>' % add_fields(v)
        return base[:-len("</div>")] + form + "</div>"
    # in place: the new row sits in Any time until its block is set, grown with its fields
    own = ('<div class="row" data-tap="Close"><span style="width:4px;flex:none"></span><span class="t"><span class="nm">%s</span></span>%s</div>' % (
        kit.ud("Brush teeth"), kit.icon_button("🗑", "Delete")))
    xp = '<div class="xp">%s%s</div>' % (own, add_fields(v))
    i = base.index('<div class="dayh">Morning</div>')
    return base[:i] + xp + base[i:]


def score_addhabit(v):
    ctl = v.get("control")
    d = adoc(addhabit_phone(v))
    tp = T.taps(d)
    names = [x["name"] for x in tp.all if x.get("seen")]
    seq = []                                   # the targets tapped, in order, after the name is typed
    keyboard = 1                               # the name
    if ctl:
        seq = ["Block Morning", "Cue own", "Add"]
        keyboard += 1
        energy = 99                            # no energy field
    else:
        if v["cue"] == "suggest":
            seq.append("Cue After breakfast")
        else:
            seq.append("Cue own")
            keyboard += 1
        if v["block"] == "chips" or v["cue"] == "text":
            seq.append("Block Morning" if v["block"] == "chips" else "Block")
            if v["block"] == "from_cue":
                seq.append("Block Morning")    # a written cue: open the block line, then choose
        seq.append("Energy Low")
        if v["form"] == "sheet":
            seq.append("Add")
        energy = 1
    taps = 1 + 1 + len(seq)                    # New habit…, the name's ✓ (inplace) or the sheet's opening, then the sequence
    found = [tp[n] for n in seq if n in tp]
    hidden = sum(1 for n in seq if n in tp and not tp[n].get("seen")) + sum(1 for n in seq if n not in tp and n != "Block Morning")
    reach = sum(T.fitts(THUMB, x) for x in found) / max(1, len(found))
    fields_seen = sum(1 for x in tp.all if x.get("seen") and (x["name"].startswith("F ") or x["name"].startswith(("Cue", "Block", "Energy"))))
    context = seen_count(tp, "Open habit")
    lost = 1 if (ctl or v["form"] == "sheet") else 0
    return {"taps": taps, "keyboard": keyboard, "reach": round(reach, 3), "hidden_targets": hidden, "energy_field": energy, "fields_seen": fields_seen,
            "context_rows": context, "lost_on_back": lost, "like_item_page": 0 if (not ctl and v["form"] == "inplace") else 1,
            "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Cue", "Block", "Energy", "Add", "Cancel"))}),
            "clutter": T.clutter_of(lambda th: adoc(addhabit_phone(v), th)),
            "desk_clutter": dclutter(lambda th: desk_doc("Hub", "Habits", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % (
                addhabit_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]), th, CSS + BASICS_CSS + ADD_CSS))}


# ==== Part routines: T3a.1b the Habits list with routines (owner, 2026-10-13) ===================================================
"""
  A routine (named by the person) carries the if-then sentence and its time; its habits are ordered steps under it. A
  habit outside any routine keeps its own sentence (its "if" above it, T3a.1). Routine checklists merged in. Fixed from
  the approvals: energy chips with High on by default; T1's Log button; a Logged step folds (as Today); with a lower
  energy level the steps above it hide and the header says how many show.
  preview  none, steps ("4 steps"), energy ("4 steps · up to Mid"), time ("4 steps · about 8 min", from each habit's
           duration)
  seq      line (a thin line joins the steps down the left), numbers (1, 2, 3 before each step), plain (rows only)
  Measured: judgment marks; what the header forecasts (facts: steps, energy, time) and whether the order is marked;
  words per row; rows seen, titles cut; clutter, Windows' clutter; and on the Low-energy drawing, whether the header
  says how many steps show.
  The sentence line shows only the parts that are set (owner, 2026-10-13): the if; the days when they are chosen
  ("every day" is the default and is not written); a set time ("08:30") or a window ("22:00–23:00").
  Control: the routine as a checklist with progress: "1/4 done · 25%" under its name, the steps plain.
  No kind glyph on any row (owner, 2026-10-13): every row on the Habits page is a habit; the mark that tells kinds
  apart stays where kinds mix (Today, the Day screen, search).
"""
ROUT_SPACE = {"preview": ["none", "steps", "energy", "time"], "seq": ["line", "numbers", "plain"]}
# a routine: (name, sentence, block, [(habit, energy, minutes, logged)]); a lone habit: (None, if, block, [(habit, ...)])
ROUTINES = [
    ("Morning routine", "After waking", "Morning", [("Make the bed", "low", 2, True), ("Wash face", "low", 2, False),
                                                              ("Brush teeth", "low", 3, False), ("Take meds", "low", 1, False)]),
    (None, "After the walk · 08:30", "Morning", [("Shower", "mid", 15, False)]),
    (None, "After lunch", "Midday", [("Tidy the desk", "mid", 10, False)]),
    (None, "When I get home · Mon, Thu", "Afternoon", [("Put a wash on", "high", 10, False)]),
    ("Evening wind-down", "Before bed · 22:00–23:00", "Night", [("Lay out clothes", "mid", 5, False), ("Floss", "low", 2, False), ("Set the alarm", "low", 1, False)]),
]
LEVEL = {"low": 0, "mid": 1, "high": 2}
ROUT_CSS = """
.rhead{display:flex;align-items:flex-end;gap:8px;padding:10px 4px 2px}.rhead .rn{font-size:15px;font-weight:600}
.rhead .rs{display:block;font-size:12px;color:var(--dim)}.rhead .rp{margin-left:auto;font-size:12px;color:var(--dim);white-space:nowrap}
.rsteps{position:relative}.rsteps.joined:before{content:"";position:absolute;left:21px;top:14px;bottom:14px;width:1.5px;background:var(--dim);opacity:.5}
.row .num{width:20px;flex:none;text-align:center;color:var(--dim);font-size:13px}
"""


def rdoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + ROUT_CSS)


def step_row(h, i, v):
    title, energy, mins, logged = h
    # no kind glyph on the Habits page: every row is a habit (owner, 2026-10-13); the mark belongs where kinds mix
    lead = '<span class="num">%d</span>' % (i + 1) if v["seq"] == "numbers" else '<span class="num"></span>'
    return '<div class="row" data-tap="Open habit" data-step="1"><span style="width:8px;flex:none"></span>%s<span class="t"><span class="nm">%s</span></span><span class="act" data-tap="Log %s"><span>Log</span></span></div>' % (
        lead, kit.ud(e(title)), title)


def routines_body(v, level="high"):
    ctl = v.get("control")
    out = []
    for name, sentence, block, steps in ROUTINES:
        fits = [h for h in steps if LEVEL[h[1]] <= LEVEL[level]]
        live = [h for h in fits if not h[3]]
        if name is None:   # a lone habit: its "if" above it, as T3a.1
            for h in live:
                out.append('<div class="row" data-tap="Open habit"><span class="t" style="padding-left:4px"><span class="bsub">%s</span><span class="nm">%s</span></span>'
                           '<span class="act" data-tap="Log %s"><span>Log</span></span></div>' % (e(sentence), kit.ud(e(h[0])), h[0]))
            continue
        if ctl:
            done = sum(1 for h in steps if h[3])
            prev = '<span data-judge="1">%d/%d done</span> · <span data-judge="1">%d%%</span>' % (done, len(steps), round(100 * done / len(steps)))
        else:
            n = len(fits)
            shown = "%d of %d steps" % (n, len(steps)) if n < len(steps) else "%d steps" % n
            top = max((h[1] for h in fits), key=lambda x: LEVEL[x]) if fits else "low"
            prev = {"none": "" if n == len(steps) else shown, "steps": shown, "energy": "%s · up to %s" % (shown, top.capitalize()),
                    "time": "%s · about %d min" % (shown, sum(h[2] for h in fits))}[v["preview"]]
        out.append('<div class="rhead" data-routine="%s"><span><span class="rn">%s</span><span class="rs">%s</span></span><span class="rp" data-facts="%d">%s</span></div>' % (
            name, kit.ud(e(name)), e(sentence), 0 if ctl else {"none": 0, "steps": 1, "energy": 2, "time": 2}[v["preview"]], prev))
        cls = "rsteps joined" if (not ctl and v["seq"] == "line") else "rsteps"
        out.append('<div class="%s">%s</div>' % (cls, "".join(step_row(h, i, v if not ctl else dict(v, seq="plain")) for i, h in enumerate(live))))
    done_n = sum(1 for _, _, _, st in ROUTINES for h in st if h[3])
    out.append('<div class="fold" data-tap="Done today"><span class="t">Done today · %d</span>▸</div>' % done_n)
    chips = '<div class="fchips">%s</div>' % "".join('<span class="%s" data-tap="Energy %s">%s</span>' % ("on" if x.lower() == level else "", x, x) for x in ("Low", "Mid", "High"))
    return chips + '<div class="zone">%s</div>' % "".join(out)


def routines_phone(v, level="high"):
    return kit.phone(kit.header("Habits", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New habit…</span></div>' + routines_body(v, level), kit.bar("Hub"))


def routines_desk(v, theme="light"):
    inner = routines_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Habits", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme, CSS + BASICS_CSS + ROUT_CSS)


ROUT_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var o={rows:0,words:0,cut:0,judge:0,facts:0,heads:0,says_hidden:0};"
           "document.querySelectorAll('[data-tap=\"Open habit\"]').forEach(function(r){var b=r.getBoundingClientRect();if(!b.height||b.bottom>vb)return;o.rows++;"
           "var t=r.querySelector('.t');o.words+=t?t.innerText.split(/\\s+/).filter(Boolean).length:0;r.querySelectorAll('.nm,.bsub').forEach(function(s){if(s.scrollWidth>s.clientWidth+1)o.cut++})});"
           "document.querySelectorAll('.rhead').forEach(function(h){var b=h.getBoundingClientRect();if(b.bottom>vb)return;o.heads++;var p=h.querySelector('.rp');"
           "o.facts+=parseInt(p.dataset.facts||'0');if(/ of /.test(p.innerText))o.says_hidden++;o.words+=h.innerText.split(/\\s+/).filter(Boolean).length});"
           "document.querySelectorAll('[data-judge]').forEach(function(j){var b=j.getBoundingClientRect();if(b.height&&b.bottom<=vb)o.judge++});return o})()")


def score_routines(v):
    ctl = v.get("control")
    d = rdoc(routines_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-rout-%s" % key_of(v), ROUT_JS)
    low = T.probe(rdoc(routines_phone(v, "low")), "t3-rout-low-%s" % key_of(v), ROUT_JS)
    units = pr["rows"] + pr["heads"]
    return {"judgment_marks": pr["judge"], "forecast_facts": round(pr["facts"] / max(1, pr["heads"]), 2),
            "order_marked": 0 if ctl else (1 if v["seq"] in ("line", "numbers") else 0),
            "low_says_hidden": 1 if low["says_hidden"] else 0, "words_per_row": round(pr["words"] / max(1, units), 2),
            "rows_seen": pr["rows"], "cut": pr["cut"],
            "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Log ", "Energy "))}),
            "clutter": T.clutter_of(lambda th: rdoc(routines_phone(v), th)), "desk_clutter": dclutter(lambda th: routines_desk(v, th))}


# ==== Part addsent: T3a.2b adding a habit as an open sentence (owner, 2026-10-13) ===============================================
"""
  The owner's sentence: [If/After/Before/When/During] [premise] then [habit], [every day / days of the week], [no set
  time / at a time / from a time to a time]. A routine carries its own sentence; a habit put in a routine inherits it.
  Its words are tappable as in T1's approved When sheet (repeat_opt's .tok: underlined, 48 dp targets).
  form    when (T1's When sheet pattern: a fixed-height sheet, the sentence pinned at its foot, the tapped word's chooser
          above it), inplace (the new row grows in the list with the sentence inside it; a tapped word's chooser opens
          under the sentence), fields (the earlier in-place form with fields, T3a.2's leader, as the baseline)
  energy  sentence ("…, low energy" is a word of the sentence), chips (Low · Mid · High under it)
  routine sentence ("…, in Morning routine", a word opening the routines and New routine), row (a line of its own)
  Walked: adding "Brush teeth" into Morning routine, Low (the routine sets after waking, every day, no set time; so
  the habit's own if is not asked): taps (typing excluded), keyboards, reach in order, hidden targets, the sentence
  reads whole (the rule as one line a person can check), lost on leaving, likeness to T1's When sheet, clutter.
  A second walk: a lone habit, "After breakfast then floss, Mon Wed Fri, at 08:30, Low": taps and keyboards.
  Control: Tendril's sheet as it is, the cue last (as in T3a.2).
"""
SENT_SPACE = {"form": ["when", "inplace", "fields"], "energy": ["sentence", "chips"], "routine": ["sentence", "row"]}
SENT_CSS = """
.sent{font-size:17px;line-height:48px}.sent .tok{display:inline-flex;min-height:48px;align-items:center;justify-content:center;padding:0 2px;min-width:48px}
.sent .tok b{font-weight:600;text-decoration:underline;text-decoration-color:var(--dim);text-underline-offset:4px}
.wsheet{position:absolute;left:0;right:0;bottom:0;height:560px;background:var(--bg);border-radius:20px 20px 0 0;box-shadow:0 -6px 24px rgba(0,0,0,.18);padding:8px 14px;z-index:30;display:flex;flex-direction:column}
.wsheet .choose{flex:1;min-height:0;overflow:hidden}.wsheet .foot{border-top:1px solid var(--zone2);padding-top:4px}
.wsheet .ur{display:flex;gap:8px;font-size:13px;color:var(--dim)}.wsheet .ur span{min-height:48px;min-width:48px;display:grid;place-items:center}
.wsheet .achips{padding-left:0}.xp .achips{padding-left:4px}
.clab{font-size:12px;color:var(--dim);letter-spacing:.04em;text-transform:uppercase;padding:6px 0 2px}
"""


def sdoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + ADD_CSS + ROUT_CSS + SENT_CSS)


def tok(name, word):
    return '<span class="tok" data-tap="Tok %s"><b>%s</b></span>' % (name, word)


def sentence_html(v, lone=False):
    """The habit's sentence, as typed so far: the habit is in, the routine (or the lone habit's if) to set."""
    if lone:
        s = "%s %s then %s, %s, %s" % (tok("conn", "After"), tok("premise", "breakfast"), tok("habit", "floss"), tok("days", "Mon, Wed, Fri"), tok("time", "at 08:30"))
    else:
        s = "%s %s then %s, %s, %s" % (tok("conn", "If"), tok("premise", "…"), tok("habit", "brush teeth"), tok("days", "every day"), tok("time", "no set time"))
    if v["energy"] == "sentence":
        s += ", " + tok("energy", "low energy" if lone else "energy…")
    if v["routine"] == "sentence" and not lone:
        s += ", " + tok("routine", "in a routine…")
    return '<div class="sent">%s.</div>' % s


def sent_extras(v, lone=False):
    out = ""
    if v["energy"] == "chips":
        out += '<div class="clab">Energy</div><div class="achips tall">%s</div>' % "".join('<span data-tap="Energy %s">%s</span>' % (x, x) for x in ("Low", "Mid", "High"))
    if v["routine"] == "row" and not lone:
        out += '<div class="fld" data-tap="Routine"><i>≡</i><span class="v">Routine<small>None · tap to put it in one</small></span></div>'
    return out


def routine_chooser():
    return '<div class="clab">Put it in</div><div class="achips tall">%s</div>' % "".join(
        '<span data-tap="R %s">%s</span>' % (r, r) for r in ("Morning routine", "Evening wind-down", "New routine…"))


def addsent_phone(v, lone=False):
    base = routines_phone({"preview": "none", "seq": "plain"})
    if v.get("control"):
        return addhabit_phone({"control": True})
    if v["form"] == "fields":
        return addhabit_phone({"form": "inplace", "cue": "suggest", "block": "from_cue"})
    chooser = routine_chooser() if not lone else ""
    if v["form"] == "when":
        sheet = ('<div class="wsheet"><div class="choose">%s%s</div><div class="foot">%s<div class="ur"><span data-tap="Undo">Undo</span><span data-tap="Redo">Redo</span></div></div></div>') % (
            chooser, sent_extras(v, lone), sentence_html(v, lone))
        return base[:-len("</div>")] + sheet + "</div>"
    own = '<div class="row" data-tap="Close"><span class="t" style="padding-left:4px"><span class="nm">%s</span></span>%s</div>' % (kit.ud("Brush teeth" if not lone else "Floss"), kit.icon_button("🗑", "Delete"))
    xp = '<div class="xp">%s%s%s%s</div>' % (own, sentence_html(v, lone), sent_extras(v, lone), chooser)
    i = base.index('<div class="rhead"')
    return base[:i] + xp + base[i:]


def walk(v, lone=False):
    """Taps after the name is typed in the capture line, and keyboards, for each walk."""
    if v.get("control"):
        return (1 + 1 + 4, 2) if not lone else (1 + 1 + 5, 2)   # New habit, Add; block, cue, Add (+ set time); the cue typed
    if v["form"] == "fields":
        # T3a.2's walk; a lone habit: New habit, ✓, the cue field (typed), the block line and Morning, Low, the Repeat
        # field and Mon, Wed, Fri, the Reminder/time field, At and the dial: the same days and time as the sentence's
        return (4, 1) if not lone else (2 + 1 + 2 + 1 + 4 + 3, 2)
    taps = 2   # New habit…, the name's ✓
    kb = 1
    if not lone:
        taps += 1 + 1                     # the routine word (or row), then Morning routine: it sets the if, days, time
        taps += 1 if v["energy"] == "chips" else 2   # the chip; or the energy word, then Low
    else:
        taps += 2 + 1                     # the connective, then After; the premise
        kb += 1                           # the premise typed
        taps += 1 + 3                     # the days word, then Mon, Wed, Fri
        taps += 1 + 2                     # the time word, then At, the dial (hour, minute: counted as 1 for the typed field)
        taps += 1 if v["energy"] == "chips" else 2
    return taps, kb


def score_addsent(v):
    ctl = v.get("control")
    d = sdoc(addsent_phone(v))
    tp = T.taps(d)
    taps, kb = walk(v)
    taps2, kb2 = walk(v, True)
    want = ["R Morning routine"] + (["Energy Low"] if (not ctl and v.get("energy") == "chips" and v.get("form") != "fields") else [])
    found = [tp[n] for n in want if n in tp]
    hidden = sum(1 for n in want if n in tp and not tp[n].get("seen"))
    reach = sum(T.fitts(THUMB, x) for x in found) / max(1, len(found)) if found else 3.5
    reads = 1 if (not ctl and v["form"] in ("when", "inplace") and v["energy"] == "sentence" and v["routine"] == "sentence") else (0.5 if (not ctl and v["form"] in ("when", "inplace")) else 0)
    return {"taps": taps, "keyboards": kb, "taps_lone": taps2, "keyboards_lone": kb2, "reach": round(reach, 3), "hidden_targets": hidden,
            "sentence_reads": reads, "lost_on_back": 0 if (not ctl) else 1, "like_when": 0 if (not ctl and v["form"] == "when") else 1,
            "context_rows": seen_count(tp, "Open habit"),
            "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Tok ", "Energy", "R ", "Undo", "Redo"))}),
            "clutter": T.clutter_of(lambda th: sdoc(addsent_phone(v), th)), "desk_clutter": dclutter(lambda th: desk_doc("Hub", "Habits",
                '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % addsent_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")],
                th, CSS + BASICS_CSS + ADD_CSS + ROUT_CSS + SENT_CSS))}


# ==== Part hsheet: T3a.2c the New habit sheet, from its prototype (owner, 2026-10-13) ==============================================
"""
  docs/screens/t3/habit-prototype.html, built on T1.5 + T1.6's approved When sheet: the sentence held at the foot, the
  sheet growing upward only, choosers above, Undo and Redo, the readout; "Available ifs" a small line above the sentence;
  no routine word. Its states are rendered from the prototype itself (as when_page.py renders the When sheet).
  blank  inline (the blanks are text boxes in the sentence), chooser (a blank is a word that opens a text box above)
  Walked (taps, typing excluded; counted along the prototype's own controls):
    join: "Open the curtains" into After waking, Low: Available ifs, the if, [the habit's box: inline it is focused
          after the if is chosen; chooser 1], the energy word, Low, Add.
    new:  "After breakfast then floss, Mon Wed Fri, at 08:30, Low": the connective and After (2), the premise box (1),
          the habit box (1), the days word and Mo, We, Fr (4), the time word, At, the hour and the minutes (4), the energy
          word and Low (2), Add (1).
  Measured on the rendered states: whether the foot's bottom stays at one pixel in every state (the When sheet's rule),
  the tiered gate (tiered_small: 48 dp for primary actions, 24 dp for a chooser's controls), the default state's clutter.
  Control: Tendril's Add habit sheet. It has no weekdays and no energy, so the new walk cannot be done (99).
"""
HSHEET_SPACE = {"blank": ["inline", "chooser"]}
PROTO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs", "screens", "t3", "habit-prototype.html")
ONLY_PHONE = ("<style>body{padding:0!important}h1,.dim,.side{display:none!important}.wrap{display:block}"
              ".phone{border-radius:0;box-shadow:none}</style>")
HSTATES = [
    ("empty", "Opened: the blanks waiting, Available ifs above the sentence", ""),
    ("ifs", "Available ifs open: it grows upward; choosing one fills the if, its days and its time", "toggleIfs()"),
    ("joined", "After waking chosen, the habit written: it joins as step 5", "pickIf(0);setText('habit','Open the curtains')"),
    ("days", "A new if: the days word tapped (Every day, Weekdays, Weekends, or the days)",
     "setConn('After');setText('premise','breakfast');setText('habit','Floss');S.days=new Set([0,2,4]);render();tapTok('days')"),
    ("time", "The time tapped: No set time, At, From–to; the dial with a typed field",
     "setConn('After');setText('premise','breakfast');setText('habit','Floss');S.days=new Set([0,2,4]);S.time.kind='at';S.time.a='08:30';render();tapTok('time')"),
    ("energy", "The energy tapped: Low, Mid, High",
     "setConn('After');setText('premise','breakfast');setText('habit','Floss');S.days=new Set([0,2,4]);S.time.kind='at';S.time.a='08:30';render();tapTok('energy')"),
]
# the When sheet's rule: the foot's bottom stays at one pixel (the sentence may gain a line as blanks fill, growing upward)
SENT_TOP_JS = "(function(){var r=document.querySelector('.foot').getBoundingClientRect();return Math.round(r.bottom)})()"


def tiered_small(tp):
    """The gate, tiered (owner, 2026-10-13: 48 dp "cannot be a blanket choice ... it would bulk up every visible element"):
    primary actions keep 48 dp (the sentence's words, Add, Available ifs, an if to choose, the blanks); a control inside a
    chooser (a chip, a weekday) needs WCAG 2.2 AA's 24 dp (2.5.8). Visual size is free; this checks hit areas only."""
    out = []
    for x in tp.all:
        if not x.get("seen"):
            continue
        n = x["name"]
        floor = 24 if n.startswith("Chip ") else (48 if n.startswith(("Tok ", "If ", "Available", "Add", "Blank")) else None)
        if floor and (x["w"] < floor or x["h"] < floor):
            out.append("%s %dx%d" % (n, x["w"], x["h"]))
    return out


def hsheet_doc(v, setup):
    page = open(PROTO, encoding="utf-8").read()
    pre = "S.v.blank='%s';" % v["blank"]
    return page.replace("</head>", ONLY_PHONE + "</head>").replace("</body>", "<script>%srender(true);%s</script></body>" % (pre, setup))


def score_hsheet(v):
    if v.get("control"):
        d = adoc(addhabit_phone({"control": True}))
        tp = T.taps(d)
        return {"taps_join": 6, "taps_new": 99, "sentence_moves": 0, "reads_as_sentence": 0, "like_when": 1,
                "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Cue", "Block", "Add", "Cancel"))}),
                "clutter": T.clutter_of(lambda th: adoc(addhabit_phone({"control": True}), th))}
    tops, small = [], []
    for name, _, setup in HSTATES:
        d = hsheet_doc(v, setup)
        tops.append(T.probe(d, "t3-hs-%s-%s" % (v["blank"], name), SENT_TOP_JS))
        tp = T.taps(d)
        small += tiered_small(tp)
    join = 1 + 1 + (0 if v["blank"] == "inline" else 1) + 2 + 1
    new = 2 + 1 + 1 + 4 + 4 + 2 + 1
    return {"taps_join": join, "taps_new": new, "sentence_moves": max(tops) - min(tops), "reads_as_sentence": 1, "like_when": 0,
            "small": sorted(set(small)), "clutter": T.clutter_of(lambda th: hsheet_doc(v, "") .replace('data-theme="light"', 'data-theme="%s"' % th))}


# ==== Part premise: T3a.2d what tapping the premise box opens (owner, 2026-10-13) ================================================
"""
  The owner: "When tapping the premise, either the available IFs do not open or only the same kind are shown. Score
  both options." The Available ifs line above the sentence stays in both.
  premise  none (the box opens nothing; the keyboard only), same (the box opens the ifs whose connective is the one
           chosen: After shows After waking, After the walk, After lunch; one with none says so)
  Axes (owner's choice): Ease, Duplicate guard, Room with keyboard, Scan load.
  Walked in the sentence's order (connective, then the premise): joining After waking: the connective word and After
  (2), the premise box (1), then same: the if (1); none: "waking" typed, the readout says it is already an if, the
  Available ifs line (1), the if (1). Writing a new "During the commute": the same in both (the connective, the box,
  typing). Measured with the keyboard up (a 280 dp block at the foot, the sheet above it): the ifs rows in view, whether
  the sentence is in view, clutter.
  Control: the box opens every if, whatever the connective (the prototype before this scoring).
"""
PREMISE_SPACE = {"premise": ["none", "same"]}
KBD = ("<style>.sheet{bottom:280px!important;max-height:452px!important;padding-bottom:8px!important}.gesture{display:none}"
       ".kbd{position:absolute;left:0;right:0;bottom:0;height:280px;background:#c9c9c4;z-index:5}</style>")
PREMISE_JS = ("(function(){var vis=0;document.querySelectorAll('.ifrow').forEach(function(r){var b=r.getBoundingClientRect();if(b.height&&b.top>=0&&b.bottom<=460)vis++});"
              "var f=document.querySelector('.sent').getBoundingClientRect();return {rows:vis,sentence:(f.top>=0&&f.bottom<=460)?1:0}})()")


def premise_doc(v, theme="light"):
    mode = "all" if v.get("control") else v["premise"]
    page = open(PROTO, encoding="utf-8").read()
    setup = "S.v.premise='%s';setConn('After');premiseFocus('premise');" % mode
    page = page.replace('data-theme="light"', 'data-theme="%s"' % theme, 1)
    return page.replace("</head>", ONLY_PHONE + KBD + "</head>").replace(
        '<div class="gesture"></div>', '<div class="gesture"></div><div class="kbd"></div>', 1).replace(
        "</body>", "<script>render(true);%s</script></body>" % setup)


def score_premise(v):
    ctl = v.get("control")
    mode = "all" if ctl else v["premise"]
    d = premise_doc(v)
    pr = T.probe(d, "t3-prem-%s" % mode, PREMISE_JS)
    tp = T.taps(d)
    join_taps = 2 + 1 + (1 if mode in ("same", "all") else 2)
    return {"taps_join": join_taps, "typed_join": 0 if mode in ("same", "all") else 1, "taps_new": 3,
            "duplicate_guard": 1 if mode in ("same", "all") else 0, "rows_in_view": pr["rows"], "sentence_in_view": pr["sentence"],
            "scan_rows": pr["rows"], "small": sorted(set(tiered_small(tp))), "clutter": T.clutter_of(lambda th: premise_doc(v, th))}


# ==== Part habits2: T3a.1c the Habits list, the optional name and every if as a header (owner, 2026-10-13) =========================
"""
  The owner: "Score the Habits screen ... with the optional name included and showing every habit with an if, against
  the current proposed screens." The forecast is OFF (the approved default), steps plain, no glyph, energy chips with
  High on, Today's Log, done steps fold.
  group  routines (the approved form: an if with two or more habits is a header with its steps; a lone habit has its
         if as a small line above it), every (every if is a header, a lone habit sitting under its own if as a routine
         of one)
  name   none (the if is the header), named (a routine has a name the person wrote, "Morning routine", over its if;
         an unnamed if keeps the if as its header)
  Measured: words per row; rows seen; titles cut; whether every habit sits in the same shape (uniform); the routines'
  names in view; header lines spent; clutter, Windows' clutter. Judgment marks for the control.
  Control: the routine as a checklist with progress, "1/4 done · 25%" (as T3a.1b's).
"""
H2_SPACE = {"group": ["routines", "every"], "name": ["none", "named"]}
H2_CSS = """
.rhead .rn2{display:block;font-size:15px;font-weight:600}.rhead .rs2{display:block;font-size:12.5px;color:var(--dim)}
.rhead.small{padding:8px 4px 0}.rhead.small .rn2{font-size:13px;font-weight:400;color:var(--dim)}
"""


def h2doc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + ROUT_CSS + H2_CSS)


def h2_step(h):
    return ('<div class="row" data-tap="Open habit"><span style="width:8px;flex:none"></span><span class="num"></span><span class="t"><span class="nm">%s</span></span>'
            '<span class="act" data-tap="Log %s"><span>Log</span></span></div>') % (kit.ud(e(h[0])), h[0])


def habits2_body(v):
    ctl = v.get("control")
    out, heads = [], 0
    for name, sentence, block, steps in ROUTINES:
        live = [h for h in steps if not h[3]]
        routine = name is not None
        if not routine and v.get("group") != "every" and not ctl:
            for h in live:   # the approved lone habit: its if above it
                out.append('<div class="row" data-tap="Open habit"><span class="t" style="padding-left:4px"><span class="bsub">%s</span><span class="nm">%s</span></span>'
                           '<span class="act" data-tap="Log %s"><span>Log</span></span></div>' % (e(sentence), kit.ud(e(h[0])), h[0]))
            continue
        heads += 1
        if ctl:
            done = sum(1 for h in steps if h[3])
            prog = '<span class="rp"><span data-judge="1">%d/%d done</span> · <span data-judge="1">%d%%</span></span>' % (done, len(steps), round(100 * done / len(steps)))
            out.append('<div class="rhead" data-head="1"><span><span class="rn2">%s</span></span>%s</div>' % (e(sentence), prog))
        elif routine and v["name"] == "named":
            out.append('<div class="rhead" data-head="1" data-named="1"><span><span class="rn2">%s</span><span class="rs2">%s</span></span></div>' % (kit.ud(e(name)), e(sentence)))
        else:
            out.append('<div class="rhead%s" data-head="1"><span><span class="rn2">%s</span></span></div>' % ("" if routine else " small", e(sentence)))
        out.append('<div class="rsteps">%s</div>' % "".join(h2_step(h) for h in live))
    done_n = sum(1 for _, _, _, st in ROUTINES for h in st if h[3])
    out.append('<div class="fold" data-tap="Done today"><span class="t">Done today · %d</span>▸</div>' % done_n)
    chips = '<div class="fchips">%s</div>' % "".join('<span class="%s" data-tap="Energy %s">%s</span>' % ("on" if x == "High" else "", x, x) for x in ("Low", "Mid", "High"))
    return chips + '<div class="zone">%s</div>' % "".join(out)


def habits2_phone(v):
    return kit.phone(kit.header("Habits", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New habit…</span></div>' + habits2_body(v), kit.bar("Hub"))


def habits2_desk(v, theme="light"):
    inner = habits2_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Habits", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme, CSS + BASICS_CSS + ROUT_CSS + H2_CSS)


H2_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var o={rows:0,words:0,cut:0,judge:0,heads:0,named:0,headpx:0};"
         "document.querySelectorAll('[data-tap=\"Open habit\"]').forEach(function(r){var b=r.getBoundingClientRect();if(!b.height||b.bottom>vb)return;o.rows++;"
         "var t=r.querySelector('.t');o.words+=t?t.innerText.split(/\\s+/).filter(Boolean).length:0;r.querySelectorAll('.nm,.bsub').forEach(function(s){if(s.scrollWidth>s.clientWidth+1)o.cut++})});"
         "document.querySelectorAll('[data-head]').forEach(function(h){var b=h.getBoundingClientRect();if(b.bottom>vb)return;o.heads++;o.headpx+=Math.round(b.height);"
         "if(h.dataset.named)o.named++;o.words+=h.innerText.split(/\\s+/).filter(Boolean).length});"
         "document.querySelectorAll('[data-judge]').forEach(function(j){var b=j.getBoundingClientRect();if(b.height&&b.bottom<=vb)o.judge++});return o})()")


def score_habits2(v):
    ctl = v.get("control")
    d = h2doc(habits2_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-h2-%s" % key_of(v), H2_JS)
    units = pr["rows"] + pr["heads"]
    return {"judgment_marks": pr["judge"], "uniform": 1 if (ctl or v["group"] == "every") else 0, "names_in_view": pr["named"],
            "words_per_row": round(pr["words"] / max(1, pr["rows"]), 2), "header_px": pr["headpx"], "rows_seen": pr["rows"], "cut": pr["cut"],
            "small": sorted(set(tiered_small(tp))),
            "clutter": T.clutter_of(lambda th: h2doc(habits2_phone(v), th)), "desk_clutter": dclutter(lambda th: habits2_desk(v, th))}


# ==== Part trackers: T3b.1 the Trackers list (Hub › Measuring › Trackers) ========================================================
"""
  Trackers are what is counted or rated (owner, 2026-10-13: water, exercise, studying, knitting); a habit is yes/no. The
  four kinds are Chronicle's: a number with a unit, yes/no, a rating 1-5, a choice. Nine placeholder trackers under four
  labels. Goals are their own screen (T3b): no goal shows here, and an amount reads plain (Tendril's rule, T3.1).
  layout   rows (the list rows of Today and Habits), grid (two columns of cards, as Track & Graph)
  says     none (the name only), today ("3 glasses today"), last ("last 11:40"), today_last (both, as Chronicle's
           "1 today · last just now"), spark (today's amount and the last 7 days as small bars; a day with no reading is
           a short tick on the baseline)
  log      sheet (Today's Log opens the Log sheet, the tracker's usual amount filled in, Log there: 2 taps), default
           (Log logs the usual amount at once and a toast offers Change and Undo; a tracker with no usual amount opens the
           sheet), stepper (− n + on the row for a number with a usual amount; the others keep Log, opening the sheet)
  group    flat (manual order), labels (under their labels, as Chronicle's categories)
  Measured: taps to log a usual glass of water; reach to the first Log (Fitts from the thumb); whether Log acts alike on
  every row (log_varies); writes made with no confirming step (unconfirmed: a pocket tap logs); the share of rows that
  say something; judgment marks (empty-day ticks, fractions, percentages, streaks); the rows read on average to find a
  tracker (scan_steps: a label header counts as one read); whether rows and Log look as Today's; rows seen, titles cut,
  words per row; clutter, Windows' clutter.
  Control: a dashboard as many tracker apps draw one: the grid, each card with today against its goal ("3/8 · 38%"), a
  progress bar, a streak and the 7-day bars, Log through the sheet.
"""
TRK_SPACE = {"layout": ["rows", "grid"], "says": ["none", "today", "last", "today_last", "spark"], "log": ["sheet", "default", "stepper"], "group": ["flat", "labels"]}
# (name, kind, label, today, last, usual amount (None: none), today's number for the stepper, last 7 days oldest first (None: no reading))
TRACKERS = [
    ("Water", "number", "Health", "3 glasses today", "last 11:40", "1 glass", 3, [6, 8, 5, 7, 8, 4, 3]),
    ("Coffee", "number", "Health", "2 cups today", "last 09:15", "1 cup", 2, [2, 2, 1, 3, 2, 2, 2]),
    ("Sleep", "number", "Health", "7.5 hours today", "last 07:10", None, None, [7, 6.5, 8, 7, None, 7.5, 7.5]),
    ("Headache", "yesno", "Health", "", "last 3 Oct", None, None, [None, None, None, None, None, None, None]),
    ("Mood", "rating", "Mind", "4 today", "last 10:20", None, None, [3, 4, None, 4, 3, 5, 4]),
    ("Exercise", "number", "Moving", "", "last Sun", "30 min", 0, [30, None, 45, None, None, 30, None]),
    ("Commute", "choice", "Moving", "Bike today", "last 08:30", None, None, ["Bike", "Bus", None, "Bike", "Bike", None, "Bike"]),
    ("Knitting", "number", "Making", "", "last Sat", "10 rows", 0, [None, 20, None, None, 12, None, None]),
    ("Studying", "number", "Making", "40 min today", "last 15:00", None, None, [60, 30, None, 45, None, 50, 40]),
]
TRK_LABELS = ["Health", "Mind", "Moving", "Making"]
GOALS = {"Water": (3, 8), "Coffee": (2, 3), "Sleep": (7.5, 8), "Headache": (0, 0), "Mood": (4, 5), "Exercise": (0, 30), "Commute": (1, 1), "Knitting": (0, 20), "Studying": (40, 60)}
TRK_CSS = """
.krow .t{min-width:0}.krow .t .nm{font-size:15px}
.spark{display:flex;align-items:flex-end;gap:2px;height:14px;margin-top:3px}.spark i{width:6px;background:var(--dim);border-radius:1px}.spark i.nil{height:2px!important;opacity:.5}
.stp{display:flex;align-items:center;flex:none}.stp .sb{width:48px;height:48px;display:grid;place-items:center;font-size:18px;color:var(--ink)}
.stp .sv{min-width:22px;text-align:center;font-size:15px;font-weight:600}
.kgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:4px 0}
.kcard{background:var(--zone2);border-radius:12px;padding:10px 10px 4px;min-height:104px;display:flex;flex-direction:column;min-width:0}
.kcard .act span{background:var(--zone)}
.kcard .nm{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.kcard .foot{margin-top:auto;display:flex;justify-content:flex-end;align-items:center}
.pbar{height:6px;border-radius:3px;background:var(--zone);margin-top:6px;overflow:hidden}.pbar b{display:block;height:100%;background:var(--ink)}
.lsheet{position:absolute;left:0;right:0;bottom:0;background:var(--zone);border-radius:20px 20px 0 0;padding:14px 16px 20px;box-shadow:0 -8px 24px rgba(0,0,0,.14)}
.lsheet h3{margin:0 0 10px;font-size:18px}.lsheet .amt{display:flex;align-items:center;justify-content:center;gap:12px;font-size:20px;margin:6px 0 14px}
.lsheet .amt span{width:48px;height:48px;display:grid;place-items:center;border-radius:24px;box-shadow:inset 0 0 0 1.5px var(--dim)}
.lsheet .go{min-height:48px;border-radius:24px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:600}
"""


def tdoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + TRK_CSS)


def trk_says(t, v):
    name, kind, label, today, last, usual, num, week = t
    s = v["says"]
    if s == "none":
        return ""
    if s in ("today", "spark"):
        return today
    if s == "last":
        return last
    return " · ".join(x for x in (today, last) if x)


def trk_spark(t):
    week = t[7]
    nums = [x if isinstance(x, (int, float)) else (1 if x else None) for x in week]
    top = max([x for x in nums if x] or [1])
    return '<span class="spark">%s</span>' % "".join(
        '<i class="nil" data-empty="1"></i>' if x is None else '<i style="height:%dpx"></i>' % max(3, round(14 * x / top)) for x in nums)


def trk_log(t, v):
    name = t[0]
    if v["log"] == "stepper" and t[5]:
        return '<span class="stp"><span class="sb" data-tap="Minus %s">−</span><span class="sv">%d</span><span class="sb" data-tap="Plus %s">+</span></span>' % (name, t[6], name)
    return '<span class="act" data-tap="Log %s"><span>Log</span></span>' % name


def trk_item(t, v):
    sub = trk_says(t, v)
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    spark = trk_spark(t) if v["says"] == "spark" else ""
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span>%s%s<span class="foot">%s</span></div>' % (
            t[0], kit.ud(e(t[0])), subh, spark, trk_log(t, v))
    return '<div class="row krow" data-tap="Open tracker" data-tr="%s"><span class="t"><span class="nm">%s</span>%s%s</span>%s</div>' % (
        t[0], kit.ud(e(t[0])), subh, spark, trk_log(t, v))


def trk_control_item(t):
    have, goal = GOALS[t[0]]
    pct = round(100 * have / goal) if goal else 0
    streak = {"Water": 13, "Coffee": 9, "Sleep": 2, "Headache": 0, "Mood": 3, "Exercise": 0, "Commute": 1, "Knitting": 0, "Studying": 2}[t[0]]
    return ('<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span><span class="bsub"><span data-judge="1">%s/%s</span> · '
            '<span data-judge="1">%d%%</span> · <span data-judge="1">streak %d</span></span><span class="pbar" data-judge="1"><b style="width:%d%%"></b></span>%s'
            '<span class="foot"><span class="act" data-tap="Log %s"><span>Log</span></span></span></div>') % (
        t[0], kit.ud(e(t[0])), ("%g" % have), ("%g" % goal), pct, streak, min(100, pct), trk_spark(t), t[0])


def trackers_body(v):
    if v.get("control"):
        return '<div class="zone"><div class="kgrid">%s</div></div>' % "".join(trk_control_item(t) for t in TRACKERS)
    wrap = (lambda items: '<div class="kgrid">%s</div>' % items) if v["layout"] == "grid" else (lambda items: items)
    if v["group"] == "flat":
        body = wrap("".join(trk_item(t, v) for t in TRACKERS))
    else:
        body = "".join('<div class="dayh">%s</div>' % lab + wrap("".join(trk_item(t, v) for t in TRACKERS if t[2] == lab)) for lab in TRK_LABELS)
    return '<div class="zone">%s</div>' % body


def trackers_phone(v, after=False):
    extra = ""
    if after and not v.get("control"):   # the state after tapping Water's Log (or +)
        if v["log"] == "sheet":
            extra = ('<div class="scrim"></div><div class="lsheet"><h3>Water</h3><div class="amt"><span data-tap="Less">−</span>%s<span data-tap="More">+</span></div>'
                     '<div class="go" data-tap="Log">Log</div></div>') % kit.ud("1 glass")
        elif v["log"] == "default":
            extra = ('<div class="toast"><span class="t">Water: 1 glass logged</span><span class="u" data-tap="Change">Change</span>'
                     '<span class="u" data-tap="Undo">Undo</span></div>')
    body = trackers_body(v)
    if after and not v.get("control"):
        body = body.replace("3 glasses today", "4 glasses today").replace('<span class="sv">3</span>', '<span class="sv">4</span>') if v["log"] != "sheet" else body
    return kit.phone(kit.header("Trackers", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New tracker…</span></div>' + body + extra, kit.bar("Hub"))


def trackers_desk(v, theme="light"):
    inner = trackers_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Trackers", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme,
                    CSS + BASICS_CSS + TRK_CSS)


TRK_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var o={rows:0,words:0,cut:0,judge:0,says:0};"
          "document.querySelectorAll('[data-tap=\"Open tracker\"]').forEach(function(r){var b=r.getBoundingClientRect();if(!b.height||b.bottom>vb)return;o.rows++;"
          "var nm=r.querySelector('.nm'),s=r.querySelector('.bsub');o.words+=(nm?nm.innerText:'').split(/\\s+/).filter(Boolean).length+(s?s.innerText.split(/\\s+/).filter(Boolean).length:0);"
          "if(s&&s.innerText.trim())o.says++;[nm,s].forEach(function(x){if(x&&x.scrollWidth>x.clientWidth+1)o.cut++})});"
          "document.querySelectorAll('[data-judge],[data-empty]').forEach(function(j){var b=j.getBoundingClientRect();if(b.height&&b.bottom<=vb)o.judge++});return o})()")


def trk_scan(v):
    """The rows read, on average, to find a tracker: its place in the list; under labels, the headers read up to its own plus
    its place under it."""
    if v.get("control") or v["group"] == "flat":
        return round(sum(i + 1 for i in range(len(TRACKERS))) / len(TRACKERS), 3)
    steps = []
    for t in TRACKERS:
        g = TRK_LABELS.index(t[2])
        within = [x[0] for x in TRACKERS if x[2] == t[2]].index(t[0])
        steps.append(g + 1 + within + 1)
    return round(sum(steps) / len(steps), 3)


def score_trackers(v):
    ctl = v.get("control")
    d = tdoc(trackers_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-trk-%s" % key_of(v), TRK_JS)
    log = "sheet" if ctl else v["log"]
    first = next((x for x in tp.all if x["name"] in ("Log Water", "Plus Water") and x.get("seen")), None)
    return {"taps_count": {"sheet": 2, "default": 1, "stepper": 1}[log], "reach_log": round(T.fitts(THUMB, first), 3) if first else 9,
            "log_varies": 0 if log == "sheet" else 1, "unconfirmed": 0 if log == "sheet" else 1,
            "says_share": round(pr["says"] / max(1, pr["rows"]), 3), "judgment_marks": pr["judge"], "scan_steps": trk_scan(v),
            "like_today": 0 if (not ctl and v["layout"] == "rows" and log != "stepper") else 1,
            "rows_seen": pr["rows"], "cut": pr["cut"], "words_per_row": round(pr["words"] / max(1, pr["rows"]), 2),
            "small": small_of(tp, {x["name"] for x in tp.all if x["name"].startswith(("Log ", "Plus ", "Minus "))}),
            "clutter": T.clutter_of(lambda th: tdoc(trackers_phone(v), th)), "desk_clutter": dclutter(lambda th: trackers_desk(v, th))}


# ==== Part measure: T3b.1b the Measuring list, taps first (owner, 2026-10-13) =====================================================
"""
  The owner: trackers belong to P4 Measuring, "one of the screens that can be busy in exchange for least taps to log data
  or start a timer". Calm and Density are dropped; a cut title or a target under its floor is a gate, not a score.
  Owner's answers: score one merged list against two screens; a stray tap's write is an axis (Recovery); Today's tracker
  rows are settled in the consistency pass (no likeness-to-Today axis here); judgment marks stay an axis.
  scope    merged (trackers and activities in one list, ▶ / ■ on an activity's row), apart (trackers only; an
           "Activities ›" row opens the Activities screen, where ▶ is)
  layout, says, group   as T3b.1
  log      sheet, default, stepper (as T3b.1), inline (a control per kind on the row: "+ 1 glass" for a number with a usual
           amount, Yes for yes/no, the five ratings as chips, the two most recent choices as chips and … for the rest; a
           number with no usual amount keeps Log, which opens the sheet)
  The walk (each entry a typical one): a usual glass of water; 7.5 hours of sleep (no usual amount: Log, typed, Log);
  Mood 4; Headache yes; Commute by bike; and starting then stopping the Reading timer. A target not in view on the
  phone adds one scroll. Taps are averaged over the walk.
  Measured: taps (mean, scrolls included); reach to the first control; Recovery: the share of the five logs written by a
  single tap with no confirming step (each one has Undo in a toast); Glance: the share of rows that say something, and
  whether a running timer shows on this screen; Judgment marks; Find (rows read to locate one); Refs.
  Gate: no title cut; primary targets (Log, +, Yes, ▶, ■, Activities) at 48 dp, chips at 24 dp (T3a's tiered rule).
  Control: T3b.1's dashboard (cards with today against a goal, a progress bar, a streak, the 7-day bars), Log through
  the sheet, activities apart.
"""
MEAS_SPACE = {"scope": ["merged", "apart"], "layout": ["rows", "grid"], "says": ["none", "today", "last", "today_last", "spark"],
              "log": ["sheet", "default", "stepper", "inline"], "group": ["flat", "labels"]}
# (name, label, today, last, running)
ACTIVITIES = [("Reading", "Mind", "25 min today", "last 21:10", False), ("Cleaning", "Home", "running 0:12", "last 10:05", True),
              ("Language practice", "Mind", "", "last Fri", False)]
MEAS_LABELS = ["Health", "Mind", "Moving", "Making", "Home"]
USUAL_YES = {"Headache"}   # a yes/no tracker's usual answer is Yes
RECENT = {"Commute": ["Bike", "Bus"]}
MEAS_CSS = """
.mrow{align-items:flex-start;padding:4px 0}.mrow .t{padding:4px 0}
.ichips{display:flex;gap:4px;margin-top:4px;flex-wrap:wrap}.ichips span{min-width:32px;height:32px;padding:0 8px;border-radius:16px;display:grid;place-items:center;font-size:13px;box-shadow:inset 0 0 0 1px var(--dim)}
.pill48{min-height:48px;min-width:48px;display:grid;place-items:center;flex:none}.pill48 span{border-radius:999px;padding:4px 12px;font-size:13px;background:var(--zone2);color:var(--ink);white-space:nowrap}
.kcard .pill48 span,.kcard .ichips span{background:var(--zone)}
.play{width:48px;height:48px;display:grid;place-items:center;flex:none;font-size:15px}.play span{width:32px;height:32px;border-radius:16px;display:grid;place-items:center;background:var(--ink);color:var(--bg);font-size:12px}
.golink{display:flex;align-items:center;min-height:48px;font-size:15px}.golink .t{flex:1}
"""


def mdoc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + TRK_CSS + MEAS_CSS)


def m_ctrl(t, v):
    """(right-hand control, chip line) for a tracker."""
    name, kind, usual = t[0], t[1], t[5]
    log = '<span class="act" data-tap="Log %s"><span>Log</span></span>' % name
    if v["log"] in ("sheet",):
        return log, ""
    if v["log"] == "default":
        return log, ""
    if v["log"] == "stepper":
        return (trk_log(t, v), "")
    # inline
    if kind == "number" and usual:
        return '<span class="pill48" data-tap="Plus %s"><span>+ %s</span></span>' % (name, e(usual)), ""
    if kind == "yesno":
        return '<span class="pill48" data-tap="Yes %s"><span>Yes</span></span>' % name, ""
    if kind == "rating":
        return "", '<span class="ichips">%s</span>' % "".join('<span data-tap="Chip %s %d">%d</span>' % (name, i, i) for i in range(1, 6))
    if kind == "choice":
        return "", '<span class="ichips">%s<span data-tap="Chip %s more">…</span></span>' % ("".join('<span data-tap="Chip %s %s">%s</span>' % (name, c, c) for c in RECENT[name]), name)
    return log, ""


def m_item(t, v):
    sub = trk_says(t, v)
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    spark = trk_spark(t) if v["says"] == "spark" else ""
    right, chips = m_ctrl(t, v)
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span>%s%s%s<span class="foot">%s</span></div>' % (
            t[0], kit.ud(e(t[0])), subh, spark, chips, right)
    return '<div class="row krow mrow" data-tap="Open tracker" data-tr="%s"><span class="t"><span class="nm">%s</span>%s%s%s</span>%s</div>' % (
        t[0], kit.ud(e(t[0])), subh, spark, chips, right)


def m_act(a, v):
    name, label, today, last, running = a
    s = v["says"]
    sub = "" if s == "none" else (today if s in ("today", "spark") else (last if s == "last" else " · ".join(x for x in (today, last) if x)))
    if running:
        sub = "running 0:12" if s == "none" else sub   # a running timer always says so
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    ctl = ('<span class="play" data-tap="Stop %s"><span>■</span></span>' if running else '<span class="play" data-tap="Start %s"><span>▶</span></span>') % name
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s" data-act="1"><span class="nm">%s</span>%s<span class="foot">%s</span></div>' % (name, kit.ud(e(name)), subh, ctl)
    return '<div class="row krow mrow" data-tap="Open tracker" data-tr="%s" data-act="1"><span class="t"><span class="nm">%s</span>%s</span>%s</div>' % (name, kit.ud(e(name)), subh, ctl)


def m_entries(v):
    """The list in order: (label, html) for trackers, then activities when merged."""
    out = [(t[2], m_item(t, v)) for t in TRACKERS]
    if v["scope"] == "merged":
        out += [(a[1], m_act(a, v)) for a in ACTIVITIES]
    return out


def measure_body(v):
    if v.get("control"):
        return trackers_body(v)
    wrap = (lambda items: '<div class="kgrid">%s</div>' % items) if v["layout"] == "grid" else (lambda items: items)
    ents = m_entries(v)
    if v["group"] == "flat":
        body = wrap("".join(h for _, h in ents))
    else:
        body = "".join('<div class="dayh">%s</div>' % lab + wrap("".join(h for l, h in ents if l == lab)) for lab in MEAS_LABELS if any(l == lab for l, _ in ents))
    link = '<div class="golink" data-tap="Open Activities"><span class="t">Activities</span>›</div>' if v["scope"] == "apart" else ""
    return '<div class="zone">%s%s</div>' % (link, body)


def measure_phone(v):
    title = "Measuring" if (not v.get("control") and v["scope"] == "merged") else "Trackers"
    link = '<div class="golink" data-tap="Open Activities"><span class="t">Activities</span>›</div>' if v.get("control") else ""
    return kit.phone(kit.header(title, (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New tracker…</span></div>' + (('<div class="zone">%s</div>' % link) if link else "") + measure_body(v), kit.bar("Hub"))


def measure_desk(v, theme="light"):
    inner = measure_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Measuring", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme,
                    CSS + BASICS_CSS + TRK_CSS + MEAS_CSS)


def m_walk(v):
    """[(target name, taps)] for the walk: each entry's first target and its taps (typing a value counts one)."""
    ctl = v.get("control")
    log = "sheet" if ctl else v["log"]
    inline = log == "inline"
    w = [("Plus Water" if log in ("stepper", "inline") else "Log Water", 2 if log == "sheet" else 1),
         ("Log Sleep", 3),
         ("Chip Mood 4" if inline else "Log Mood", 1 if inline else 3),
         ("Yes Headache" if inline else "Log Headache", 1 if (inline or log == "default") else 2),
         ("Chip Commute Bike" if inline else "Log Commute", 1 if inline else 3)]
    merged = (not ctl) and v["scope"] == "merged"
    w.append(("Start Reading" if merged else "Open Activities", 2 if merged else 4))   # start, later stop (apart: Activities each time)
    one_tap = sum(1 for n, k in w[:5] if k == 1)
    return w, one_tap


MEAS_JS = TRK_JS


def m_scan(v):
    if v.get("control"):
        return trk_scan(v)
    names = [(t[2], t[0]) for t in TRACKERS] + ([(a[1], a[0]) for a in ACTIVITIES] if v["scope"] == "merged" else [])
    if v["group"] == "flat":
        return round(sum(i + 1 for i in range(len(names))) / len(names), 3)
    labs = [lab for lab in MEAS_LABELS if any(l == lab for l, _ in names)]
    steps = [labs.index(l) + 1 + [n for ll, n in names if ll == l].index(n) + 1 for l, n in names]
    return round(sum(steps) / len(steps), 3)


def score_measure(v):
    ctl = v.get("control")
    d = mdoc(measure_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-meas-%s" % key_of(v), MEAS_JS)
    walk, one_tap = m_walk(v)
    seen = {x["name"] for x in tp.all if x.get("seen")}
    taps = [k + (0 if n in seen else 1) for n, k in walk]
    # reach: every first target of the walk that is in view (one found on 2026-10-13: reach to Water's Log alone put the control on the front,
    # its progress bar having pushed that one button nearer the thumb)
    reach = [x for n, _ in walk for x in [next((y for y in tp.all if y["name"] == n and y.get("seen")), None)] if x]
    gate = []
    for x in tp.all:
        if not x.get("seen"):
            continue
        n = x["name"]
        floor = 24 if n.startswith("Chip ") else (48 if n.startswith(("Log ", "Plus ", "Minus ", "Yes ", "Start ", "Stop ", "Open Activities")) else None)
        if floor and (x["w"] < floor or x["h"] < floor):
            gate.append("%s %dx%d" % (n, x["w"], x["h"]))
    if pr["cut"]:
        gate.append("titles cut %d" % pr["cut"])
    running = (not ctl) and v["scope"] == "merged"
    return {"taps_mean": round(sum(taps) / len(taps), 3), "scrolls": sum(1 for n, _ in walk if n not in seen),
            "reach_mean": round(sum(T.fitts(THUMB, x) for x in reach) / len(reach), 3) if reach else 9, "one_tap_writes": round(one_tap / 5, 3),
            "says_share": round(pr["says"] / max(1, pr["rows"]), 3), "running_shown": 1 if running else 0,
            "judgment_marks": pr["judge"], "scan_steps": m_scan(v), "rows_seen": pr["rows"], "words_per_row": round(pr["words"] / max(1, pr["rows"]), 2),
            "small": sorted(set(gate))}


# ==== Part measure2: T3b.1c the Measuring list, scroll counted (owner, 2026-10-13) ================================================
"""
  The owner: fewer taps on the row made the cards taller, "increases the amount of scrolling needed to find the desired
  element and ... hides a lot of trackers that then need to be searched for". T3b.1b counted at most one scroll per entry
  for six entries near the top, and Find read rows in list order whatever their height. Here:
  Taps     every item's typical log, weighted by how often it is logged (a placeholder profile: Water 6 a day ... Weight
           0.15), plus the scrolls to bring its control into view from where it really sits (a page is the list area's
           height), or a search (⌕, two letters, the result: 3) when cheaper; folded labels add the tap that opens one.
           Scored with 12 items and with 30; the worse rank counts, and fewest taps leads at both (T.LEAD).
  Overview the share of items in view, or behind a label header in view (one tap); the screens the list spans.
  scope    merged, apart (as T3b.1b); layout rows, grid, compact (rows whose rating and choice chips fold into the row: a
           tap on it opens them; single buttons stay); says none, today, last, today_last (the spark dropped: it lost on
           Judgment in T3b.1b); log sheet, inline (default and stepper cannot reach a taps-led front); group flat, labels,
           folding (labels as headers that open, all closed at first, each with its count); order manual, recent (the most
           logged first; under labels, within each and the labels by their most logged)
  Kept: Reach (mean over the controls in view), Recovery (the logged share written by one tap with no confirming step,
  weighted), Glance, Judgment; Refs as information (owner). Gate: no title cut at either size; primary targets 48 dp,
  chips 24 dp.
  Control: T3b.1's dashboard, apart, in manual order.
"""
MEAS2_SPACE = {"scope": ["merged", "apart"], "layout": ["rows", "grid", "compact"], "says": ["none", "today", "last", "today_last"],
               "log": ["sheet", "inline"], "group": ["flat", "labels", "folding", "hybrid_fit", "hybrid_6", "hybrid_pinned"],
               "order": ["manual", "recent"]}
# hybrid_*: the most used open at the top with their controls, the rest under folded labels with their counts (owner, 2026-10-13);
# the open ones are as many as fit one screen above the folded labels (fit), the 6 most used (6), or six the person pins (pinned,
# scored as the 6 most used: they differ in whether they move on their own as use changes, "moves")


def _it(n, k, lab, today, last, f, usual=None, cur=None, recent=None, running=False):
    return {"n": n, "k": k, "lab": lab, "today": today, "last": last, "f": f, "usual": usual, "cur": cur, "recent": recent, "running": running}


ITEMS12 = [
    _it("Water", "number", "Health", "3 glasses today", "last 11:40", 6, "1 glass", 3), _it("Coffee", "number", "Health", "2 cups today", "last 09:15", 2, "1 cup", 2),
    _it("Sleep", "number", "Health", "7.5 hours today", "last 07:10", 1), _it("Headache", "yesno", "Health", "", "last 3 Oct", 0.2),
    _it("Mood", "rating", "Mind", "4 today", "last 10:20", 2), _it("Exercise", "number", "Moving", "", "last Sun", 0.5, "30 min", 0),
    _it("Commute", "choice", "Moving", "Bike today", "last 08:30", 1.4, recent=["Bike", "Bus"]), _it("Knitting", "number", "Making", "", "last Sat", 0.3, "10 rows", 0),
    _it("Studying", "number", "Making", "40 min today", "last 15:00", 1), _it("Reading", "activity", "Mind", "25 min today", "last 21:10", 1),
    _it("Cleaning", "activity", "Home", "running 0:12", "last 10:05", 0.5, running=True), _it("Language practice", "activity", "Mind", "", "last Fri", 0.4),
]
ITEMS30 = ITEMS12 + [
    _it("Tea", "number", "Health", "1 cup today", "last 16:00", 1.5, "1 cup", 1), _it("Steps", "number", "Moving", "4,200 today", "last 18:00", 1),
    _it("Weight", "number", "Health", "", "last Mon", 0.15), _it("Vitamins", "yesno", "Health", "yes today", "last 08:00", 1),
    _it("Energy", "rating", "Mind", "3 today", "last 12:00", 1.5), _it("Focus", "rating", "Mind", "", "last Sat", 0.8),
    _it("Pain", "rating", "Health", "", "last 30 Sep", 0.3), _it("Snack", "choice", "Health", "Fruit today", "last 15:30", 1, recent=["Fruit", "Nuts"]),
    _it("Pages", "number", "Mind", "", "last Sun", 0.6, "10 pages", 0), _it("Screen time", "number", "Mind", "", "last Sun", 0.5),
    _it("Plants watered", "yesno", "Home", "", "last Thu", 0.3), _it("Social", "choice", "Mind", "", "last Fri", 0.3, recent=["Call", "Visit"]),
    _it("Sketching", "number", "Making", "", "last Sat", 0.2, "1 sketch", 0), _it("Walking", "activity", "Moving", "30 min today", "last 13:10", 0.7),
    _it("Cooking", "activity", "Home", "", "last Sun", 0.7), _it("Gardening", "activity", "Home", "", "last 4 Oct", 0.15),
    _it("Guitar", "activity", "Making", "", "last Wed", 0.3), _it("Meditation", "activity", "Mind", "", "last Fri", 0.3),
]
M2_LABELS = ["Health", "Mind", "Moving", "Making", "Home"]
M2_CSS = """
.fhead{display:flex;align-items:center;min-height:48px;font-size:14px;font-weight:600;border-bottom:1px solid var(--zone2)}.fhead .t{flex:1}.fhead .c{color:var(--dim);font-weight:400;margin-right:8px}
"""


def m2doc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS)


def m2_says(it, v):
    s = v["says"]
    if it["running"]:
        return "running 0:12"   # a running timer always says so
    if s == "none":
        return ""
    if s == "today":
        return it["today"]
    if s == "last":
        return it["last"]
    return " · ".join(x for x in (it["today"], it["last"]) if x)


def m2_ctrl(it, v):
    """(right-hand control, chip line) for an item."""
    n, k = it["n"], it["k"]
    if k == "activity":
        return ('<span class="play" data-tap="Stop %s"><span>■</span></span>' if it["running"] else '<span class="play" data-tap="Start %s"><span>▶</span></span>') % n, ""
    log = '<span class="act" data-tap="Log %s"><span>Log</span></span>' % n
    if v["log"] == "sheet" or (k == "number" and not it["usual"]):
        return log, ""
    if k == "number":
        return '<span class="pill48" data-tap="Plus %s"><span>+ %s</span></span>' % (n, e(it["usual"])), ""
    if k == "yesno":
        return '<span class="pill48" data-tap="Yes %s"><span>Yes</span></span>' % n, ""
    if v["layout"] == "compact":   # the chips fold into the row: a tap on it opens them
        return '<span class="trail">▾</span>', ""
    if k == "rating":
        return "", '<span class="ichips">%s</span>' % "".join('<span data-tap="Chip %s %d">%d</span>' % (n, i, i) for i in range(1, 6))
    return "", '<span class="ichips">%s<span data-tap="Chip %s more">…</span></span>' % ("".join('<span data-tap="Chip %s %s">%s</span>' % (n, c, c) for c in it["recent"]), n)


def m2_item(it, v):
    sub = m2_says(it, v)
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    right, chips = m2_ctrl(it, v)
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span>%s%s<span class="foot">%s</span></div>' % (
            it["n"], kit.ud(e(it["n"])), subh, chips, right)
    return '<div class="row krow mrow" data-tap="Open tracker" data-tr="%s"><span class="t"><span class="nm">%s</span>%s%s</span>%s</div>' % (
        it["n"], kit.ud(e(it["n"])), subh, chips, right)


def m2_items(v, items):
    its = [it for it in items if v["scope"] == "merged" or it["k"] != "activity"]
    if v["order"] == "recent":
        its = sorted(its, key=lambda it: -it["f"])
    return its


def m2_labels(v, its):
    labs = [lab for lab in M2_LABELS if any(it["lab"] == lab for it in its)]
    if v["order"] == "recent":
        labs = sorted(labs, key=lambda lab: -max(it["f"] for it in its if it["lab"] == lab))
    return labs


def m2_control_item(it):
    have = it["cur"] or (1 if it["today"] else 0)
    goal = max(1, (it["cur"] or 1) * 2)
    pct = round(100 * have / goal)
    ctl = m2_ctrl(it, {"log": "sheet", "layout": "grid"})[0]
    return ('<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span><span class="bsub"><span data-judge="1">%s/%s</span> · '
            '<span data-judge="1">%d%%</span> · <span data-judge="1">streak %d</span></span><span class="pbar" data-judge="1"><b style="width:%d%%"></b></span>'
            '<span class="foot">%s</span></div>') % (it["n"], kit.ud(e(it["n"])), have, goal, pct, len(it["n"]) % 7, min(100, pct), ctl)


def m2_top(v, items, its):
    """The open items of a hybrid, the most used first."""
    if v["group"] == "hybrid_fit":
        n = m2_fit(v, items)
    else:
        n = 6
    return sorted(its, key=lambda it: -it["f"])[:n]


def m2_fit(v, items):
    """How many of the most used fit one phone screen above the folded labels: measured on the list drawn flat, most used first."""
    vf = dict(v, group="flat", order="recent")
    pr = T.probe(m2doc(measure2_phone(vf, items)), "t3-m2fit-%d-%s" % (len(items), key_of(vf)), M2_JS)
    labs = len({it["lab"] for it in m2_items(vf, items)})
    room = pr["vb"] - 48 * labs
    return sum(1 for x in pr["items"] if x["bottom"] <= room)


def measure2_body(v, items, closed=False):
    if v.get("control"):
        its = [it for it in items if it["k"] != "activity"]
        link = '<div class="golink" data-tap="Open Activities"><span class="t">Activities</span>›</div>'
        return '<div class="zone">%s<div class="kgrid">%s</div></div>' % (link, "".join(m2_control_item(it) for it in its))
    its = m2_items(v, items)
    wrap = (lambda h: '<div class="kgrid">%s</div>' % h) if v["layout"] == "grid" else (lambda h: h)
    head = ""
    if v["group"].startswith("hybrid"):
        top = m2_top(v, items, its)
        head = wrap("".join(m2_item(it, v) for it in top))
        its = [it for it in its if it not in top]
    if v["group"] == "flat":
        body = wrap("".join(m2_item(it, v) for it in its))
    else:
        body = head
        for lab in m2_labels(v, its):
            part = [it for it in its if it["lab"] == lab]
            if v["group"] == "labels":
                body += '<div class="dayh" data-lab="%s">%s</div>' % (lab, lab) + wrap("".join(m2_item(it, v) for it in part))
            else:
                body += '<div class="fhead" data-lab="%s" data-tap="Label %s"><span class="t">%s</span><span class="c">%d</span>%s</div>' % (
                    lab, lab, lab, len(part), "▸" if closed else "▾") + ("" if closed else wrap("".join(m2_item(it, v) for it in part)))
    link = '<div class="golink" data-tap="Open Activities"><span class="t">Activities</span>›</div>' if v["scope"] == "apart" else ""
    return '<div class="zone">%s%s</div>' % (link, body)


def measure2_phone(v, items=ITEMS12, closed=False):
    title = "Measuring" if (not v.get("control") and v["scope"] == "merged") else "Trackers"
    return kit.phone(kit.header(title, (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>New tracker…</span></div>' + measure2_body(v, items, closed), kit.bar("Hub"))


def measure2_desk(v, theme="light"):
    inner = measure2_phone(v, ITEMS12, v.get("group", "") in ("folding", "hybrid_fit", "hybrid_6", "hybrid_pinned")).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Measuring", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme,
                    CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS)


M2_JS = ("(function(){var vb=document.querySelector('.bar').getBoundingClientRect().top;var o={vb:vb,items:[],heads:[],cut:0,judge:0,says:0,rows:0};"
         "var z=document.querySelector('.zone');o.top=z?z.getBoundingClientRect().top:0;"
         "document.querySelectorAll('[data-tr]').forEach(function(r){var b=r.getBoundingClientRect();var c=[];"
         "r.querySelectorAll('[data-tap]').forEach(function(t){var q=t.getBoundingClientRect();c.push({n:t.dataset.tap,x:q.left+q.width/2,y:q.top+q.height/2,w:Math.round(q.width),h:Math.round(q.height)})});"
         "var nm=r.querySelector('.nm'),s=r.querySelector('.bsub');var cut=0;[nm,s].forEach(function(x){if(x&&x.scrollWidth>x.clientWidth+1)cut++});o.cut+=cut;"
         "if(b.bottom<=vb){o.rows++;if(s&&s.innerText.trim())o.says++}"
         "o.items.push({tr:r.dataset.tr,top:b.top,bottom:b.bottom,c:c})});"
         "document.querySelectorAll('[data-lab]').forEach(function(h){var b=h.getBoundingClientRect();o.heads.push({lab:h.dataset.lab,top:b.top,bottom:b.bottom})});"
         "document.querySelectorAll('[data-judge]').forEach(function(j){var b=j.getBoundingClientRect();if(b.height&&b.bottom<=vb)o.judge++});return o})()")
SEARCH_COST = 3   # ⌕, two letters, the result


def m2_entry(it, v, ctl):
    """Taps on screen for one typical log (activities: start, then stop)."""
    k = it["k"]
    log = "sheet" if ctl else v["log"]
    if k == "activity":
        return 2 if (not ctl and v["scope"] == "merged") else 4
    if k == "number":
        return 3 if not it["usual"] else (2 if log == "sheet" else 1)
    if k == "yesno":
        return 2 if log == "sheet" else 1
    return 3 if log == "sheet" else (2 if v["layout"] == "compact" else 1)   # rating, choice


def m2_measure(v, items, key):
    ctl = v.get("control")
    d = m2doc(measure2_phone(v, items))
    pr = T.probe(d, key, M2_JS)
    vb, top = pr["vb"], pr["top"]
    page = vb - top
    by = {x["tr"]: x for x in pr["items"]}
    heads = {h["lab"]: h for h in pr["heads"]}
    folding = (not ctl) and (v["group"] == "folding" or v["group"].startswith("hybrid"))
    open_top = {it["n"] for it in m2_top(v, items, m2_items(v, items))} if (not ctl and v["group"].startswith("hybrid")) else set()
    if folding:   # all closed at first: label i's header sits at top + 48 i; opening one puts its items under it
        labs = [h["lab"] for h in pr["heads"]]
        folded_top = {lab: pr["heads"][0]["top"] + 48 * i for i, lab in enumerate(labs)}
    tot = cost = 0.0
    reach, oneshot, logged, in_view = [], 0.0, 0.0, 0
    for it in items:
        if it["k"] == "activity" and (ctl or v["scope"] == "apart"):
            tot += it["f"]; cost += it["f"] * m2_entry(it, v, ctl)
            continue
        x = by[it["n"]]
        bottom = x["bottom"]
        extra = 0
        if folding and it["n"] not in open_top:
            h = heads[it["lab"]]
            bottom = folded_top[it["lab"]] + 48 + (x["bottom"] - h["bottom"])
            extra = 1
            if folded_top[it["lab"]] + 48 <= vb:
                in_view += 1
        elif bottom <= vb:
            in_view += 1
        scrolls = 0 if bottom <= vb else math.ceil((bottom - vb) / page)
        visits = 2 if it["k"] == "activity" else 1
        reach_cost = min(scrolls + extra, SEARCH_COST)
        tot += it["f"]
        cost += it["f"] * (m2_entry(it, v, ctl) + visits * reach_cost)
        if it["k"] != "activity":
            logged += it["f"]
            if not ctl and v["log"] == "inline" and m2_entry(it, v, ctl) == 1:
                oneshot += it["f"]
        if (not folding or it["n"] in open_top) and x["c"] and x["bottom"] <= vb:
            reach.append(x["c"][0])
    if folding:   # a folded label's first tap is its header (48 high, the zone's width)
        reach += [{"x": 180, "y": t + 24, "w": 312, "h": 48} for t in folded_top.values() if t + 48 <= vb]
    shown = [it for it in items if not (it["k"] == "activity" and (ctl or v["scope"] == "apart"))]
    span = ((pr["heads"][0]["top"] - top + len(pr["heads"]) * 48) if (folding and pr["heads"]) else max(x["bottom"] for x in pr["items"]) - top) / page
    gate = ["%s %dx%d" % (c["n"], c["w"], c["h"]) for x in pr["items"] if x["bottom"] <= vb for c in x["c"]
            if (c["n"].startswith("Chip ") and (c["w"] < 24 or c["h"] < 24)) or
            (c["n"].startswith(("Log ", "Plus ", "Yes ", "Start ", "Stop ")) and (c["w"] < 48 or c["h"] < 48))]
    if pr["cut"]:
        gate.append("titles cut %d" % pr["cut"])
    return {"taps": round(cost / tot, 3), "overview": round(in_view / len(shown), 3), "screens": round(span, 2),
            "reach": round(sum(T.fitts(THUMB, c) for c in reach) / len(reach), 3) if reach else 9,
            "one_tap_writes": round(oneshot / logged, 3), "says_share": round(pr["says"] / max(1, pr["rows"]), 3),
            "judgment_marks": pr["judge"], "gate": gate}


def score_measure2(v):
    a = m2_measure(v, ITEMS12, "t3-m2-12-%s" % key_of(v))
    b = m2_measure(v, ITEMS30, "t3-m2-30-%s" % key_of(v))
    running = (not v.get("control")) and v["scope"] == "merged"
    return {"taps_12": a["taps"], "taps_30": b["taps"], "overview_12": a["overview"], "overview_30": b["overview"],
            "screens_12": a["screens"], "screens_30": b["screens"], "reach": a["reach"], "one_tap_writes": a["one_tap_writes"],
            "says_share": a["says_share"], "running_shown": 1 if running else 0, "judgment_marks": a["judgment_marks"],
            # items moving on their own as use changes: most used first, or a hybrid's open ones chosen by use
            "moves": 0 if v.get("control") else (1 if (v["order"] == "recent" or v["group"] in ("hybrid_fit", "hybrid_6")) else 0),
            "small": sorted(set(a["gate"] + ["30: " + g for g in b["gate"]]))}


# ==== Part acts: T3b.2 the Activities list (P4 Measuring, taps first; owner, 2026-10-13) ==========================================
"""
  Activities are timed: ▶ starts a session, ■ ends it; several may run at once (SPEC §3.7). Scored as T3b.1c was: taps
  first (within 0.25 a log at both sizes), every item's typical use weighted by how often, the scrolls to reach it from
  where it sits (or a search, 3), at 12 and 30 items, the worse counting.
  Owner's answers (2026-10-13): half the sessions are live, half added afterwards; score every place for running timers;
  and Chronicle's "Last used" (Break Down Timer's timed run: a length and chimes at fractions of it, remembered per
  activity) as an addition, named differently: here "Same as last".
  layout   rows, grid;  says  last, today_last (Trackers' pick and its fuller form)
  arrange  flat (manual), recent (flat, most used first), labels (manual), hybrid (Trackers' pick: the most used open, as
           many as fit, the rest under folded labels)
  running  top (running rows pinned first), place (marked where they are), strip (a strip above the list with each
           running timer and its ■; the rows stay in place)
  past     page (the activity's page: Add time, the length, Save), row (a "+ time" chip on the row opens the same small
           sheet), capture (typed into the capture line at the top: "Studying 40 min", Add; T1.3's line)
  plan     menu (▶ and a ▾ beside it: Start now, Same as last; Chronicle's), chip (a "↻ 25 min" chip beside ▶), default
           (▶ starts Same as last when there is one; ▾ holds Start now), page (only on the activity's page)
  The walk: each activity's sessions, half live (a start, plain or Same as last, then ■), half afterwards. How often a
  live start uses Same as last is unknown: scored at 25% and at 75%, the worse counting. Only activities with a plan
  can use it.
  Measured: taps (the four combinations, the worst rank); Overview (as T3b.1c); whether every running timer is in view on
  arrival; Reach; Glance (rows that say something); Predictable (rows moving on their own: most used first, the hybrid's
  open top, running rows pinned first); Judgment. Gate: no title cut; 48 dp primaries, 24 dp chips.
  Control: Chronicle's Track tab with a dashboard's marks: cards, a streak and a share of the week's goal on each, running
  in place, Same as last and Add time only on the page.
"""
ACTS_SPACE = {"layout": ["rows", "grid"], "says": ["last", "today_last"], "arrange": ["flat", "recent", "labels", "hybrid"],
              "running": ["top", "place", "strip"], "past": ["page", "row", "capture"], "plan": ["menu", "chip", "default", "page"]}


def _ac(n, lab, today, last, f, plan=None, running=None):
    return {"n": n, "lab": lab, "today": today, "last": last, "f": f, "plan": plan, "running": running}


ACTS12 = [
    _ac("Reading", "Mind", "25 min today", "last 21:10", 1, "25 min"), _ac("Cleaning", "Home", "", "last 10:05", 0.5, running="0:12"),
    _ac("Work", "Work", "3 h 10 min today", "last 08:40", 2, "50 min", running="1:05"), _ac("Language practice", "Mind", "", "last Fri", 0.4, "15 min"),
    _ac("Walking", "Moving", "30 min today", "last 13:10", 0.7), _ac("Cooking", "Home", "", "last Sun", 0.7),
    _ac("Guitar", "Making", "", "last Wed", 0.3, "20 min"), _ac("Meditation", "Mind", "", "last Fri", 0.3, "10 min"),
    _ac("Gardening", "Home", "", "last 4 Oct", 0.15), _ac("Studying", "Work", "40 min today", "last 15:00", 1, "45 min"),
    _ac("Email", "Work", "20 min today", "last 11:30", 1), _ac("Yoga", "Moving", "", "last Mon", 0.3, "30 min"),
]
ACTS30 = ACTS12 + [
    _ac("Running", "Moving", "", "last Sat", 0.3, "40 min"), _ac("Cycling", "Moving", "", "last Sun", 0.2), _ac("Drawing", "Making", "", "last Thu", 0.3, "30 min"),
    _ac("Knitting", "Making", "", "last Sat", 0.3), _ac("Writing", "Mind", "", "last Tue", 0.5, "25 min"), _ac("Laundry", "Home", "", "last Mon", 0.3),
    _ac("Shopping", "Home", "", "last Sat", 0.2), _ac("Calls", "Work", "15 min today", "last 12:00", 0.8), _ac("Meetings", "Work", "", "last Fri", 0.6),
    _ac("Planning", "Work", "", "last Mon", 0.4, "15 min"), _ac("Piano", "Making", "", "last Sun", 0.2, "20 min"), _ac("Stretching", "Moving", "", "last Wed", 0.3, "10 min"),
    _ac("Podcast", "Mind", "", "last Thu", 0.3), _ac("Gaming", "Mind", "", "last Sat", 0.3), _ac("Admin", "Work", "", "last Tue", 0.3, "25 min"),
    _ac("Tidying", "Home", "", "last Sun", 0.3), _ac("Baking", "Home", "", "last 1 Oct", 0.1), _ac("Swimming", "Moving", "", "last 28 Sep", 0.1),
]
ACT_LABELS = ["Work", "Mind", "Moving", "Making", "Home"]
ACTS_CSS = """
.astrip{display:flex;flex-direction:column;gap:0;margin-bottom:6px;border-radius:12px;background:var(--zone2);padding:0 4px 0 12px}
.astrip .sr{display:flex;align-items:center;min-height:48px;font-size:14px}.astrip .sr .t{flex:1}
.pmenu{width:28px;height:48px;display:grid;place-items:center;flex:none;color:var(--dim);font-size:12px;margin-left:-6px}
.achip{min-height:48px;display:grid;place-items:center;flex:none}.achip span{border-radius:999px;padding:4px 10px;font-size:12.5px;box-shadow:inset 0 0 0 1px var(--dim);white-space:nowrap}
.aright{display:flex;align-items:center;flex:none}
.kcard .aright{justify-content:flex-end}
"""


def adoc2(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS + ACTS_CSS)


def a_says(it, v):
    if it["running"]:
        return "running %s" % it["running"]
    return it["last"] if v["says"] == "last" else " · ".join(x for x in (it["today"], it["last"]) if x)


def a_ctrls(it, v):
    n = it["n"]
    if it["running"]:
        return '<span class="play" data-tap="Stop %s"><span>■</span></span>' % n
    out = ""
    if v["past"] == "row":
        out += '<span class="achip" data-tap="Time %s"><span>+ time</span></span>' % n
    if v["plan"] == "chip" and it["plan"]:
        out += '<span class="achip" data-tap="Again %s"><span>↻ %s</span></span>' % (n, it["plan"])
    out += '<span class="play" data-tap="Start %s"><span>▶</span></span>' % n
    if v["plan"] in ("menu", "default"):
        out += '<span class="pmenu" data-tap="Menu %s">▾</span>' % n
    return '<span class="aright">%s</span>' % out


def a_item(it, v):
    sub = a_says(it, v)
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span>%s<span class="foot">%s</span></div>' % (it["n"], kit.ud(e(it["n"])), subh, a_ctrls(it, v))
    return '<div class="row krow mrow" data-tap="Open tracker" data-tr="%s"><span class="t"><span class="nm">%s</span>%s</span>%s</div>' % (it["n"], kit.ud(e(it["n"])), subh, a_ctrls(it, v))


def a_order(v, items):
    its = list(items)
    if v["arrange"] in ("recent", "hybrid"):
        its = sorted(its, key=lambda it: -it["f"])
    if v["running"] == "top":
        its = [it for it in its if it["running"]] + [it for it in its if not it["running"]]
    return its


def a_top(v, items):
    """The hybrid's open items: as many of the most used as fit above the folded labels (measured on the flat list)."""
    vf = dict(v, arrange="recent")
    pr = T.probe(adoc2(acts_phone(vf, items)), "t3-actfit-%d-%s" % (len(items), key_of(vf)), M2_JS)
    labs = len({it["lab"] for it in items})
    room = pr["vb"] - 48 * labs
    fit = {x["tr"] for x in pr["items"] if x["bottom"] <= room}
    return [it for it in a_order(vf, items) if it["n"] in fit]


def acts_body(v, items, closed=False):
    if v.get("control"):
        cards = ""
        for it in items:
            cards += ('<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span><span class="bsub"><span data-judge="1">streak %d</span> · '
                      '<span data-judge="1">%d%% of goal</span></span><span class="pbar" data-judge="1"><b style="width:%d%%"></b></span><span class="foot">%s</span></div>') % (
                it["n"], kit.ud(e(it["n"])), len(it["n"]) % 6, (len(it["n"]) * 13) % 100, (len(it["n"]) * 13) % 100,
                ('<span class="play" data-tap="Stop %s"><span>■</span></span>' if it["running"] else '<span class="play" data-tap="Start %s"><span>▶</span></span>') % it["n"])
        return '<div class="zone"><div class="kgrid">%s</div></div>' % cards
    its = a_order(v, items)
    wrap = (lambda h: '<div class="kgrid">%s</div>' % h) if v["layout"] == "grid" else (lambda h: h)
    strip = ""
    if v["running"] == "strip":
        strip = '<div class="astrip">%s</div>' % "".join('<div class="sr"><span class="t">%s · %s</span><span class="play" data-tap="Stop %s"><span>■</span></span></div>' % (
            e(it["n"]), it["running"], it["n"]) for it in items if it["running"])
    if v["arrange"] in ("flat", "recent"):
        body = wrap("".join(a_item(it, v) for it in its))
    else:
        head = ""
        if v["running"] == "top" and v["arrange"] == "labels":   # pinned above the labels while running
            head = wrap("".join(a_item(it, v) for it in its if it["running"]))
            its = [it for it in its if not it["running"]]
        if v["arrange"] == "hybrid":
            top = a_top(v, items)
            head = wrap("".join(a_item(it, v) for it in top))
            its = [it for it in its if it not in top]
        body = head
        labs = [lab for lab in ACT_LABELS if any(it["lab"] == lab for it in its)]
        if v["arrange"] == "hybrid":
            labs = sorted(labs, key=lambda lab: -max(it["f"] for it in its if it["lab"] == lab))
        for lab in labs:
            part = [it for it in its if it["lab"] == lab]
            if v["arrange"] == "labels":
                body += '<div class="dayh" data-lab="%s">%s</div>' % (lab, lab) + wrap("".join(a_item(it, v) for it in part))
            else:
                body += '<div class="fhead" data-lab="%s" data-tap="Label %s"><span class="t">%s</span><span class="c">%d</span>%s</div>' % (
                    lab, lab, lab, len(part), "▸" if closed else "▾") + ("" if closed else wrap("".join(a_item(it, v) for it in part)))
    return '<div class="zone">%s%s</div>' % (strip, body)


def acts_phone(v, items=ACTS12, closed=False):
    ph = "Add an activity or time…" if (not v.get("control") and v["past"] == "capture") else "New activity…"
    return kit.phone(kit.header("Activities", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>%s</span></div>' % ph + acts_body(v, items, closed), kit.bar("Hub"))


def acts_desk(v, theme="light"):
    inner = acts_phone(v, ACTS12, v.get("arrange") == "hybrid").split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Activities", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme,
                    CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS + ACTS_CSS)


def a_costs(it, v, ctl):
    """(live start plain, live start with Same as last, stop, afterwards): taps on screen, no scrolling."""
    plan = "page" if ctl else v["plan"]
    past = "page" if ctl else v["past"]
    plain = {"menu": 1, "chip": 1, "default": 2, "page": 1}[plan] if it["plan"] else 1
    again = {"menu": 2, "chip": 1, "default": 1, "page": 2}[plan] if it["plan"] else plain
    after = {"page": 4, "row": 3, "capture": 3}[past]
    return plain, again, 1, after


def a_measure(v, items, key):
    ctl = v.get("control")
    pr = T.probe(adoc2(acts_phone(v, items)), key, M2_JS)
    vb, top = pr["vb"], pr["top"]
    page = vb - top
    by = {}
    for x in pr["items"]:
        by.setdefault(x["tr"], x)
    heads = {h["lab"]: h for h in pr["heads"]}
    hybrid = (not ctl) and v["arrange"] == "hybrid"
    open_top = {it["n"] for it in a_top(v, items)} if hybrid else set()
    folded_top = {h["lab"]: pr["heads"][0]["top"] + 48 * i for i, h in enumerate(pr["heads"])} if hybrid else {}
    strip_stop = (not ctl) and v["running"] == "strip"
    out = {}
    for p_share in (0.25, 0.75):
        tot = cost = 0.0
        for it in items:
            x = by[it["n"]]
            bottom, extra = x["bottom"], 0
            if hybrid and it["n"] not in open_top:
                h = heads[it["lab"]]
                bottom = folded_top[it["lab"]] + 48 + (x["bottom"] - h["bottom"])
                extra = 1
            reach_row = min((0 if bottom <= vb else math.ceil((bottom - vb) / page)) + extra, SEARCH_COST)
            plain, again, stop, after = a_costs(it, v, ctl)
            start = (p_share * again + (1 - p_share) * plain) if it["plan"] else plain
            stop_reach = 0 if strip_stop else reach_row   # a session's stop: the strip is at the top
            if it["running"] and not ctl and v["running"] == "top":
                stop_reach = 0
            live = start + reach_row + stop + stop_reach
            past = (not ctl) and v["past"] == "capture"
            afterwards = after + (0 if past else reach_row)
            tot += it["f"]
            cost += it["f"] * (0.5 * live + 0.5 * afterwards)
        out[p_share] = round(cost / tot, 3)
    in_view = sum(1 for it in items if (by[it["n"]]["bottom"] <= vb) if not (hybrid and it["n"] not in open_top)) + \
        (sum(1 for it in items if hybrid and it["n"] not in open_top and folded_top[it["lab"]] + 48 <= vb))
    running_seen = all(any(x["tr"] == it["n"] and x["bottom"] <= vb for x in pr["items"]) for it in items if it["running"]) or strip_stop
    span = ((pr["heads"][0]["top"] - top + len(pr["heads"]) * 48) if (hybrid and pr["heads"]) else max(x["bottom"] for x in pr["items"]) - top) / page
    reach = [x["c"][-1] for x in pr["items"] if x["c"] and x["bottom"] <= vb and not (hybrid and x["tr"] not in open_top)]
    gate = ["%s %dx%d" % (c["n"], c["w"], c["h"]) for x in pr["items"] if x["bottom"] <= vb for c in x["c"]
            if (c["n"].startswith(("Time ", "Again ", "Menu ")) and (c["w"] < 24 or c["h"] < 24)) or
            (c["n"].startswith(("Start ", "Stop ")) and (c["w"] < 48 or c["h"] < 48))]
    if pr["cut"]:
        gate.append("titles cut %d" % pr["cut"])
    return {"t25": out[0.25], "t75": out[0.75], "overview": round(in_view / len(items), 3), "screens": round(span, 2), "running_seen": 1 if running_seen else 0,
            "reach": round(sum(T.fitts(THUMB, c) for c in reach) / len(reach), 3) if reach else 9,
            "says_share": round(pr["says"] / max(1, pr["rows"]), 3), "judgment_marks": pr["judge"], "gate": gate}


def score_acts(v):
    a = a_measure(v, ACTS12, "t3-acts-12-%s" % key_of(v))
    b = a_measure(v, ACTS30, "t3-acts-30-%s" % key_of(v))
    ctl = v.get("control")
    moves = 0 if ctl else (1 if (v["arrange"] in ("recent", "hybrid") or v["running"] == "top") else 0)
    return {"taps_12_25": a["t25"], "taps_12_75": a["t75"], "taps_30_25": b["t25"], "taps_30_75": b["t75"],
            "overview_12": a["overview"], "overview_30": b["overview"], "screens_12": a["screens"], "screens_30": b["screens"],
            "running_seen": min(a["running_seen"], b["running_seen"]), "reach": a["reach"], "says_share": a["says_share"],
            "judgment_marks": a["judgment_marks"], "moves": moves, "small": sorted(set(a["gate"] + ["30: " + g for g in b["gate"]]))}


# ==== Part measure3: T3b.1d the Measuring list, trackers and activities as one (owner, 2026-10-14) ================================
"""
  The owner: in Chronicle trackers and activities were both Data, the names only saying how each is measured ("water
  cannot be a timed activity"); they belong on one screen. T3b.1c and T3b.2 scored one list from two sides. The data
  layer does not change (owner: charts still need discrete readings and continuous spans).
  Owner's answers: sizes 12 and 40 (28 logged, 12 timed); re-score everything (the full space); Chronicle's "Last used"
  is the Paced timer (a beginning and an end, planned pauses; the last interval remembered per activity), its sheet
  re-compared with Break Down Timer as its own part next. Here only where it starts from is scored.
  An item's control follows how it is measured: a logged one as T3b.1c (inline: "+ usual", Yes, ratings, recent choices;
  Log for a number with no usual amount; sheet: Log), a timed one ▶ / ■, with its Paced timer per `plan`.
  layout   rows, grid, compact;  says  none, today, last, today_last;  log  sheet, inline
  group    flat, labels, folding, hybrid_fit, hybrid_6, hybrid_pinned (T3b.1c);  order  manual, recent
  running  top, place, strip (T3b.2);  past  page, row, capture (T3b.2);  plan  menu, chip, default, page (T3b.2; the chip
           reads "↻ 25 min", the last interval)
  The walk: every item's typical use, weighted by how often (a placeholder profile). Logged: as T3b.1c. Timed: half live
  (a start, plain or Paced, then ■), half afterwards. The Paced share of live starts is unknown: 25% and 75%, the worse
  counting. T1.3's capture line is always there ("water 2", "Studying 40 min": 3 actions, no scroll), as search is, so
  an item costs the cheaper of its row (with the scrolls or a search to reach it) and the capture line.
  Axes: Taps (12 and 40, Paced 25% and 75%, the worst rank), Overview, Reach, Recovery, Glance (rows that say something;
  every running timer in view), Predictable (moves on its own), Judgment; Refs as information. Lead: fewest taps, within
  0.25 a use. Gate: no title cut; 48 dp primaries, 24 dp chips.
  Control: a dashboard: cards with today against a goal, a streak and a progress bar; Log and the Paced timer through
  their sheet and page; running in place.
"""
MEAS3_SPACE = {"layout": ["rows", "grid", "compact"], "says": ["none", "today", "last", "today_last"], "log": ["sheet", "inline"],
               "group": ["flat", "labels", "folding", "hybrid_fit", "hybrid_6", "hybrid_pinned"], "order": ["manual", "recent"],
               "running": ["top", "place", "strip"], "past": ["page", "row", "capture"], "plan": ["menu", "chip", "default", "page"]}
_PLANS = {"Reading": "25 min", "Language practice": "15 min", "Guitar": "20 min", "Meditation": "10 min", "Work": "50 min", "Writing": "25 min", "Yoga": "30 min"}


def _m3(items):
    out = []
    for it in items:
        it = dict(it)
        if it["k"] == "activity":
            it["plan"] = _PLANS.get(it["n"])
            it["running"] = "0:12" if it["n"] == "Cleaning" else ("1:05" if it["n"] == "Work" else None)
        else:
            it["plan"], it["running"] = None, None
        out.append(it)
    return out


ITEMS3_12 = _m3(ITEMS12)
ITEMS3_40 = _m3(ITEMS30 + [
    _it("Fruit", "number", "Health", "2 today", "last 13:00", 1, "1 piece", 2), _it("Sugar", "yesno", "Health", "", "last Mon", 0.4),
    _it("Calm", "rating", "Mind", "", "last Sat", 0.5), _it("Lunch", "choice", "Health", "Home today", "last 13:00", 1, recent=["Home", "Out"]),
    _it("Push-ups", "number", "Moving", "", "last Fri", 0.3, "10", 0), _it("Rows knitted", "number", "Making", "", "last 2 Oct", 0.1),
    _it("Work", "activity", "Work", "3 h 10 min today", "last 08:40", 2), _it("Writing", "activity", "Making", "", "last Tue", 0.5),
    _it("Yoga", "activity", "Moving", "", "last Mon", 0.3), _it("Email", "activity", "Work", "20 min today", "last 11:30", 1),
])
M3_LABELS = ["Health", "Mind", "Moving", "Making", "Home", "Work"]


def m3doc(html, theme="light"):
    return doc(html, theme, CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS + ACTS_CSS)


def m3_ctrls(it, v):
    """(right-hand controls, chip line) for an item, by how it is measured."""
    if it["k"] != "activity":
        return m2_ctrl(it, v)
    n = it["n"]
    if it["running"]:
        return '<span class="play" data-tap="Stop %s"><span>■</span></span>' % n, ""
    out = ""
    if v["past"] == "row":
        out += '<span class="achip" data-tap="Time %s"><span>+ time</span></span>' % n
    if v["plan"] == "chip" and it["plan"]:
        out += '<span class="achip" data-tap="Paced %s"><span>↻ %s</span></span>' % (n, it["plan"])
    out += '<span class="play" data-tap="Start %s"><span>▶</span></span>' % n
    if v["plan"] in ("menu", "default"):
        out += '<span class="pmenu" data-tap="Menu %s">▾</span>' % n
    return '<span class="aright">%s</span>' % out, ""


def m3_says(it, v):
    if it["running"]:
        return "running %s" % it["running"]
    return m2_says(it, v)


def m3_item(it, v):
    sub = m3_says(it, v)
    subh = '<span class="bsub">%s</span>' % e(sub) if sub else ""
    right, chips = m3_ctrls(it, v)
    if v["layout"] == "grid":
        return '<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span>%s%s<span class="foot">%s</span></div>' % (
            it["n"], kit.ud(e(it["n"])), subh, chips, right)
    return '<div class="row krow mrow" data-tap="Open tracker" data-tr="%s"><span class="t"><span class="nm">%s</span>%s%s</span>%s</div>' % (
        it["n"], kit.ud(e(it["n"])), subh, chips, right)


def m3_order(v, items):
    its = list(items)
    if v["order"] == "recent":
        its = sorted(its, key=lambda it: -it["f"])
    return its


def m3_top(v, items):
    """A hybrid's open items: the 6 most used, or as many of them as fit above the folded labels (measured on the list
    drawn flat, most used first)."""
    by_use = sorted(items, key=lambda it: -it["f"])
    if v["group"] in ("hybrid_6", "hybrid_pinned"):
        return by_use[:6]
    vf = dict(v, group="flat", order="recent")
    pr = T.probe(m3doc(measure3_phone(vf, items)), "t3-m3fit-%d-%s" % (len(items), key_of(vf)), M2_JS)
    room = pr["vb"] - 48 * (len({it["lab"] for it in items}) + (1 if v.get("recent_head") else 0))   # a Recent header takes a row too
    fit = {x["tr"] for x in pr["items"] if x["bottom"] <= room}
    return [it for it in by_use if it["n"] in fit]


def m3_control_item(it):
    have = it["cur"] or (1 if it["today"] else 0)
    goal = max(1, (it["cur"] or 1) * 2)
    pct = round(100 * have / goal)
    if it["k"] == "activity":
        ctl = ('<span class="play" data-tap="Stop %s"><span>■</span></span>' if it["running"] else '<span class="play" data-tap="Start %s"><span>▶</span></span>') % it["n"]
    else:
        ctl = '<span class="act" data-tap="Log %s"><span>Log</span></span>' % it["n"]
    return ('<div class="kcard" data-tap="Open tracker" data-tr="%s"><span class="nm">%s</span><span class="bsub"><span data-judge="1">%s/%s</span> · '
            '<span data-judge="1">%d%%</span> · <span data-judge="1">streak %d</span></span><span class="pbar" data-judge="1"><b style="width:%d%%"></b></span>'
            '<span class="foot">%s</span></div>') % (it["n"], kit.ud(e(it["n"])), have, goal, pct, len(it["n"]) % 7, min(100, pct), ctl)


def measure3_body(v, items, closed=False):
    if v.get("control"):
        return '<div class="zone"><div class="kgrid">%s</div></div>' % "".join(m3_control_item(it) for it in items)
    its = m3_order(v, items)
    wrap = (lambda h: '<div class="kgrid">%s</div>' % h) if v["layout"] == "grid" else (lambda h: h)
    strip = ""
    if v["running"] == "strip":
        strip = '<div class="astrip">%s</div>' % "".join('<div class="sr"><span class="t">%s · %s</span><span class="play" data-tap="Stop %s"><span>■</span></span></div>' % (
            e(it["n"]), it["running"], it["n"]) for it in items if it["running"])
    head = ""
    if v["running"] == "top":   # pinned first while running (above any labels)
        head = wrap("".join(m3_item(it, v) for it in its if it["running"]))
        its = [it for it in its if not it["running"]]
    if v["group"].startswith("hybrid"):
        top = [it for it in m3_top(v, items) if it in its]
        if v.get("recent_head"):   # the open top as a collapsible label of its own, "Recent" (owner, 2026-10-14)
            head += '<div class="fhead" data-rhead="1" data-tap="Label Recent"><span class="t">Recent</span><span class="c">%d</span>▾</div>' % len(top)
        head += wrap("".join(m3_item(it, v) for it in top))
        if not v.get("recent_head"):   # under a Recent header the open ones also stay in their labels: folding Recent hides nothing (2026-10-14)
            its = [it for it in its if it not in top]
    if v["group"] == "flat":
        body = head + wrap("".join(m3_item(it, v) for it in its))
    else:
        body = head
        labs = [lab for lab in M3_LABELS if any(it["lab"] == lab for it in its)]
        if v["order"] == "recent":
            labs = sorted(labs, key=lambda lab: -max(it["f"] for it in its if it["lab"] == lab))
        for lab in labs:
            part = [it for it in its if it["lab"] == lab]
            if v["group"] == "labels":
                body += '<div class="dayh" data-lab="%s">%s</div>' % (lab, lab) + wrap("".join(m3_item(it, v) for it in part))
            else:
                body += '<div class="fhead" data-lab="%s" data-tap="Label %s"><span class="t">%s</span><span class="c">%d</span>%s</div>' % (
                    lab, lab, lab, len(part), "▸" if closed else "▾") + ("" if closed else wrap("".join(m3_item(it, v) for it in part)))
    return '<div class="zone">%s%s</div>' % (strip, body)


def measure3_phone(v, items=ITEMS3_12, closed=False):
    return kit.phone(kit.header("Measuring", (("⌕", "Search"), ("✎", "Edit")), ("‹", "Back")),
                     '<div class="cap" data-tap="Capture">+ <span>Log, time or add…</span></div>' + measure3_body(v, items, closed), kit.bar("Hub"))


def measure3_desk(v, theme="light"):
    folds = v.get("group", "") in ("folding", "hybrid_fit", "hybrid_6", "hybrid_pinned")
    inner = measure3_phone(v, ITEMS3_12, folds).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Measuring", '<div class="dcol" style="width:440px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme,
                    CSS + BASICS_CSS + TRK_CSS + MEAS_CSS + M2_CSS + ACTS_CSS)


CAPTURE_COST = 3   # T1.3's line: tap it, type ("water 2"), Add


def m3_uses(it, v, ctl, p_paced):
    """Taps on screen for an item's typical use (no reaching), and how many times the row must be reached; and the
    capture line's cost for the same use (None: the line cannot do it)."""
    if it["k"] != "activity":
        return m2_entry(it, v, ctl), 1, CAPTURE_COST
    plan = "page" if ctl else v["plan"]
    past = "page" if ctl else v["past"]
    plain = ({"menu": 1, "chip": 1, "default": 2, "page": 1}[plan]) if it["plan"] else 1
    paced = ({"menu": 2, "chip": 1, "default": 1, "page": 2}[plan]) if it["plan"] else plain
    start = p_paced * paced + (1 - p_paced) * plain
    after = {"page": 4, "row": 3, "capture": 3}[past]
    return (start, after), None, CAPTURE_COST


def m3_measure(v, items, key):
    ctl = v.get("control")
    pr = T.probe(m3doc(measure3_phone(v, items)), key, M2_JS)
    vb, top = pr["vb"], pr["top"]
    page = vb - top
    by = {}
    for x in pr["items"]:
        if x["tr"] not in by:
            by[x["tr"]] = x
    heads = {h["lab"]: h for h in pr["heads"]}
    folding = (not ctl) and v["group"] != "flat" and v["group"] != "labels"
    open_top = {it["n"] for it in m3_top(v, items)} if (not ctl and v["group"].startswith("hybrid")) else set()
    if not ctl and v["running"] == "top":
        open_top |= {it["n"] for it in items if it["running"]}
    folded_top = {h["lab"]: pr["heads"][0]["top"] + 48 * i for i, h in enumerate(pr["heads"])} if (folding and pr["heads"]) else {}
    strip = (not ctl) and v["running"] == "strip"
    res = {}
    for p_paced in (0.25, 0.75):
        tot = cost = 0.0
        for it in items:
            x = by[it["n"]]
            bottom, extra = x["bottom"], 0
            if folding and it["n"] not in open_top:
                h = heads[it["lab"]]
                bottom = folded_top[it["lab"]] + 48 + (x["bottom"] - h["bottom"])
                extra = 1
            reach = min((0 if bottom <= vb else math.ceil((bottom - vb) / page)) + extra, SEARCH_COST)
            on, _, cap = m3_uses(it, v, ctl, p_paced)
            if it["k"] != "activity":
                use = min(on + reach, cap)
            else:
                start, after = on
                stop_reach = 0 if (strip or (it["running"] and not ctl and v["running"] == "top")) else reach
                live = start + reach + 1 + stop_reach
                afterwards = min(after + (0 if (not ctl and v["past"] == "capture") else reach), cap)
                use = 0.5 * live + 0.5 * afterwards
            tot += it["f"]
            cost += it["f"] * use
        res[p_paced] = round(cost / tot, 3)
    in_view = 0
    for it in items:
        if folding and it["n"] not in open_top:
            in_view += 1 if folded_top[it["lab"]] + 48 <= vb else 0
        else:
            in_view += 1 if by[it["n"]]["bottom"] <= vb else 0
    running_seen = strip or all(by[it["n"]]["bottom"] <= vb for it in items if it["running"])
    span = ((pr["heads"][0]["top"] - top + len(pr["heads"]) * 48) if (folding and pr["heads"]) else max(x["bottom"] for x in pr["items"]) - top) / page
    reach_t = [x["c"][-1] for x in pr["items"] if x["c"] and x["bottom"] <= vb and not (folding and x["tr"] not in open_top)]
    if folding:
        reach_t += [{"x": 180, "y": t + 24, "w": 312, "h": 48} for t in folded_top.values() if t + 48 <= vb]
    logged = sum(it["f"] for it in items if it["k"] != "activity")
    oneshot = sum(it["f"] for it in items if it["k"] != "activity" and not ctl and v["log"] == "inline" and m2_entry(it, v, ctl) == 1)
    gate = ["%s %dx%d" % (c["n"], c["w"], c["h"]) for x in pr["items"] if x["bottom"] <= vb for c in x["c"]
            if (c["n"].startswith(("Chip ", "Time ", "Paced ", "Menu ")) and (c["w"] < 24 or c["h"] < 24)) or
            (c["n"].startswith(("Log ", "Plus ", "Yes ", "Start ", "Stop ")) and (c["w"] < 48 or c["h"] < 48))]
    if pr["cut"]:
        gate.append("titles cut %d" % pr["cut"])
    return {"t25": res[0.25], "t75": res[0.75], "overview": round(in_view / len(items), 3), "screens": round(span, 2),
            "running_seen": 1 if running_seen else 0, "reach": round(sum(T.fitts(THUMB, c) for c in reach_t) / len(reach_t), 3) if reach_t else 9,
            "one_tap_writes": round(oneshot / logged, 3), "says_share": round(pr["says"] / max(1, pr["rows"]), 3), "judgment_marks": pr["judge"], "gate": gate}


def score_measure3(v):
    a = m3_measure(v, ITEMS3_12, "t3-m3-12-%s" % key_of(v))
    b = m3_measure(v, ITEMS3_40, "t3-m3-40-%s" % key_of(v))
    ctl = v.get("control")
    moves = 0 if ctl else (1 if (v["order"] == "recent" or v["group"] in ("hybrid_fit", "hybrid_6") or v["running"] == "top") else 0)
    return {"taps_12_25": a["t25"], "taps_12_75": a["t75"], "taps_40_25": b["t25"], "taps_40_75": b["t75"],
            "overview_12": a["overview"], "overview_40": b["overview"], "screens_12": a["screens"], "screens_40": b["screens"],
            "running_seen": min(a["running_seen"], b["running_seen"]), "reach": a["reach"], "one_tap_writes": a["one_tap_writes"],
            "says_share": a["says_share"], "judgment_marks": a["judgment_marks"], "moves": moves,
            "small": sorted(set(a["gate"] + ["40: " + g for g in b["gate"]]))}


# ==== Part pace: T3b.4 the Paced timer sheet (owner, 2026-10-14) =================================================================
"""
  The owner: Chronicle's "Last used" was wrongly named. It opens a different, more sophisticated kind of tracking, a run
  with a beginning and an end and planned pauses: the Paced timer, remembering its last interval per activity
  (the chip on the Measuring list starts that one). Re-compared with Break Down Timer (de.jepfa.bdt, captured
  2026-10-14: presets cycled with ‹ ›, a pin; a length or finish-time switch of two icons; a 60-slice ring, a tap
  toggling a numbered break labelled with its time; the system clock picker for the length; Repeat once / forever /
  none under Start's ▾). Its breaks are instants (a chime); Chronicle's rests with a length were never built.
  Owner's answers: pauses of both kinds (a chime, or a rest with a length); a beginning and an end by length, by
  finish time, or from a later start; axes Taps, Ease, Precision, Consistency with When, target size as a gate;
  every way of placing pauses scored.
  mode    switch (For | Until | From as a segmented control, then one writable box per time), sentence (the When sheet's:
          "For [25 min]", the first word cycling For, Until, From…to; one writable box per time), fields (Starts and Ends
          rows, each opening a picker)
  place   ring (BDT's 60 slices, a tap toggles a pause), line (a bar from start to end, a pause dragged to its minute
          with a readout), presets (chips: ½, ⅓, ¼s, every 15 min, ½ ¼ ⅛, Split into…), sentence ("with [a chime]
          [halfway]", the words cycling: halfway / every [n] / at [time]; chime / [n]-min rest), ring + presets,
          line + presets
  Each pause's kind under the placer (Chime | Rest [5 min]), but in the sentence, where it is a word.
  The walk: (1) 25 min, a chime halfway; (2) until 15:30 (from 13:00), a chime every 15 min; (3) from 14:00 to 15:30,
  a 5-min rest in the middle. Starting the remembered run is the list's chip, the same in every option, so not walked.
  Measured: Taps (the walk's); Ease (keyboards opened; reach to the sheet's targets); Precision (a pause at any exact
  minute; the smallest step on a 150-min run); Consistency with When (the run and the pauses as a sentence with
  writable boxes). Gate: pause places 24 dp (a chooser's), Start 48 dp; a ring slice is its outer arc.
  Control: Break Down Timer as it is (no later start, no rests: those runs count 9 taps each, as undoable).
"""
PACE_SPACE = {"mode": ["switch", "sentence", "fields"], "place": ["ring", "line", "presets", "sentence", "ring_presets", "line_presets"]}
PACE_CSS = """
.psheet{position:absolute;left:0;right:0;bottom:0;background:var(--zone);border-radius:20px 20px 0 0;padding:12px 16px 16px;box-shadow:0 -8px 24px rgba(0,0,0,.14);max-height:640px;overflow:hidden}
.psheet h3{margin:0 0 8px;font-size:17px}.seg{display:flex;border-radius:24px;box-shadow:inset 0 0 0 1px var(--dim);overflow:hidden;margin-bottom:8px}
.seg span{flex:1;min-height:48px;display:grid;place-items:center;font-size:14px}.seg span.on{background:var(--zone2);font-weight:600}
.psent{font-size:19px;line-height:2.3}.ptok{border-bottom:2px dotted var(--dim);padding:0 2px;min-height:48px;display:inline-block;line-height:48px}
.pbox{display:inline-block;min-width:64px;min-height:44px;line-height:44px;padding:0 10px;border-radius:10px;box-shadow:inset 0 0 0 1.5px var(--dim);text-align:center;font-size:17px;margin:0 2px}
.prow{display:flex;align-items:center;min-height:48px;border-bottom:1px solid var(--zone2);font-size:15px}.prow .t{flex:1;color:var(--dim)}
.pline{position:relative;height:56px;margin:8px 4px}.pline .bar{position:absolute;left:0;right:0;top:20px;height:8px;border-radius:4px;background:var(--zone2)}
.pline .mk{position:absolute;top:0;width:48px;height:48px;margin-left:-24px;display:grid;place-items:center}.pline .mk i{width:14px;height:28px;border-radius:4px;background:var(--ink)}
.pline .lab{position:absolute;top:44px;font-size:11px;color:var(--dim);transform:translateX(-50%)}
.pchips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}.pchips span{min-height:32px;min-width:32px;padding:0 10px;border-radius:16px;display:grid;place-items:center;font-size:13px;box-shadow:inset 0 0 0 1px var(--dim)}
.pchips span.on{background:var(--zone2);box-shadow:none;font-weight:600}
.plist{font-size:13px;color:var(--dim);margin:4px 0}.pstart{min-height:48px;border-radius:24px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:600;margin-top:8px}
.pring{display:block;margin:4px auto}
"""


def pdoc(html, theme="light"):
    return doc(html, theme, CSS + PACE_CSS)


def p_mode_html(v):
    if v["mode"] == "switch":
        return ('<div class="seg"><span class="on" data-tap="Mode For">For</span><span data-tap="Mode Until">Until</span><span data-tap="Mode From">From…to</span></div>'
                '<div class="psent"><span class="pbox" data-tap="Box a">%s</span> · ends 13:25</div>') % kit.ud("25 min")
    if v["mode"] == "sentence":
        return '<div class="psent"><span class="ptok" data-tap="Tok For">For</span> <span class="pbox" data-tap="Box a">%s</span> <span class="small">· ends 13:25</span></div>' % kit.ud("25 min")
    return ('<div class="prow" data-tap="Row Starts"><span class="t">Starts</span>Now ▸</div>'
            '<div class="prow" data-tap="Row Ends"><span class="t">Ends</span>After 25 min ▸</div>')


def p_ring():
    import math as _m
    cx = cy = 120
    r1, r2 = 70, 112
    out = []
    for i in range(60):
        a0, a1 = 2 * _m.pi * i / 60 - _m.pi / 2, 2 * _m.pi * (i + 1) / 60 - _m.pi / 2
        pts = [(cx + r2 * _m.cos(a0), cy + r2 * _m.sin(a0)), (cx + r2 * _m.cos(a1), cy + r2 * _m.sin(a1)),
               (cx + r1 * _m.cos(a1), cy + r1 * _m.sin(a1)), (cx + r1 * _m.cos(a0), cy + r1 * _m.sin(a0))]
        d = "M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z" % tuple(c for p in pts for c in p)
        out.append('<path d="%s" fill="%s" stroke="var(--zone)" stroke-width="1" data-slice="%d"/>' % (d, "var(--ink)" if i == 30 else "var(--zone2)", i))
    return ('<svg class="pring" data-ring="1" width="240" height="240" viewBox="0 0 240 240">%s<text x="120" y="126" text-anchor="middle" font-size="15" fill="var(--ink)">25 min</text></svg>'
            % "".join(out))


def p_place_html(v):
    pl = v["place"]
    out = ""
    if pl in ("ring", "ring_presets"):
        out += p_ring()
    if pl in ("line", "line_presets"):
        out += ('<div class="pline" data-line="1"><span class="bar"></span><span class="mk" style="left:50%%" data-tap="Mark 1"><i></i></span>'
                '<span class="lab" style="left:0">13:00</span><span class="lab" style="left:50%%">13:12</span><span class="lab" style="left:100%%">13:25</span></div>')
    if pl in ("presets", "ring_presets", "line_presets"):
        out += '<div class="pchips">%s</div>' % "".join('<span class="%s" data-tap="Chip %s">%s</span>' % ("on" if c == "½" else "", c, c)
                                                      for c in ("½", "⅓", "¼ ¼ ¼", "every 15 min", "½ ¼ ⅛", "Split into…"))
    if pl == "sentence":
        out += ('<div class="psent">with <span class="ptok" data-tap="Tok kind">a chime</span> <span class="ptok" data-tap="Tok where">halfway</span>'
                ' <span class="small" data-tap="Tok add">+ pause</span></div>')
    else:
        out += '<div class="seg"><span class="on" data-tap="Kind Chime">Chime</span><span data-tap="Kind Rest">Rest · 5 min</span></div>'
    out += '<div class="plist">1 chime · 13:12</div>'
    return out


def pace_phone(v):
    if v.get("control"):
        sheet = ('<div class="psheet"><h3>Reading</h3><div class="seg"><span class="on" data-tap="Mode For">⏱</span><span data-tap="Mode Until">⏰</span></div>%s'
                 '<div class="plist">1 breaks placed</div><div class="pstart" data-tap="Start">▶ Start ▾</div></div>') % p_ring()
    else:
        sheet = '<div class="psheet"><h3>Paced timer · Reading</h3>%s%s<div class="pstart" data-tap="Start">▶ Start</div></div>' % (p_mode_html(v), p_place_html(v))
    return kit.phone(kit.header("Measuring", (("⌕", "Search"),), ("‹", "Back")), '<div class="scrim"></div>' + sheet, kit.bar("Hub"))


PACE_JS = ("(function(){var r=document.querySelector('[data-ring]');var o={ring:0,top:0};if(r){var b=r.getBoundingClientRect();o.ring=b.width}"
           "var s=document.querySelector('.psheet').getBoundingClientRect();o.top=s.top;return o})()")
# the walk, per option: (taps, keyboards) for runs 1, 2 and 3 (see the docstring)
P_MODE = {"switch": [(1, 1), (2, 1), (3, 1)], "sentence": [(1, 1), (2, 1), (4, 1)], "fields": [(3, 0), (3, 0), (6, 0)]}
P_PLACE = {"ring": [(1, 0), (9, 0), (3, 1)], "line": [(1, 0), (9, 0), (3, 1)], "presets": [(1, 0), (1, 0), (3, 1)], "sentence": [(1, 0), (3, 1), (3, 1)],
           "ring_presets": [(1, 0), (1, 0), (3, 1)], "line_presets": [(1, 0), (1, 0), (3, 1)]}
P_EXACT = {"ring": 0, "line": 1, "presets": 0, "sentence": 1, "ring_presets": 0, "line_presets": 1}
P_STEP = {"ring": 2.5, "line": 1, "presets": 9.4, "sentence": 1, "ring_presets": 2.5, "line_presets": 1}   # minutes, a 150-min run (presets: its 1/16)


def score_pace(v):
    ctl = v.get("control")
    d = pdoc(pace_phone(v))
    tp = T.taps(d)
    pr = T.probe(d, "t3-pace-%s" % key_of(v), PACE_JS)
    if ctl:   # BDT: the clock picker (centre, hour, minute, OK); runs 2's switch; run 3 cannot be made (no later start, no rest)
        taps, kbd = 4 + 1 + (1 + 4 + 9), 0
        exact, step, like = 0, 2.5, 0
    else:
        taps = sum(m[0] + p[0] for m, p in zip(P_MODE[v["mode"]], P_PLACE[v["place"]]))
        kbd = sum(m[1] + p[1] for m, p in zip(P_MODE[v["mode"]], P_PLACE[v["place"]]))
        exact, step = P_EXACT[v["place"]], P_STEP[v["place"]]
        like = {"sentence": 1, "switch": 0.5, "fields": 0}[v["mode"]] + (1 if v["place"] == "sentence" else 0)
    seen = [x for x in tp.all if x.get("seen")]
    reach = [T.fitts(THUMB, x) for x in seen if x["name"] not in ("Back", "Search", "Hub", "Today", "Calendar", "Pages", "Check-in")]
    gate = ["%s %dx%d" % (x["name"], x["w"], x["h"]) for x in seen if
            (x["name"].startswith(("Chip ", "Tok ", "Kind ", "Mark ", "Mode ", "Box ", "Row ")) and (x["w"] < 24 or x["h"] < 24)) or (x["name"] == "Start" and (x["w"] < 48 or x["h"] < 48))]
    arc = round(3.14159 * pr["ring"] / 60, 1) if pr["ring"] else None
    if arc is not None and arc < 24 and not ctl:   # the control keeps it measured, not gated: a gated control would not count as beaten
        gate.append("ring slice %.1f dp" % arc)
    return {"ring_slice_dp": arc, "taps": taps, "keyboards": kbd, "reach": round(sum(reach) / len(reach), 3) if reach else 9, "exact_any": exact, "step_min": step,
            "like_when": like, "small": sorted(set(gate))}


def build_refs():
    with open(os.path.join(T.OUT, "t3-references.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    out = {"habits": [], "basics": []}
    for r in src["habits_list"]:
        if r["app"] == "org.isoron.uhabits":
            out["habits"].append({"app": r["app"], "presence": None, "group": "flat", "log": "cells", "amount": "plain"})
        elif r["app"] == "com.tendril.app.debug":
            out["habits"].append({"app": r["app"], "presence": "none", "group": "blocks", "log": "row", "amount": "plain"})
    out["basics"] = [{"app": "org.isoron.uhabits", "layout": None, "filter": None, "mark": "none", "done": "stay"},
                     {"app": "com.tendril.app.debug", "layout": "blocks", "filter": None, "mark": "none", "done": "stay"}]
    out["acts"] = [{"app": r["app"], **r["as_space"]} for r in src.get("activities_list", [])]
    out["measure2"] = [{"app": r["app"], "scope": "apart", "order": "manual", **{k: (x if k != "group" or x != "labels" else "folding") for k, x in r["as_space"].items()}}
                       for r in src.get("trackers_list", [])]   # Chronicle's categories fold
    out["measure"] = [{"app": r["app"], "scope": "apart", **r["as_space"]} for r in src.get("trackers_list", [])]
    out["trackers"] = [{"app": r["app"], **r["as_space"]} for r in src.get("trackers_list", [])]
    with open(os.path.join(T.OUT, "t3-refs.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)


# ==== the tables and pages through toast_opt's machinery =========================================================================
T.PREFIX, T.REFS, T.NAME = "t3", "t3-refs.json", "T3 habits, trackers, time, goals, charts and checklists"
T.OUT = os.path.join(os.path.dirname(M2.T.OUT), "t3")
# T3.1 "habits" (presence, the first scoring) is kept in t3-habits-v1.json and in the code above; T3a replaced it (owner, 2026-10-13)
T.SPACES = {"pace": PACE_SPACE, "measure3": MEAS3_SPACE, "acts": ACTS_SPACE, "measure2": MEAS2_SPACE, "measure": MEAS_SPACE, "trackers": TRK_SPACE, "basics": BASICS_SPACE, "addhabit": ADD_SPACE, "routines": ROUT_SPACE, "addsent": SENT_SPACE, "hsheet": HSHEET_SPACE, "premise": PREMISE_SPACE, "habits2": H2_SPACE}
T.SCORERS = {"pace": score_pace, "measure3": score_measure3, "acts": score_acts, "measure2": score_measure2, "measure": score_measure, "trackers": score_trackers, "basics": score_basics, "addhabit": score_addhabit, "routines": score_routines, "addsent": score_addsent, "hsheet": score_hsheet, "premise": score_premise, "habits2": score_habits2}
T.CONTROLS = {"pace": ({"mode": "bdt", "place": "bdt", "control": True}, "Break Down Timer as it is: two mode icons, the clock picker, the 60-slice ring; no later start, no rests"),
              "measure3": ({"layout": "grid", "says": "goal", "log": "sheet", "group": "flat", "order": "manual", "running": "place", "past": "page", "plan": "page", "control": True},
                           "a dashboard: cards with today against a goal ('3/8 · 38%'), a streak and a progress bar; Log, a past session and the Paced timer through sheets and pages; running in place"),
              "acts": ({"layout": "grid", "says": "last", "arrange": "flat", "running": "place", "past": "page", "plan": "page", "control": True},
                       "Chronicle's Track tab with a dashboard's marks: cards with a streak and a share of the week's goal, running in place, Same as last and Add time on the page only"),
              "measure2": ({"scope": "apart", "layout": "grid", "says": "goal", "log": "sheet", "group": "flat", "order": "manual", "control": True},
                           "T3b.1's dashboard: today against a goal ('3/8 · 38%'), a progress bar, a streak; Log through the sheet; activities apart"),
              "measure": ({"scope": "apart", "layout": "grid", "says": "goal", "log": "sheet", "group": "flat", "control": True},
                          "T3b.1's dashboard: today against a goal ('3/8 · 38%'), a progress bar, a streak, the 7-day bars; Log through the sheet; activities apart"),
              "trackers": ({"layout": "grid", "says": "goal", "log": "sheet", "group": "flat", "control": True},
                           "a dashboard: each card with today against its goal ('3/8 · 38%'), a progress bar, a streak and the 7-day bars"),
              "habits2": ({"group": "checklist", "name": "progress", "control": True}, "every if as a checklist with progress: '1/4 done · 25%'"),
              "premise": ({"premise": "all", "control": True}, "the premise box opens every if, whatever the connective (the prototype before this scoring)"),
              "hsheet": ({"blank": "tendril", "control": True}, "Tendril's Add habit sheet: no weekdays, no energy (the new walk cannot be done)"),
              "addsent": ({"form": "tendril", "energy": "none", "routine": "none", "control": True}, "Tendril's sheet as it is, the cue last (as in T3a.2)"),
              "routines": ({"preview": "progress", "seq": "plain", "control": True}, "the routine as a checklist with progress: '1/4 done · 25%' under its name, the steps plain"),
              "addhabit": ({"form": "tendril", "cue": "last", "block": "where", "control": True},
                           "Tendril's sheet as it is, the cue last: schedule, every N, where, counts something, area, note, Cancel and Add"),
              "basics": ({"layout": "blocks", "filter": "chips", "mark": "streak", "done": "fold", "control": True},
                         "the leading design with history added: a streak and a share of days on every row"),
              "habits": ({"presence": "streak", "group": "flat", "log": "cells", "amount": "percent", "control": True},
                         "Loop-like with streaks and a score: a streak and a percentage on every row, the last 4 days as ticks and crosses")}
T.AXES = {"pace": {"Taps": ("taps",), "Ease": ("keyboards", "reach"), "Precision": ("-exact_any", "step_min"), "Consistency": ("-like_when",)},
          "measure3": {"Taps": ("max:taps_12_25|taps_12_75|taps_40_25|taps_40_75",), "Overview": ("max:-overview_12|-overview_40", "max:screens_12|screens_40"),
                       "Reach": ("reach",), "Recovery": ("one_tap_writes",), "Glance": ("-says_share", "-running_seen"), "Predictable": ("moves",), "Judgment": ("judgment_marks",)},
          "acts": {"Taps": ("max:taps_12_25|taps_12_75|taps_30_25|taps_30_75",), "Overview": ("max:-overview_12|-overview_30", "max:screens_12|screens_30"),
                   "Reach": ("reach",), "Glance": ("-says_share", "-running_seen"), "Predictable": ("moves",), "Judgment": ("judgment_marks",)},
          "measure2": {"Taps": ("max:taps_12|taps_30",), "Overview": ("max:-overview_12|-overview_30", "max:screens_12|screens_30"),
                       "Reach": ("reach",), "Recovery": ("one_tap_writes",), "Glance": ("-says_share", "-running_shown"), "Judgment": ("judgment_marks",), "Predictable": ("moves",)},
          "measure": {"Taps": ("taps_mean",), "Reach": ("reach_mean",), "Recovery": ("one_tap_writes",), "Glance": ("-says_share", "-running_shown"),
                      "Judgment": ("judgment_marks",), "Find": ("scan_steps",)},
          "trackers": {"Ease": ("taps_count", "reach_log"), "Predictable": ("log_varies", "unconfirmed"), "Glance": ("-says_share",),
                       "Judgment": ("judgment_marks",), "Find": ("scan_steps",), "Consistency": ("like_today",),
                       "Density": ("-rows_seen", "cut", "words_per_row"), "Calm": ("clutter", "desk_clutter")},
          "habits2": {"Judgment": ("judgment_marks",), "Clarity": ("-uniform", "-names_in_view"), "Low capacity": ("words_per_row",),
                      "Density": ("-rows_seen", "cut", "header_px"), "Calm": ("clutter", "desk_clutter")},
          "premise": {"Ease": ("taps_join", "typed_join", "taps_new"), "Duplicate guard": ("-duplicate_guard",), "Room with keyboard": ("-sentence_in_view", "clutter"),
                      "Scan load": ("scan_rows",)},
          "hsheet": {"Ease": ("taps_join", "taps_new"), "Stability": ("sentence_moves",), "Clarity": ("-reads_as_sentence",), "Consistency": ("like_when",), "Calm": ("clutter",)},
          "addsent": {"Ease": ("taps", "keyboards", "taps_lone", "keyboards_lone", "reach", "hidden_targets"), "Clarity": ("-sentence_reads",),
                      "Safety": ("lost_on_back",), "Consistency": ("like_when",), "Context": ("-context_rows",), "Calm": ("clutter", "desk_clutter")},
          "routines": {"Judgment": ("judgment_marks",), "Expect": ("-forecast_facts", "-order_marked", "-low_says_hidden"), "Low capacity": ("words_per_row",),
                       "Density": ("-rows_seen", "cut"), "Calm": ("clutter", "desk_clutter")},
          "addhabit": {"Ease": ("taps", "keyboard", "reach", "hidden_targets"), "Complete": ("energy_field",), "Context": ("-context_rows",),
                       "Clarity": ("-fields_seen",), "Safety": ("lost_on_back",), "Consistency": ("like_item_page",), "Calm": ("clutter", "desk_clutter")},
          "basics": {"Judgment": ("judgment_marks",), "Cue": ("-cue_shown", "disorder"), "Low capacity": ("words_per_row", "filter_actions", "reach_filter", "reach_log"),
                     "Choice": ("-filter_says_mid",), "Consistency": ("like_today",), "Density": ("-rows_seen", "cut"), "Calm": ("clutter", "desk_clutter")},
          "habits": {"Ease": ("log_actions", "reach_log"), "Presence": ("-presence_shown", "presence_marks"), "Calm": ("guilt_marks", "clutter", "desk_clutter"),
                     "Density": ("-rows_seen", "cut"), "Consistency": ("like_today",)}}
T.TITLES = {"pace": "T3b.4 The Paced timer sheet: setting the run, placing pauses (chimes or rests)", "measure3": "T3b.1d The Measuring list: trackers and activities as one, each item's control by how it is measured", "acts": "T3b.2 The Activities list: running timers, adding a past session, Same as last (Chronicle's Last used)", "measure2": "T3b.1c The Measuring list, scroll counted at 12 and 30 items: compact rows, folding labels, most used first", "measure": "T3b.1b The Measuring list, taps first: merged with activities or apart, rows or cards, what Log does (a control per kind)", "trackers": "T3b.1 The Trackers list: rows or cards, what a row says, what Log does, grouping", "habits2": "T3a.1c The Habits list: the optional name, and every if as a header", "premise": "T3a.2d What tapping the premise box opens: nothing, or the ifs with the same connective", "hsheet": "T3a.2c The New habit sheet (prototype): the blanks as text boxes in the sentence, or opened above it", "addsent": "T3a.2b Adding a habit as an open sentence: the When sheet, in place, or fields; energy and routine as words or rows", "routines": "T3a.1b The Habits list with routines: the 'what to expect' preview, how the sequence shows", "addhabit": "T3a.2 Adding a habit: in place or a sheet, the If, the block", "basics": "T3a.1 Habits as Daily basics: layout, the energy filter, its mark, done today", "habits": "T3.1 The Habits list: presence, grouping, where Log sits, a count's amount"}
T.DRAW = {"pace": lambda v: [pdoc(pace_phone(v))], "measure3": lambda v: [m3doc(measure3_phone(v, ITEMS3_12, v.get("group", "") not in ("flat", "labels"))), m3doc(measure3_phone(v, ITEMS3_40)), measure3_desk(v)], "acts": lambda v: [adoc2(acts_phone(v, ACTS12, v.get("arrange") == "hybrid")), adoc2(acts_phone(v, ACTS30)), acts_desk(v)], "measure2": lambda v: [m2doc(measure2_phone(v, ITEMS12, v.get("group", "") in ("folding", "hybrid_fit", "hybrid_6", "hybrid_pinned"))), m2doc(measure2_phone(v, ITEMS30)), measure2_desk(v)], "measure": lambda v: [mdoc(measure_phone(v)), measure_desk(v)], "trackers": lambda v: [tdoc(trackers_phone(v))] + ([] if v.get("control") else [tdoc(trackers_phone(v, True))]) + [trackers_desk(v)], "habits2": lambda v: [h2doc(habits2_phone(v)), habits2_desk(v)], "premise": lambda v: [premise_doc(v)], "hsheet": lambda v: [adoc(addhabit_phone({"control": True}))] if v.get("control") else [hsheet_doc(v, st) for _, _, st in HSTATES], "addsent": lambda v: [sdoc(addsent_phone(v))] + ([] if (v.get("control") or v["form"] == "fields") else [sdoc(addsent_phone(v, True))]), "routines": lambda v: [rdoc(routines_phone(v)), rdoc(routines_phone(v, "low")), routines_desk(v)], "addhabit": lambda v: [adoc(addhabit_phone(v))], "basics": lambda v: [bdoc(basics_phone(v)), basics_desk(v)], "habits": lambda v: [hdoc(habits_phone(v)), habits_desk(v)]}
T.POOL = {"trackers": lambda ok: [min((r for r in ok if r.get("front") and r["v"]["layout"] == lay and r["v"]["log"] == lg), key=lambda r: r["total"])
                                    for lay in ("rows", "grid") for lg in ("sheet", "default", "stepper")
                                    if any(r.get("front") and r["v"]["layout"] == lay and r["v"]["log"] == lg for r in ok)]
                       + [r for r in ok if r["v"]["layout"] == "rows" and r["v"]["log"] == "sheet" and r["v"]["group"] == "labels" and r["v"]["says"] != "none"]}
T.POOL["measure"] = lambda ok: [r for r in ok if r.get("front")]   # the taps-led front
T.DRAW_MAX["measure"] = 8
T.LEAD["measure"] = ("taps_mean", 0.17)   # fewest taps first (owner, 2026-10-13); 0.17 is one tap in the six-entry walk
T.REFS_INFO.add("measure")
T.REFS_INFO.add("measure2")
T.REFS_INFO.add("acts")
T.REFS_INFO.add("measure3")
T.LEAD["measure3"] = [("taps_12_25", 0.25), ("taps_12_75", 0.25), ("taps_40_25", 0.25), ("taps_40_75", 0.25)]   # fewest taps, within 0.25 a use
T.POOL["measure3"] = lambda ok: [r for r in ok if r.get("front")]
T.DRAW_MAX["measure3"] = 8
T.LEAD["acts"] = [("taps_12_25", 0.25), ("taps_12_75", 0.25), ("taps_30_25", 0.25), ("taps_30_75", 0.25)]   # as T3b.1c: fewest taps, within 0.25 a log
T.POOL["acts"] = lambda ok: [r for r in ok if r.get("front")]
T.DRAW_MAX["acts"] = 8
T.LEAD["measure2"] = [("taps_12", 0.25), ("taps_30", 0.25)]   # fewest taps first at both sizes, within 0.25 a log (one tap more in four logs; owner, 2026-10-13, widened from 0.1 for the hybrids)
T.POOL["measure2"] = lambda ok: [r for r in ok if r.get("front")]
T.DRAW_MAX["measure2"] = 8   # the references all log through a sheet: shown, not ranked (owner, 2026-10-13)
T.DRAW_MAX["trackers"] = 10   # and the leader's family with each thing a row can say: whether a row says anything is the trade (Glance against Calm)   # the best of each family drawn: a front of 40 would draw one family
# the owner's picks (decision 19) shown, the rest folded; superseded parts folded whole (owner, 2026-10-13)
T.PICKED = {"routines": [{"preview": "none", "seq": "plain"}, {"preview": "energy", "seq": "numbers"}], "hsheet": [{"blank": "inline"}], "premise": [{"premise": "same"}],
            "habits2": [{"group": "routines", "name": "named"}],
            "measure2": [{"scope": "apart", "layout": "rows", "says": "last", "log": "inline", "group": "hybrid_fit", "order": "recent"}],
            "measure3": [{"layout": "rows", "says": "last", "log": "inline", "group": "hybrid_fit", "order": "recent", "running": "strip", "past": "page", "plan": "chip"}]}
T.SUPERSEDED = {"measure2": "trackers and activities are one screen (owner, 2026-10-14): T3b.1d replaced it; its pick shaped T3b.1d's space",
                "acts": "trackers and activities are one screen (owner, 2026-10-14): T3b.1d replaced it", "measure": "scroll was undercounted (owner, 2026-10-13): T3b.1c replaced it", "trackers": "P4 Measuring is scored taps first (owner, 2026-10-13): T3b.1b replaced it", "habits": "re-cut by purpose; T3a.1 Daily basics replaced it", "basics": "routines replaced it (T3a.1b)",
                "addhabit": "the open sentence replaced it (T3a.2b), then the prototype (T3a.2c)", "addsent": "the prototype sheet replaced it (T3a.2c)"}
T.v2.TOL.setdefault("_reach_log", 0.05)
T.v2.TOL.setdefault("_reach_mean", 0.05)
T.v2.TOL.setdefault("_reach_filter", 0.05)


if __name__ == "__main__":
    os.makedirs(T.OUT, exist_ok=True)
    build_refs()
    for p in T.SPACES:
        if p in sys.argv[1:]:
            T.run_part(p)
    if "page_html" in sys.argv[1:]:
        T.options_page()
    if "scores" in sys.argv[1:]:
        T.scores_page()
