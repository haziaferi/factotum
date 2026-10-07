"""T1 shared parts (decision 17), one screen at a time. Writes docs/screens/t1/screens.html and
docs/screens/t1/scores.md. Each screen has options, a control that must lose (exit 2 otherwise), states, the
phone and Windows, real copy, and measured scores beside real apps' numbers.

    PYTHONUTF8=1 python tools/screens/tier_t1.py
"""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import screen_score as ss  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t1")
e = html.escape
TARGETS = ["Search", "Capture", "Hub", "Settings"]
REFERENCE_SCREENS = ["bearable/00-main.png", "daylio/00-main.png", "howwefeel/00-main.png", "loop/00-main.png",
                     "tasks-org/00-main.png", "ticktick/00-main.png", "anytype/space.png", "obsidian/00-main.png"]

# ---- T1.1 header and bar ----------------------------------------------------------------------------------
TITLE = "Today · Mon 5 Oct"  # the date is the app's, not user data: no dotted outline
APPROVED_BUTTONS = (("⌕", "Search"), ("⚙", "Settings"))  # T1.1 approved: A, with Settings right of Search (owner, 2026-10-07)
SYNC_LINE = '<div class="note">Can\'t reach the sync folder. Changes stay on this phone until it\'s back.</div>'
EXTRA = """
.note{margin:0 12px;padding:10px 14px;border-radius:12px;background:var(--zone2);font-size:13px;color:var(--ink)}
.hdr.bottom{background:var(--zone)}
.bigdate{font-size:26px;font-weight:600;margin:10px 4px 2px}
.srchbar{flex:1;margin:0 8px 0 0}
"""


def desk_today(title_html, extra_buttons=()):
    head = ('<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything '
            '<span class="kbd">Ctrl+K</span></span>%s</div>') % (title_html, "".join(kit.icon_button(*b) for b in extra_buttons))
    page = ('<div class="page"><div class="kbd">Pages › ' + kit.ud("Garden plan") + '</div><h3>' + kit.ud("Garden plan") +
            '</h3><p>' + kit.ud("Raised beds go along the south fence.") + '</p></div>')
    return kit.desk(kit.rail("Today"), head, '<div class="dcol">%s</div>%s' % (kit.today_body(), page))


OPTIONS_T11 = [
    {"id": "A", "name": "Quiet header", "how": "direct",
     "about": "The title, then one Search button. Everything else lives in the bar, or in the Hub (Settings is a card there).",
     "phone": lambda: kit.phone(kit.header(TITLE, (("⌕", "Search"),)), kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "A′", "name": "Approved: quiet header with Settings", "how": "approved",
     "about": "The owner's choice (2026-10-07): option A, with a Settings button right of Search.",
     "phone": lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {}},
    {"id": "B", "name": "Search field as the header", "how": "direct",
     "about": "The header is the search field itself. Tapping it opens the keyboard. The date moves into the page as a large title.",
     "phone": lambda: kit.phone('<div class="hdr"><span class="cap srchbar" data-tap="Search">⌕ Search</span></div>',
                                '<div class="bigdate">%s</div>' % TITLE + kit.today_body(), kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "C", "name": "Header at the thumb (oblique: Peripheral Glance)", "how": "oblique",
     "about": "The header strip sits just above the bar, where the thumb already is, as Safari's address bar does. The top of the screen holds only content.",
     "phone": lambda: kit.phone("", kit.today_body() + '<div style="flex:1"></div>',
                                kit.header(TITLE, (("⌕", "Search"),)).replace('class="hdr"', 'class="hdr bottom"') + kit.bar("Today")),
     "desk": lambda: desk_today(TITLE), "declared": {"Settings": 2}},
    {"id": "X", "name": "Control: a busy header", "how": "control",
     "about": "Search, filter, sort, notifications and a profile in the header, plus a floating + button. It must lose.",
     "phone": lambda: kit.phone(kit.header(TITLE, (("⌕", "Search"), ("⚲", "Filter"), ("⇅", "Sort"), ("🔔", "Notifications"), ("◐", "Profile"))),
                                kit.today_body() + '<span class="ib" data-tap="Capture" style="position:absolute;right:16px;bottom:88px;background:var(--ink);color:var(--bg);width:56px;height:56px;font-size:26px">+</span>',
                                kit.bar("Today").replace('opacity:.65', '')),
     "desk": lambda: desk_today(TITLE, (("⚲", "Filter"), ("⇅", "Sort"), ("🔔", "Notifications"), ("◐", "Profile"))), "declared": {"Settings": 2}},
]
# X's receded bar items are made full strength on purpose: the control ignores depth coding.
CONTROL_CSS = ".bar .s{opacity:1;color:var(--ink)}"

STATES_T11 = [
    ("Normal", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(), kit.bar("Today"))),
    ("Hub open (the centre slot active)", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(),
                                                            kit.bar("Hub").replace('class="s hub"', 'class="s on hub"'))),
    ("Slot 5 re-pinned to the ledger", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.today_body(),
                                                       kit.bar("Today", kit.BAR[:4] + [("◇", "Ledger")]))),
    ("Long title", lambda: kit.phone(kit.header("Pages · " + kit.ud("Garden plan for the allotment, spring and summer"), (("⌕", "Search"), ("⋯", "More"))),
                                     kit.today_body(), kit.bar("Pages"))),
    ("Error: sync folder unreachable", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), SYNC_LINE + kit.today_body(), kit.bar("Today"))),
]


def make(fn, css=""):
    return lambda theme, score: kit.document(fn(), theme, EXTRA + css, score)


def score_screen(options):
    rows = []
    for o in options:
        css = CONTROL_CSS if o["how"] == "control" else ""
        r = ss.score_option(make(o["phone"], css), 360, 740, TARGETS, o["declared"])
        rd = ss.score_option(make(o["desk"], css), 1100, 660, TARGETS, o["declared"])
        r["desk_clutter"] = rd["clutter"]
        r["small"] = len(r["small_taps"]) + len(rd["small_taps"])
        r["faint_n"] = len(r["faint"]) + len(rd["faint"])
        r["min_text_short"] = max(0, 14 - r["min_text"])  # px below a 14 px floor
        r["steps_sum"] = sum(v[0] for v in r["steps"].values())
        rows.append(r)
    low = ("clutter", "desk_clutter", "strong_nav", "far_nav", "faint_n", "small", "min_text_short", "steps_sum")
    fr = ss.front(rows, low)
    return rows, fr, low


def frame(inner, theme_toggle=True):
    return inner


def section_t11(refs):
    rows, fr, low = score_screen(OPTIONS_T11)
    ctrl = [i for i, o in enumerate(OPTIONS_T11) if o["how"] == "control"]
    beaten = all(i not in fr for i in ctrl)
    head = "<tr><th>Option</th><th>Clutter (phone)</th><th>Clutter (Windows)</th><th>Strong nav items</th><th>Nav in the top quarter</th><th>Faint labels</th><th>Taps under 48 dp</th><th>Smallest text</th><th>Steps to Search · Capture · Hub · Settings</th><th></th></tr>"
    body = ""
    for o, r, i in zip(OPTIONS_T11, rows, range(len(rows))):
        steps = " · ".join("%s%s" % (v[0], "*" if v[1] == "declared" else "") for v in r["steps"].values())
        tag = "control" if o["how"] == "control" else ("front" if i in fr else "dominated")
        body += "<tr><td><b>%s</b> %s</td><td>%.3f</td><td>%.3f</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td><td>%g px</td><td>%s</td><td>%s</td></tr>" % (
            o["id"], e(o["name"]), r["clutter"], r["desk_clutter"], r["strong_nav"], r["far_nav"], r["faint_n"], e(", ".join(r["small_taps"]) or "none"), r["min_text"], steps, tag)
    refrow = " · ".join("%s %.3f" % (k.split("/")[0], v) for k, v in refs.items())
    opts = "".join('<div class="opt"><h3>%s · %s <span class="tag">%s</span></h3><p class="dim">%s</p><div class="pair">%s<div class="dwrap">%s</div></div></div>' % (
        o["id"], e(o["name"]), o["how"], e(o["about"]), o["phone"](), o["desk"]()) for o in OPTIONS_T11)
    states = "".join('<div><div class="cap2">%s</div>%s</div>' % (e(n), f()) for n, f in STATES_T11)
    refimgs = "".join('<figure><img src="../../../_screens-sources/reference/%s" alt=""><figcaption>%s · %.3f</figcaption></figure>' % (k, k.split("/")[0], v) for k, v in refs.items())
    html_ = ('<section id="t1-1"><h2>T1.1 Header and bar <span class="tag">approved 2026-10-07: A′</span></h2>'
             '<p>The chrome every screen shares: the header (title, Search) and the bar of Today · Calendar · Hub · Pages · [check-in]. '
             'Data the person would type is in a <span class="ud">dotted outline</span>. Steps marked * go through the Hub.</p>'
             '<h3>Scores</h3><table>%s%s</table><p class="dim">Clutter of the real apps\' main screens, measured the same way: %s. '
             'Lower is calmer. %s</p>'
             '<h3>Options</h3>%s<h3>States (approved: A′)</h3><div class="states">%s</div>'
             '<details><summary>Real apps compared (local screenshots, not in the public repo)</summary><div class="refs">%s</div></details></section>') % (
        head, body, refrow, "The control loses, as it must." if beaten else "<b>The control is on the front: the measures are not discriminating.</b>",
        opts, states, refimgs)
    return html_, rows, fr, beaten


# ---- T1.2 item rows ---------------------------------------------------------------------------------------
# Title only by default (decision 17). Done: tap the circle, with Undo; long press: the other actions; no swipes.
# kind, title, time, action word, secondary line (variants chapter), chips (variants chapter)
KINDS = [
    ("event", "Dentist", "09:00", "", "09:00–09:45 · Health", ["Health"]),
    ("task", "Pay the fine", "", "Done", "Due today · Car", ["Car"]),
    ("reminder", "Call the bank", "15:00", "Done", "Reminder · Money", ["Money"]),
    ("habit", "Walk", "", "Log", "Every day · Health", ["Health"]),
    ("habit", "Water", "14:00", "Log", "3 of 8 · next block 14:00", ["Health"]),  # n a day: its next block's start
    ("checklist", "Morning routine", "07:00", "Open", "Checklist · 3 of 5", []),  # a set time
    ("reading", "Sleep", "", "Add", "Reading due · hours", ["Sleep"]),
    ("task", "Return library books", "", "Done", "Due today · Errands · repeats weekly", ["Errands", "Weekly"]),
]
T12_CSS = """
.row .sub{display:block;font-size:13px;color:var(--dim);margin-top:1px}
.row .t{padding:4px 0}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--dim);margin:2px 6px 0 0}.chip::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--dim)}
.act{min-width:48px;height:48px;display:grid;place-items:center;flex:none}
.act span{border-radius:999px;padding:4px 12px;font-size:13px;background:var(--zone2);color:var(--ink)}
.mark{width:48px;height:48px;display:grid;place-items:center;margin:0 -13px;flex:none}
.mark.sq::before{content:"";width:20px;height:20px;border:2px solid var(--dim);border-radius:6px}
.mark.list::before{content:"≡";color:var(--dim);font-size:18px}
.mark.read::before{content:"∿";color:var(--dim);font-size:18px}
.word{min-width:64px;height:48px;display:grid;place-items:center;flex:none;font-size:14px;font-weight:600;color:var(--ink)}
.xrow{display:flex;align-items:center;gap:6px;min-height:40px;border-bottom:1px solid var(--dim);font-size:14px}
.xrow .t{flex:1}.xrow .ico{font-size:13px;color:var(--ink)}
.menu{position:absolute;left:12px;right:12px;bottom:84px;background:var(--zone);border-radius:16px;padding:6px;box-shadow:0 8px 28px rgba(0,0,0,.25)}
.menu .mi{min-height:48px;display:flex;align-items:center;padding:0 14px;border-radius:10px;font-size:15px}
.menu .mh{padding:8px 14px 4px;font-size:12px;color:var(--dim)}
.scrim{position:absolute;inset:0;background:rgba(0,0,0,.28)}
.toast{position:absolute;left:12px;right:12px;bottom:84px;background:var(--ink);color:var(--bg);border-radius:12px;min-height:48px;display:flex;align-items:center;padding:0 6px 0 16px;font-size:14px}
.toast .t{flex:1}.toast .u{min-width:64px;height:48px;display:grid;place-items:center;font-weight:700}
.fold{display:flex;align-items:center;min-height:48px;color:var(--dim);font-size:14px}.fold .t{flex:1}
.tm.span{line-height:1.25;font-size:12px}.tm.kind{font-size:17px;text-align:center;width:44px}.tm.when{font-size:12px}
.mark.bar::before{content:"";width:4px;height:30px;border-radius:2px;background:var(--dim)}
.mark.plus::before{content:"+";color:var(--dim);font-size:22px}
.trail{color:var(--dim);font-size:13px;flex:none;padding-right:4px}
.clamp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
"""


def sub_html(variant, sub, chips):
    if variant == "line":
        return '<span class="sub">%s</span>' % kit.ud(e(sub))
    if variant == "chips" and chips:
        return '<span class="sub">%s</span>' % "".join('<span class="chip">%s</span>' % kit.ud(e(c)) for c in chips)
    return ""


def row_a(k, variant="title"):
    """Leading mark: the left slot says what the row is (circle, time, square, list, wave); actions on the right."""
    kind, title, time, act, sub, chips = k
    if kind in ("event", "reminder"):
        lead = '<span class="tm">%s</span>' % time
    elif kind == "task":
        lead = '<span class="ck" data-tap="Done"></span>'
    else:
        lead = '<span class="mark %s"></span>' % {"habit": "sq", "checklist": "list", "reading": "read"}[kind]
    if kind == "reminder":
        lead += '<span class="ck" data-tap="Done"></span>'
    right = '<span class="act" data-tap="%s"><span>%s</span></span>' % (act, act) if kind in ("habit", "checklist", "reading") else ""
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, sub, chips), right)


def row_b(k, variant="title"):
    """Trailing action: time (if any) on the left, every action at the right edge, under the thumb."""
    kind, title, time, act, sub, chips = k
    lead = '<span class="tm">%s</span>' % time
    if kind in ("task", "reminder"):
        right = '<span class="ck" data-tap="Done" style="margin:0 -13px 0 0"></span>'
    elif kind == "event":
        right = ""
    else:
        right = '<span class="act" data-tap="%s"><span>%s</span></span>' % (act, act)
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, sub, chips), right)


def row_c(k, variant="title"):
    """Words, not marks (oblique: the Arbitrary Constraint, no glyphs): the action is a word at the right."""
    kind, title, time, act, sub, chips = k
    lead = '<span class="tm">%s</span>' % time
    right = '<span class="word" data-tap="%s">%s</span>' % (act, act) if act else ""
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, sub, chips), right)


# An event is a block of time, not a to-do (decision 02: no task state on an event), so its lead shows the
# span (start over end) where a to-do shows one time (owner's question, 2026-10-07).
EVENT_END = {"Dentist": "09:45"}
# When an untimed row belongs: its time block (decision 06b's blocks; Water's next block is 14:00), else Any time.
WHEN = {"Walk": "Morning", "Water": "14:00", "Morning routine": "Morning", "Sleep": "Evening",
        "Pay the fine": "Any time", "Return library books": "Any time"}
BLOCK_START = {"Morning": "06:00", "Afternoon": "12:00", "Evening": "18:00"}  # placeholder block starts; time blocks are set in T3
APPROVED_T12 = "D"  # owner, 2026-10-07
KIND_MARK = {"task": "◦", "habit": "↻", "checklist": "≡", "reading": "∿"}


def lead_time(k):
    kind, title, time = k[0], k[1], k[2]
    if kind == "event" and title in EVENT_END:
        return '<span class="tm span">%s<br>%s</span>' % (time, EVENT_END[title])
    return '<span class="tm">%s</span>' % time


def right_action(k):
    kind, act = k[0], k[3]
    if kind in ("task", "reminder"):
        return '<span class="ck" data-tap="Done" style="margin:0 -13px 0 0"></span>'
    if kind == "event":
        return ""
    return '<span class="act" data-tap="%s"><span>%s</span></span>' % (act, act)


def row_d(k, variant="title"):
    """A and B merged: the left column always says what or when (a time, an event's span, or a quiet kind mark),
    and every action sits at the right, under the thumb."""
    kind, title, time = k[0], k[1], k[2]
    lead = lead_time(k) if time else '<span class="tm kind">%s</span>' % KIND_MARK[kind]
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, k[4], k[5]), right_action(k))


def row_e(k, variant="title"):
    """The left column is always time: a clock time, an event's span, the habit's time block, or Any time.
    Actions at the right. The day reads top to bottom as a schedule."""
    kind, title, time = k[0], k[1], k[2]
    lead = lead_time(k) if time else '<span class="tm when">%s</span>' % WHEN.get(title, "Any time")
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, k[4], k[5]), right_action(k))


def row_f(k, variant="title"):
    """Oblique (Inversion of B): the action leads, the time trails. Every doable row starts with its control
    (circle, Log square, list, +); an event starts with a span bar. Times sit quietly at the right."""
    kind, title, time = k[0], k[1], k[2]
    if kind in ("task", "reminder"):
        lead = '<span class="ck" data-tap="Done"></span>'
    elif kind == "event":
        lead = '<span class="mark bar"></span>'
    else:
        lead = '<span class="mark %s" data-tap="%s"></span>' % ({"habit": "sq", "checklist": "list", "reading": "plus"}[kind], k[3])
    trail = '<span class="trail">%s%s</span>' % (time, "–" + EVENT_END[title] if title in EVENT_END else "") if time else ""
    return '<div class="row" data-tap="Open item">%s<span class="t">%s%s</span>%s</div>' % (lead, kit.ud(e(title)), sub_html(variant, k[4], k[5]), trail)


def row_x(k, variant="title"):
    kind, title, time, act, sub, chips = k
    return ('<div class="xrow row" data-tap="Open item"><span class="ico" data-tap="Done">☐</span><span class="ico">%s</span><span class="t">%s %s</span>'
            '<span class="ico" data-tap="Flag">⚑</span><span class="ico" data-tap="More">⋯</span></div>') % (
        {"event": "📅", "task": "✓", "reminder": "⏰", "habit": "↻", "checklist": "≡", "reading": "∿"}[kind], kit.ud(e(title)),
        " ".join('<span class="chip">%s</span>' % kit.ud(c) for c in chips + [time] if c))


def rows_today(rowf, variant="title", done=False):
    agenda = [k for k in KINDS if k[0] in ("event", "task", "reminder") and not (done and k[1] == "Pay the fine")]  # done: it folded away
    # Routines in chronological order (owner, 2026-10-07): a set time sorts by that time; an untimed routine sits at
    # the start of its time block (BLOCK_START); with neither, at the end. Done rows leave, so the next one rises.
    routines = sorted((k for k in KINDS if k[0] not in ("event", "task", "reminder")),
                      key=lambda k: k[2] or BLOCK_START.get(WHEN.get(k[1]), "99:99"))
    fold_a = '<div class="fold" data-tap="Done today"><span class="t">Done today · 2</span>▸</div>' if done else ""
    return (kit.zone("Agenda", "".join(rowf(k, variant) for k in agenda) + fold_a) +
            kit.zone("Routines", "".join(rowf(k, variant) for k in routines)))


def t12_phone(rowf, variant="title", overlay="", done=False):
    return kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap" data-tap="Capture">+ <span>Add…</span></div>' + rows_today(rowf, variant, done),
                     kit.bar("Today") + overlay)


def t12_desk(rowf):
    head = '<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything <span class="kbd">Ctrl+K</span></span></div>' % TITLE
    page = '<div class="page"><div class="kbd">Pages › %s</div><h3>%s</h3></div>' % (kit.ud("Garden plan"), kit.ud("Garden plan"))
    return kit.desk(kit.rail("Today"), head, '<div class="dcol">%s</div>%s' % (rows_today(rowf), page))


OPTIONS_T12 = [
    {"id": "A", "name": "Leading mark", "how": "direct", "f": row_a,
     "about": "The left slot says what the row is: a circle for a task, the time for an event, a square for a habit. Habit and reading actions sit at the right."},
    {"id": "B", "name": "Action at the thumb", "how": "direct", "f": row_b,
     "about": "Times line up in one column on the left. Every action sits at the right edge, where a right thumb rests: the Done circle and the Log, Open and Add buttons. Events have no action."},
    {"id": "C", "name": "Words, not marks (oblique: Arbitrary Constraint)", "how": "oblique", "f": row_c,
     "about": "No glyphs at all. The action is a word at the right: Done, Log, Open, Add. Reads in any language a symbol might not."},
    {"id": "D", "name": "A and B merged: mark or time left, action right", "how": "merged", "f": row_d,
     "about": "The left column is never empty: a time, an event's span (09:00 over 09:45), or a quiet mark for the kind (◦ task, ↻ habit, ≡ checklist, ∿ reading). Every action sits at the right, under the thumb."},
    {"id": "E", "name": "Time column, always", "how": "refined", "f": row_e,
     "about": "The left column is always time: the clock time, an event's span, a habit's time block (Morning, 14:00, Evening), or Any time. The day reads top to bottom as a schedule. Actions at the right."},
    {"id": "F", "name": "Action leads, time trails (oblique: Inversion)", "how": "oblique", "f": row_f,
     "about": "B turned inside out: each row starts with its control (circle, Log square, list, +), and an event starts with a span bar. Times sit quietly at the right edge, as in Things and Google Tasks."},
    {"id": "X", "name": "Control: dense rows", "how": "control", "f": row_x,
     "about": "40 px rows with rules, a checkbox, a kind icon, chips, a flag and an overflow ⋯ on every row. It must lose."},
]
MENU = ('<div class="scrim"></div><div class="menu"><div class="mh">%s</div>%s</div>' % (
    kit.ud("Pay the fine"), "".join('<div class="mi" data-tap="%s">%s</div>' % (a, a) for a in
                                     ("Move to later…", "Skip this one", "Edit", "Label…", "Delete"))))
TOAST = '<div class="toast"><span class="t">Done: %s</span><span class="u" data-tap="Undo">Undo</span></div>' % kit.ud("Pay the fine")
TOAST_DEL = '<div class="toast"><span class="t">Moved to Trash.</span><span class="u" data-tap="Undo">Undo</span></div>'
LONG = ("task", "Renew the parking permit before the end of the month, and bring last year's receipt", "", "Done", "", [])


def states_t12(rowf):
    long_row = rowf(LONG).replace('class="t"', 'class="t clamp"', 1)
    return [
        ("Normal", t12_phone(rowf)),
        ("Done, with Undo (the row folds into Done today)", t12_phone(rowf, overlay=TOAST, done=True)),
        ("Long press: the other actions", t12_phone(rowf, overlay=MENU)),
        ("Deleted: to Trash, with Undo", t12_phone(rowf, overlay=TOAST_DEL)),
        ("A long title, two lines at most", kit.phone(kit.header(TITLE, APPROVED_BUTTONS), kit.zone("Agenda", long_row + rowf(KINDS[0])), kit.bar("Today"))),
    ]


def section_t12():
    rows = []
    for o in OPTIONS_T12:
        css = EXTRA + T12_CSS
        r = ss.score_option(lambda t, s, o=o: kit.document(t12_phone(o["f"]), t, css, s), 360, 740, ["Done", "Log", "Capture"], {})
        rd = ss.score_option(lambda t, s, o=o: kit.document(t12_desk(o["f"]), t, css, s), 1100, 660)
        r["desk_clutter"] = rd["clutter"]
        r["faint_n"] = len(r["faint"]) + len(rd["faint"])
        r["small"] = len(r["small_taps"]) + len(rd["small_taps"])
        r["fewer_rows"] = -r["rows_visible"]
        r["strong_all"] = r["strong"]
        rows.append(r)
    low = ("clutter", "desk_clutter", "faint_n", "small", "fewer_rows", "blank_lead", "title_edges")
    fr = ss.front(rows, low)
    ctrl = [i for i, o in enumerate(OPTIONS_T12) if o["how"] == "control"]
    beaten = all(i not in fr for i in ctrl)
    head = "<tr><th>Option</th><th>Clutter (phone)</th><th>Clutter (Windows)</th><th>Rows in view</th><th>Blank left column</th><th>Title edges</th><th>Faint labels</th><th>Taps under 48 dp</th><th>Strong targets</th><th></th></tr>"
    body = "".join("<tr><td><b>%s</b> %s</td><td>%.3f</td><td>%.3f</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (
        o["id"], e(o["name"]), r["clutter"], r["desk_clutter"], r["rows_visible"], r["blank_lead"], r["title_edges"], r["faint_n"], e(", ".join(r["small_taps"]) or "none"), r["strong"],
        "control" if o["how"] == "control" else ("front" if i in fr else "dominated")) for i, (o, r) in enumerate(zip(OPTIONS_T12, rows)))
    opts = "".join('<div class="opt"><h3>%s · %s <span class="tag">%s</span></h3><p class="dim">%s</p><div class="pair">%s<div class="dwrap">%s</div></div></div>' % (
        o["id"], e(o["name"]), o["how"], e(o["about"]), t12_phone(o["f"]), t12_desk(o["f"])) for o in OPTIONS_T12)
    lead = next(o for o in OPTIONS_T12 if o["id"] == APPROVED_T12)  # states and variants are drawn on the approved row
    states = "".join('<div><div class="cap2">%s</div>%s</div>' % (e(n), h) for n, h in states_t12(lead["f"]))
    variants = "".join('<div><div class="cap2">%s</div>%s</div>' % (n, t12_phone(lead["f"], v)) for v, n in (
        ("title", "Title only (the default for now)"), ("line", "Title and one quiet line"), ("chips", "Title and label chips")))
    vscores = []
    for v in ("title", "line", "chips"):
        vs = ss.score_option(lambda t, s, v=v: kit.document(t12_phone(lead["f"], v), t, EXTRA + T12_CSS, s), 360, 740)
        vscores.append("%s: clutter %.3f, %d rows in view" % ({"title": "title only", "line": "quiet line", "chips": "chips"}[v], vs["clutter"], vs["rows_visible"]))
    html_ = ('<section id="t1-2"><h2>T1.2 Item rows <span class="tag">approved 2026-10-07: D, routines in time order</span></h2>'
             '<p>Every kind of row on one screen: an event, a task, a reminder, two habits, a checklist and a reading. Titles only (decision 17). '
             'Tap the circle for Done, with Undo; long-press for the other actions; no swipes.</p>'
             '<h3>Scores</h3><table>%s%s</table><p class="dim">%s</p><h3>Options</h3>%s'
             '<h3>States (%s)</h3><div class="states">%s</div>'
             '<h3>Chapter: what a row shows (%s)</h3><p class="dim">The three variants from decision 17, to decide later. %s.</p><div class="states">%s</div></section>') % (
        head, body, "The control loses, as it must." if beaten else "<b>The control is on the front.</b>", opts,
        e(lead["id"] + " · " + lead["name"]), states, e(lead["id"]), "; ".join(vscores), variants)
    return html_, rows, fr, beaten


# ---- generic screen section (T1.3 onward) ------------------------------------------------------------------
COLS = {  # key: (header, format)
    "clutter": ("Clutter (phone)", "%.3f"), "desk_clutter": ("Clutter (Windows)", "%.3f"), "strong": ("Strong targets", "%d"),
    "faint_n": ("Faint labels", "%d"), "small": ("Taps under 48 dp", "%d"), "steps_sum": ("Taps to finish", "%d"),
    "far_primary": ("Main action out of thumb reach", "%d"), "fields": ("Fields shown", "%d"),
}


def build_section(sid, title, intro, options, states, css, low, extra=None, approved=None):
    """options: dicts with id, name, how, about, phone(), desk(); extra(option, phone_result) adds measures.
    Returns (html, rows, front indices, control beaten)."""
    rows = []
    for o in options:
        r = ss.score_option(lambda t, s, o=o: kit.document(o["phone"](), t, EXTRA + T12_CSS + css, s), 360, 740)
        rd = ss.score_option(lambda t, s, o=o: kit.document(o["desk"](), t, EXTRA + T12_CSS + css, s), 1100, 660)
        r["desk_clutter"] = rd["clutter"]
        r["faint_n"] = len(r["faint"]) + len(rd["faint"])
        r["small"] = len(r["small_taps"]) + len(rd["small_taps"])
        r["small_list"] = r["small_taps"] + rd["small_taps"]
        if extra:
            r.update(extra(o, r))
        rows.append(r)
    fr = ss.front(rows, low)
    beaten = all(i not in fr for i, o in enumerate(options) if o["how"] == "control")
    head = "<tr><th>Option</th>%s<th></th></tr>" % "".join("<th>%s</th>" % COLS[k][0] for k in low)
    body = "".join("<tr><td><b>%s</b> %s</td>%s<td>%s</td></tr>" % (
        o["id"], e(o["name"]), "".join("<td>%s</td>" % (COLS[k][1] % r[k]) for k in low),
        "control" if o["how"] == "control" else ("front" if i in fr else "dominated")) for i, (o, r) in enumerate(zip(options, rows)))
    opts = "".join('<div class="opt"><h3>%s · %s <span class="tag">%s</span></h3><p class="dim">%s</p><div class="pair">%s<div class="dwrap">%s</div></div></div>' % (
        o["id"], e(o["name"]), o["how"], e(o["about"]), o["phone"](), o["desk"]()) for o in options)
    st = "".join('<div><div class="cap2">%s</div>%s</div>' % (e(n), f()) for n, f in states)
    smalls = sorted({x for r in rows for x in r["small_list"]})
    tag = ' <span class="tag">approved: %s</span>' % e(approved) if approved else ""
    html_ = ('<section id="%s"><h2>%s%s</h2><p>%s</p><h3>Scores</h3><table>%s%s</table><p class="dim">%s%s</p>'
             '<h3>Options</h3>%s<h3>States</h3><div class="states">%s</div></section>') % (
        sid, e(title), tag, intro, head, body, "The control loses, as it must." if beaten else "<b>The control is on the front.</b>",
        (" Small targets: " + e(", ".join(smalls)) + ".") if smalls else "", opts, st)
    return html_, rows, fr, beaten


# ---- T1.3 capture sheet ------------------------------------------------------------------------------------
# Decision 17: natural-language line, parsed chips under it; the text stays as typed; tap a chip to fix or drop it.
T13_CSS = """
.kb{height:250px;background:var(--zone2);flex:none;display:grid;place-items:center;color:var(--dim);font-size:12px}
.sheet{background:var(--zone);border-radius:20px 20px 0 0;padding:10px 12px 8px;flex:none;box-shadow:0 -8px 24px rgba(0,0,0,.12)}
.grab{width:36px;height:4px;border-radius:2px;background:var(--dim);margin:0 auto 8px;opacity:.5}
.line{display:flex;align-items:center;gap:8px;min-height:48px;font-size:16px}
.line .in{flex:1}.line .ph{color:var(--dim)}.caret{display:inline-block;width:2px;height:20px;background:var(--ink);vertical-align:-4px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 6px}
/* a chip is drawn 34 px tall inside a 48 px tap target (screen_score caught 36 px chips) */
.pc{min-height:48px;display:inline-flex;align-items:center;font-size:13px;color:var(--ink)}
.pc>b{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 12px;border-radius:999px;background:var(--zone2);font-weight:400;white-space:nowrap}
.pc{flex:none}
.pc.q>b{box-shadow:inset 0 0 0 1.5px var(--dim)}
.chips{row-gap:0}
.addb{min-width:64px;height:48px;border-radius:999px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:600;font-size:15px;flex:none}
.hint{font-size:12px;color:var(--dim);padding:2px 2px 6px}
.form .fl{min-height:48px;display:flex;align-items:center;border-bottom:1px solid var(--zone2);font-size:14px;color:var(--dim)}
.qa{width:520px;background:var(--zone);border-radius:14px;padding:12px 14px;box-shadow:0 12px 40px rgba(0,0,0,.28);margin:60px auto 0}
.qwin{width:1100px;height:660px;background:var(--bg);border-radius:10px;box-shadow:0 0 0 1px var(--zone2);position:relative;overflow:hidden}
.qwin .dim2{position:absolute;inset:0;opacity:.35}
"""
TYPED = "Dentist tomorrow 9am every 6 months"
CHIPS = [("📅", "Tue 6 Oct"), ("◷", "09:00"), ("↻", "Every 6 months"), ("▣", "Event")]


def chips_html(chips, question=None):
    out = "".join('<span class="pc" data-tap="Fix %s"><b>%s %s</b></span>' % (t, g, t) for g, t in chips)
    if question:
        out += '<span class="pc q" data-tap="Choose"><b>%s</b></span>' % question
    return '<div class="chips">%s</div>' % out


def capture_line(text, placeholder=False, add=True):
    inner = ('<span class="ph">Add a task, event or reminder…</span>' if placeholder else kit.ud(e(text)) + '<span class="caret"></span>')
    return '<div class="line"><span class="in">%s</span>%s</div>' % (inner, '<span class="addb" data-tap="Add">Add</span>' if add else "")


def sheet(text=TYPED, chips=CHIPS, question=None, placeholder=False, hint=""):
    return ('<div class="sheet"><div class="grab"></div>%s%s%s</div><div class="kb">keyboard</div>' % (
        capture_line(text, placeholder), "" if placeholder else chips_html(chips, question), '<div class="hint">%s</div>' % hint if hint else ""))


def behind():
    return '<div class="scrim" style="position:static;flex:1;background:rgba(0,0,0,.28)"></div>'


def cap_phone_a(**kw):
    return '<div class="phone">%s<div style="position:relative;flex:1;display:flex;flex-direction:column">%s</div>%s</div>' % (
        kit.header(TITLE, APPROVED_BUTTONS), behind(), sheet(**kw))


def cap_phone_b():
    """Inline: the home's capture line grows in place; the list stays visible above the keyboard."""
    line = '<div class="sheet" style="border-radius:14px;box-shadow:none;margin:0 0 4px">%s%s</div>' % (capture_line(TYPED), chips_html(CHIPS))
    return kit.phone(kit.header(TITLE, APPROVED_BUTTONS), line + kit.zone("Agenda", "".join(row_d(k) for k in KINDS[:2])), '<div class="kb">keyboard</div>')


def cap_phone_c():
    """Oblique (Build From the Defect: the keyboard takes half the screen): the parse rides in the keyboard's own
    suggestion strip, one row, and the line sits right on top of it. Nothing else is drawn."""
    strip = '<div class="chips" style="flex-wrap:nowrap;overflow:hidden;background:var(--zone2);margin:0;padding:0 8px;gap:6px">%s</div>' % "".join(
        '<span class="pc" data-tap="Fix %s"><b style="background:var(--zone)">%s %s</b></span>' % (t, g, t) for g, t in CHIPS)
    return '<div class="phone">%s%s<div class="sheet" style="border-radius:0;box-shadow:none;padding:4px 12px">%s</div>%s<div class="kb" style="height:214px">keyboard</div></div>' % (
        kit.header(TITLE, APPROVED_BUTTONS), behind(), capture_line(TYPED), strip)


def cap_phone_x():
    fields = "".join('<div class="fl">%s</div>' % f for f in ("Title", "Kind: Task ▾", "Date", "Time", "Repeat", "Reminder", "Labels", "Project page", "Notes"))
    return kit.phone(kit.header("New item", (("✕", "Cancel"), ("✓", "Save")), ("‹", "Back")), '<div class="zone form">%s</div>' % fields, "")


def cap_desk(content):
    # the dimmed app behind the quick-add window cannot be tapped: its targets are not targets here
    return '<div class="qwin"><div class="dim2">%s</div>%s</div>' % (desk_today(TITLE).replace("data-tap=", "data-behind="), content)


DESK_QA = '<div class="qa" style="position:relative">%s%s<div class="hint">Enter adds · Esc closes · Ctrl+Shift+Space from anywhere in Windows</div></div>' % (capture_line(TYPED), chips_html(CHIPS))

OPTIONS_T13 = [
    {"id": "A", "name": "Sheet over the screen", "how": "direct", "phone": cap_phone_a, "desk": lambda: cap_desk(DESK_QA),
     "about": "The capture line opens as a sheet just above the keyboard, with the parsed chips under it and Add at the thumb. The screen behind it dims. On Windows it is a small window, from anywhere (Ctrl+Shift+Space)."},
    {"id": "B", "name": "Grows in place", "how": "direct", "phone": cap_phone_b, "desk": lambda: cap_desk(DESK_QA),
     "about": "The home's capture line grows where it is, so the day stays in view beneath it while you type."},
    {"id": "C", "name": "In the keyboard's strip (oblique: Build From the Defect)", "how": "oblique", "phone": cap_phone_c,
     "desk": lambda: cap_desk(DESK_QA),
     "about": "The keyboard takes half the screen anyway, so the parse rides in one strip right on top of it, like word suggestions. The line sits above. Nothing else is drawn."},
    {"id": "X", "name": "Control: a full form", "how": "control", "phone": cap_phone_x,
     "desk": lambda: cap_desk('<div class="qa zone form" style="position:relative">%s</div>' % "".join('<div class="fl">%s</div>' % f for f in ("Title", "Kind", "Date", "Time", "Repeat", "Reminder", "Labels", "Notes"))),
     "about": "A screen of nine fields to fill one by one. It must lose."},
]
STATES_T13 = [
    ("Empty: what it accepts", lambda: cap_phone_a(placeholder=True, hint="Try: dentist tomorrow 9am · water plants every 3 days · call mum fri")),
    ("Typed: understood", lambda: cap_phone_a()),
    ("Two readings: asks, never guesses", lambda: cap_phone_a(text="Call mum fri", chips=[("▣", "Task")], question="Fri 9 Oct or every Friday?")),
    ("Nothing to understand: added as typed", lambda: cap_phone_a(text="Buy stamps", chips=[("▣", "Task"), ("📅", "No date")])),
    ("Added, with Undo", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' +
                                            kit.zone("Agenda", "".join(row_d(k) for k in KINDS[:3])), kit.bar("Today") +
                                            '<div class="toast"><span class="t">Added to Tue 6 Oct</span><span class="u" data-tap="Undo">Undo</span></div>')),
]


def t13_extra(o, r):
    # taps from Today to a saved item, typing excluded: open capture (1) + Add (1) for the line options; the form
    # needs a tap per field to set date, time, repeat and kind (4) plus open and save
    return {"steps_sum": 6 if o["how"] == "control" else 2, "fields": 9 if o["how"] == "control" else 1}


PAGE_CSS = """
body{padding:20px 16px 48px}h1{font-size:21px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 6px}h3{font-size:15px;margin:18px 0 6px}
p{max-width:95ch}.dim{color:var(--dim)}
table{border-collapse:collapse;font-size:13px}td,th{padding:5px 10px;text-align:left;border-top:1px solid var(--zone2);vertical-align:top}th{color:var(--dim);font-weight:600}
.opt{background:var(--zone);border-radius:16px;padding:12px 16px;margin:12px 0}
.opt .phone,.states .phone{box-shadow:0 0 0 1px var(--zone2)}
.pair{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding-bottom:6px}.dwrap{flex:none}
.tag{font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;background:var(--zone2);color:var(--dim)}
.states{display:flex;gap:16px;overflow-x:auto;padding-bottom:6px}.cap2{font-size:12px;color:var(--dim);margin:0 0 6px;max-width:360px}
.refs{display:flex;gap:12px;flex-wrap:wrap}.refs img{width:180px;border-radius:12px}figure{margin:0}figcaption{font-size:12px;color:var(--dim)}
.sw{display:flex;gap:6px;margin:10px 0}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    refs = ss.reference_clutter(REFERENCE_SCREENS)
    s11, rows, fr, beaten = section_t11(refs)
    s12, rows12, fr12, beaten12 = section_t12()
    s13, rows13, fr13, beaten13 = build_section(
        "t1-3", "T1.3 Capture sheet",
        "One line in plain language; what it understood shows as chips under the line (decision 17). The text stays as typed; "
        "a chip is tapped to fix or drop it. Taps exclude typing. Windows: a small window from anywhere.",
        OPTIONS_T13, STATES_T13, T13_CSS, ("clutter", "desk_clutter", "faint_n", "small", "steps_sum", "fields"), t13_extra)
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Factotum T1 shared parts</title><style>%s\n%s\n%s\n%s\n%s</style></head><body>' % (kit.theme_css(), kit.BASE_CSS, EXTRA, T12_CSS + T13_CSS, PAGE_CSS),
            '<h1>T1 · Shared parts</h1><p class="dim">Decision 17. Greys only; colour comes after every screen is settled. '
            'Type and icons are placeholders. One screen at a time: each waits for the owner\'s approval.</p>',
            '<div class="sw"><button onclick="document.documentElement.dataset.theme=\'light\'">Light</button>'
            '<button onclick="document.documentElement.dataset.theme=\'dark\'">Dark</button><button onclick="document.documentElement.dataset.theme=\'oled\'">OLED</button></div>',
            s13, s12, s11, "</body></html>"]
    with open(os.path.join(OUT, "screens.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(page))
    md = ["# T1 scores", "", "Generated by `tools/screens/tier_t1.py`.", "", "## T1.1 Header and bar", "",
          "| Option | Clutter phone | Clutter Windows | Strong nav | Nav in top quarter | Faint labels | Taps < 48 dp | Smallest text | Steps (Search, Capture, Hub, Settings) | Status |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for o, r, i in zip(OPTIONS_T11, rows, range(len(rows))):
        md.append("| %s %s | %.3f | %.3f | %d | %d | %d | %s | %g px | %s | %s |" % (o["id"], o["name"], r["clutter"], r["desk_clutter"], r["strong_nav"], r["far_nav"], r["faint_n"],
                  ", ".join(r["small_taps"]) or "none", r["min_text"], " · ".join(str(v[0]) for v in r["steps"].values()),
                  "control" if o["how"] == "control" else ("front" if i in fr else "dominated")))
    md += ["", "Reference main screens: " + ", ".join("%s %.3f" % kv for kv in refs.items())]
    md += ["", "## T1.2 Item rows", "", "| Option | Clutter phone | Clutter Windows | Rows in view | Blank left | Title edges | Faint | Taps < 48 dp | Status |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s %s | %.3f | %.3f | %d | %d | %d | %d | %s | %s |" % (o["id"], o["name"], r["clutter"], r["desk_clutter"], r["rows_visible"], r["blank_lead"], r["title_edges"], r["faint_n"],
           ", ".join(r["small_taps"]) or "none", "control" if o["how"] == "control" else ("front" if i in fr12 else "dominated"))
           for i, (o, r) in enumerate(zip(OPTIONS_T12, rows12))]
    md += ["", "## T1.3 Capture sheet", ""] + ["- %s %s: clutter %.3f / %.3f, faint %d, small %d, taps %d, fields %d, %s" % (
        o["id"], o["name"], r["clutter"], r["desk_clutter"], r["faint_n"], r["small"], r["steps_sum"], r["fields"],
        "control" if o["how"] == "control" else ("front" if i in fr13 else "dominated")) for i, (o, r) in enumerate(zip(OPTIONS_T13, rows13))]
    with open(os.path.join(OUT, "scores.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md[-5:]))
    if not (beaten and beaten12 and beaten13):
        sys.exit(2)


if __name__ == "__main__":
    main()
