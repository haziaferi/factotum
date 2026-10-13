"""T3 habits, trackers, time, goals, charts and checklists (decision 19), scored as T2 was, a control per part.

    python tools/screens/t3_opt.py habits                 score a part (docs/screens/t3/t3-<part>.json)
    python tools/screens/t3_opt.py page_html scores       t3-options.html, t3-scores.html (fails if a control wins)

Parts:
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
T.SPACES = {"basics": BASICS_SPACE}
T.SCORERS = {"basics": score_basics}
T.CONTROLS = {"basics": ({"layout": "blocks", "filter": "chips", "mark": "streak", "done": "fold", "control": True},
                         "the leading design with history added: a streak and a share of days on every row"),
              "habits": ({"presence": "streak", "group": "flat", "log": "cells", "amount": "percent", "control": True},
                         "Loop-like with streaks and a score: a streak and a percentage on every row, the last 4 days as ticks and crosses")}
T.AXES = {"basics": {"Judgment": ("judgment_marks",), "Cue": ("-cue_shown", "disorder"), "Low capacity": ("words_per_row", "filter_actions", "reach_filter", "reach_log"),
                     "Choice": ("-filter_says_mid",), "Consistency": ("like_today",), "Density": ("-rows_seen", "cut"), "Calm": ("clutter", "desk_clutter")},
          "habits": {"Ease": ("log_actions", "reach_log"), "Presence": ("-presence_shown", "presence_marks"), "Calm": ("guilt_marks", "clutter", "desk_clutter"),
                     "Density": ("-rows_seen", "cut"), "Consistency": ("like_today",)}}
T.TITLES = {"basics": "T3a.1 Habits as Daily basics: layout, the energy filter, its mark, done today", "habits": "T3.1 The Habits list: presence, grouping, where Log sits, a count's amount"}
T.DRAW = {"basics": lambda v: [bdoc(basics_phone(v)), basics_desk(v)], "habits": lambda v: [hdoc(habits_phone(v)), habits_desk(v)]}
T.POOL = {}
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
