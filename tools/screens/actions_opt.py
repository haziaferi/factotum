"""T1.8 G, rescored as where actions live (owner, 2026-10-09; vocabulary in docs/screens/t1/actions-inventory.md).
Parts are added to toast_opt's tables, so this module is the entry point for them:

    python tools/screens/actions_opt.py i|n|s|m|t     score a part into docs/screens/t1/toasts-<part>.json
    python tools/screens/actions_opt.py scores page   rebuild toasts-scores.html and toasts-options.html with every part

  I  an element's own actions: a long-press menu, the selection bar, a ⋯ inside the element, or the element's page
  N  a screen's own actions (Search and Settings stay in the header, T1.1; Empty Trash stays top right): beside them in the
     header, behind a header ⋯, in a bar above the nav bar, or behind a floating button
  S  how a selection starts: a long press selects, the long-press menu's Select, Select as a screen action, or a drag down
     the left column
  M  what a selection of mixed kinds offers: only what all share, or each action where it applies with a count
  T  Trash's Pages section: one group per page (its sub-pages, rows and database parts under it), or one list
Each part has a control built to lose. Counted paths are written beside each variant; geometry is measured as in toast_opt.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
import repeat_opt as R  # noqa: E402
import toast_opt as T  # noqa: E402

CSS = T.G_CSS + """
.selhdr{background:var(--zone2)}.selhdr .ttl{flex:1 0 auto;white-space:nowrap}
.row.sel{background:var(--zone2);border-radius:10px}
.rowdots{min-width:48px;height:48px;display:grid;place-items:center;color:var(--dim);flex:none}
.strip{display:flex;gap:0;flex:none}.strip .act2{min-width:40px;padding:0 4px;font-size:13px}
.trsec{font-size:12px;color:var(--dim);padding:10px 14px 4px;letter-spacing:.04em}
.grp{min-height:52px;display:flex;align-items:center;padding:0 14px;font-size:15px;font-weight:600;border-bottom:1px solid var(--zone2)}
.grp .t{flex:1}.grp .n{color:var(--dim);font-weight:400;font-size:13px;margin-right:6px}
.trow .path{display:block;font-size:12px;color:var(--dim)}
.cnt{font-size:11px;color:var(--dim);margin-left:2px}
"""
ROW = "Call the bank"


def doc(html, theme="light"):
    return T.doc(html, theme, CSS)


def today(overlay="", header=None, sel=(), dots=False, strip=False):
    """Today (T1.2's rows); optionally a selection header, selected rows, a ⋯ in every row, or a control strip."""
    html = t.t12_phone(t.row_d)
    if header is not None:
        html = re.sub(r'<div class="hdr">.*?</div>', header, html, count=1, flags=re.S)
    for name in sel:
        html = re.sub(r'(<div class="row)(" data-tap="Open item">(?:(?!<div class="row").)*?%s)' % re.escape(name), r'\1 sel\2', html, count=1, flags=re.S)
    if dots or strip:
        def add(m):
            extra = '<span class="rowdots" data-tap="Row more">⋯</span>' if dots else (
                '<span class="strip">%s</span>' % "".join('<span class="act2" data-tap="Strip %s">%s</span>' % (n, g) for n, g in (("When", "◷"), ("Label", "●"), ("Remind", "◴"), ("Delete", "🗑"))))
            return m.group(0)[:-len("</div>")] + extra + "</div>"
        html = re.sub(r'<div class="row[^"]*" data-tap="Open item">.*?</div>(?=<div class="row|<div class="fold|</div>)', add, html, flags=re.S)
    return html[:-len("</div>")] + overlay + "</div>"


def sel_header(n, acts, more=False):
    btns = "".join('<span class="act2" data-tap="A %s">%s</span>' % (a, l) for a, l in acts)
    return '<div class="hdr selhdr">%s<span class="ttl">%d selected</span>%s%s</div>' % (kit.icon_button("✕", "End"), n, btns, kit.icon_button("⋯", "More") if more else "")


# ==== Part I: an element's own actions ====================================================================================
"""
  place  menu (a long press opens a sheet of the element's actions), selbar (a long press selects it; the selection bar
         over the header shows its actions, ⋯ for the rest; the same bar serves many), dots (a ⋯ inside each element,
         top right of its bounds, opens its actions), page (tapping the element opens its page, where its actions are;
         Back returns)
  Tasks, on Today's task "Call the bank": When, Label, Reminder, Delete.
    menu: long press + the action = 2 each; selbar: long press + the bar's action (2: When, Delete), Label and Reminder behind its ⋯ (3);
    dots: ⋯ + the action = 2 each; page: open + the action + Back = 3 each.
  Measured: reach to the way in (the row for a long press or a tap, the ⋯), title room, clutter at rest, whether the way
  in can be seen at rest.
  Control: a strip of four glyph buttons on every row, always shown.
"""
I_SPACE = {"place": ["menu", "selbar", "dots", "page"]}
I_ACTS = [("When", "◷ When"), ("Label", "● Label"), ("Remind", "◴ Reminder"), ("Delete", "🗑 Delete")]


def i_docs(v):
    p = v["place"]
    rest = doc(today(dots=(p == "dots"), strip=(p == "control")))
    if p == "menu":
        menu = '<div class="scrim"></div><div class="menu" style="bottom:12px"><div class="mh">%s</div>%s</div>' % (
            kit.ud(ROW), "".join('<div class="mi" data-tap="A %s">%s</div>' % (a, l) for a, l in I_ACTS))
        open_ = doc(today(menu))
    elif p == "selbar":
        open_ = doc(today(header=sel_header(1, [I_ACTS[0], I_ACTS[3]], more=True), sel=(ROW,)))
    elif p == "dots":
        menu = '<div class="menu3" style="top:220px">%s</div>' % "".join('<div class="mi2" data-tap="A %s"><span class="t">%s</span></div>' % (a, l) for a, l in I_ACTS)
        open_ = doc(today(menu, dots=True))
    elif p == "page":
        open_ = doc(T.g_screen("item", "bottom", "glyphword")[0])
    else:
        open_ = rest
    return rest, open_


def score_i(v):
    p = v["place"]
    rest, open_ = i_docs(v)
    m = ss.measure(rest, 360, 740)
    row = [x for x in m["taps"] if x["name"] == "Open item" and x.get("seen")]
    target = [x for x in m["taps"] if x["name"] in ("Row more", "Strip When") and x.get("seen")] or row
    actions = {"menu": 8, "selbar": 10, "dots": 8, "page": 12, "control": 4}[p]   # selbar: When and Delete in the bar (2 each), Label and Reminder behind its ⋯ (3 each)
    room = T.probe(rest, "act-i-room-" + p, "(function(){var a=[].map.call(document.querySelectorAll('.row .t'),function(e){return e.clientWidth});return Math.round(a.reduce(function(s,x){return s+x},0)/a.length)})()")
    seen_way = 1 if p in ("dots", "page", "control") else 0   # a ⋯, a strip, or the row itself (tapping a row is what rows are for)
    return {"actions": actions, "reach": round(T.fitts(T.THUMB, target[len(target) // 2]), 3), "title_room": room, "seen_at_rest": seen_way,
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in ss.measure(open_, 360, 740)["taps"] + m["taps"]
                             if x.get("seen") and x["name"].startswith(("A ", "Row more", "Strip")) and (x["w"] < 48 or x["h"] < 48)}) if p != "control" else [],
            "clutter": T.clutter_of(lambda th: doc(today(dots=(p == "dots"), strip=(p == "control")), th))}


# ==== Part N: a screen's own actions ======================================================================================
"""
  place  header (beside Search and Settings), overflow (behind a ⋯ in the header), bottom (a bar above the nav bar),
         fab (a floating button at the lower right opening them)
  Screens and their own actions (inventory b): Today: Edit home, Select; Pages: Sort, Select; Reminders: Sort, Select.
  Search and Settings stay in the header (T1.1); Empty Trash stays top right (owner); adding stays on the capture line.
  Tasks: every action once. Measured: reach, header controls, room for content, Sort's stray between Pages and
  Reminders, clutter.
  Control: Today's in the header, Pages' in a bottom bar, Reminders' behind a floating button.
"""
N_SPACE = {"place": ["header", "overflow", "bottom", "fab"]}
N_SCREENS = {"Today": [("Edit home", "✎"), ("Select", "☐")], "Pages": [("Sort", "⇅"), ("Select", "☐")], "Reminders": [("Sort", "⇅"), ("Select", "☐")]}


def n_screen(name, place):
    acts = N_SCREENS[name]
    base = [("⌕", "Search"), ("⚙", "Settings")]
    body = {"Today": None, "Pages": [("Garden plan", "today"), ("Reading notes", "2 Oct"), ("Recipes", "28 Sep"), ("Trip to Lisbon", "25 Sep")],
            "Reminders": [("Call the bank", "15:00"), ("Water", "14:00"), ("Pills", "21:00"), ("Bins out", "Tue 07:00")]}[name]
    head_extra, bar_extra, overlay = "", "", ""
    if place == "header":
        head_extra = "".join(kit.icon_button(g, a) for a, g in acts)
    elif place == "overflow":
        head_extra = kit.icon_button("⋯", "More")
    elif place == "bottom":
        bar_extra = '<div class="abar" style="height:56px">%s</div>' % "".join('<span class="act2" data-tap="%s">%s %s</span>' % (a, g, a) for a, g in acts)
    else:
        overlay = '<span class="fab2" data-tap="FAB">⋯</span>'
    header = '<div class="hdr"><span class="ttl">%s</span>%s%s</div>' % (t.TITLE if name == "Today" else name, head_extra, "".join(kit.icon_button(*b) for b in base))
    if body is None:
        html = t.t12_phone(t.row_d)
        html = re.sub(r'<div class="hdr">.*?</div>', header, html, count=1, flags=re.S)
        html = html.replace('<div class="bar">', bar_extra + '<div class="bar">', 1)
    else:
        rows = "".join('<div class="trow" data-tap="Open %s"><span class="t">%s</span><span class="d">%s</span></div>' % (n, kit.ud(n), d) for n, d in body)
        html = kit.phone(header, '<div class="c2">%s</div>' % rows, bar_extra + kit.bar("Pages" if name == "Pages" else "Hub"))
    return html[:-len("</div>")] + overlay + "</div>"


def score_n(v):
    actions, ids, heads, rooms, cl, sorts = 0, [], [], [], [], {}
    for name, acts in N_SCREENS.items():
        place = {"Today": "header", "Pages": "bottom", "Reminders": "fab"}[name] if v["place"] == "control" else v["place"]
        d = doc(n_screen(name, place))
        m = ss.measure(d, 360, 740)
        tp = {x["name"]: x for x in m["taps"]}
        for a, _ in acts:
            way = a if a in tp else ("More" if "More" in tp else "FAB")
            actions += 1 if way == a else 2
            if tp.get(way):
                ids.append(T.fitts(T.THUMB, tp[way]))
            if a == "Sort" and tp.get(way):
                sorts[name] = (tp[way]["x"], tp[way]["y"])
        heads.append(sum(1 for x in m["taps"] if x.get("nav") and x["y"] < 56))
        rooms.append(T.probe(d, "act-n-room-%s-%s" % (name, place), "(function(){var b=document.querySelector('.body');return b?Math.round(b.getBoundingClientRect().height):0})()"))
        cl.append(sum(ss.edge_density(ss.render(doc(n_screen(name, place), th), 360, 740)) for th in ("light", "dark")) / 2)
    (ax, ay), (bx, by) = sorts["Pages"], sorts["Reminders"]
    return {"actions": actions, "reach": round(sum(ids) / len(ids), 3), "header_controls": round(sum(heads) / len(heads), 1),
            "room_px": round(sum(rooms) / len(rooms)), "sort_stray": round(math.hypot(ax - bx, ay - by)), "small": [], "clutter": round(sum(cl) / len(cl), 4)}


# ==== Part S: how a selection starts ======================================================================================
"""
  start  longpress (a long press selects; taps add), menu (a long press opens the menu, Select in it; taps add),
         screen (Select is the screen's action, behind its ⋯ or where part N puts it: counted as 1; the circles turn into
         checkboxes; taps add), drag (pressing a row's left column and dragging down selects the run; taps add others)
  Tasks on Today: (s1) delete three adjacent rows (Pay the fine, Call the bank, Return library books); (s2) delete two
  apart (Dentist, Return library books). The Delete in the bar is 1.
    longpress: s1 1+2+1, s2 1+1+1; menu: s1 2+2+1, s2 2+1+1; screen: s1 1+3+1, s2 1+2+1; drag: s1 1+1, s2 1+1+1.
  Also counted: a gesture that clashes with another (drag down a list also scrolls it: 1), and a way in seen at rest.
  Control: Select lives in ⚙ › Select, a page of its own: s1 2+3+1+1 (Back), s2 2+2+1+1.
"""
S_SPACE = {"start": ["longpress", "menu", "screen", "drag"]}


def s_doc(v, theme="light"):
    st = v["start"]
    acts = [("Delete", "🗑 Delete"), ("When", "◷ When")]
    sel = ("Pay the fine", "Call the bank", "Return library books")
    if st == "menu":
        menu = '<div class="scrim"></div><div class="menu" style="bottom:12px"><div class="mh">%s</div>%s</div>' % (
            kit.ud(ROW), "".join('<div class="mi" data-tap="%s">%s</div>' % (a, a) for a in ("Select", "When", "Label", "Reminder", "Delete")))
        return doc(today(menu), theme)
    if st == "screen":
        return doc(today(header='<div class="hdr"><span class="ttl">%s</span>%s%s%s</div>' % (t.TITLE, kit.icon_button("☐", "Select"), kit.icon_button("⌕", "Search"), kit.icon_button("⚙", "Settings"))), theme)
    if st == "control":
        return doc(kit.phone(kit.header("Select", (), ("‹", "Back")), '<div class="c2">%s</div>' % "".join(
            '<div class="trow" data-tap="Pick %d"><span class="ck3"></span><span class="t">%s</span></div>' % (i, kit.ud(n)) for i, n in enumerate(("Dentist",) + sel)), ""), theme)
    return doc(today(header=sel_header(3, acts[:1]), sel=sel), theme)


def score_s(v):
    st = v["start"]
    s1 = {"longpress": 4, "menu": 5, "screen": 5, "drag": 2, "control": 7}[st]
    s2 = {"longpress": 3, "menu": 4, "screen": 4, "drag": 3, "control": 6}[st]
    clash = 1 if st == "drag" else 0
    seen = 1 if st in ("screen", "control") else 0
    m = ss.measure(s_doc(v), 360, 740)
    way = [x for x in m["taps"] if x["name"] in ("Select",) and x.get("seen")] or [x for x in m["taps"] if x["name"] == "Open item" and x.get("seen")]
    return {"actions": s1 + s2, "gesture_clash": clash, "seen_at_rest": seen, "reach": round(T.fitts(T.THUMB, way[0]), 3) if way else None,
            "small": [], "clutter": T.clutter_of(lambda th: s_doc(v, th))}


# ==== Part M: a selection of mixed kinds ==================================================================================
"""
  offer  shared (only what every selected element has), each (every action any of them has, each saying how many it
         touches: "✓ Done 2", "● Label 4", "🗑 Delete 4")
  Selection on Today: two tasks, an event, a habit. Tasks: (m1) Done for the two tasks; (m2) Label on all four;
  (m3) Delete all four.
    shared: m1 = end the selection and tap the two circles (3), m2 1, m3 1; each: 1 + 1 + 1.
  Counted: an action that touches fewer than were selected without saying so. Measured: the bar's buttons, clutter.
  Control: every action any of them has, with no counts: Done touches two of four silently.
"""
M_SPACE = {"offer": ["shared", "each"]}


def m_doc(v, theme="light"):
    o = v["offer"]
    if o == "shared":
        acts = [("Label", "● Label"), ("Delete", "🗑 Delete")]
    elif o == "each":
        acts = [("Done", '✓<span class="cnt">2</span>'), ("Label", '●<span class="cnt">4</span>'), ("Delete", '🗑<span class="cnt">4</span>')]
    else:
        acts = [("Done", "✓ Done"), ("Label", "● Label"), ("Delete", "🗑 Delete")]
    return doc(today(header=sel_header(4, acts), sel=("Dentist", "Pay the fine", "Call the bank", "Walk")), theme)


def score_m(v):
    o = v["offer"]
    acts = {"shared": 3 + 1 + 1, "each": 3, "control": 3}[o]
    silent = 1 if o == "control" else 0
    m = ss.measure(m_doc(v), 360, 740)
    bar = [x for x in m["taps"] if x["name"].startswith("A ") and x.get("seen")]
    return {"actions": acts, "silent_subset": silent, "bar_buttons": len(bar), "reach": round(sum(T.fitts(T.THUMB, x) for x in bar) / max(1, len(bar)), 3),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in bar if x["w"] < 48 or x["h"] < 48}), "clutter": T.clutter_of(lambda th: m_doc(v, th))}


# ==== Part T: Trash's Pages section =======================================================================================
"""
  pages  grouped (under Pages, one group per page that went to Trash, with what went with it: its sub-pages, rows and
         database parts; a group is folded, with a count), flat (under Pages, one row per page or part, each with its
         path, newest first)
  Trash holds 14 pages and parts: Garden plan (5 with it), Reading notes (3), Recipes (4), and Trip to Lisbon (2).
  Tasks: (t1) restore "Raised beds", a sub-page of Garden plan; (t2) restore Garden plan and everything with it;
  (t3) delete forever everything that went with Recipes. A selection starts with a long press (part S's first option).
    grouped: t1 unfold + long press + Restore = 3; t2 long press on the group + Restore = 2; t3 long press on the group +
    Delete forever (held) = 2. flat: t1 long press + Restore = 2, after scanning to its row; t2 long press on Garden plan
    + Restore = 2 (a page's restore brings back what went with it); t3 long press + 3 taps + Delete forever = 5.
  Measured: rows read before the target (averaged over Raised beds, near the top, and Day plan, near the end) and rows shown.
  Control: no sections; every kind in one list with no path.
"""
T_SPACE = {"pages": ["grouped", "flat"]}
TRASHED = [("Garden plan", ["Raised beds", "Seed order", "Watering", "Compost", "Fence"]), ("Reading notes", ["Notes 1", "Notes 2", "Quotes"]),
           ("Recipes", ["Soups", "Bread", "Cakes", "Pickles"]), ("Trip to Lisbon", ["Hotels", "Day plan"])]


def t_doc(v, theme="light"):
    pg = v["pages"]
    secs = '<div class="trsec">TASKS AND EVENTS · 2</div><div class="trow"><span class="t">%s</span><span class="d">today</span></div><div class="trsec">PAGES · 18</div>' % kit.ud("Return library books")
    if pg == "grouped":
        rows = "".join('<div class="grp" data-tap="Group %s"><span class="t">%s</span><span class="n">%d with it</span>▸</div>' % (p, kit.ud(p), len(c)) for p, c in TRASHED)
    elif pg == "flat":
        flat = []
        for p, c in TRASHED:
            flat.append((p, "Pages"))
            flat += [(x, "Pages › " + p) for x in c]
        rows = "".join('<div class="trow" data-tap="Row %s"><span class="t">%s<span class="path">%s</span></span></div>' % (n, kit.ud(n), path) for n, path in flat)
    else:
        secs = ""
        mixed = ["Return library books"] + [x for p, c in TRASHED for x in [p] + c]
        rows = "".join('<div class="trow" data-tap="Row %s"><span class="t">%s</span></div>' % (n, kit.ud(n)) for n in mixed)
    header = '<div class="hdr">%s<span class="ttl">Trash</span><span class="act2 hold" data-tap="Empty">🗑 Empty</span></div>' % kit.icon_button("‹", "Back")
    return doc(kit.phone(header, '<div class="c2">%s%s</div>' % (secs, rows), kit.bar("Hub")), theme)


def score_t(v):
    pg = v["pages"]
    acts = {"grouped": 3 + 2 + 2, "flat": 2 + 2 + 5, "control": 2 + 2 + 5}[pg]
    m = ss.measure(t_doc(v), 360, 740)
    names = [x["name"] for x in m["taps"] if x["name"].startswith(("Row ", "Group "))]
    # rows read before reaching the target, averaged over one near the top (Raised beds) and one near the end (Day plan)
    if pg == "grouped":
        scan = ((names.index("Group Garden plan") + 1 + 1) + (names.index("Group Trip to Lisbon") + 1 + 2)) / 2   # the group, then its rows once unfolded
    else:
        scan = (names.index("Row Raised beds") + 1 + names.index("Row Day plan") + 1) / 2
    shown = sum(1 for x in m["taps"] if x["name"].startswith(("Row ", "Group ")) and x.get("seen"))
    return {"actions": acts, "scan_rows": scan, "rows_shown": shown, "small": [], "clutter": T.clutter_of(lambda th: t_doc(v, th))}


# ==== registered in toast_opt's tables ======================================================================================
T.SPACES.update({"i": I_SPACE, "n": N_SPACE, "s": S_SPACE, "m": M_SPACE, "t": T_SPACE})
T.SCORERS.update({"i": score_i, "n": score_n, "s": score_s, "m": score_m, "t": score_t})
T.CONTROLS.update({
    "i": ({"place": "control"}, "a strip of four glyph buttons on every row, always shown"),
    "n": ({"place": "control"}, "each screen its own way: Today's in the header, Pages' in a bottom bar, Reminders' behind a floating button"),
    "s": ({"start": "control"}, "Select lives in ⚙ › Select, a page of its own"),
    "m": ({"offer": "control"}, "every action any of them has, with no counts: Done touches two of four silently"),
    "t": ({"pages": "control"}, "no sections: every kind in one list, with no path"),
})
T.AXES.update({
    "i": {"Ease": ("actions", "reach"), "Calm": ("-title_room", "clutter"), "Seen": ("-seen_at_rest",)},
    "n": {"Ease": ("actions", "reach"), "Calm": ("header_controls", "-room_px", "clutter"), "Consistency": ("sort_stray",)},
    "s": {"Ease": ("actions", "reach"), "Safety": ("gesture_clash",), "Seen": ("-seen_at_rest",), "Calm": ("clutter",)},
    "m": {"Ease": ("actions", "reach"), "Safety": ("silent_subset",), "Calm": ("bar_buttons", "clutter")},
    "t": {"Ease": ("actions", "scan_rows"), "Calm": ("rows_shown", "clutter")},
})
T.TITLES.update({"g": "G (superseded 2026-10-09). One placement for all four screens", "i": "I. An element's own actions",
                 "n": "N. A screen's own actions", "s": "S. How a selection starts", "m": "M. A selection of mixed kinds", "t": "T. Trash's Pages section"})
T.DRAW = {"i": lambda v: list(i_docs(v)), "n": lambda v: [doc(n_screen(s, {"Today": "header", "Pages": "bottom", "Reminders": "fab"}[s] if v["place"] == "control" else v["place"])) for s in N_SCREENS],
          "s": lambda v: [s_doc(v)], "m": lambda v: [m_doc(v)], "t": lambda v: [t_doc(v)]}


if __name__ == "__main__":
    for p in "insmt":
        if p in sys.argv[1:]:
            T.run_part(p)
    # the drawings first: the tables exit non-zero when a control reaches a front, which stopped the page from being rebuilt
    if "page" in sys.argv[1:]:
        T.options_page()
    if "scores" in sys.argv[1:]:
        T.scores_page()
