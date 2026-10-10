"""T2 items, calendar and alarms (decision 17, owner's answers 2026-10-10), scored as T1.8 and T1.9 were, a control per part.

    python tools/screens/t2_opt.py page cal day rem alarm     score parts (t2-<part>.json)
    python tools/screens/t2_opt.py page_html scores           t2-options.html, t2-scores.html (fails if a control wins)

Parts:
  page   how an item's page opens (a full page, a sheet over the list, the row expanding in place), which fields it shows,
         and how it saves
  cal    the calendar's default view (month, week, day, agenda) and how the views are switched
  day    what a calendar day holds (events; with tasks and reminders; everything) and the filter for it
  rem    the Reminders list: its order, day headers, and where Skip for today sits
  alarm  the alarm ringing: full screen or a heads-up card, the dismiss gesture, the snooze choices, where Skip for today sits

Measured from the drawings (headless Edge, 360x740 phone, 1100x660 Windows): reach (Fitts' ID from the thumb's rest),
targets seen, titles cut, events and hours on screen, clutter (edge density, light and dark), text size.
Walked: actions for each task, along the paths written beside each part.
Modelled, and so assumptions:
  - the calendar questions (what is next, is Thursday afternoon free, what is on the 20th, how full is the week) and the
    actions each view needs for them, written out in CAL_INVIEW;
  - a half-asleep tap: aimed at Snooze's centre, it lands with a round Gaussian scatter of sigma 3 mm (19 dp), twice
    the ~1.5 mm of an alert adult (Bi, Li and Zhai 2013, FFitts law); the share that lands on a tap-to-dismiss or Skip
    target is one risk, the share that misses Snooze another (added 2026-10-10: without it the control, a small Snooze
    word, reached the front); and a blind slap anywhere on the screen, whose risk is the share of the screen that dismisses
    on a tap.
References: docs/screens/t1/t2-references.json (the phone captures), normalised into t2-refs.json by this script.
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
import actions_opt as A  # noqa: E402
import toast_opt as T  # noqa: E402

e = kit.e
THUMB = T.THUMB
SIGMA_GROGGY = 19.0      # dp: 3 mm at 160 dp an inch, twice an alert adult's scatter (assumption, see above)

CSS = """
.hdr .vchip{min-height:48px;display:flex;align-items:center;padding:0 10px;font-size:15px;font-weight:600;color:var(--ink)}
.vtabs{display:flex;flex:none;background:var(--zone2);border-radius:999px;margin:0 0 4px}
.vtabs span{flex:1;min-height:48px;display:grid;place-items:center;font-size:14px;color:var(--dim);border-radius:999px}
.vtabs span.on{background:var(--zone);color:var(--ink);font-weight:600}
.cal{flex:1;position:relative;overflow:hidden;background:var(--zone);border-radius:14px;min-height:0}
.mgrid{display:grid;grid-template-columns:repeat(7,1fr);height:100%;grid-template-rows:20px repeat(6,1fr)}
.mgrid .wd{font-size:12px;color:var(--dim);text-align:center}
.mgrid .c{border-top:1px solid var(--zone2);padding:2px 2px 0;overflow:hidden;min-width:0}
.mgrid .c .n{font-size:12px;color:var(--dim);display:block;text-align:center}
.mgrid .c.out .n{opacity:.5}.mgrid .c.today .n{color:var(--bg);background:var(--ink);border-radius:999px;width:22px;margin:0 auto}
.ev{font-size:12px;line-height:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;background:var(--zone2);border-radius:4px;padding:0 3px;margin:1px 0;color:var(--ink)}
.ev .tt{display:block;overflow:hidden;text-overflow:ellipsis}
.more{font-size:12px;color:var(--dim);padding:0 3px}
.tgrid{position:absolute;left:0;right:0;top:0;bottom:0;overflow:hidden}
.hr{position:absolute;left:0;right:0;border-top:1px solid var(--zone2);font-size:12px;color:var(--dim)}
.hr span{position:absolute;left:2px;top:-1px}
.tev{position:absolute;background:var(--zone2);border-radius:6px;padding:1px 4px;font-size:12px;line-height:15px;overflow:hidden;box-shadow:inset 3px 0 0 var(--dim)}
.tev .tt{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tev .tm2{display:block;color:var(--dim)}
.wkhead{display:flex;flex:none;font-size:12px;color:var(--dim)}.wkhead span{flex:1;text-align:center}
.tray{background:var(--zone);border-radius:14px;padding:2px 12px;flex:none}
.tray .row{min-height:44px}
.dayh{font-size:12px;color:var(--dim);letter-spacing:.04em;padding:8px 2px 2px;text-transform:uppercase}
.fchips{display:flex;gap:6px;flex:none;overflow:hidden}
.fchips span{min-height:48px;min-width:48px;justify-content:center;display:flex;align-items:center;padding:0 12px;border-radius:999px;font-size:14px;box-shadow:inset 0 0 0 1px var(--zone2);color:var(--dim);white-space:nowrap}
.fchips span.on{background:var(--zone2);color:var(--ink);font-weight:600;box-shadow:none}
.ipage{display:flex;flex-direction:column;gap:2px}
.ipage .ttl2{font-size:22px;font-weight:600;padding:6px 4px 10px}
.fld{min-height:48px;display:flex;align-items:center;gap:12px;padding:0 4px;font-size:15px;border-bottom:1px solid var(--zone2)}
.fld i{font-style:normal;width:24px;text-align:center;color:var(--dim)}.fld .v{flex:1}.fld.unset .v{color:var(--dim)}
.fld.two{min-height:64px}.fld.two .v small{display:block;color:var(--dim);font-size:12px}
.xp{background:var(--zone2);border-radius:12px;padding:4px 8px;margin:2px -6px}
.xp .fld{border-bottom-color:var(--zone)}
.grab{width:36px;height:4px;border-radius:2px;background:var(--zone2);margin:0 auto 8px}
.rrow{display:flex;align-items:center;gap:12px;min-height:56px;border-bottom:1px solid var(--zone2)}
.rrow .tm{width:56px;color:var(--dim);font-size:13px;flex:none;line-height:1.25}.rrow .t{flex:1;font-size:15px;min-width:0}
.rrow .sub{display:block;font-size:13px;color:var(--dim)}
.rrow.tall{min-height:84px}
.ring{position:absolute;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;padding:56px 24px 28px;z-index:40}
.ring .clock{font-size:64px;font-weight:300;line-height:1}.ring .what{font-size:18px;margin:10px 0 0}
.ring .sp{flex:1}
.bigsnooze{width:312px;min-height:120px;border-radius:28px;background:var(--zone2);display:grid;place-items:center;font-size:22px;font-weight:600}
.snchips{display:flex;gap:8px;width:312px}.snchips span{flex:1;min-height:96px;border-radius:24px;background:var(--zone2);display:grid;place-items:center;font-size:18px;font-weight:600;text-align:center;line-height:1.2}
.dbtn{width:312px;min-height:64px;border-radius:32px;box-shadow:inset 0 0 0 2px var(--dim);display:grid;place-items:center;font-size:17px;font-weight:600}
.dbtn.hold{box-shadow:inset 0 0 0 2px var(--dim),inset 0 -5px 0 var(--zone2)}
.track{width:312px;min-height:64px;border-radius:32px;background:var(--zone2);display:flex;align-items:center;padding:0 8px;font-size:15px;color:var(--dim);gap:12px}
.track .knob{width:48px;height:48px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center;flex:none}
.skipb{min-height:48px;display:grid;place-items:center;padding:0 16px;font-size:15px;color:var(--ink);text-decoration:underline}
.hup{position:absolute;left:8px;right:8px;top:8px;background:var(--bg);border-radius:20px;padding:12px 12px 10px;box-shadow:0 8px 28px rgba(0,0,0,.3);z-index:40}
.hup .l1{font-size:12px;color:var(--dim)}.hup .l2{font-size:16px;font-weight:600;margin:2px 0 8px}
.hup .bts{display:flex;gap:16px}.hup .bts span{flex:1;min-height:52px;border-radius:14px;background:var(--zone2);display:grid;place-items:center;font-size:15px;font-weight:600}
.hup .bts span.wide{flex:2}
.hup .chs{display:flex;gap:6px;margin-bottom:8px}.hup .chs span{flex:1;min-height:48px;border-radius:14px;background:var(--zone2);display:grid;place-items:center;font-size:14px;font-weight:600}
.lock{position:absolute;inset:0;background:#000;color:#ddd;z-index:35}
.notif{position:absolute;left:12px;right:12px;top:300px;background:#222;color:#eee;border-radius:18px;padding:12px 14px;font-size:14px}
.notif .acts{display:flex;gap:8px;margin-top:6px}.notif .acts span{min-height:48px;display:grid;place-items:center;padding:0 12px;font-weight:600}
"""


def doc(html, theme="light", extra=""):
    return A.doc(html, theme).replace("</style>", CSS + extra + "</style>", 1)


def today():
    return A.today(header=header(t.TITLE))


def header(title, chip=""):
    return '<div class="hdr"><span class="ttl">%s</span>%s%s%s%s</div>' % (
        title, chip, kit.icon_button("⌕", "Search"), kit.icon_button("✎", "Edit"), kit.icon_button("⚙", "Settings"))


def desk_doc(rail_on, head_title, cols_html, theme="light", extra=""):
    head = ('<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything '
            '<span class="kbd">Ctrl+K</span></span></div>') % head_title
    html = '<div class="desk">%s<div class="dmain">%s<div style="flex:1;display:flex;gap:16px;padding:4px 16px 16px;overflow:hidden;min-height:0">%s</div></div></div>' % (
        kit.rail(rail_on), head, cols_html)
    return kit.document(html, theme, t.EXTRA + t.T12_CSS + A.CSS + T.CSS + CSS + extra, True)


def key_of(v):
    """A variant as a file-name-safe cache key (the probe names its file with it)."""
    return "-".join("%s" % v[k] for k in sorted(v)).replace(" ", "_")


def dclutter(make):
    return T.clutter_of(make, 1100, 660)


def seen_count(tp, name):
    return sum(1 for x in tp.all if x["name"] == name and x.get("seen"))


def small_of(tp, names):
    return sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in tp.all if x.get("seen") and x["name"] in names and (x["w"] < 48 or x["h"] < 48)})


# ==== Part page: an item's page ===========================================================================================
"""
  form    page (a full page over the screen; ‹ returns), sheet (a sheet over the list, the list visible above it; a tap
          on the list or a swipe down closes it), inplace (the row grows where it is, its fields under its title; a tap
          on the title closes it)
  fields  all (every field the kind has, set or not: an unset one reads "Add a reminder"), set (only the fields that
          are set, then "Add…" which lists the rest)
  save    auto (every change is kept as made; T1.8 H gives Undo), button (✓ Save; leaving without it loses the change)
  Kinds: the task "Pay the fine", the event "Dentist", the reminder "Call the bank", opened from Today.
  Tasks walked, once the item is open: change its date (set on all three); add a reminder to the task, a repeat to
  the event (both unset): "all" 1 each; "set" 2 (Add…, then the field). A field below the fold costs a scroll (+1).
  Close: 1 for all (‹, the list or the title, or ✓). Leaving without ✓ when save is "button": the change is lost
  ("lost_on_back" 1).
  Measured: Today's rows still seen while the item is open, fields seen, reach to the fields and to close, clutter,
  and Windows' clutter (the item in the right column, a panel over the column, or the row growing in the column).
  Control: a full page with every field on two lines (fifteen, as Tasks.org has), Cancel and Save in words at the top
  left, Delete as a filled button at the foot, nothing kept without Save.
"""
PAGE_SPACE = {"form": ["page", "sheet", "inplace"], "fields": ["all", "set"], "save": ["auto", "button"]}
FIELDS = {  # kind: (title, [(glyph, field, value or None)])
    "task": ("Pay the fine", [("◷", "When", "Today, Mon 5 Oct"), ("↻", "Repeat", None), ("◴", "Reminder", None), ("●", "Label", "Car"),
                              ("☐", "Subtasks", None), ("¶", "Notes", None)]),
    "event": ("Dentist", [("◷", "When", "Mon 5 Oct, 09:00–09:45"), ("↻", "Repeat", None), ("◴", "Reminder", "15 min before"), ("●", "Label", "Health"),
                          ("¶", "Notes", None)]),
    "reminder": ("Call the bank", [("◷", "When", "Today, 15:00"), ("↻", "Repeat", None), ("♪", "Alert", "Notification"), ("●", "Label", "Money"),
                                   ("¶", "Notes", None)]),
}
ADD_WORD = {"Repeat": "Add a repeat", "Reminder": "Add a reminder", "Subtasks": "Add a subtask", "Notes": "Add notes", "Label": "Add a label"}
EDITS = [("task", "When"), ("task", "Reminder"), ("event", "Repeat"), ("event", "When")]
CONTROL_FIELDS = ["Title", "Start date", "Due date", "Repeat", "Priority", "List", "Tags", "Subtasks", "Reminder", "Description",
                  "Location", "Attachment", "Add to calendar", "Timer", "Created"]


def fields_html(kind, v):
    title, fl = FIELDS[kind]
    if v.get("control"):
        return "".join('<div class="fld two" data-tap="F %s"><i>·</i><span class="v">%s<small>%s</small></span></div>' % (n, n, "Not set") for n in CONTROL_FIELDS)
    out = []
    for g, n, val in fl:
        if val is not None:
            out.append('<div class="fld" data-tap="F %s"><i>%s</i><span class="v">%s</span></div>' % (n, g, kit.ud(e(val))))
        elif v["fields"] == "all":
            out.append('<div class="fld unset" data-tap="F %s"><i>%s</i><span class="v">%s</span></div>' % (n, g, ADD_WORD.get(n, "Add " + n.lower())))
    if v["fields"] == "set":
        out.append('<div class="fld unset" data-tap="Add more"><i>+</i><span class="v">Add…</span></div>')
    return "".join(out)


def item_inner(kind, v):
    title = FIELDS[kind][0]
    return '<div class="ipage"><div class="ttl2" data-tap="Title">%s</div>%s</div>' % (kit.ud(e(title)), fields_html(kind, v))


def page_phone(kind, v):
    title = FIELDS[kind][0]
    if v.get("control"):
        head = ('<div class="hdr"><span class="btn text" data-tap="Close">Cancel</span><span class="btn text" data-tap="Save">Save</span>'
                '<span class="ttl"></span></div>')
        body = item_inner(kind, v) + '<span class="btn fill wide" data-tap="Delete" style="flex:none">Delete</span>'
        return kit.phone(head, body, "")
    acts = (("✓", "Save"),) if v["save"] == "button" else ()
    if v["form"] == "page":
        head = kit.header("", acts + (("🗑", "Delete"),), ("‹", "Close"))
        return kit.phone(head, item_inner(kind, v), "")
    base = today()
    if v["form"] == "sheet":
        top = ('<div class="hdr" style="padding:0;height:48px"><span class="ttl"></span>%s</div>' % "".join(kit.icon_button(*b) for b in acts + (("🗑", "Delete"),)))
        sheet = '<div class="scrim" data-tap="Close"></div><div class="bsheet" style="max-height:78%%;overflow:hidden"><div class="grab"></div>%s%s</div>' % (top, item_inner(kind, v))
        return T.with_overlay(base, sheet)
    # in place: the row grows where it is (its own row on top, a tap on it closes; its actions at its end)
    m = re.search(r'<div class="row[^"]*" data-tap="Open item">(?:(?!<div class="row).)*?%s.*?</div>' % re.escape(kit.ud(e(title))), base, re.S)
    own = m.group(0).replace('data-tap="Open item"', 'data-tap="Close"', 1)
    own = own[:-len("</div>")] + "".join(kit.icon_button(*b) for b in acts + (("🗑", "Delete"),)) + "</div>"
    return base.replace(m.group(0), '<div class="xp">%s%s</div>' % (own, fields_html(kind, v)), 1)


def page_desk(v, theme="light"):
    kind = "task"
    col = '<div class="dcol" style="width:380px;flex:none">%s</div>' % t.rows_today(t.row_d)
    if v.get("control") or v["form"] == "page":
        right = '<div class="page" style="flex:1">%s</div>' % (page_phone(kind, v).split('<div class="body">', 1)[1].rsplit("</div>", 2)[0] if v.get("control") else item_inner(kind, v))
        return desk_doc("Today", t.TITLE, col + right, theme)
    if v["form"] == "sheet":
        panel = '<div class="page" style="width:420px;flex:none;box-shadow:0 8px 28px rgba(0,0,0,.18)">%s</div>' % item_inner(kind, v)
        return desk_doc("Today", t.TITLE, col + panel + '<div class="page" style="flex:1;opacity:.6"></div>', theme)
    title = FIELDS[kind][0]
    rows = t.rows_today(t.row_d)
    m = re.search(r'<div class="row[^"]*" data-tap="Open item">(?:(?!<div class="row).)*?%s.*?</div>' % re.escape(kit.ud(e(title))), rows, re.S)
    rows = rows.replace(m.group(0), '<div class="xp"><div class="row" data-tap="Close"><span class="tm kind">◦</span><span class="t">%s</span></div>%s</div>' % (
        kit.ud(e(title)), fields_html(kind, v)), 1)
    return desk_doc("Today", t.TITLE, '<div class="dcol" style="width:380px;flex:none">%s</div><div class="page" style="flex:1"></div>' % rows, theme)


def score_page(v):
    reach, ctx, fseen, fhid, cl, small, edits = [], [], [], [], [], [], []
    for kind in FIELDS:
        d = doc(page_phone(kind, v))
        tp = T.taps(d)
        ctx.append(seen_count(tp, "Open item"))
        fl = [x for x in tp.all if x["name"].startswith("F ") or x["name"] == "Add more"]
        fseen.append(sum(1 for x in fl if x.get("seen")))
        fhid.append(sum(1 for x in fl if not x.get("seen")))
        aim = [x for x in fl if x.get("seen")] + [tp["Close"]] if "Close" in tp else [x for x in fl if x.get("seen")]
        reach.append(sum(T.fitts(THUMB, x) for x in aim) / len(aim))
        small += small_of(tp, {x["name"] for x in fl} | {"Close", "Save", "Delete"})
        cl.append(T.clutter_of(lambda th: doc(page_phone(kind, v), th)))
        for k2, f in EDITS:
            if k2 != kind:
                continue
            n = [x for x in tp.all if x["name"] == "F " + f]
            if n:
                edits.append(1 + (0 if n[0].get("seen") else 1))
            else:
                more = tp.get("Add more")
                edits.append(2 + (0 if more and more.get("seen") else 1))
    lost = 1 if (v.get("control") or v["save"] == "button") else 0
    return {"edit_actions": round(sum(edits) / len(edits), 2), "close_actions": 1, "reach": round(sum(reach) / len(reach), 3),
            "context_rows": round(sum(ctx) / len(ctx), 1), "fields_seen": round(sum(fseen) / len(fseen), 1), "fields_below": round(sum(fhid) / len(fhid), 1),
            "lost_on_back": lost, "small": sorted(set(small)), "clutter": round(sum(cl) / len(cl), 4), "desk_clutter": dclutter(lambda th: page_desk(v, th))}


# ==== Part cal: the calendar's default view and the way between views ======================================================
"""
  default  month, week, day, agenda: what Calendar opens on
  switch   tabs (Month · Week · Day · Agenda under the header: 1 tap), menu (the view's name in the header, ▾: 2 taps)
  Sample: Mon 5 Oct 2026 is today; a placeholder week of 13 things and a month of 21 (events, two tasks, a reminder).
  Measured on each view's drawing: things seen, titles cut, hours seen (week and day); on Windows, the same view at
  1100x660. Walked, the four questions (CAL_INVIEW): what is next today; is Thursday afternoon free; what is on the 20th;
  how full is this week. Each costs the fewer of: answering in the default view, or switching (1 or 2) and answering
  in the best other view.
  Control: the year view by default (twelve small months, no titles), the views behind ⚙ › Calendar view.
"""
CAL_SPACE = {"default": ["month", "week", "day", "agenda"], "switch": ["tabs", "menu"]}
VIEWS = ["month", "week", "day", "agenda"]
# (day of October, start, end, title, kind) ; end None: no time span; start None: no time (all day, or a task)
EVENTS = [
    (2, 10.0, 11.0, "Plumber", "event"), (5, 9.0, 9.75, "Dentist", "event"), (5, 15.0, None, "Call the bank", "reminder"),
    (5, None, None, "Pay the fine", "task"), (6, 10.0, 11.0, "Team call", "event"), (6, 16.5, 17.25, "Physio", "event"),
    (7, 18.0, 19.0, "Yoga class", "event"), (8, 12.5, 13.5, "Lunch with Sam", "event"), (8, None, None, "Pay rent", "task"),
    (9, 7.17, 9.33, "Train to Milan", "event"), (9, 11.0, 12.5, "Client meeting", "event"), (10, 10.0, 11.0, "Farmers market", "event"),
    (10, 20.0, 22.0, "Dinner at Ana's", "event"), (11, None, None, "Hike", "event"), (14, 17.0, 17.5, "Haircut", "event"),
    (14, 19.0, 20.0, "Mum's birthday dinner", "event"), (20, 8.5, 9.5, "Car service", "event"), (22, 19.0, 21.0, "Book club", "event"),
    (27, None, None, "Parents visit", "event"), (30, 21.0, 23.0, "Concert", "event"), (30, 9.0, 10.0, "Dentist check", "event"),
]
WEEK = range(5, 12)
NOW = 10.25   # 10:15 on Mon 5 Oct
# the questions, and what each view needs to answer them by itself (actions; 99: it cannot)
CAL_Q = ["next", "thu_free", "the_20th", "week_full"]
CAL_INVIEW = {
    "month": {"next": 1, "thu_free": 1, "the_20th": 1, "week_full": 0},     # times are not in the cells: open the day; the week's row is seen
    "week": {"next": 0, "thu_free": 0, "the_20th": 2, "week_full": 0},      # two swipes to the 20th's week
    "day": {"next": 0, "thu_free": 3, "the_20th": 15, "week_full": 6},      # a swipe a day
    "agenda": {"next": 0, "thu_free": 1, "the_20th": 3, "week_full": 1},    # scrolls; free time read from the times
}


def hh(x):
    return "%02d:%02d" % (int(x), round((x - int(x)) * 60))


def ev_html(ev, show_time=False):
    d, s, en, title, kind = ev
    return '<div class="ev" data-tap="Open event"><span class="tt">%s%s</span></div>' % (hh(s) + " " if (show_time and s is not None) else "", kit.ud(e(title)))


def month_html():
    cells = ['<span class="wd">%s</span>' % w for w in "MTWTFSS"]
    for i in range(42):
        day = i - 3   # the grid starts Mon 28 Sep
        if day < 1:
            n, out = 30 + day, True
        elif day > 31:
            n, out = day - 31, True
        else:
            n, out = day, False
        evs = [] if out else sorted([x for x in EVENTS if x[0] == day], key=lambda x: (x[1] is not None, x[1] or 0))
        inner = "".join(ev_html(x) for x in evs[:3]) + ('<div class="more">+%d</div>' % (len(evs) - 3) if len(evs) > 3 else "")
        cells.append('<div class="c%s%s" data-tap="Day %d"><span class="n">%d</span>%s</div>' % (" out" if out else "", " today" if (day == 5 and not out) else "", n, n, inner))
    return '<div class="cal"><div class="mgrid">%s</div></div>' % "".join(cells)


def timegrid(days, hour_px, first=7.0, gutter=34, with_tray=None):
    """A time grid for the given days (columns); events placed by start and end."""
    hrs = "".join('<div class="hr" style="top:%dpx"><span>%02d</span></div>' % ((h - first) * hour_px, h) for h in range(int(first), 24))
    evs = []
    n = len(days)
    for ci, day in enumerate(days):
        for x in EVENTS:
            if x[0] != day or x[1] is None:
                continue
            end = x[2] if x[2] is not None else x[1] + 0.5
            top = (x[1] - first) * hour_px
            h = max(16 if n > 1 else 34, (end - x[1]) * hour_px - 2)
            left = "calc(%dpx + (100%% - %dpx) * %g + 1px)" % (gutter, gutter, ci / n)
            width = "calc((100%% - %dpx) / %d - 2px)" % (gutter, n)
            sub = '<span class="tm2">%s</span>' % (hh(x[1]) + ("–" + hh(x[2]) if x[2] else "")) if n == 1 else ""
            evs.append('<div class="tev ev" data-tap="Open event" style="top:%dpx;height:%dpx;left:%s;width:%s"><span class="tt">%s</span>%s</div>' % (top, h, left, width, kit.ud(e(x[3])), sub))
    return '<div class="tgrid" style="top:%dpx">%s%s</div>' % (-int((NOW - 1 - first) * hour_px) if False else 0, hrs, "".join(evs))


def week_html(hour_px=40):
    head = '<div class="wkhead"><span style="flex:0 0 34px"></span>%s</div>' % "".join('<span data-tap="Day %d">%s %d</span>' % (d, w, d) for w, d in zip("MTWTFSS", WEEK))
    allday = [x for x in EVENTS if x[0] in WEEK and x[1] is None]
    strip = '<div class="wkhead" style="min-height:20px"><span style="flex:0 0 34px"></span>%s</div>' % "".join(
        '<span>%s</span>' % "".join('<div class="ev" data-tap="Open event"><span class="tt">%s</span></div>' % kit.ud(e(x[3])) for x in allday if x[0] == d) for d in WEEK)
    return head + strip + '<div class="cal">%s</div>' % timegrid(list(WEEK), hour_px)


def day_html(hour_px=48, tray_items=None):
    tray = ""
    if tray_items:
        tray = '<div class="tray">%s</div>' % "".join(
            '<div class="row" data-tap="Open item"><span class="tm kind">%s</span><span class="t">%s</span></div>' % (g, kit.ud(e(n))) for g, n in tray_items)
    return '<div class="dayh">Mon 5 Oct</div>' + tray + '<div class="cal">%s</div>' % timegrid([5], hour_px)


def agenda_html():
    out = []
    for d in range(5, 32):
        evs = sorted([x for x in EVENTS if x[0] == d], key=lambda x: (x[1] is not None, x[1] or 0))
        if not evs:
            continue
        out.append('<div class="dayh">%s %d Oct</div>' % (["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][(d - 5) % 7], d))
        for x in evs:
            tm = (hh(x[1]) + ("<br>" + hh(x[2]) if x[2] else "")) if x[1] is not None else ("◦" if x[4] == "task" else "all day")
            out.append('<div class="row ev" data-tap="Open event" style="background:none;font-size:15px;line-height:1.3;white-space:normal"><span class="tm">%s</span><span class="t tt">%s</span></div>' % (tm, kit.ud(e(x[3]))))
    return '<div class="cal" style="background:none">%s</div>' % "".join(out)


VIEW_HTML = {"month": month_html, "week": week_html, "day": day_html, "agenda": agenda_html}
VIEW_NAME = {"month": "Month", "week": "Week", "day": "Day", "agenda": "Agenda"}


def cal_phone(view, switch):
    if switch == "control":
        return kit.phone(header("2026"), '<div class="cal" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:8px;background:none">%s</div>' % "".join(
            '<div data-tap="Month %d" style="font-size:12px;color:var(--dim)"><b style="color:var(--ink)">%s</b><br>%s</div>' % (i, m, " ".join(str(n) for n in range(1, 29))) for i, m in enumerate(
                ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])), kit.bar("Calendar"))
    title = "October 2026" if view in ("month", "agenda") else ("5–11 Oct" if view == "week" else "Mon 5 Oct")
    if switch == "tabs":
        tabs = '<div class="vtabs">%s</div>' % "".join('<span class="%s" data-tap="View %s">%s</span>' % ("on" if x == view else "", x, VIEW_NAME[x]) for x in VIEWS)
        return kit.phone(header(title), tabs + VIEW_HTML[view](), kit.bar("Calendar"))
    chip = '<span class="vchip" data-tap="View menu">%s ▾</span>' % VIEW_NAME[view]
    return kit.phone(header(title, chip), VIEW_HTML[view](), kit.bar("Calendar"))


def cal_desk(view, switch, theme="light"):
    if switch == "control":
        inner = cal_phone(view, switch).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
        return desk_doc("Calendar", "2026", '<div style="flex:1;display:flex;flex-direction:column">%s</div>' % inner, theme)
    body = VIEW_HTML[view]() if view != "week" else week_html(28)
    if switch == "tabs":
        body = '<div class="vtabs" style="width:420px">%s</div>' % "".join('<span class="%s" data-tap="View %s">%s</span>' % ("on" if x == view else "", x, VIEW_NAME[x]) for x in VIEWS) + body
    title = "October 2026" + ("" if switch == "tabs" else ' <span class="vchip" data-tap="View menu" style="display:inline-flex">%s ▾</span>' % VIEW_NAME[view])
    return desk_doc("Calendar", title, '<div style="flex:1;display:flex;flex-direction:column;gap:6px;min-width:0">%s</div>' % body, theme)


DENSITY_JS = ("(function(){var c=document.querySelector('.cal')||document.body;var cb=c.getBoundingClientRect();var seen=0,cut=0,narrow=999;"
              "document.querySelectorAll('.ev').forEach(function(e){var r=e.getBoundingClientRect();if(!r.height)return;"
              "if(r.top>=Math.min(cb.top,r.top)&&r.bottom<=cb.bottom+1&&r.top<cb.bottom){seen++;var tt=e.querySelector('.tt')||e;"
              "if(tt.scrollWidth>tt.clientWidth+1||tt.scrollHeight>tt.clientHeight+1)cut++;narrow=Math.min(narrow,Math.round(r.width))}});"
              "var hrs=document.querySelectorAll('.hr');var hs=0;hrs.forEach(function(h){var r=h.getBoundingClientRect();if(r.top>=cb.top-1&&r.top<=cb.bottom)hs++});"
              "return [seen,cut,hs,narrow]})()")


def view_density(view, desk=False):
    if desk:
        d = cal_desk(view, "tabs")
        return T.probe(d, "t2-dens-desk-" + view, DENSITY_JS, 1100, 660)
    return T.probe(doc(cal_phone(view, "tabs")), "t2-dens-" + view, DENSITY_JS)


def score_cal(v):
    if v.get("control"):
        d = doc(cal_phone("month", "control"))
        tp = T.taps(d)
        # the year view answers nothing by itself; ⚙ › Calendar view › a view = 3, then that view's actions
        q = [3 + min(CAL_INVIEW[x][k] for x in VIEWS) for k in CAL_Q]
        return {"q_actions": round(sum(q) / len(q), 2), "switch_actions": 3, "seen": 0, "cut": 0, "hours": 0, "narrow_px": 0,
                "reach_switch": round(T.fitts(THUMB, tp["Settings"]), 3), "desk_seen": 0, "desk_cut": 0, "small": [],
                "clutter": T.clutter_of(lambda th: doc(cal_phone("month", "control"), th)), "desk_clutter": dclutter(lambda th: cal_desk("month", "control", th))}
    view, sw = v["default"], v["switch"]
    cost = 1 if sw == "tabs" else 2
    q = [min(CAL_INVIEW[view][k], cost + min(CAL_INVIEW[x][k] for x in VIEWS if x != view)) for k in CAL_Q]
    seen, cut, hours, narrow = view_density(view)
    dseen, dcut, _, _ = view_density(view, True)
    d = doc(cal_phone(view, sw))
    tp = T.taps(d)
    way = tp.get("View month" if view != "month" else "View week") or tp.get("View menu")
    return {"q_actions": round(sum(q) / len(q), 2), "switch_actions": cost, "seen": seen, "cut": cut, "hours": hours, "narrow_px": narrow if narrow < 999 else 0,
            "reach_switch": round(T.fitts(THUMB, way), 3), "desk_seen": dseen, "desk_cut": dcut,
            "small": small_of(tp, {"View menu", "View month", "View week", "View day", "View agenda"}),
            "clutter": T.clutter_of(lambda th: doc(cal_phone(view, sw), th)), "desk_clutter": dclutter(lambda th: cal_desk(view, sw, th))}


# ==== Part day: what a calendar day holds, and its filter =====================================================================
"""
  show    events (events only), tasks (events, tasks and reminders), everything (events, tasks, reminders, habits,
          checklists and readings: all that Today shows for the day)
  filter  none (what the day holds is fixed), chips (All · Events · Tasks · Routines under the header: one tap shows one
          kind, All again shows the setting), menu (✎ › Show: the kinds as switches; 2 actions)
  The day: Mon 5 Oct, on the day view (things with no time in a tray above the hours). Counted: the day's things shown
  of the 13 Today has (Today's own rows), the actions to see another set (none: it cannot, 99). Measured: titles cut,
  hours seen (the tray pushes the hours down), clutter, and Windows' clutter (the day beside Today's column).
  Control: everything on two-line rows, a filter only in ⚙ › Calendar › Layers (3 actions).
"""
DAY_SPACE = {"show": ["events", "tasks", "everything"], "filter": ["none", "chips", "menu"]}
DAY_ALL = [x for x in EVENTS if x[0] == 5]   # Dentist, Call the bank, Pay the fine
ROUTINE_ITEMS = [("↻", "Walk"), ("↻", "Water · 3 of 8"), ("≡", "Morning routine"), ("∿", "Sleep")]
TODAY_TOTAL = len(t.KINDS) + 0   # the 8 rows Today shows for Mon 5 Oct
SHOW_COUNT = {"events": 1, "tasks": 4, "everything": len(t.KINDS)}   # Dentist; + Pay the fine, Call the bank, Return library books; + 4 routines


def day_tray(show):
    if show == "events":
        return []
    tray = [("◦", "Pay the fine"), ("◦", "Return library books")]
    if show == "everything":
        tray += ROUTINE_ITEMS
    return tray


def day_phone(v):
    if v.get("control"):
        tray = [(g, n) for g, n in day_tray("everything")]
        body = '<div class="dayh">Mon 5 Oct</div><div class="tray">%s</div>' % "".join(
            '<div class="row" data-tap="Open item" style="min-height:64px"><span class="tm kind">%s</span><span class="t">%s<span class="sub">%s</span></span></div>' % (g, kit.ud(e(n)), "No time · Today") for g, n in tray) + '<div class="cal">%s</div>' % timegrid([5], 48)
        return kit.phone(header("Mon 5 Oct"), body, kit.bar("Calendar"))
    show, flt = v["show"], v["filter"]
    events_only = show == "events"
    grid_evs = None if not events_only else None
    body = day_html(48, day_tray(show))
    if not events_only and show == "tasks":
        pass
    # reminders are timed: Call the bank sits on the hours unless only events are shown
    if events_only:
        body = body.replace('data-tap="Open event" style="top:%dpx' % ((15.0 - 7) * 48), 'data-tap="Open event" hidden style="top:%dpx' % ((15.0 - 7) * 48))
    if show == "everything":
        body = body.replace('<div class="tgrid" style="top:0px">', '<div class="tgrid" style="top:0px"><div class="tev ev" data-tap="Open event" style="top:%dpx;height:22px;left:calc(34px + 1px);width:calc(100%% - 36px)"><span class="tt">%s</span></div>' % (
            (14 - 7) * 48 + 24, kit.ud("Water · next block")), 1)
    chip = ""
    if flt == "chips":
        body = '<div class="fchips">%s</div>' % "".join('<span class="%s" data-tap="Show %s">%s</span>' % ("on" if i == 0 else "", n, n) for i, n in enumerate(("All", "Events", "Tasks", "Routines"))) + body
    return kit.phone(header("Mon 5 Oct"), body, kit.bar("Calendar"))


def day_desk(v, theme="light"):
    inner = day_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Calendar", "Mon 5 Oct", '<div class="dcol" style="width:380px;flex:none">%s</div><div style="flex:1;display:flex;flex-direction:column;gap:6px">%s</div>' % (
        t.rows_today(t.row_d), inner), theme)


def score_day(v):
    d = doc(day_phone(v))
    tp = T.taps(d)
    seen, cut, hours, _ = T.probe(d, "t2-day-%s" % key_of(v), DENSITY_JS)
    if v.get("control"):
        shown, other = len(t.KINDS), 3
    else:
        shown = SHOW_COUNT[v["show"]]
        other = {"none": 99, "chips": 1, "menu": 2}[v["filter"]]
    rows_seen = seen_count(tp, "Open item") + seen_count(tp, "Open event")
    return {"shown": shown, "missed": TODAY_TOTAL - shown, "other_actions": other, "rows_seen": rows_seen, "cut": cut, "hours": hours,
            "small": small_of(tp, {"Show All", "Show Events", "Show Tasks", "Show Routines"}),
            "clutter": T.clutter_of(lambda th: doc(day_phone(v), th)), "desk_clutter": dclutter(lambda th: day_desk(v, th))}


# ==== Part rem: the Reminders list ===========================================================================================
"""
  order   next (the soonest first), title (A to Z), manual (as arranged; drawn in the order made)
  group   days (Today · Tomorrow · This week · Later headers), flat
  skip    selection (T1.8 I: a long press selects, Skip for today sits in the selection's header: 2 actions),
          swipe (a swipe left on the row: 1 gesture, seen nowhere), page (the row opens its page, Skip for today
          there, then ‹: 3)
  Ten placeholder reminders; now is Mon 5 Oct, 10:15. Measured: rows seen, where the soonest sits (its place in the
  list), the disorder against time (the share of pairs out of time order), reach to Skip, clutter, Windows' clutter.
  Counted: swipe can be set off by a sideways scroll (accident 1) and is found by no mark on screen (hidden 1).
  Control: oldest made first, day headers, every row on three lines, Skip only in the page's ⋯ menu (4 actions).
"""
REM_SPACE = {"order": ["next", "title", "manual"], "group": ["days", "flat"], "skip": ["selection", "swipe", "page"]}
# (title, next as hours from now, when text, repeat text, made order)
REMS = [
    ("Call the bank", 4.75, "15:00", "Once", 3), ("Take vitamins", 21.75, "Tue<br>08:00", "Every day", 0), ("Stretch", 1.75, "12:00", "Every 2 hours", 5),
    ("Bins out", 33.75, "Tue<br>20:00", "Every Tuesday", 1), ("Mum's birthday", 9 * 24, "Wed<br>14 Oct", "Every year", 2),
    ("Renew passport", 28 * 24, "Mon<br>2 Nov", "Once", 8), ("Back up laptop", 26 * 24, "Sun<br>1 Nov", "Every month", 4),
    ("Stand up", 0.25, "10:30", "Every 30 min, 9–18", 6), ("Evening pills", 10.75, "21:00", "Every day", 7), ("Book the vet", 3 * 24 + 1, "Thu<br>11:00", "Once", 9),
]


def rem_sorted(order):
    if order == "next":
        return sorted(REMS, key=lambda r: r[1])
    if order == "title":
        return sorted(REMS, key=lambda r: r[0])
    return sorted(REMS, key=lambda r: r[4])


def day_group(h):
    end_today = 24 - NOW
    if h < end_today:
        return "Today"
    if h < end_today + 24:
        return "Tomorrow"
    if h < end_today + 6 * 24:
        return "This week"
    return "Later"


def rem_phone(v):
    ctl = v.get("control")
    order = "made" if ctl else v["order"]
    rs = sorted(REMS, key=lambda r: r[4]) if ctl else rem_sorted(order)
    rows, last = [], None
    grouped = ctl or v["group"] == "days"
    for r in rs:
        g = day_group(r[1])
        if grouped and g != last and (ctl or order == "next"):
            rows.append('<div class="dayh">%s</div>' % g)
            last = g
        rows.append('<div class="rrow%s" data-tap="Open reminder"><span class="tm">%s</span><span class="t">%s<span class="sub">%s</span>%s</span></div>' % (
            " tall" if ctl else "", r[2], kit.ud(e(r[0])), r[3], '<span class="sub">Made 2 Oct · Notification</span>' if ctl else ""))
    if grouped and not ctl and order != "next":
        # day headers only make sense in time order; for title and manual they group by first letter and by nothing:
        # drawn as the same days, each list sorted within its day
        rows = []
        for g in ("Today", "Tomorrow", "This week", "Later"):
            part = [r for r in rs if day_group(r[1]) == g]
            if part:
                rows.append('<div class="dayh">%s</div>' % g)
                rows += ['<div class="rrow" data-tap="Open reminder"><span class="tm">%s</span><span class="t">%s<span class="sub">%s</span></span></div>' % (
                    r[2], kit.ud(e(r[0])), r[3]) for r in part]
    body = '<div class="cap" data-tap="Capture">+ <span>Remind me to…</span></div><div class="zone" style="flex:1;overflow:hidden">%s</div>' % "".join(rows)
    return kit.phone(header("Reminders"), body, kit.bar("Hub"))


def rem_shown_order(v):
    html = rem_phone(v)
    titles = [m for m in re.findall(r'<span class="ud">([^<]*)</span>', html)]
    by = {e(r[0]): r for r in REMS}
    return [by[x] for x in titles if x in by]


def rem_skip_doc(v):
    """Where Skip for today is, drawn: the selection's header, the row's swipe, or the page."""
    ctl = v.get("control")
    base = rem_phone(v)
    first = re.search(r'<div class="rrow[^"]*" data-tap="Open reminder">.*?</span></span></div>', base, re.S).group(0)
    if not ctl and v["skip"] == "selection":
        html = base.replace(first, first.replace('class="rrow', 'class="rrow sel', 1), 1)
        return re.sub(r'<div class="hdr">.*?</div>', A.sel_header(1, (("Skip", "Skip for today"), ("Delete", "🗑"))).replace('data-tap="A Skip"', 'data-tap="Skip"'), html, count=1, flags=re.S)
    if not ctl and v["skip"] == "swipe":
        return base.replace(first, '<div style="display:flex;background:var(--zone2);border-radius:10px"><span class="skipb" data-tap="Skip" style="text-decoration:none;font-weight:600">Skip for today</span>%s</div>' % first.replace(
            'class="rrow"', 'class="rrow" style="flex:1;transform:translateX(0);background:var(--zone)"', 1), 1)
    r = rem_shown_order(v)[0]
    flds = ('<div class="ipage"><div class="ttl2">%s</div><div class="fld"><i>◷</i><span class="v">%s</span></div><div class="fld"><i>↻</i><span class="v">%s</span></div></div>' % (
        kit.ud(e(r[0])), r[2].replace("<br>", " "), r[3]))
    if ctl:
        menu = '<div class="menu3"><div class="mi2"><span class="t">Duplicate</span></div><div class="mi2" data-tap="Skip"><span class="t">Skip for today</span></div><div class="mi2"><span class="t">Delete</span></div></div>'
        return kit.phone(kit.header("", (("⋯", "More"),), ("‹", "Back")), flds, "" ) [:-len("</div>")] + menu + "</div>"
    return kit.phone(kit.header("", (("🗑", "Delete"),), ("‹", "Back")), flds + '<span class="btn text" data-tap="Skip" style="align-self:flex-start">Skip for today</span>', "")


def rem_desk(v, theme="light"):
    inner = rem_phone(v).split('<div class="body">', 1)[1].rsplit('<div class="bar">', 1)[0][:-len("</div>")]
    return desk_doc("Hub", "Reminders", '<div class="dcol" style="width:420px;flex:none">%s</div><div class="page" style="flex:1"></div>' % inner, theme)


def score_rem(v):
    ctl = v.get("control")
    d = doc(rem_phone(v))
    tp = T.taps(d)
    shown = rem_shown_order(v)
    soonest = min(REMS, key=lambda r: r[1])
    pos = shown.index(soonest) + 1
    pairs = [(a, b) for i, a in enumerate(shown) for b in shown[i + 1:]]
    disorder = sum(1 for a, b in pairs if a[1] > b[1]) / len(pairs)
    sk = T.taps(doc(rem_skip_doc(v)))
    skip = 4 if ctl else {"selection": 2, "swipe": 1, "page": 3}[v["skip"]]
    hidden = 1 if (not ctl and v["skip"] == "swipe") else 0
    return {"rows_seen": seen_count(tp, "Open reminder"), "soonest_at": pos, "disorder": round(disorder, 3), "skip_actions": skip,
            "skip_hidden": hidden, "skip_accident": hidden, "reach_skip": round(T.fitts(THUMB, sk["Skip"]), 3),
            "small": small_of(sk, {"Skip"}), "clutter": T.clutter_of(lambda th: doc(rem_phone(v), th)), "desk_clutter": dclutter(lambda th: rem_desk(v, th))}


# ==== Part alarm: the alarm ringing ===========================================================================================
"""
  form     full (over the lock screen and over any app: the whole screen), headsup (a card at the top; on a locked
           phone, a notification on the lock screen, opened before its buttons show)
  dismiss  tap (a button), hold (a button held for 1 s), slide (a knob slid along a track)
  snooze   one (one Snooze, the length set in the reminder), choices (5 · 10 · 15 · 30 min: the tap picks the length)
  skip     ring (Skip for today on the ringing screen: today's other rings of a reminder that rings several times a day
           do not come), upcoming (a quiet notification an hour before, with Skip for today), list (only from the
           Reminders list: T1.8 I, 3 actions with opening Factotum)
  The sample: "Wake up", 07:00, every day. Measured: reach to Snooze and to Dismiss; half-asleep safety: a tap aimed
  at Snooze (the 10-min choice when there are choices), scattered at sigma 19 dp, landing on a tap-to-dismiss or a Skip
  target (aim_risk), the same tap missing Snooze, so it rings on (snooze_miss), and a blind slap anywhere (slap_risk: the share of the screen that dismisses or skips on a tap);
  how loud Dismiss is beside Snooze (dismiss_pull: Dismiss's share of the two targets' visual mass, read off the
  rendered pixels; a groggy eye and thumb go to the louder); the screen covered while the phone is in use; clutter. Counted: actions to snooze and to skip (the mean of skipping
  before it rings and of stopping today's later rings), the extra action on a locked phone (opening the notification),
  the effort to dismiss (tap 0, slide 0.5 s, hold 1 s).
  Windows: an alarm rings on the phone; Windows shows Factotum's ordinary notification, not scored here.
  Control: a heads-up card with Dismiss filled and wide under the thumb's side, a small Snooze beside it, a tap
  dismisses, six snooze lengths, Skip only from the list.
"""
ALARM_SPACE = {"form": ["full", "headsup"], "dismiss": ["tap", "hold", "slide"], "snooze": ["one", "choices"], "skip": ["ring", "upcoming", "list"]}
DISMISS_WORD = {"tap": "Dismiss", "hold": "Hold to dismiss", "slide": "Slide to dismiss"}


def alarm_phone(v):
    behind = today()
    if v.get("control"):
        card = ('<div class="hup"><div class="l1">Factotum · now</div><div class="l2">%s · 07:00</div>'
                '<div class="chs">%s</div><div class="bts"><span data-tap="Snooze" style="flex:none;width:72px;background:none">Snooze</span>'
                '<span class="wide" data-tap="Dismiss" style="background:var(--ink);color:var(--bg)">Dismiss</span></div></div>') % (
            kit.ud("Wake up"), "".join('<span data-tap="Snooze %d">%d</span>' % (m, m) for m in (1, 3, 5, 10, 15, 30)))
        return T.with_overlay(behind, card)
    skip = '<span class="skipb" data-tap="Skip">Skip for today</span>' if v["skip"] == "ring" else ""
    if v["form"] == "full":
        if v["snooze"] == "one":
            sn = '<div class="bigsnooze" data-tap="Snooze">Snooze 10 min</div>'
        else:
            sn = '<div class="snchips">%s</div>' % "".join('<span data-tap="%s">%d<br>min</span>' % ("Snooze" if m == 10 else "Snooze %d" % m, m) for m in (5, 10, 15, 30))
        if v["dismiss"] == "slide":
            dis = '<div class="track"><span class="knob" data-tap="Dismiss knob">›</span>Slide to dismiss</div>'
        else:
            dis = '<div class="dbtn%s" data-tap="Dismiss">%s</div>' % (" hold" if v["dismiss"] == "hold" else "", DISMISS_WORD[v["dismiss"]])
        ring = '<div class="ring"><div class="clock">07:00</div><div class="what">%s</div>%s<div class="sp"></div>%s<div style="height:28px"></div>%s</div>' % (
            kit.ud("Wake up"), skip, sn, dis)
        return T.with_overlay(behind, ring)
    if v["snooze"] == "one":
        sn = '<span data-tap="Snooze">Snooze 10 min</span>'
        chs = ""
    else:
        sn = ""
        chs = '<div class="chs">%s</div>' % "".join('<span data-tap="%s">%d min</span>' % ("Snooze" if m == 10 else "Snooze %d" % m, m) for m in (5, 10, 15, 30))
    if v["dismiss"] == "slide":
        dis = '<span style="background:var(--zone2);justify-content:start;display:flex;align-items:center;gap:8px;padding:0 4px"><b class="knob" data-tap="Dismiss knob" style="width:44px;height:44px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center">›</b>Slide</span>'
    else:
        dis = '<span data-tap="Dismiss"%s>%s</span>' % (' style="box-shadow:inset 0 -4px 0 var(--dim)"' if v["dismiss"] == "hold" else "", "Hold to dismiss" if v["dismiss"] == "hold" else "Dismiss")
    card = '<div class="hup"><div class="l1">Factotum · alarm</div><div class="l2">%s · 07:00</div>%s<div class="bts">%s%s</div>%s</div>' % (
        kit.ud("Wake up"), chs, sn, dis, skip.replace('class="skipb"', 'class="skipb" style="margin:6px auto 0;width:fit-content"'))
    return T.with_overlay(behind, card)


def upcoming_doc():
    shade = ('<div class="lock"><div class="notif"><div style="font-size:12px;color:#aaa">Factotum · in 1 hour</div><div>%s · 07:00</div>'
             '<div class="acts"><span data-tap="Skip">Skip for today</span></div></div></div>') % kit.ud("Wake up")
    return doc(T.with_overlay(today(), shade))


def p_in(mu, lo, hi, s):
    def cdf(x):
        return 0.5 * (1 + math.erf((x - mu) / (s * math.sqrt(2))))
    return max(0.0, cdf(hi) - cdf(lo))


def mass(png, box, bg):
    """Visual mass of a target as drawn: the summed difference of its pixels from the page's background (as T1.3's
    sheet_weight read the ✓ disc), in units of a full-contrast px."""
    from PIL import Image
    im = Image.open(png).convert("L")
    k = im.width / 360.0
    x0, y0, w, h = [round(c * k) for c in box]
    crop = im.crop((max(0, x0), max(0, y0), min(im.width, x0 + w), min(im.height, y0 + h)))
    return sum(abs(px - bg) for px in crop.getdata()) / 255.0 / (k * k)


def score_alarm(v):
    ctl = v.get("control")
    d = doc(alarm_phone(v))
    tp = T.taps(d)
    sn = tp["Snooze"]
    tap_dismiss = ctl or v["dismiss"] == "tap"
    bad = [x for x in tp.all if x.get("seen") and ((x["name"] == "Dismiss" and tap_dismiss) or x["name"] == "Skip")]
    aim = sum(p_in(sn["x"], b["box"][0], b["box"][0] + b["box"][2], SIGMA_GROGGY) * p_in(sn["y"], b["box"][1], b["box"][1] + b["box"][3], SIGMA_GROGGY) for b in bad)
    slap = sum(b["box"][2] * b["box"][3] for b in bad) / (360 * 740)
    hit = p_in(sn["x"], sn["box"][0], sn["box"][0] + sn["box"][2], SIGMA_GROGGY) * p_in(sn["y"], sn["box"][1], sn["box"][1] + sn["box"][3], SIGMA_GROGGY)
    png = ss.render(d, 360, 740)
    from PIL import Image
    bgpx = Image.open(png).convert("L").getpixel((2, 2))   # the page's background, top left (under the card's margin)
    card = (tp.get("Dismiss") or tp.get("Dismiss knob"))
    m_d = mass(png, card["box"], bgpx)
    m_s = mass(png, sn["box"], bgpx)
    pull = m_d / (m_d + m_s) if (m_d + m_s) else 0.5
    form = "headsup" if ctl else v["form"]
    dis = tp.get("Dismiss") or tp.get("Dismiss knob")
    skipw = "list" if ctl else v["skip"]
    skip_before = {"ring": 3, "upcoming": 1, "list": 3}[skipw]
    skip_later = {"ring": 1, "upcoming": 1 + 3, "list": 1 + 3}[skipw]
    cover = 360 * 740 if form == "full" else T.probe(d, "t2-hup-%s" % key_of(v), "(function(){var r=document.querySelector('.hup').getBoundingClientRect();return Math.round(r.width*r.height)})()")
    return {"aim_risk": round(aim, 4), "slap_risk": round(slap, 4), "snooze_miss": round(1 - hit, 4), "dismiss_pull": round(pull, 3), "snooze_actions": 1, "skip_actions": (skip_before + skip_later) / 2,
            "lock_extra": 0 if form == "full" else 1, "dismiss_effort_s": 0 if tap_dismiss else (1.0 if v["dismiss"] == "hold" else 0.5),
            "snooze_choice": 1 if (ctl or v["snooze"] == "choices") else 0, "reach": round((T.fitts(THUMB, sn) + T.fitts(THUMB, dis)) / 2, 3),
            "cover_kpx": round(cover / 1000, 1), "small": small_of(tp, {"Snooze", "Dismiss", "Skip", "Snooze 5", "Snooze 15", "Snooze 30"}),
            "clutter": T.clutter_of(lambda th: doc(alarm_phone(v), th))}


# ==== the references, normalised to the variants' names ========================================================================
def build_refs():
    with open(os.path.join(T.OUT, "t2-references.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    out = {"page": [], "cal": [], "day": [], "rem": [], "alarm": []}
    for r in src["item"]:
        s = r.get("save", "")
        out["page"].append({"app": r["app"], "form": r.get("open"), "save": "auto" if "autosave" in s else ("button" if "Save" in s else None)})
    for r in src["calendar"]:
        dflt = {"3-day": "week"}.get(r.get("default"), r.get("default"))
        sw = "menu" if r["app"] in ("org.fossify.calendar", "ws.xsoh.etar", "com.tendril.app.debug") else None
        out["cal"].append({"app": r["app"], "default": dflt, "switch": sw})
        flt = {"org.fossify.calendar": "chips", "ws.xsoh.etar": "menu", "com.tendril.app.debug": "menu"}.get(r["app"], "none")
        show = "tasks" if r["app"] == "com.tendril.app.debug" else "events"
        out["day"].append({"app": r["app"], "show": show, "filter": flt})
    for r in src["reminders"]:
        srt = r.get("sort") or ""
        order = "manual" if "manual" in srt else ("next" if r["app"] == "felixwiemuth.simplereminder" else None)
        group = "days" if r["app"] == "felixwiemuth.simplereminder" else "flat"
        out["rem"].append({"app": r["app"], "order": order, "group": group, "skip": None})
    for r in src["alarm"]:
        sn = "one" if (r.get("snooze_minutes") or r.get("snooze_bounds_dp")) else None   # one Snooze button, its length set elsewhere
        if "stepper" in (r.get("snooze_choices") or ""):
            sn = "choices"   # the length is picked on the ringing screen (Cyclic Alarms' -/+)
        out["alarm"].append({"app": r["app"], "form": r.get("form"), "dismiss": r.get("dismiss"), "snooze": sn, "skip": None})
    with open(os.path.join(T.OUT, "t2-refs.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)


# ==== the tables and pages through toast_opt's machinery =========================================================================
T.PREFIX, T.REFS, T.NAME = "t2", "t2-refs.json", "T2 items, calendar and alarms"
T.SPACES = {"page": PAGE_SPACE, "cal": CAL_SPACE, "day": DAY_SPACE, "rem": REM_SPACE, "alarm": ALARM_SPACE}
T.SCORERS = {"page": score_page, "cal": score_cal, "day": score_day, "rem": score_rem, "alarm": score_alarm}
T.CONTROLS = {
    "page": ({"form": "page", "fields": "fifteen", "save": "words", "control": True}, "a full page, fifteen fields on two lines, Cancel and Save in words top left, Delete filled at the foot, nothing kept without Save"),
    "cal": ({"default": "year", "switch": "settings", "control": True}, "the year view by default (twelve small months, no titles), the views behind ⚙"),
    "day": ({"show": "everything", "filter": "settings", "control": True}, "everything on two-line rows, the filter only in ⚙ › Calendar › Layers"),
    "rem": ({"order": "made", "group": "days", "skip": "page menu", "control": True}, "oldest made first, day headers, three-line rows, Skip only in the page's ⋯ menu"),
    "alarm": ({"form": "headsup", "dismiss": "tap", "snooze": "six", "skip": "list", "control": True}, "a heads-up card, Dismiss filled and wide on the thumb's side, a small Snooze beside it, six lengths, Skip only from the list"),
}
T.AXES = {
    "page": {"Ease": ("edit_actions", "reach"), "Context": ("-context_rows",), "Safety": ("lost_on_back",), "Clarity": ("-fields_seen", "fields_below"), "Calm": ("clutter", "desk_clutter")},
    "cal": {"Ease": ("q_actions", "switch_actions", "reach_switch"), "Density": ("-seen", "cut", "-hours", "-desk_seen", "desk_cut"), "Calm": ("clutter", "desk_clutter")},
    "day": {"Completeness": ("missed",), "Ease": ("other_actions",), "Density": ("-rows_seen", "cut", "-hours"), "Calm": ("clutter", "desk_clutter")},
    "rem": {"Clarity": ("soonest_at", "disorder"), "Ease": ("skip_actions", "reach_skip", "skip_hidden"), "Safety": ("skip_accident",), "Density": ("-rows_seen",), "Calm": ("clutter", "desk_clutter")},
    "alarm": {"Half-asleep": ("aim_risk", "slap_risk", "snooze_miss", "dismiss_pull"), "Ease": ("snooze_actions", "skip_actions", "lock_extra", "dismiss_effort_s", "reach"), "Choice": ("-snooze_choice",), "Calm": ("cover_kpx", "clutter")},
}
T.TITLES = {"page": "An item's page: how it opens, its fields, how it saves", "cal": "Calendar: the default view and the way between views",
            "day": "What a calendar day holds, and its filter", "rem": "The Reminders list: order, day headers, Skip for today",
            "alarm": "The alarm ringing: form, dismiss, snooze, Skip for today"}
T.DRAW = {
    "page": lambda v: [doc(page_phone(k, v)) for k in FIELDS] + [page_desk(v)],
    "cal": lambda v: ([doc(cal_phone("month", "control"))] if v.get("control") else [doc(cal_phone(v["default"], v["switch"])), cal_desk(v["default"], v["switch"])]),
    "day": lambda v: [doc(day_phone(v)), day_desk(v)],
    "rem": lambda v: [doc(rem_phone(v)), doc(rem_skip_doc(v)), rem_desk(v)],
    "alarm": lambda v: [doc(alarm_phone(v))] + ([upcoming_doc()] if (not v.get("control") and v["skip"] == "upcoming") else []),
}
for _k in ("_reach_switch", "_reach_skip"):
    T.v2.TOL.setdefault(_k, 0.05)


if __name__ == "__main__":
    build_refs()
    for p in T.SPACES:
        if p in sys.argv[1:]:
            T.run_part(p)
    if "page_html" in sys.argv[1:]:
        T.options_page()
    if "scores" in sys.argv[1:]:
        T.scores_page()
