"""T1 shared parts (decision 17), one screen at a time. Writes docs/screens/t1/screens.html and
docs/screens/t1/scores.md. Each screen has options, a control that must lose (exit 2 otherwise), states, the
phone and Windows, real copy, and measured scores beside real apps' numbers.

    PYTHONUTF8=1 python tools/screens/tier_t1.py
"""
import html
import math
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
APPROVED_T11 = "A′"  # owner, 2026-10-07
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
     "phone": lambda: kit.phone(kit.header(TITLE, (("⌕", "Search"), ("⚲", "Filter"), ("⇅", "Sort"), ("◔", "Notifications"), ("◐", "Profile"))),
                                kit.today_body() + '<span class="ib" data-tap="Capture" style="position:absolute;right:16px;bottom:88px;background:var(--ink);color:var(--bg);width:56px;height:56px;font-size:26px">+</span>',
                                kit.bar("Today").replace('opacity:.65', '')),
     "desk": lambda: desk_today(TITLE, (("⚲", "Filter"), ("⇅", "Sort"), ("◔", "Notifications"), ("◐", "Profile"))), "declared": {"Settings": 2}},
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


def options_html(items, approved=None):
    """items: (option, phone html, desk html). Once a screen is approved, the options not picked fold into one
    closed <details> under the picked one (owner, 2026-10-07); before that, every option is open."""
    def block(o, ph, dk):
        return ('<div class="opt"><h3>%s · %s <span class="tag">%s</span></h3><p class="dim">%s</p><div class="pair">%s<div class="dwrap">%s</div></div></div>'
                % (o["id"], e(o["name"]), o["how"], e(o["about"]), ph, dk))
    if not approved:
        return "".join(block(*it) for it in items)
    picked = "".join(block(*it) for it in items if it[0]["id"] == approved)
    rest = [it for it in items if it[0]["id"] != approved]
    return picked + '<details class="notpicked"><summary>Options not picked (%s)</summary>%s</details>' % (
        ", ".join(e(it[0]["id"]) for it in rest), "".join(block(*it) for it in rest))


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
    opts = options_html([(o, o["phone"](), o["desk"]()) for o in OPTIONS_T11], APPROVED_T11)
    states = "".join('<div><div class="cap2">%s</div>%s</div>' % (e(n), f()) for n, f in STATES_T11)
    refimgs = "".join('<figure><img src="../../../_screens-sources/reference/%s" alt=""><figcaption>%s · %.3f</figcaption></figure>' % (k, k.split("/")[0], v) for k, v in refs.items())
    html_ = ('<section id="t1-1"><h2>T1.1 Header and bar <span class="tag">approved 2026-10-07: A′</span></h2>'
             '<p>The chrome every screen shares: the header (title, Search) and the bar of Today · Calendar · Hub · Pages · [Check-in]. '
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
        {"event": "◷", "task": "✓", "reminder": "◴", "habit": "↻", "checklist": "≡", "reading": "∿"}[kind], kit.ud(e(title)),
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
    opts = options_html([(o, t12_phone(o["f"]), t12_desk(o["f"])) for o in OPTIONS_T12], APPROVED_T12)
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


def build_section(sid, title, intro, options, states, css, low, extra=None, approved=None, must=None):
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
    # must(row) -> None or the reason a row breaks an owner requirement; such a row cannot be on the front
    fails = {i: must(r) for i, r in enumerate(rows)} if must else {}
    ok = [i for i in range(len(rows)) if not fails.get(i)]
    fr = [ok[j] for j in ss.front([rows[i] for i in ok], low)]
    beaten = all(i not in fr for i, o in enumerate(options) if o["how"] == "control")
    head = "<tr><th>Option</th>%s<th></th></tr>" % "".join("<th>%s</th>" % COLS[k][0] for k in low)
    body = "".join("<tr><td><b>%s</b> %s</td>%s<td>%s</td></tr>" % (
        o["id"], e(o["name"]), "".join("<td>%s</td>" % (COLS[k][1] % r[k]) for k in low),
        ("control" if o["how"] == "control" else ("front" if i in fr else "dominated")) + (" · fails: " + e(fails[i]) if fails.get(i) else ""))
        for i, (o, r) in enumerate(zip(options, rows)))
    opts = options_html([(o, o["phone"](), o["desk"]()) for o in options], approved)
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
.addc{width:48px;height:48px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-size:20px;font-weight:700;flex:none}
.addb{min-width:64px;height:48px;border-radius:999px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:600;font-size:15px;flex:none}
.hint{font-size:12px;color:var(--dim);padding:2px 2px 6px}
.form .fl{min-height:48px;display:flex;align-items:center;border-bottom:1px solid var(--zone2);font-size:14px;color:var(--dim)}
.qa{width:520px;background:var(--zone);border-radius:14px;padding:12px 14px;box-shadow:0 12px 40px rgba(0,0,0,.28);margin:60px auto 0}
.qwin{width:1100px;height:660px;background:var(--bg);border-radius:10px;box-shadow:0 0 0 1px var(--zone2);position:relative;overflow:hidden}
.qwin .dim2{position:absolute;inset:0;opacity:.35}
"""
TYPED = "Dentist tomorrow 9am every 6 months"
# chips are text only: no emoji, no icons (owner, 2026-10-07)
CHIPS = [("", "Tue 6 Oct"), ("", "09:00"), ("", "Every 6 months"), ("", "Event")]


def chips_html(chips, question=None):
    out = "".join('<span class="pc" data-tap="Fix %s"><b>%s</b></span>' % (t, t) for g, t in chips)
    if question:
        out += '<span class="pc q" data-tap="Choose"><b>%s</b></span>' % question
    return '<div class="chips">%s</div>' % out


def capture_line(text, placeholder=False, add=True, approved=False):
    """approved (T1.3 A′, owner 2026-10-07): Add is a 48 px check, and a small Full form button sits before it."""
    inner = ('<span class="ph">Add a task, event or reminder…</span>' if placeholder else kit.ud(e(text)) + '<span class="caret"></span>')
    if approved:
        btns = '<span class="ib" data-tap="Full form" title="Full form">▤</span><span class="addc" data-tap="Add" title="Add">✓</span>'
    else:
        btns = '<span class="addb" data-tap="Add">Add</span>' if add else ""
    return '<div class="line"><span class="in">%s</span>%s</div>' % (inner, btns)


def sheet(text=TYPED, chips=CHIPS, question=None, placeholder=False, hint="", approved=False):
    return ('<div class="sheet"><div class="grab"></div>%s%s%s</div><div class="kb">keyboard</div>' % (
        capture_line(text, placeholder, approved=approved), "" if placeholder else chips_html(chips, question),
        '<div class="hint">%s</div>' % hint if hint else ""))


def cap_phone_a2(**kw):
    """T1.3 approved, A′: the sheet over Today, which stays visible under a slight shade (as on Windows)."""
    today = kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + rows_today(row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")  # behind the sheet: seen, not tapped
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div>'
               '<div style="position:absolute;left:0;right:0;bottom:0">%s</div>' % sheet(approved=True, **kw))
    return today[:-len("</div>")] + overlay + "</div>"


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
        '<span class="pc" data-tap="Fix %s"><b style="background:var(--zone)">%s</b></span>' % (t, t) for g, t in CHIPS)
    return '<div class="phone">%s%s<div class="sheet" style="border-radius:0;box-shadow:none;padding:4px 12px">%s</div>%s<div class="kb" style="height:214px">keyboard</div></div>' % (
        kit.header(TITLE, APPROVED_BUTTONS), behind(), capture_line(TYPED), strip)


def cap_phone_x():
    fields = "".join('<div class="fl">%s</div>' % f for f in ("Title", "Kind: Task ▾", "Date", "Time", "Repeat", "Reminder", "Labels", "Project page", "Notes"))
    return kit.phone(kit.header("New item", (("✕", "Cancel"), ("✓", "Save")), ("‹", "Back")), '<div class="zone form">%s</div>' % fields, "")


def cap_desk(content):
    # the dimmed app behind the quick-add window cannot be tapped: its targets are not targets here
    return '<div class="qwin"><div class="dim2">%s</div>%s</div>' % (desk_today(TITLE).replace("data-tap=", "data-behind="), content)


DESK_QA2 = '<div class="qa" style="position:relative">%s%s<div class="hint">Enter adds · Esc closes · Ctrl+Shift+Space from anywhere in Windows</div></div>' % (capture_line(TYPED, approved=True), chips_html(CHIPS))
DESK_QA = '<div class="qa" style="position:relative">%s%s<div class="hint">Enter adds · Esc closes · Ctrl+Shift+Space from anywhere in Windows</div></div>' % (capture_line(TYPED), chips_html(CHIPS))

# T1.3 v4, selected by the owner (2026-10-07; decision 17): no chips, the understood words highlighted; ⋯ beside the
# text box, level with its first line; the box spans the full width and is one line high until the text wraps; the hint
# scrolls through the 14 shorthands while empty, and shows the kind and its field markers once a kind is typed; Enter
# adds; Details opens the full page; the placeholder follows the screen capture opens from.
V4_PLACEHOLDER = {"Today": "Add anything…", "Journal": "Write a line…", "Water tracker": "Log water…", "Calendar": "Add an event…"}


def cap_v4(state="empty", opened_from="Today"):
    import legend_opt as L  # imported here: legend_opt imports this module
    return L.phone("both", state).replace("Add a task, event, log or journal line…", e(V4_PLACEHOLDER[opened_from]))


def desk_v4():
    import legend_opt as L
    # Windows has room (owner, 2026-10-07: two rows of instructive text are fine on desktop): the empty line's 14 shorthands
    # wrap onto rows instead of scrolling sideways, and the keyboard line sits under them
    sheet = L.sheet("both", "empty").replace('class="sheet" style="position:relative"', 'class="qa" style="position:relative"')
    sheet = sheet.replace('class="hint scroll"', 'class="hint" style="white-space:normal"').replace(
        "Add a task, event, log or journal line…", e(V4_PLACEHOLDER["Today"]))
    # the keyboard line sits inside the window, under the shorthand hint (a first draft put it outside, over the rail)
    sheet = sheet[:-len("</div>")] + '<div class="hint">Enter adds · Esc closes · Ctrl+Shift+Space from anywhere in Windows</div></div>'
    return cap_desk('<div class="c2">%s</div>' % sheet)


APPROVED_T13 = "v4"  # owner, 2026-10-07 (A′ was approved earlier the same day, then superseded)
OPTIONS_T13 = [
    {"id": "v4", "name": "Selected: highlighted parse, ⋯ beside the line, shorthand hint, context-aware placeholder", "how": "approved",
     "phone": cap_v4, "desk": desk_v4,
     "about": "The owner's design (decision 17, T1.3 v4), after scoring chips, routing, add, kind display, legend and placeholder: "
              "no chips, the understood words highlighted in the text; ⋯ beside the text box, level with its first line (it opens the "
              "full page); the box keeps its full width and one-line height until the text wraps; while empty, the hint scrolls through "
              "the 14 shorthands (on Windows they wrap onto two rows, with the keyboard line under them); once a kind is typed it shows the kind and its field markers; Enter adds; the placeholder says what "
              "the screen it opens from will make."},
    {"id": "A′", "name": "Approved earlier on 2026-10-07, superseded by v4: sheet over a visible Today, check to add, full form button", "how": "direct",
     "phone": cap_phone_a2, "desk": lambda: cap_desk(DESK_QA2),
     "about": "The owner's choice (2026-10-07): option A, with Today left visible under a slight shade (as on Windows), Add as a check, and a small button that opens the full form."},
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
    ("Empty, from Today: Add anything…", lambda: cap_v4("empty", "Today")),
    ("A kind typed: the kind and its field markers", lambda: cap_v4("typed")),
    ("Wrapped: the text keeps its rectangle, ⋯ level with the first line", lambda: cap_v4("wrapped")),
    ("Empty, from Journal: Write a line…", lambda: cap_v4("empty", "Journal")),
    ("Empty, from the water tracker: Log water…", lambda: cap_v4("empty", "Water tracker")),
    ("Empty, from Calendar: Add an event…", lambda: cap_v4("empty", "Calendar")),
]
STATES_T13_A2 = [
    ("Empty: what it accepts", lambda: cap_phone_a2(placeholder=True, hint="Try: dentist tomorrow 9am · water plants every 3 days · call mum fri")),
    ("Typed: understood", lambda: cap_phone_a2()),
    ("Two readings: asks, never guesses", lambda: cap_phone_a2(text="Call mum fri", chips=[("", "Task")], question="Fri 9 Oct or every Friday?")),
    ("Nothing to understand: added as typed", lambda: cap_phone_a2(text="Buy stamps", chips=[("", "Task"), ("", "No date")])),
    ("Added, with Undo", lambda: kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' +
                                            kit.zone("Agenda", "".join(row_d(k) for k in KINDS[:3])), kit.bar("Today") +
                                            '<div class="toast"><span class="t">Added to Tue 6 Oct</span><span class="u" data-tap="Undo">Undo</span></div>')),
]


def t13_extra(o, r):
    # taps from Today to a saved item, typing excluded: open capture (1) + Add (1) for the line options; the form
    # needs a tap per field to set date, time, repeat and kind (4) plus open and save
    return {"steps_sum": 6 if o["how"] == "control" else 2, "fields": 9 if o["how"] == "control" else 1}


# ---- T1.3 refined: sizes and the place of ✓ and ▤ ------------------------------------------------------------
# Owner, 2026-10-07: free = ✓/▤ placement and sizes; balanced (a front); right thumb, with a left-hand mirror setting.
# The options are capture_opt.py's balanced picks, held in all four frame x thumb-rest runs; the reference apps were
# measured on the owner's phone (capture_opt.REFERENCES). Here each is drawn and re-measured from the render.
ENTER_KEY = (330, 712)  # the mockup keyboard is 250 px tall at the phone's foot, as in capture_opt's model frame


def sheet_v(place, font, add, text=TYPED, chips=CHIPS, mirror=False, placeholder=False, question=None, hint="", form_px=48,
            add_style="filled", form_glyph="▤"):
    """place: line | chips | row | split | top (the control). add: ✓'s diameter in px; form_px: ▤'s target.
    Glyphs follow Material's proportions, so the size drawn is the size scored: ✓ at 43% of its disc (24 in a 56 FAB),
    ▤ at 24 (the standard icon size), where the first run kept them at 20 and 18 whatever the target."""
    inner = ('<span class="ph">Add a task, event or reminder…</span>' if placeholder else kit.ud(e(text)) + '<span class="caret"></span>')
    fword = form_glyph.isalpha()
    form = '<span class="ib" data-tap="Full form" title="Full form" style="%sheight:%dpx;font-size:%s">%s</span>' % (
        "width:auto;padding:0 10px;" if fword else "width:%dpx;" % form_px, form_px, "14px;color:var(--ink)" if fword else "24px", form_glyph)
    ok = add_button(add, add_style)
    rev = ";flex-direction:row-reverse" if mirror else ""
    on_line = {"line": form + ok, "split": form, "top": ok}.get(place, "")
    line = '<div class="line" style="font-size:%dpx%s"><span class="in">%s</span>%s</div>' % (font, rev, inner, on_line)
    ch = "" if placeholder else chips_html(chips, question)
    if place in ("chips", "split"):
        btns = (form + ok) if place == "chips" else ok
        ch = '<div style="display:flex;align-items:flex-end;gap:4px%s"><div style="flex:1;min-width:0">%s</div>%s</div>' % (rev, ch, btns)
    row = '<div style="display:flex;justify-content:space-between;margin-top:4px%s">%s%s</div>' % (rev, form, ok) if place == "row" else ""
    return '<div class="sheet" style="padding-top:16px">%s%s%s%s</div>' % (line, ch, row, '<div class="hint">%s</div>' % hint if hint else "")


# ✓'s look (owner, 2026-10-07: "consider changing the icons"): the fill decides the button's visual mass far more
# than its size does. filled = ink disc (as approved); tonal = the zone2 grey with an ink glyph (Material's tonal
# button); outline = a ring; arrow = tonal with a send arrow (Microsoft To Do, Todoist); word = a tonal "Add" pill.
ADD_STYLES = {
    "filled": ("✓", "background:var(--ink);color:var(--bg)"),
    "tonal": ("✓", "background:var(--zone2);color:var(--ink)"),
    "outline": ("✓", "background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--dim)"),
    "arrow": ("↑", "background:var(--zone2);color:var(--ink)"),
    "word": ("Add", "background:var(--zone2);color:var(--ink)"),
}


def add_button(size, style="filled"):
    glyph, paint = ADD_STYLES[style]
    if style == "word":
        return ('<span class="addc" data-tap="Add" title="Add" style="width:auto;padding:0 18px;border-radius:999px;height:%dpx;'
                'font-size:15px;font-weight:600;%s">Add</span>' % (size, paint))
    return '<span class="addc" data-tap="Add" title="Add" style="width:%dpx;height:%dpx;font-size:%dpx;%s">%s</span>' % (
        size, size, round(size * 0.43), paint, glyph)


def cap_phone_v(place, font, add, **kw):
    today = kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + rows_today(row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    if place == "top":  # the control: Any.do's layout, the line at the top of the screen with Add at its far end
        overlay = ('<div class="cover" style="position:absolute;inset:0;background:var(--bg);display:flex;flex-direction:column">%s'
                   '<div style="flex:1"></div><div class="kb">keyboard</div></div>') % sheet_v(place, font, add, **kw).replace(
                       'class="sheet" style="', 'class="sheet" style="border-radius:0;box-shadow:none;')
    else:
        overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div style="position:absolute;left:0;right:0;bottom:0">%s'
                   '<div class="kb">keyboard</div></div>') % sheet_v(place, font, add, **kw)
    return today[:-len("</div>")] + overlay + "</div>"


def desk_v(place, font, add):
    s = sheet_v(place, min(font, 16), min(add, 48)).replace('class="sheet" style="', 'class="qa" style="position:relative;')
    return cap_desk(s)


T13R = [  # (id, name, how, place, font, ✓ px, about)
    ("A′", "As approved: ✓ and ▤ on the line, 16 px", "approved", "line", 16, 48,
     "T1.3 as approved. The line keeps 104 px for its buttons, so the sample wraps to two lines, and ✓ sits at the line's end, above the chips."),
    ("K", "Knee: ✓ and ▤ at the end of the chip row, 18 px, ✓ 56", "direct", "chips", 18, 56,
     "The whole front's knee in every frame and thumb position tried. The line gets the full width, so the sample reads on one line at 18 px; "
     "✓ drops to the chip row, nearer the thumb resting on Enter, and grows to 56. As Todoist does, with a bigger target."),
    ("K64", "K with ✓ 64", "direct", "chips", 18, 64,
     "K at the next size up. Thumb travel 0.12 bits less than K (about 15-25 ms a capture); the disc's area grows by a third."),
    ("K72", "K with ✓ 72", "direct", "chips", 18, 72,
     "The largest size searched: where the optimizer lands when nothing weighs a button's size. 0.27 bits less than K; the disc's area is 65% larger."),
    ("S", "Split: ▤ on the line, ✓ at the end of the chip row, 16 px, ✓ 56", "direct", "split", 16, 56,
     "The quieter action stays up on the line, and only ✓ comes down to the thumb. One line at 16 px; ✓ and ▤ are far apart, so a slip cannot open the form."),
    ("R", "Action row: ▤ left, ✓ right, above the keyboard, 18 px, ✓ 52", "direct", "row", 18, 52,
     "A row of its own just above the keyboard, as TickTick and Google Tasks have. The most spacing round ✓, at the cost of the tallest sheet."),
    ("X", "Control: Any.do's top line, ✓ 40 at the top right", "control", "top", 16, 40,
     "The line opens at the top of the screen with Add at its far end, as Any.do does: the furthest the thumb can travel. It must lose."),
]
OPTIONS_T13R = [{"id": i, "name": n, "how": h, "about": a, "phone": (lambda p=p, f=f, s=s: cap_phone_v(p, f, s)),
                 "desk": (lambda p=p, f=f, s=s: desk_v(p, f, s))} for i, n, h, p, f, s, a in T13R]
STATES_T13R = [
    ("K, empty: what it accepts", lambda: cap_phone_v("chips", 18, 56, placeholder=True, hint="Try: dentist tomorrow 9am · water plants every 3 days")),
    ("K, two readings: asks, never guesses", lambda: cap_phone_v("chips", 18, 56, text="Call mum fri", chips=[("", "Task")], question="Fri 9 Oct or every Friday?")),
    ("K, left-hand setting (mirrored)", lambda: cap_phone_v("chips", 18, 56, mirror=True)),
    ("S, left-hand setting (mirrored)", lambda: cap_phone_v("split", 16, 56, mirror=True)),
]


def t13r_extra(o, r):
    taps = {t["name"]: t for t in r["taps_raw"]}

    def fid(name):
        t = taps[name]
        return math.log2(math.hypot(ENTER_KEY[0] - t["x"], ENTER_KEY[1] - t["y"]) / min(t["w"], t["h"]) + 1)
    font = next(f for i, n, h, p, f, s, a in T13R if i == o["id"])
    return {"fitts_add": round(fid("Add"), 2), "fitts_form": round(fid("Full form"), 2) if "Full form" in taps else 9.0,
            "sheet_h": r["sheet_h"], "lines": r["line_lines"], "text_small": 18 - font}


COLS.update({"fitts_add": ("Thumb travel to ✓ (Fitts ID from Enter)", "%.2f"), "fitts_form": ("Thumb travel to ▤", "%.2f"),
             "sheet_h": ("Sheet height dp", "%d"), "lines": ("Lines the sample wraps to", "%d"), "text_small": ("Text px under 18", "%d")})


# ---- T1.4 Hub sheet (cards) -------------------------------------------------------------------------------
# Owner, 2026-10-07: cards, so every screen of a module is visible (the working form, not the final one). The Hub
# opens on the capture line (A+'s definition); a long press on the Hub captures directly.
HUB_GROUPS = [
    ("Calendar", "▦", ["Day", "Week", "Month", "Planner"]),
    ("Routines", "↻", ["Habits", "Trackers", "Activities", "Checklists", "Charts", "Goals"]),
    ("Check-in", "◎", ["Check-in", "Ledger", "Sensory", "Trend"]),
    ("Pages", "☰", ["Journal", "Tree", "Templates", "Road Map"]),
    ("Review", "↗", ["This week", "Time totals", "History"]),
    ("App", "⚙", ["Labels", "Time blocks", "Calendars", "Settings", "Trash", "About"]),
]
FEATURES = [f for _, _, fs in HUB_GROUPS for f in fs]
RECENT = ["Journal", "Ledger", "Trackers", kit.ud("Garden plan")]
T14_CSS = """
.hubsheet{position:absolute;left:0;right:0;top:36px;bottom:72px;background:var(--bg);border-radius:20px 20px 0 0;padding:8px 12px;overflow:hidden;box-shadow:0 -8px 28px rgba(0,0,0,.18)}
.card{background:var(--zone);border-radius:14px;padding:4px 10px 4px;margin:0 0 8px}
.card h5{margin:2px 0 0;font-size:12px;font-weight:600;color:var(--dim);display:flex;gap:6px;align-items:center}
.ft{display:flex;flex-wrap:wrap;column-gap:6px}
.fe{min-height:48px;min-width:48px;display:inline-flex;align-items:center;justify-content:center;padding:0 8px;font-size:14px;color:var(--ink)}
.ft{margin:0 -8px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid2 .card{margin:0}
.hlist .hr{min-height:48px;display:flex;align-items:center;border-bottom:1px solid var(--zone2);font-size:15px;padding:0 4px}
.hlist .hh{font-size:12px;color:var(--dim);padding:8px 4px 2px;font-weight:600}
.subl{font-size:12px;color:var(--dim);margin:2px 2px 0}
.hubpanel{position:absolute;left:100px;top:12px;width:760px;bottom:12px;background:var(--bg);border-radius:16px;padding:14px;box-shadow:0 12px 40px rgba(0,0,0,.25);overflow:hidden}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.grid3 .card{margin:0}
"""


def feat(f):
    # plain text on the card, no pill: a box inside a box doubled the clutter (0.065 against the list's 0.035)
    return '<span class="fe" data-tap="%s">%s</span>' % (re_strip(f), f)


def re_strip(f):
    return f.replace('<span class="ud">', "").replace("</span>", "")


def card(name, glyph, feats):
    return '<div class="card"><h5>%s %s</h5><div class="ft">%s</div></div>' % (glyph, e(name), "".join(feat(f) for f in feats))


def hub_top():
    return ('<div class="grab"></div><div class="line" style="background:var(--zone2);border-radius:14px;padding:0 6px 0 14px;margin-bottom:4px">'
            '<span class="in ph" style="color:var(--dim)">Add a task, event or reminder…</span><span class="ib" data-tap="Full form">▤</span></div>'
            '<div class="subl">Pinned and recent</div><div class="ft" style="margin-bottom:4px">%s</div>' % "".join(feat(f) for f in RECENT))


def hub_phone(body, top=True, v4=False):
    today = kit.phone(kit.header(TITLE, APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + rows_today(row_d),
                      kit.bar("Hub").replace('class="s hub"', 'class="s on hub"'))
    today = today.replace('data-tap="Open item"', 'data-behind="x"').replace('data-tap="Done"', 'data-behind="x"').replace('data-tap="Capture"', 'data-behind="x"')
    return today[:-len("</div>")] + '<div class="scrim" style="bottom:72px;background:rgba(0,0,0,.16)"></div><div class="hubsheet">%s%s</div></div>' % (
        hub_top() if top and not v4 else "", body)


def hub_a():
    return hub_phone("".join(card(*g) for g in HUB_GROUPS))


def hub_b():
    return hub_phone('<div class="grid2">%s</div>' % "".join(card(*g) for g in HUB_GROUPS))


def hub_c():
    """Oblique (Cross-Domain Raid, a store map): cards sit where the bar says they live. Calendar and Routines on the
    left under Calendar's slot, Pages and Check-in on the right under theirs, Review and App across the foot."""
    by = {g[0]: g for g in HUB_GROUPS}
    left = card(*by["Calendar"]) + card(*by["Routines"])
    right = card(*by["Pages"]) + card(*by["Check-in"])
    foot = '<div class="grid2">%s%s</div>' % (card(*by["Review"]), card(*by["App"]))
    return hub_phone('<div class="grid2"><div>%s</div><div>%s</div></div>%s' % (left, right, foot))


def hub_x():
    rows = "".join('<div class="hh">%s</div>%s' % (e(n), "".join('<div class="hr" data-tap="%s">%s</div>' % (f, f) for f in fs)) for n, _, fs in HUB_GROUPS)
    return hub_phone('<div class="hlist">%s</div>' % rows, top=False)


def hub_desk(inner):
    d = desk_today(TITLE).replace('class="s hub"', 'class="s on hub"')
    d = d.replace('data-tap="Open item"', 'data-behind="x"').replace('data-tap="Done"', 'data-behind="x"').replace('data-tap="Capture"', 'data-behind="x"').replace('data-tap="Search"', 'data-behind="x"')
    return d[:-len("</div>")] + '<div class="hubpanel">%s</div></div>' % inner


DESK_HUB = '<div class="grid3">%s</div>' % "".join(card(*g) for g in HUB_GROUPS)


def hub_v4(oid):
    """T1.4 re-scored with T1.3's carry-overs (owner, 2026-10-07): hub_opt.py builds every option on the v4 line."""
    import hub_opt  # imported here: hub_opt imports this module
    return dict((o[0], o[3]) for o in hub_opt.OPTIONS)[oid]()


def hub_desk_v4():
    import hub_opt
    return hub_opt.DESK()


APPROVED_T14 = "A0"  # owner, 2026-10-08: the App card leaves the Hub for ⚙; one column, Pinned and recent kept


def settings_v4():
    """⚙ (T1.1's header, top right) now holds the App card's screens (owner, 2026-10-08)."""
    rows = "".join('<div class="row" data-tap="%s"><span class="t">%s</span></div>' % (n, n)
                   for n in ("Settings", "Labels", "Time blocks", "Calendars", "Trash", "About"))
    return kit.phone(kit.header("Settings", (), ("‹", "Back")), kit.zone("App", rows), kit.bar("Today"))


OPTIONS_T14 = [
    {"id": "C", "name": "Cards where the bar says they live (store map), with Pinned and recent", "how": "oblique", "phone": lambda: hub_v4("C"),
     "desk": hub_desk_v4,
     "about": "A store map: Calendar and Routines on the left, under Calendar's slot; Pages and Check-in on the right, under theirs; Review and App across the foot. The T1.3 v4 capture line on top, then Pinned and recent."},
    {"id": "B-", "name": "Two columns of cards, no Pinned and recent", "how": "direct", "phone": lambda: hub_v4("B-"), "desk": hub_desk_v4,
     "about": "Two cards across, with Pinned and recent left out so that every screen fits."},
    {"id": "C-", "name": "Store map, no Pinned and recent", "how": "oblique", "phone": lambda: hub_v4("C-"), "desk": hub_desk_v4,
     "about": "The store map without Pinned and recent."},
    {"id": "A0", "name": "Selected: one column, no App card (App's screens behind ⚙)", "how": "approved", "phone": lambda: hub_v4("A0"),
     "desk": lambda: __import__("hub_opt").DESK_NOAPP(), "names": "noapp",
     "about": "The App card (Labels, Time blocks, Calendars, Settings, Trash, About) leaves the Hub for the header's ⚙ (owner's question, 2026-10-08). One column then fits every remaining screen with Pinned and recent kept; nearest the ideal on all three axes."},
    {"id": "A0-tight", "name": "One column, tighter cards, no App card", "how": "direct", "phone": lambda: hub_v4("A0-tight"),
     "desk": lambda: __import__("hub_opt").DESK_NOAPP(), "names": "noapp",
     "about": "A0 with 2 px card padding and 4 px gaps."},
    {"id": "C0", "name": "Store map, no App card", "how": "oblique", "phone": lambda: hub_v4("C0"),
     "desk": lambda: __import__("hub_opt").DESK_NOAPP(), "names": "noapp",
     "about": "The store map with Review alone across the foot; App's screens behind ⚙."},
    {"id": "A-tight-", "name": "One column, tighter cards, no Pinned and recent", "how": "direct", "phone": lambda: hub_v4("A-tight-"), "desk": hub_desk_v4,
     "about": "Option A with 2 px card padding and 4 px gaps, and Pinned and recent left out: the 48 px rows stay, and every screen fits (owner's question, 2026-10-07)."},
    {"id": "A", "name": "One column of cards", "how": "direct", "phone": lambda: hub_v4("A"), "desk": hub_desk_v4,
     "about": "One card per module, top to bottom, under the capture line and Pinned and recent."},
    {"id": "B", "name": "Two columns of cards", "how": "direct", "phone": lambda: hub_v4("B"), "desk": hub_desk_v4,
     "about": "The same cards, two across, with Pinned and recent."},
    {"id": "X", "name": "Control: one long list", "how": "control", "phone": lambda: hub_v4("X"),
     "desk": lambda: hub_desk('<div class="hlist">%s</div>' % "".join('<div class="hr" data-tap="%s">%s</div>' % (f, f) for f in FEATURES)),
     "about": "Every screen as a row under a heading, no cards and no capture line. It must lose."},
]


def t14_extra(o, r):
    # an option without the App card is checked against the 21 screens it is meant to show (App's six are behind ⚙)
    names = __import__("hub_opt").NOAPP_NAMES if o.get("names") == "noapp" else [re_strip(f) for f in FEATURES]
    # hit-tested (T1.3's finding): a feature cut off by the sheet's edge keeps its box, so its position alone counted it seen
    seen = {t["name"] for t in r["taps_raw"] if t["name"] in names and t.get("seen")}
    # the same ease measures as hub_opt.py: thumb reach from the Hub's slot, and whether Pinned and recent is there
    vis = [t for t in r["taps_raw"] if t["name"] in names and t.get("seen")]
    reach = sum(math.log2(math.hypot(180 - t["x"], 712 - t["y"]) / min(t["w"], t["h"]) + 1) for t in vis) / max(1, len(vis))
    return {"hidden": len(names) - len(seen), "fields": len(names), "reach": round(reach, 2),
            "no_pinned": 0 if any(t["name"] == "Garden plan" for t in r["taps_raw"]) else 1}


COLS["hidden"] = ("Screens hidden (of those the option shows: 27, or 21 without App)", "%d")
COLS["reach"] = ("Thumb travel to a screen (Fitts ID from the Hub)", "%.2f")
COLS["no_pinned"] = ("No Pinned and recent", "%d")
STATES_T14 = [
    ("Open from the bar (the Hub slot active)", lambda: hub_v4("A0")),
    ("⚙ in the header: the App card's screens now live here", settings_v4),
    ("Long press on the Hub: straight to capture (T1.3 v4)", lambda: cap_v4("empty", "Today")),
]


# ---- T1.5 date and time picker -----------------------------------------------------------------------------
# Owner, 2026-10-08: typing sets the date and time (a typed date is never asked again); the picker is opened by the
# person, from ⋯ › Date beside the line or the full page's Date row, straight on the month; two steps in a sheet
# (the month, then the time); the time view holds the typed field with suggestions and the dial together, the
# keyboard only when the field is tapped. Scored by picker3_opt.py (actions, reach, coverage, visibility) and
# picker_desk.py (Windows); here the options are drawn and measured again with the page's own measures.
APPROVED_T15 = "Dial + typed"
T15_CSS = """
.keepw{position:relative;display:inline-block}
.keep{position:absolute;left:0;bottom:calc(100% + 6px);min-height:48px;display:flex;align-items:center;white-space:nowrap}
.keep>b{display:inline-flex;align-items:center;height:34px;padding:0 12px;border-radius:999px;background:var(--bg);font-weight:400;font-size:13px;box-shadow:0 2px 10px rgba(0,0,0,.18)}
"""


def _p3():
    import picker3_opt  # imported here: picker3_opt imports this module
    return picker3_opt


def t15_v(entry, steps="two", container="sheet", end="duration"):
    return {"steps": steps, "container": container, "entry": entry, "end": end}


def t15_desk(shape="dropdown2"):
    import picker_desk
    return cap_desk(picker_desk.body(shape))


def t15_keyboard(v):
    """Step 2 with the typed field tapped: the keyboard rises under the sheet (the owner's rule: everything still shows)."""
    html_ = _p3().phone(v, 2)
    i = html_.rfind("</div></div>")
    return html_[:i] + '<div class="kb" style="height:290px">keyboard</div>' + html_[i:]


def t15_keep():
    """A highlight tapped (owner, 2026-10-08): dates and times offer "Keep as text" like every highlight, since in a
    Journal line "tomorrow" may be only a word; no picker opens from it."""
    html_ = cap_v4("typed")
    return html_.replace('<span class="hl">tomorrow 9am</span>',
                         '<span class="keepw"><span class="hl">tomorrow 9am</span><span class="keep" data-tap="Keep as text"><b>Keep as text</b></span></span>', 1)


OPTIONS_T15 = [
    {"id": "Dial + typed", "name": "Selected: two steps in a sheet; the time view holds the typed field with suggestions and the dial", "how": "approved",
     "phone": lambda: _p3().phone(t15_v("dialtyped"), 2), "desk": t15_desk, "v": t15_v("dialtyped"),
     "about": "Step 1 is the month with its day load and Done; a day tapped opens step 2: the typed field with 09:00 and 21:00, the clock dial under it, "
              "the duration presets and Done. The keyboard rises only when the field is tapped (owner's proposal, 2026-10-08). Ties the dial alone, "
              "and keeps typing for exact minutes. Windows: the month beside the time, in a drop-down under the line."},
    {"id": "Dial", "name": "Two steps in a sheet, the clock dial alone", "how": "direct", "phone": lambda: _p3().phone(t15_v("dial"), 2), "desk": t15_desk,
     "v": t15_v("dial"), "about": "The front's only member once wheel steps were counted one by one; no typing for an exact minute."},
    {"id": "Typed", "name": "Two steps in a sheet, the typed field with suggestions alone", "how": "direct", "phone": lambda: _p3().phone(t15_v("typed"), 2),
     "desk": t15_desk, "v": t15_v("typed"), "about": "The best reach; every time but a suggestion brings up the keyboard."},
    {"id": "Blocks", "name": "Two steps in a sheet, the person's time blocks as presets", "how": "direct", "phone": lambda: _p3().phone(t15_v("blocks"), 2),
     "desk": t15_desk, "v": t15_v("blocks"), "about": "Morning, Afternoon, Evening from T1.6's blocks; any other time goes through Other time and typing."},
    {"id": "Wheels", "name": "Two steps in a sheet, hour and minute wheels", "how": "direct", "phone": lambda: _p3().phone(t15_v("wheel"), 2),
     "desk": t15_desk, "v": t15_v("wheel"), "about": "One action per wheel step (owner, 2026-10-08): 14:30 from 09:00 is 11 of them."},
    {"id": "X", "name": "Control: one view in the keyboard's place, wheels and an end time", "how": "control",
     "phone": lambda: _p3().phone(t15_v("wheel", "one", "keyboard", "endtime"), 1), "desk": lambda: t15_desk("dropdown"),
     "v": t15_v("wheel", "one", "keyboard", "endtime"),
     "about": "Month, wheels and an end time packed into the keyboard's 290 px, the usual Android swap. It cuts controls off and must lose."},
]


def t15_extra(o, r):
    s = _p3().score(o["v"])
    return {"actions": s["taps"] + s["keys"] + s["drags"], "reach15": s["reach"], "covered": s["covered"], "unseen": s["unseen"]}


COLS["actions"] = ("Actions over the 4 tasks (taps + keys + wheel steps)", "%d")
COLS["reach15"] = ("Thumb reach (mean Fitts ID)", "%.2f")
COLS["covered"] = ("Share of the screen covered", "%.2f")
COLS["unseen"] = ("Needed controls not drawn", "%d")
STATES_T15 = [
    ("Step 1: ⋯ › Date opens the month (day load under each day)", lambda: _p3().phone(t15_v("dialtyped"), 1)),
    ("Step 2: a day tapped; the field, the dial, the end, Done", lambda: _p3().phone(t15_v("dialtyped"), 2)),
    ("Step 2, the field tapped: the keyboard rises and everything still fits", lambda: t15_keyboard(t15_v("dialtyped"))),
    ("A highlighted date tapped: Keep as text, no picker", t15_keep),
]


PAGE_CSS = """
body{padding:20px 16px 48px}h1{font-size:21px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 6px}h3{font-size:15px;margin:18px 0 6px}
p{max-width:95ch}.dim{color:var(--dim)}
table{border-collapse:collapse;font-size:13px}td,th{padding:5px 10px;text-align:left;border-top:1px solid var(--zone2);vertical-align:top}th{color:var(--dim);font-weight:600}
.opt{background:var(--zone);border-radius:16px;padding:12px 16px;margin:12px 0}
.opt .phone,.states .phone{box-shadow:0 0 0 1px var(--zone2)}
.pair{display:flex;gap:16px;align-items:flex-start;overflow-x:auto;padding-bottom:6px}.dwrap{flex:none}
.tag{font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;background:var(--zone2);color:var(--dim)}
.states{display:flex;gap:16px;overflow-x:auto;padding-bottom:6px}.cap2{font-size:12px;color:var(--dim);margin:0 0 6px;max-width:360px}
details.notpicked{margin:10px 0}details.notpicked>summary{cursor:pointer;color:var(--dim);font-weight:600;padding:8px 0}
.refs{display:flex;gap:12px;flex-wrap:wrap}.refs img{width:180px;border-radius:12px}figure{margin:0}figcaption{font-size:12px;color:var(--dim)}
.sw{display:flex;gap:6px;margin:10px 0}.sw button{font:inherit;color:var(--ink);background:var(--zone);border:1px solid var(--zone2);border-radius:999px;padding:4px 14px;cursor:pointer}
"""


def _load_capture_opt():
    import importlib.util
    spec = importlib.util.spec_from_file_location("capture_opt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_opt.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    os.makedirs(OUT, exist_ok=True)
    refs = ss.reference_clutter(REFERENCE_SCREENS)
    s11, rows, fr, beaten = section_t11(refs)
    s12, rows12, fr12, beaten12 = section_t12()
    s13, rows13, fr13, beaten13 = build_section(
        "t1-3", "T1.3 Capture sheet",
        "One line in plain language for every module (decision 17). Selected: v4 (owner, 2026-10-07), after scoring chips against "
        "highlighting, routing (kind chip, kind row, prefixes, Todoist's +, TickTick's ⋯), the add (Enter, ✓), the kind's display, the "
        "shorthand legend and the placeholder: see capture-v2/v3/v4, legend-options and placeholder-opt beside this page. Taps exclude "
        "typing. Windows: a small window from anywhere.",
        OPTIONS_T13, STATES_T13, T13_CSS + __import__("legend_opt").CSS, ("clutter", "desk_clutter", "faint_n", "small", "steps_sum", "fields"), t13_extra, APPROVED_T13)
    co = _load_capture_opt()
    ref_rows = "".join("<tr><td>%s</td><td>%s</td><td>%dx%d</td><td>%.2f</td><td>%s</td><td>%s</td></tr>" % (
        e(r["app"]), r["place"], r["add"][2], r["add"][3], r["id_enter"], r["sheet"] or "full screen", "yes" if r["parses"] else "no") for r in co.reference_rows())
    s13r, rows13r, fr13r, beaten13r = build_section(
        "t1-3r", "T1.3 refined: where ✓ and ▤ go, and how big",
        "Owner (2026-10-07): ✓ and ▤ placement and sizes are free; balanced; right thumb, with a left-hand mirror setting. "
        "<code>tools/screens/capture_opt.py</code> searched 1,296 layouts; these are its balanced picks, each one held in both the "
        "assumed 360 dp phone and the owner's phone (384 dp, measured), with the thumb resting on Enter or on the keyboard's centre. "
        "Here they are drawn and measured again from the render. Thumb travel is Fitts' index of difficulty from the Enter key: lower is easier."
        "<h3>Reference apps, measured on the owner's phone</h3><p class=dim>Same measure, from the phone's own Enter key. Placeholder accounts; "
        "the sample was typed and cleared, nothing saved.</p><table><tr><th>App</th><th>Add sits</th><th>Add dp</th>"
        "<th>Thumb travel to Add</th><th>Sheet dp</th><th>Parses</th></tr>" + ref_rows + "</table>",
        OPTIONS_T13R, STATES_T13R, T13_CSS, ("fitts_add", "fitts_form", "sheet_h", "lines", "text_small", "small", "faint_n"), t13r_extra)
    s14, rows14, fr14, beaten14 = build_section(
        "t1-4", "T1.4 Hub sheet (cards)",
        "The Hub in the bar's centre opens this sheet: the capture line, Pinned and recent, then every screen of every module "
        "on cards (owner: cards for now, so every screen is visible). A long press on the Hub goes straight to capture. "
        "Unpaused and re-scored 2026-10-07 with T1.3's carry-overs: the v4 capture line on top; plain text on 48 px targets; "
        "feature names outweighing the card headers; empty space measured; every card on Windows. Hidden screens are now "
        "hit-tested (a feature cut off by the sheet's edge counts as hidden). Three-axis scores (harmony, ease, clutter): "
        "<code>tools/screens/hub_opt.py</code>, <code>docs/screens/t1/hub-opt.json</code>.",
        OPTIONS_T14, STATES_T14, T13_CSS + T14_CSS + __import__("legend_opt").CSS + __import__("hub_opt").TIGHT_CSS, ("clutter", "desk_clutter", "faint_n", "small", "reach", "no_pinned", "hidden"), t14_extra,
        must=lambda r: "%d screens below the fold (owner: every screen visible)" % r["hidden"] if r["hidden"] else None, approved=APPROVED_T14)
    s15, rows15, fr15, beaten15 = build_section(
        "t1-5", "T1.5 Date and time picker",
        "Typing sets the date and time; a typed date is never asked again, and tapping its highlight offers only Keep as text. "
        "The picker is opened by the person, from ⋯ › Date beside the line or the full page's Date row, straight on the month "
        "(owner, 2026-10-08). Two steps in a sheet: the month with its day load, then the time and the event's end. Week start "
        "and the 12/24 h clock follow the system. Four tasks: Fri 16; Fri 16 at 14:30; an event Fri 16 at 15:00 for 1 h; the 3rd "
        "of next month. Scores: <code>tools/screens/picker3_opt.py</code> (60 variants), <code>picker_desk.py</code> (Windows), "
        "<code>docs/screens/t1/picker3-opt.json</code>, <code>picker3-actions.json</code>. Repeat (cron and its calculator) is T1.6.",
        OPTIONS_T15, STATES_T15, T13_CSS + T15_CSS + __import__("legend_opt").CSS + __import__("picker_opt").CSS,
        ("clutter", "desk_clutter", "faint_n", "small", "actions", "reach15", "covered", "unseen"), t15_extra,
        must=lambda r: "%d needed controls not drawn (owner: everything a task needs visible)" % r["unseen"] if r["unseen"] else None, approved=APPROVED_T15)
    page = ['<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Factotum T1 shared parts</title><style>%s\n%s\n%s\n%s\n%s</style></head><body>' % (kit.theme_css(), kit.BASE_CSS, EXTRA, T12_CSS + T13_CSS + T14_CSS + T15_CSS + __import__("legend_opt").CSS + __import__("picker_opt").CSS, PAGE_CSS),
            '<h1>T1 · Shared parts</h1><p class="dim">Decision 17. Greys only; colour comes after every screen is settled. '
            'Type and icons are placeholders. One screen at a time: each waits for the owner\'s approval.</p>',
            '<div class="sw"><button onclick="document.documentElement.dataset.theme=\'light\'">Light</button>'
            '<button onclick="document.documentElement.dataset.theme=\'dark\'">Dark</button><button onclick="document.documentElement.dataset.theme=\'oled\'">OLED</button></div>',
            # the selected T1.3 first (owner, 2026-10-07: the choice must be what the page opens on); the superseded ✓/▤ size
            # exploration is folded at the foot of T1.3, closed
            s13, '<details class="notpicked"><summary>T1.3 exploration, superseded by v4: where ✓ and ▤ go, and how big</summary>%s</details>' % s13r,
            s14, s15, s12, s11, "</body></html>"]
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
    md += ["", "## T1.4 Hub sheet", ""] + ["- %s %s: clutter %.3f / %.3f, faint %d, small %d, below the fold %d of 27, %s" % (
        o["id"], o["name"], r["clutter"], r["desk_clutter"], r["faint_n"], r["small"], r["hidden"],
        "control" if o["how"] == "control" else ("front" if i in fr14 else "dominated")) for i, (o, r) in enumerate(zip(OPTIONS_T14, rows14))]
    with open(os.path.join(OUT, "scores.md"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(chr(10).join(md) + chr(10))
    print(chr(10).join(md[-5:]))
    md += ["", "## T1.3 refined: ✓ and ▤", "", "| Option | ID to ✓ | ID to ▤ | Sheet dp | Lines | Text px | Taps < 48 | Faint | Status |", "|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s %s | %.2f | %.2f | %d | %d | %d | %d | %d | %s |" % (o["id"], o["name"], r["fitts_add"], r["fitts_form"], r["sheet_h"], r["lines"], 18 - r["text_small"],
           r["small"], r["faint_n"], "control" if o["how"] == "control" else ("front" if i in fr13r else "dominated")) for i, (o, r) in enumerate(zip(OPTIONS_T13R, rows13r))]
    with open(os.path.join(OUT, "scores.md"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(chr(10).join(md) + chr(10))
    print(chr(10).join(md[-7:]))
    md += ["", "## T1.5 Date and time picker", ""] + ["- %s %s: clutter %.3f / %.3f, actions %d, reach %.2f, covered %.2f, not drawn %d, %s" % (
        o["id"], o["name"], r["clutter"], r["desk_clutter"], r["actions"], r["reach15"], r["covered"], r["unseen"],
        "control" if o["how"] == "control" else ("front" if i in fr15 else "dominated")) for i, (o, r) in enumerate(zip(OPTIONS_T15, rows15))]
    with open(os.path.join(OUT, "scores.md"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(chr(10).join(md) + chr(10))
    print(chr(10).join(md[-8:]))
    print("controls beaten:", beaten, beaten12, beaten13, beaten13r, beaten14, beaten15)
    if not (beaten and beaten12 and beaten13 and beaten13r and beaten14 and beaten15):
        sys.exit(2)


if __name__ == "__main__":
    main()
