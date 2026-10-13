"""T3 habits, trackers, time, goals, charts and checklists (decision 19), scored as T2 was, a control per part.

    python tools/screens/t3_opt.py habits                 score a part (docs/screens/t3/t3-<part>.json)
    python tools/screens/t3_opt.py page_html scores       t3-options.html, t3-scores.html (fails if a control wins)

Parts:
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
    with open(os.path.join(T.OUT, "t3-refs.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)


# ==== the tables and pages through toast_opt's machinery =========================================================================
T.PREFIX, T.REFS, T.NAME = "t3", "t3-refs.json", "T3 habits, trackers, time, goals, charts and checklists"
T.OUT = os.path.join(os.path.dirname(M2.T.OUT), "t3")
# T3.1 "habits" (presence, the first scoring) is kept in t3-habits-v1.json and in the code above; T3a replaced it (owner, 2026-10-13)
T.SPACES = {"basics": BASICS_SPACE, "addhabit": ADD_SPACE, "routines": ROUT_SPACE, "addsent": SENT_SPACE, "hsheet": HSHEET_SPACE, "premise": PREMISE_SPACE, "habits2": H2_SPACE}
T.SCORERS = {"basics": score_basics, "addhabit": score_addhabit, "routines": score_routines, "addsent": score_addsent, "hsheet": score_hsheet, "premise": score_premise, "habits2": score_habits2}
T.CONTROLS = {"habits2": ({"group": "checklist", "name": "progress", "control": True}, "every if as a checklist with progress: '1/4 done · 25%'"),
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
T.AXES = {"habits2": {"Judgment": ("judgment_marks",), "Clarity": ("-uniform", "-names_in_view"), "Low capacity": ("words_per_row",),
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
T.TITLES = {"habits2": "T3a.1c The Habits list: the optional name, and every if as a header", "premise": "T3a.2d What tapping the premise box opens: nothing, or the ifs with the same connective", "hsheet": "T3a.2c The New habit sheet (prototype): the blanks as text boxes in the sentence, or opened above it", "addsent": "T3a.2b Adding a habit as an open sentence: the When sheet, in place, or fields; energy and routine as words or rows", "routines": "T3a.1b The Habits list with routines: the 'what to expect' preview, how the sequence shows", "addhabit": "T3a.2 Adding a habit: in place or a sheet, the If, the block", "basics": "T3a.1 Habits as Daily basics: layout, the energy filter, its mark, done today", "habits": "T3.1 The Habits list: presence, grouping, where Log sits, a count's amount"}
T.DRAW = {"habits2": lambda v: [h2doc(habits2_phone(v)), habits2_desk(v)], "premise": lambda v: [premise_doc(v)], "hsheet": lambda v: [adoc(addhabit_phone({"control": True}))] if v.get("control") else [hsheet_doc(v, st) for _, _, st in HSTATES], "addsent": lambda v: [sdoc(addsent_phone(v))] + ([] if (v.get("control") or v["form"] == "fields") else [sdoc(addsent_phone(v, True))]), "routines": lambda v: [rdoc(routines_phone(v)), rdoc(routines_phone(v, "low")), routines_desk(v)], "addhabit": lambda v: [adoc(addhabit_phone(v))], "basics": lambda v: [bdoc(basics_phone(v)), basics_desk(v)], "habits": lambda v: [hdoc(habits_phone(v)), habits_desk(v)]}
T.POOL = {}
# the owner's picks (decision 19) shown, the rest folded; superseded parts folded whole (owner, 2026-10-13)
T.PICKED = {"routines": [{"preview": "none", "seq": "plain"}, {"preview": "energy", "seq": "numbers"}], "hsheet": [{"blank": "inline"}], "premise": [{"premise": "same"}],
            "habits2": [{"group": "routines", "name": "named"}]}
T.SUPERSEDED = {"habits": "re-cut by purpose; T3a.1 Daily basics replaced it", "basics": "routines replaced it (T3a.1b)",
                "addhabit": "the open sentence replaced it (T3a.2b), then the prototype (T3a.2c)", "addsent": "the prototype sheet replaced it (T3a.2c)"}
T.v2.TOL.setdefault("_reach_log", 0.05)
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
