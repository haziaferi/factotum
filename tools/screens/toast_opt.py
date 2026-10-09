"""T1.8 toasts and dialogs (decision 17, owner's answers 2026-10-09): every part scored, with a control that must lose.

    python tools/screens/toast_opt.py a|b|c|d|e|f      score a part into docs/screens/t1/toasts-<part>.json
    python tools/screens/toast_opt.py scores           the tables: docs/screens/t1/toasts-scores.html (fails if a control wins)
    python tools/screens/toast_opt.py page             the mockups of each part's front: docs/screens/t1/toasts-options.html

Parts:
  A  where the toast sits (phone: above the bar, anchored above the capture line when it is open, at the top; Windows too)
  B  how long Undo lasts, what several in a row do, and the way back once the toast has gone
  C  the two dialogs (empty Trash, discard an unsaved page): form, button order, labels, how to confirm
  D  the sync clash: how it reaches you, and the answer screen
  E  permission asks: when
  F  failures: toast, banner or mark

Measured from the drawings (headless Edge, 360x740 and 1100x660): reach (Fitts' ID from the thumb's rest, or from the
pointer's last place on Windows), what a toast hides, how far it sits from where you acted, clutter (edge density, light
and dark), text size. Walked: actions for each task, along paths written out beside each variant. One modelled value,
in B: the time to read a toast, at 238 words a minute (Brysbaert 2019, the mean adult silent reading rate for
non-fiction); the time to move to Undo is not counted.
"""
import itertools
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
import picker_opt as P  # noqa: E402
import repeat_opt as R  # noqa: E402

THUMB = P.THUMB            # (180, 700), the right thumb's rest on a 360x740 phone
THUMB_KB = (180, 615)      # with the keyboard up, the thumb rests on it (as T1.3)
READ_WPM = 238             # Brysbaert 2019
OUT = v2.OUT


def fitts(frm, tap):
    return math.log2(math.hypot(frm[0] - tap["x"], frm[1] - tap["y"]) / min(tap["w"], tap["h"]) + 1)


def probe(document, key, expr, w=360, h=740):
    """One value read off the laid-out page (the marker split so the regex never matches the script itself; the DOM dump
    writes the id back with quotes)."""
    js = '<script>document.body.insertAdjacentHTML("beforeend","<pre id=__pr"+"obe>"+JSON.stringify(%s)+"</pre>")</script>' % expr
    res = ss._edge(["--dump-dom"], True, key, document.replace("</body>", js + "</body>"), w + 300, h + 300)
    return json.loads(re.search(r'<pre id="__probe">(.*?)</pre>', res.stdout, re.S).group(1).replace("&quot;", '"'))


def clutter_of(make_doc, w=360, h=740):
    return round(sum(ss.edge_density(ss.render(make_doc(th), w, h)) for th in ("light", "dark")) / 2, 4)


class Taps(dict):
    """The page's targets by name (the first of each name), with every target kept in .all (rows share names)."""


def taps(doc, w=360, h=740):
    every = ss.measure(doc, w, h)["taps"]
    out = Taps()
    for x in every:
        out.setdefault(x["name"], x)
    out.all = every
    return out


def hidden_by(before, after):
    """Targets that can no longer be reached once the toast, card or banner is there: per name, how many fewer are seen
    (a row pushed down but still on screen is not hidden; one pushed off the screen or covered is)."""
    from collections import Counter
    b = Counter(x["name"] for x in before.all if x.get("seen"))
    a = Counter(x["name"] for x in after.all if x.get("seen"))
    return sorted(n for n in b for _ in range(max(0, b[n] - a[n])))


CSS = """
.toast{position:absolute;left:12px;right:12px;background:var(--ink);color:var(--bg);border-radius:12px;min-height:48px;display:flex;align-items:center;padding:0 6px 0 16px;font-size:14px;z-index:20}
.toast .t{flex:1}.toast .u{min-width:64px;height:48px;display:grid;place-items:center;font-weight:700}
.toast .x{min-width:48px;height:48px;display:grid;place-items:center}
.dlg{position:absolute;left:24px;right:24px;background:var(--bg);border-radius:20px;padding:20px 16px 8px;box-shadow:0 10px 32px rgba(0,0,0,.28);z-index:30}
.dlg h4{font-size:18px;font-weight:600;margin:0 0 8px}.dlg p{font-size:14px;color:var(--dim);margin:0 0 12px;line-height:1.4}
.dlg .btns{display:flex;justify-content:flex-end;gap:8px}
.bsheet{position:absolute;left:0;right:0;bottom:0;background:var(--bg);border-radius:20px 20px 0 0;padding:16px 16px 12px;box-shadow:0 -8px 28px rgba(0,0,0,.22);z-index:30}
.bsheet h4{font-size:18px;font-weight:600;margin:0 0 6px}.bsheet p{font-size:14px;color:var(--dim);margin:0 0 12px;line-height:1.4}
.bsheet .col{display:flex;flex-direction:column;gap:8px}
.btn{min-height:48px;min-width:64px;padding:0 16px;border-radius:24px;display:inline-flex;align-items:center;justify-content:center;font-size:15px;font-weight:600;gap:6px}
.btn.fill{background:var(--ink);color:var(--bg)}.btn.text{color:var(--ink)}.btn.wide{width:100%}
.btn.hold{background:var(--ink);color:var(--bg);box-shadow:inset 0 -4px 0 var(--dim)}
.typed{min-height:48px;border-radius:12px;box-shadow:inset 0 0 0 1px var(--dim);display:flex;align-items:center;padding:0 12px;color:var(--dim);margin:0 0 12px;font-size:15px}
.banner{display:flex;align-items:center;gap:8px;min-height:48px;padding:0 6px 0 14px;background:var(--zone2);border-radius:12px;font-size:14px;flex:none}
.banner .t{flex:1}
.badge{position:absolute;top:6px;right:calc(50% - 22px);width:10px;height:10px;border-radius:50%;background:var(--ink);box-shadow:0 0 0 2px var(--zone2)}
.clash{display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--ink);transform:rotate(45deg);margin-left:6px;vertical-align:middle}
.card{background:var(--zone);border-radius:14px;padding:10px 12px;display:flex;align-items:center;gap:8px;font-size:14px;flex:none}
.card .t{flex:1}
.vers{display:flex;gap:8px}.vers.stacked{flex-direction:column}
.ver{flex:1;background:var(--zone);border-radius:12px;padding:10px 12px;font-size:15px;min-width:0}
.ver .who{font-size:12px;color:var(--dim);margin-bottom:4px}
.page2{padding:8px 16px;display:flex;flex-direction:column;gap:12px}
.mi2{min-height:48px;display:flex;align-items:center;padding:0 14px;font-size:15px;border-bottom:1px solid var(--zone2)}
.mi2 .t{flex:1}.mi2 .d{color:var(--dim);font-size:13px}
.menu3{position:absolute;right:8px;top:52px;width:250px;background:var(--bg);border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:4px 0;z-index:25}
"""


def doc(phone_html, theme="light", extra=""):
    import legend_opt as L
    return kit.document(phone_html, theme, t.EXTRA + t.T12_CSS + t.T13_CSS + L.CSS + CSS + extra, True)


def with_overlay(phone_html, overlay):
    return phone_html[:-len("</div>")] + overlay + "</div>"


def toast(text, place_css, extra_btn=""):
    return '<div class="toast" style="%s"><span class="t">%s</span>%s<span class="u" data-tap="Undo">Undo</span></div>' % (place_css, text, extra_btn)


# ==== Part A: where the toast sits ======================================================================================
"""
  place  bar (just above the bar; with the keyboard up, Android lifts it to the keyboard's top edge, over the capture
         line), anchored (above the bar, and above the capture sheet when it is open), top (under the header)
  States: (1) Today, a row's circle tapped: "Done: Pay the fine"; (2) the capture sheet open, an item just added, the line
  emptied for the next: "Added to Tue 6 Oct"; (3) Windows, Today's column, a row done.
  Control: a notice in the middle of the screen over a shade, with Undo and OK.
"""
A_SPACE = {"place": ["bar", "anchored", "top"]}
DONE_TEXT = "Done: " + kit.ud("Pay the fine")
ADDED_TEXT = "Added to Tue 6 Oct"


def today_html(done=False):
    return t.t12_phone(t.row_d, done=done)


def capture_html():
    return t.cap_v4("empty", "Today")


def a_place_css(place, state, sheet_top=None):
    if place == "control":
        return "top:300px;bottom:auto;left:24px;right:24px;min-height:96px;flex-wrap:wrap;padding:12px 16px"
    if place == "top":
        return "top:60px;bottom:auto"
    if state == "today":
        return "bottom:84px;top:auto"
    kb_top = 740 - 250  # the mockup keyboard is 250 px (T1.3)
    if place == "bar":
        return "bottom:%dpx;top:auto" % (740 - kb_top + 8)
    return "bottom:%dpx;top:auto" % (740 - sheet_top + 8)


def a_docs(v, theme="light"):
    place = v["place"]
    extra = '<span class="u" data-tap="OK">OK</span>' if place == "control" else ""
    shade = '<div class="scrim"></div>' if place == "control" else ""
    today = with_overlay(today_html(True), shade + toast(DONE_TEXT, a_place_css(place, "today"), extra))
    cap0 = capture_html()
    top = ss.measure(doc(cap0), 360, 740)["boxes"]["sheet"][1]
    cap = with_overlay(cap0, shade + toast(ADDED_TEXT, a_place_css(place, "capture", top), extra))
    return {"today": doc(today, theme), "capture": doc(cap, theme), "today0": doc(today_html(True), theme), "capture0": doc(cap0, theme)}


DESK_CSS = ".desk .toast{left:auto;right:auto;width:420px}"


def a_desk(v, theme="light", bare=False):
    """Windows: Today's column beside a page; a row done in the column."""
    place = v["place"]
    head = '<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything <span class="kbd">Ctrl+K</span></span></div>' % t.TITLE
    page = '<div class="page"><div class="kbd">Pages › %s</div><h3>%s</h3></div>' % (kit.ud("Garden plan"), kit.ud("Garden plan"))
    body = kit.desk(kit.rail("Today"), head, '<div class="dcol">%s</div>%s' % (t.rows_today(t.row_d, done=True), page))
    if not bare:
        pos = {"bar": "left:530px;bottom:16px;top:auto", "anchored": "left:100px;bottom:16px;top:auto", "top": "left:640px;top:64px;bottom:auto",
               "control": "left:340px;top:250px;bottom:auto;min-height:96px;flex-wrap:wrap;padding:12px 16px"}[place]
        extra = '<span class="u" data-tap="OK">OK</span>' if place == "control" else ""
        body = with_overlay(body, ('<div class="scrim"></div>' if place == "control" else "") + toast(DONE_TEXT, pos, extra))
    return kit.document(body, theme, t.EXTRA + t.T12_CSS + CSS + DESK_CSS, True)


def place_blocks(v):
    """Whether the notice sits over a shade (it then takes a tap before anything else can be)."""
    return '<div class="scrim">' in a_docs(v)["today"]


def score_a(v):
    d = a_docs(v)
    out = {}
    tb, ta = taps(d["today0"]), taps(d["today"])
    cb, ca = taps(d["capture0"]), taps(d["capture"])
    done_pt = [x for x in ss.measure(d["today0"], 360, 740)["taps"] if x["name"] == "Done"]
    act_y = {"today": done_pt[0]["y"] if done_pt else 300}
    line = ss.measure(d["capture0"], 360, 740)["boxes"].get("line", [0, 600, 0, 0])
    act_y["capture"] = line[1] + line[3] / 2
    reach, look, seen = [], [], 0
    for st, tp, frm in (("today", ta, THUMB), ("capture", ca, THUMB_KB)):
        u = tp.get("Undo")
        if u and u.get("seen"):
            seen += 1
            reach.append(fitts(frm, u))
            look.append(abs(u["y"] - act_y[st]))
    m = ss.measure(d["capture"], 360, 740)
    # a notice over a shade must be dismissed (OK or Undo) before anything else can be tapped
    out["continue_actions"] = 1 if place_blocks(v) else 0
    out.update(undo_seen=seen, reach=round(sum(reach) / max(1, len(reach)), 3), look=round(sum(look) / max(1, len(look))),
               hidden=len(hidden_by(tb, ta)) + len(hidden_by(cb, ca)), hidden_names=hidden_by(tb, ta) + hidden_by(cb, ca),
               line_covered=bool(m.get("line_covered")), clutter=clutter_of(lambda th: a_docs(v, th)["today"]))
    # Windows: pointer from the circle it just clicked to Undo; what the toast hides
    db, da = taps(a_desk(v, bare=True), 1100, 660), taps(a_desk(v), 1100, 660)
    dn = [x for x in ss.measure(a_desk(v, bare=True), 1100, 660)["taps"] if x["name"] == "Done"]
    u = da.get("Undo")
    out.update(desk_reach=round(fitts((dn[0]["x"], dn[0]["y"]), u), 3) if u and dn else None,
               desk_look=round(math.hypot(u["x"] - dn[0]["x"], u["y"] - dn[0]["y"])) if u and dn else None,
               desk_hidden=len(hidden_by(db, da)), desk_clutter=clutter_of(lambda th: a_desk(v, th), 1100, 660))
    return out


# ==== Part B: how long Undo lasts, several in a row, and the way back ===================================================
"""
  timing   4, 7, 10 s, or until the next action. Android's own "Time to take action" setting (Accessibility) lengthens a
           timed toast in every variant (AccessibilityManager.getRecommendedTimeoutMillis), which meets WCAG 2.2.1.
  stack    replace (a new toast replaces the old), stack (up to three, newest at the bottom), merge (one toast:
           "3 moved to Trash", Undo all, and ▸ to pick one)
  way      menu (a ⋯ added to the header: Undo the last action, and History), recent (⚙ › Recently done, every action
           of the last 7 days, each with Undo), trash (only what exists: ⚙ › Trash for deletions, the Done today fold for
           done and skipped items, the When sheet to move an item back)
  Tasks after three deletions in a row (Calm, Body, Books): (s1) undo the last; (s2) undo the first only; (s3) undo all.
  Tasks after the toast has gone: (w1) bring back a deleted row; (w2) undo a move made earlier today; (w3) undo a Done;
  (w4) undo a skip.
  Measured: the stacked toasts' height; the header's controls. Modelled: reading time.
  Control: 2 s, a stack of every toast with no limit, and no way back but Trash.
"""
B_SPACE = {"timing": [4, 7, 10, "next"], "stack": ["replace", "stack", "merge"], "way": ["menu", "recent", "trash"]}
LONGEST = "Moved to Trash: Return library books"   # the longest toast text in the drawings


def read_s(text):
    return len(text.split()) / (READ_WPM / 60.0)


# way-back paths, each written out (taps from Today)
WAY = {
    "menu": {"w1": ["⋯", "Undo: deleted Books"], "w2": ["⋯", "History", "Moved: Call the bank"], "w3": ["⋯", "History", "Done: Walk"],
             "w4": ["⋯", "History", "Skipped: Water"]},
    "recent": {k: ["⚙", "Recently done", "the action", "Undo"] for k in ("w1", "w2", "w3", "w4")},
    "trash": {"w1": ["⚙", "Trash", "Books", "Restore"], "w2": ["Calendar", "Tue 6 Oct", "Call the bank", "⋯", "Date", "Today"],
              "w3": ["Done today · n", "Walk's circle"], "w4": ["Done today · n", "Water", "Unskip"]},
}


def b_toasts(v):
    """The toasts after three deletions, drawn above the bar."""
    items = ["Calm", "Body", "Books"]
    if v["stack"] == "replace":
        return [toast("Moved to Trash: " + kit.ud("Books"), "bottom:84px")]
    if v["stack"] == "merge":
        return ['<div class="toast" style="bottom:84px"><span class="t">3 moved to Trash</span><span class="x" data-tap="Pick">▸</span>'
                '<span class="u" data-tap="Undo all">Undo all</span></div>']
    n = len(items) if v.get("limit", 3) else len(items)
    return [('<div class="toast" style="bottom:%dpx"><span class="t">Moved to Trash: %s</span><span class="u" data-tap="Undo %s">Undo</span></div>') % (
        84 + 56 * (n - 1 - i), kit.ud(x), x) for i, x in enumerate(items)]


def b_doc(v, theme="light"):
    phone = today_html()
    if v["way"] == "menu":  # the header gains ⋯
        phone = re.sub(r'(<div class="hdr">.*?)(</div>)', lambda m: m.group(1) + kit.icon_button("⋯", "Menu") + m.group(2), phone, count=1, flags=re.S)
    return doc(with_overlay(phone, "".join(b_toasts(v))), theme)


def score_b(v):
    timing = v["timing"]
    margin = 99 if timing == "next" else round(timing - read_s(LONGEST), 2)
    linger = 99 if timing == "next" else timing
    m = ss.measure(b_doc(v), 360, 740)
    toasts = [x for x in m["taps"] if x["name"].startswith("Undo")]
    cover = (max(x["box"][1] + x["box"][3] for x in toasts) - min(x["box"][1] for x in toasts)) if toasts else 0
    way = {k: len(p) for k, p in WAY[v["way"]].items()}
    gone = way["w1"] if v["way"] != "menu" else 3  # an older deletion: ⋯ › History › the item
    s1 = 1
    s2 = {"replace": gone, "stack": 1, "merge": 2}[v["stack"]]           # merge: ▸ then the one
    s3 = {"replace": 1 + 2 * gone, "stack": 3, "merge": 1}[v["stack"]]
    head = len([x for x in m["taps"] if x.get("nav") and x["y"] < 60])
    reach = round(sum(fitts(THUMB, x) for x in toasts) / max(1, len(toasts)), 3)
    return {"margin_s": margin, "linger_s": linger, "stack_actions": s1 + s2 + s3, "way_actions": sum(way.values()), "cover_px": round(cover),
            "header_controls": head, "reach": reach, "clutter": clutter_of(lambda th: b_doc(v, th))}


# ==== Part C: the dialogs ===============================================================================================
"""
  form     dialog (centred), sheet (from the bottom), inplace (the button itself turns into "Tap again to empty" for 4 s)
  order    away (the destructive choice away from the thumb: left in a dialog, top in a sheet), near (under the thumb)
  labels   verbs ("Empty Trash", "Keep"), glyphs (🗑 and ✕, an accessible name each), both (glyph and verb)
  confirm  tap, hold (press for 1 s; a fill shows it), type (type EMPTY first)
  States: (1) Trash, Empty tapped (top right); (2) a page with unsaved changes, Back tapped (top left): Discard or Keep editing.
  Measured: actions to confirm and to back out, reach to the safe choice, the distance from the button just tapped to
  the destructive one (a double tap or a resting thumb lands there), clutter, words on the buttons.
  Control: "Are you sure?" with Yes and No, Yes filled under the thumb, a tap confirms.
"""
C_SPACE = {"form": ["dialog", "sheet", "inplace"], "order": ["away", "near"], "labels": ["verbs", "glyphs", "both"], "confirm": ["tap", "hold", "type"]}
SCEN = {
    "trash": {"title": "Empty Trash?", "body": "4 items are deleted for good. This cannot be undone.", "go": ("Empty Trash", "🗑"), "keep": ("Keep", "✕"),
              "trigger": ("Empty", "Empty", "right"), "word": "EMPTY"},
    "page": {"title": "Discard changes?", "body": "Your edits to this page since it was opened are lost.", "go": ("Discard", "🗑"), "keep": ("Keep editing", "✎"),
             "trigger": ("‹", "Back", "left"), "word": "DISCARD"},
}


def c_label(v, which, sc):
    word, glyph = SCEN[sc][which]
    if v.get("control"):
        return {"go": "Yes", "keep": "No"}[which]
    return {"verbs": word, "glyphs": glyph, "both": "%s %s" % (glyph, word)}[v["labels"]]


def c_base(sc):
    if sc == "trash":
        rows = "".join('<div class="mi2"><span class="t">%s</span><span class="d">deleted %s</span></div>' % (kit.ud(n), d) for n, d in
                       (("Return library books", "today"), ("Garden plan draft", "2 Oct"), ("Old shopping list", "28 Sep"), ("Call the bank", "25 Sep")))
        return kit.phone(kit.header("Trash", (("🗑", "Empty"),), ("‹", "Back")), '<div class="c2">%s</div>' % rows, "")
    return kit.phone(kit.header(kit.ud("Garden plan"), (("⋯", "More"),), ("‹", "Back")),
                     '<div class="page2"><p>%s</p><p>%s</p></div>' % (kit.ud("Raised beds go along the south fence."), kit.ud("Tomatoes in the second bed, beans in the third.")), "")


def c_overlay(v, sc):
    s = SCEN[sc]
    go_l, keep_l = c_label(v, "go", sc), c_label(v, "keep", sc)
    if v["form"] == "inplace":
        return None
    typed = '<div class="typed" data-tap="Type field">Type %s to confirm</div>' % s["word"] if v["confirm"] == "type" else ""
    hold = v["confirm"] == "hold"
    go = '<span class="btn %s" data-tap="Go">%s</span>' % ("hold" if hold else "fill", go_l + (" (hold)" if hold else ""))
    keep = '<span class="btn text" data-tap="Keep">%s</span>' % keep_l
    if v["form"] == "dialog":
        pair = (go + keep) if v["order"] == "away" else (keep + go)
        return '<div class="scrim"></div><div class="dlg" style="top:240px"><h4>%s</h4><p>%s</p>%s<div class="btns">%s</div></div>' % (
            "Are you sure?" if v.get("control") else s["title"], s["body"], typed, pair)
    go = go.replace('class="btn ', 'class="btn wide ')
    keep = keep.replace('class="btn ', 'class="btn wide ')
    pair = (go + keep) if v["order"] == "away" else (keep + go)
    return '<div class="scrim"></div><div class="bsheet"><h4>%s</h4><p>%s</p>%s<div class="col">%s</div></div>' % (s["title"], s["body"], typed, pair)


def c_doc(v, sc, theme="light", opened=True):
    base = c_base(sc)
    if not opened:
        return doc(base, theme)
    if v["form"] == "inplace":  # the trigger itself changes: its word, then a second tap
        trig_name = SCEN[sc]["trigger"][1]
        lab = {"verbs": "Tap again to %s" % SCEN[sc]["go"][0].lower().replace("empty trash", "empty"), "glyphs": "🗑?", "both": "🗑 Tap again"}[v["labels"]]
        if v["confirm"] == "hold":
            lab = {"verbs": "Hold to %s" % SCEN[sc]["go"][0].lower(), "glyphs": "🗑 ⏵", "both": "🗑 Hold"}[v["labels"]]
        if v["confirm"] == "type":
            lab = "Type %s" % SCEN[sc]["word"]
        pill = '<span class="btn fill" data-tap="Go" style="font-size:13px;padding:0 12px">%s</span>' % lab
        base = re.sub(r'<span[^>]*data-tap="%s"[^>]*>.*?</span>' % re.escape(trig_name), pill, base, count=1)
        if v["confirm"] == "type":
            base = with_overlay(base, '<div class="toast" style="top:60px;bottom:auto;background:var(--zone2);color:var(--ink)"><span class="t" data-tap="Type field">Type %s</span><span class="u" data-tap="Keep">%s</span></div>' % (SCEN[sc]["word"], c_label(v, "keep", sc)))
        return doc(base, theme)
    return doc(with_overlay(base, c_overlay(v, sc)), theme)


def score_c(v):
    conf, back, reach_keep, dist, small, words = 0, 0, [], [], [], 0
    for sc in ("trash", "page"):
        before = taps(c_doc(v, sc, opened=False))
        trig = before[SCEN[sc]["trigger"][1]]
        tp = taps(c_doc(v, sc))
        go, keep = tp.get("Go"), tp.get("Keep")
        n = 1 + 1                                            # the trigger, then the confirm
        if v["confirm"] == "type":
            n += 1 + len(SCEN[sc]["word"])                   # the field, then the word
        conf += n
        back += 1 + (1 if keep and keep.get("seen") else 1)  # the trigger, then Keep (in place: tap anywhere, or wait 4 s)
        if keep and keep.get("seen"):
            reach_keep.append(fitts(THUMB, keep))
        elif v["form"] == "inplace":
            reach_keep.append(0.0)   # backing out: tap anywhere else, or wait 4 s
        if go:
            dist.append(math.hypot(go["x"] - trig["x"], go["y"] - trig["y"]))
            dist.append(math.hypot(go["x"] - THUMB[0], go["y"] - THUMB[1]))
        small += ["%s %dx%d" % (x["name"], x["w"], x["h"]) for x in tp.values() if x.get("seen") and (x["w"] < 48 or x["h"] < 48) and x["name"] in ("Go", "Keep")]
        words += sum(1 for w_ in (c_label(v, "go", sc), c_label(v, "keep", sc)) if re.search(r"[A-Za-z]{2,}", w_))
    steps = {"tap": 0, "hold": 1, "type": 1}[v["confirm"]]
    specific = 0 if v.get("control") else 1
    m = ss.measure(c_doc(v, "trash"), 360, 740)
    return {"confirm_actions": conf, "back_actions": back, "reach_keep": round(sum(reach_keep) / max(1, len(reach_keep)), 3) if reach_keep else None,
            "go_distance": round(min(dist)) if dist else 0, "extra_step": steps, "named": words, "specific": specific,
            "min_text": m["min_text"], "small": sorted(set(small)), "clutter": clutter_of(lambda th: c_doc(v, "trash", th))}


# ==== Part D: the sync clash ============================================================================================
"""
  form     mark (a small diamond after the item's title; the item's page shows the clash), card (a card at the top of
           Today: "Call the bank changed on two devices", Review), toast (a toast with Review, and the mark left behind),
           dialog (asks at once, over whatever is open)
  answer   side (the two versions side by side), stacked (one above the other)
  words    words ("Keep this", "Keep both"), marks (✓ under each version, ⧉ for both)
  Task: the task "Call the bank" was renamed on the phone and on the laptop; keep the laptop's.
  Control: a dialog at once, stacked, marks, and no "later": it must be answered.
"""
D_SPACE = {"form": ["mark", "card", "toast", "dialog"], "answer": ["side", "stacked"], "words": ["words", "marks"]}
V_A, V_B = "Call the bank about the card", "Call the bank before Friday about the new card"


def d_answer(v):
    lab = (lambda w, m: w) if v["words"] == "words" else (lambda w, m: m)
    vers = ('<div class="vers %s"><div class="ver"><div class="who">This phone · 09:12</div>%s<div style="margin-top:8px">%s</div></div>'
            '<div class="ver"><div class="who">Laptop · 09:40</div>%s<div style="margin-top:8px">%s</div></div></div>') % (
        "stacked" if v["answer"] == "stacked" else "", kit.ud(V_A), '<span class="btn text" data-tap="Keep A">%s</span>' % lab("Keep this", "✓"),
        kit.ud(V_B), '<span class="btn fill" data-tap="Keep B">%s</span>' % lab("Keep this", "✓"))
    both = '<span class="btn text" data-tap="Keep both">%s</span>' % lab("Keep both", "⧉")
    later = "" if v.get("control") else '<span class="btn text" data-tap="Later">Later</span>'
    return '<h4>Changed on two devices</h4>%s<div class="btns" style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">%s%s</div>' % (vers, later, both)


def d_today(v, state="found"):
    phone = today_html()
    mark = '<span class="clash"></span>'
    if v["form"] in ("mark", "toast"):
        phone = phone.replace("Call the bank</span>", "Call the bank</span>" + mark, 1)
    if v["form"] == "card":
        phone = phone.replace('<div class="cap"', '<div class="card" data-tap="Review"><span class="t">%s changed on two devices</span><span class="btn text">Review</span></div><div class="cap"' % kit.ud("Call the bank"), 1)
    if v["form"] == "toast":
        phone = with_overlay(phone, '<div class="toast" style="bottom:84px"><span class="t">%s changed on two devices</span><span class="u" data-tap="Review">Review</span></div>' % kit.ud("Call the bank"))
    if v["form"] == "dialog":
        phone = with_overlay(phone, '<div class="scrim"></div><div class="dlg" style="top:120px">%s</div>' % d_answer(v))
    return phone


def d_page(v):
    return kit.phone(kit.header("Task", (("⋯", "More"),), ("‹", "Back")), '<div class="page2">%s</div>' % d_answer(v), "")


def score_d(v):
    today = taps(doc(d_today(v)))
    clean = taps(doc(today_html()))
    ans = taps(doc(d_page(v))) if v["form"] != "dialog" else today
    # actions to keep the laptop's version: mark: the row (1) + Keep (1); card / toast: Review (1) + Keep (1); dialog: Keep (1)
    act = {"mark": 2, "card": 2, "toast": 2, "dialog": 1}[v["form"]]
    keep = ans.get("Keep B")
    m = ss.measure(doc(d_page(v)) if v["form"] != "dialog" else doc(d_today(v)), 360, 740)
    key = "-".join(str(x) for x in v.values())
    hs = probe(doc(d_page(v)) if v["form"] != "dialog" else doc(d_today(v)), "t18-d-" + key,
               "[].map.call(document.querySelectorAll('.ver'),function(e){return e.scrollHeight})")
    sig = probe(doc(d_today(v)), "t18-dsig-" + key,
                "[].reduce.call(document.querySelectorAll('.dlg,.card,.toast,.clash'),function(s,e){var q=e.getBoundingClientRect();return s+Math.round(q.width*q.height)},0)")
    return {"actions": act, "interrupts": 1 if v["form"] == "dialog" else 0, "must_answer": 1 if v.get("control") else 0,
            "signal_px2": sig, "reach": round(fitts(THUMB, keep), 3) if keep else None,
            "versions_h": max(hs) if hs else 0, "named": int(v["words"] == "words"), "hidden": len(hidden_by(clean, today)),
            "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in ans.values() if x.get("seen") and x["name"].startswith("Keep") and (x["w"] < 48 or x["h"] < 48)}),
            "clutter": clutter_of(lambda th: doc(d_today(v), th))}


# ==== Part E: permission asks, when =====================================================================================
"""
  when   need (when a feature first needs it: notifications and exact alarms at the first reminder, battery at the
         first late alarm), first (all three at first run), settings (never asked; ⚙ › Settings › Reminders)
  Each ask is a short sheet that says why, then Android's own prompt. Actions, per permission: notifications: Allow (1)
  + Android's Allow (1); exact alarms: Allow (1) + the system page's switch (1) + Back (1); battery: Allow (1) +
  Android's Allow (1).
  Measured on the drawn ask: reach to Allow, clutter. Counted: actions before the app is usable, actions in all,
  reminders that would fail silently until the user finds the setting.
  Control: all three at first run, with no explanation, and asked again at every start until granted.
"""
E_SPACE = {"when": ["need", "first", "settings"]}
PERMS = [("Notifications", 2), ("Exact alarms", 3), ("Battery", 2)]


def e_doc(v, theme="light"):
    sheet = ('<div class="scrim"></div><div class="bsheet"><h4>Reminders need to notify you</h4><p>So that “%s” can ring at 09:00, '
             'Factotum needs to show notifications. Android asks next.</p><div class="col"><span class="btn fill wide" data-tap="Allow">Allow</span>'
             '<span class="btn text wide" data-tap="Not now">Not now</span></div></div>') % kit.ud("Call the bank")
    if v["when"] == "control":
        sheet = '<div class="scrim"></div><div class="dlg" style="top:250px"><h4>Allow Factotum to send you notifications?</h4><div class="btns"><span class="btn text" data-tap="Deny">Don\'t allow</span><span class="btn fill" data-tap="Allow">Allow</span></div></div>'
    if v["when"] == "settings":
        rows = "".join('<div class="mi2" data-tap="%s"><span class="t">%s</span><span class="d">Off</span></div>' % (n, n) for n, _ in PERMS)
        return doc(kit.phone(kit.header("Reminders", (), ("‹", "Back")), '<div class="c2">%s</div>' % rows, ""), theme)
    base = t.cap_v4("typed") if v["when"] == "need" else kit.phone(kit.header("Welcome", (), None), '<div class="page2"><p>Factotum keeps your day in one place.</p></div>', "")
    return doc(with_overlay(base, sheet), theme)


def score_e(v):
    total = sum(n for _, n in PERMS)
    before = {"need": 0, "first": total, "settings": 0, "control": total}[v["when"]]
    silent = {"need": 0, "first": 0, "settings": 1, "control": 0}[v["when"]]
    nav = {"settings": 3}.get(v["when"], 0)                     # ⚙ › Settings › Reminders, to reach the switches
    repeat = 1 if v["when"] == "control" else 0
    context = 1 if v["when"] == "need" else 0
    tp = taps(e_doc(v))
    a = tp.get("Allow") or tp.get("Notifications")
    return {"before_use": before, "actions": total + nav, "silent_fail": silent, "repeats": repeat, "context": context,
            "reach": round(fitts(THUMB, a), 3) if a else None, "clutter": clutter_of(lambda th: e_doc(v, th))}


# ==== Part F: failures ==================================================================================================
"""
  form   toast (6 s, with Fix), banner (under the header until fixed, with Fix), mark (a dot on the bar's Hub; the Hub
         sheet's top card says what and offers Fix)
  Case: the sync folder cannot be reached. Tasks: (f1) notice it on Today after it happened while the app was closed;
  (f2) open the fix.
  Control: a dialog at every failure, "Error 13", OK only.
"""
F_SPACE = {"form": ["toast", "banner", "mark"]}
FAIL = "Sync folder unreachable. Changes are kept on this phone."


def f_doc(v, theme="light"):
    phone = today_html()
    if v["form"] == "toast":
        phone = with_overlay(phone, '<div class="toast" style="bottom:84px"><span class="t">%s</span><span class="u" data-tap="Fix">Fix</span></div>' % FAIL)
    elif v["form"] == "banner":
        phone = phone.replace('<div class="cap"', '<div class="banner"><span class="t">%s</span><span class="btn text" data-tap="Fix">Fix</span></div><div class="cap"' % FAIL, 1)
    elif v["form"] == "mark":
        phone = phone.replace('data-tap="Hub"', 'data-tap="Hub" style="position:relative"', 1)
        phone = re.sub(r'(data-tap="Hub"[^>]*>)', r'\1<span class="badge"></span>', phone, count=1)
    else:
        phone = with_overlay(phone, '<div class="scrim"></div><div class="dlg" style="top:280px"><h4>Error 13</h4><p>Sync failed.</p><div class="btns"><span class="btn fill" data-tap="OK">OK</span></div></div>')
    return doc(phone, theme)


def score_f(v):
    clean = taps(doc(today_html()))
    tp = taps(f_doc(v))
    noticed = {"toast": 0, "banner": 1, "mark": 1, "control": 1}[v["form"]]   # f1: still visible after the app was closed
    fix = {"toast": 3, "banner": 1, "mark": 2, "control": 3}[v["form"]]       # toast gone: ⚙ › Settings › Sync; mark: Hub › Fix
    persists = {"toast": 0, "banner": 1, "mark": 1, "control": 0}[v["form"]]
    blocks = 1 if v["form"] == "control" else 0
    m = ss.measure(f_doc(v), 360, 740)
    return {"noticed": noticed, "fix_actions": fix, "persists": persists, "blocks": blocks, "hidden": len(hidden_by(clean, tp)),
            "rows_visible": m.get("rows_visible"), "clutter": clutter_of(lambda th: f_doc(v, th))}


# ==== running, controls, ranking ========================================================================================
SPACES = {"a": A_SPACE, "b": B_SPACE, "c": C_SPACE, "d": D_SPACE, "e": E_SPACE, "f": F_SPACE}
SCORERS = {"a": score_a, "b": score_b, "c": score_c, "d": score_d, "e": score_e, "f": score_f}
CONTROLS = {
    "a": ({"place": "control"}, "a notice in the middle of the screen over a shade, with Undo and OK"),
    "b": ({"timing": 2, "stack": "stack", "way": "trash", "limit": 0}, "2 s, every toast stacked with no limit, and no way back but what Trash and the folds hold"),
    "c": ({"form": "dialog", "order": "near", "labels": "generic", "confirm": "tap", "control": True}, "\"Are you sure?\" with Yes and No, Yes filled under the thumb, a tap confirms"),
    "d": ({"form": "dialog", "answer": "stacked", "words": "marks", "control": True}, "a dialog at once, stacked versions, marks only, and no Later: it must be answered"),
    "e": ({"when": "control"}, "all three at first run, no explanation, asked again at every start until granted"),
    "f": ({"form": "control"}, "a dialog at every failure, \"Error 13\", OK only"),
}
AXES = {
    "a": {"Ease": ("continue_actions", "reach", "desk_reach"), "Cover": ("hidden", "desk_hidden", "line_covered", "clutter", "desk_clutter"), "Notice": ("-undo_seen", "look", "desk_look")},
    "b": {"Safety": ("-margin_s",), "Ease": ("stack_actions", "way_actions", "reach"), "Cover": ("linger_s", "cover_px", "header_controls", "clutter")},
    "c": {"Ease": ("confirm_actions", "back_actions", "reach_keep"), "Safety": ("-go_distance", "-extra_step"), "Clutter": ("clutter",), "Legibility": ("-named", "-specific", "-min_text")},
    "d": {"Ease": ("actions", "reach"), "Calm": ("interrupts", "must_answer", "hidden", "clutter"), "Seen": ("-signal_px2",), "Legibility": ("versions_h", "-named")},
    "e": {"Ease": ("before_use", "actions", "reach"), "Safety": ("silent_fail",), "Calm": ("repeats", "-context")},  # clutter left out: the three are different screens
    "f": {"Seen": ("-noticed", "-persists"), "Ease": ("fix_actions",), "Calm": ("blocks", "hidden", "-rows_visible", "clutter")},
}


def run_part(p):
    rows = []
    for c in itertools.product(*SPACES[p].values()):
        vv = dict(zip(SPACES[p], c))
        rows.append(dict(v=vv, **SCORERS[p](vv)))
        print(p, rows[-1], flush=True)
    cv, why = CONTROLS[p]
    rows.append(dict(v=cv, why=why, control=True, **SCORERS[p](cv)))
    print(p, "control", rows[-1], flush=True)
    with open(os.path.join(OUT, "toasts-%s.json" % p), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


def ranked(p):
    with open(os.path.join(OUT, "toasts-%s.json" % p), encoding="utf-8") as fh:
        rows = json.load(fh)
    refs_path = os.path.join(OUT, "toast-references.json")
    if os.path.exists(refs_path):
        with open(refs_path, encoding="utf-8") as fh:
            refs = json.load(fh).get(p, [])
        keys = list(SPACES[p])
        for r in rows:
            parts = []
            for k in keys:
                have = [x.get(k) for x in refs if x.get(k) is not None]
                if have:
                    parts.append(sum(str(h) != str(r["v"].get(k)) for h in have) / len(have))
            r["ref_distance"] = round(sum(parts) / len(parts), 3) if parts else None
    ok = [r for r in rows if not r.get("small")]
    axes = dict(AXES[p])
    if any(r.get("ref_distance") is not None for r in ok):
        axes["Refs"] = ("ref_distance",)
    for r in ok:
        for k in [k.lstrip("-") for ks in axes.values() for k in ks]:
            x = r.get(k)
            r["_" + k] = (99 if x is None else float(x))
    for a, ks in axes.items():
        for r in ok:
            r[a] = 0
        for k in ks:
            sign, k2 = (-1, k[1:]) if k.startswith("-") else (1, k)
            for r, rk in zip(ok, v2.ranks(ok, "_" + k2, sign)):
                r[a] += rk
    ax = list(axes)
    for r in ok:
        r["front"] = not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)
        r["total"] = sum(r[a] for a in ax)
    return rows, ok, axes


TITLES = {"a": "A. Where the toast sits", "b": "B. How long Undo lasts, several in a row, the way back", "c": "C. The dialogs: empty Trash, discard changes",
          "d": "D. The sync clash", "e": "E. Permission asks: when", "f": "F. Failures"}


def scores_page():
    import html as H
    out, lost = [], {}
    for p in "abcdef":
        if not os.path.exists(os.path.join(OUT, "toasts-%s.json" % p)):
            continue
        rows, ok, axes = ranked(p)
        ctl = next(r for r in rows if r.get("control"))
        lost[p] = ctl in ok and not ctl.get("front")
        worse = sum(1 for r in ok if r is not ctl and r.get("total", 0) < ctl.get("total", 1e9))
        vk = [k for k in dict.fromkeys(k for r in rows for k in r["v"]) if k not in ("control", "limit")]
        cols = [k for k in rows[0] if k not in ("v", "why", "control", "hidden_names", "small", "front", "total") and not k.startswith("_") and k not in axes] + (["ref_distance"] if "Refs" in axes and "ref_distance" not in rows[0] else [])

        def cell(x):
            if x is None:
                return "—"
            if isinstance(x, bool):
                return "yes" if x else "no"
            if x == 99:
                return "∞"
            return "%g" % x if isinstance(x, (int, float)) else H.escape(str(x))
        order = sorted(rows, key=lambda r: (r not in ok, not r.get("front"), r.get("total", 1e9)))
        head = "".join("<th>%s</th>" % k for k in vk) + "".join("<th>%s</th>" % c for c in cols) + "".join("<th class=ax>%s</th>" % a for a in axes) + "<th class=ax>sum</th><th>front</th><th>gate</th>"
        body = []
        for r in order:
            gate = "pass" if r in ok else "fails: " + H.escape(", ".join(r.get("small", [])))
            cls = " ".join(c for c in ("fr" if r.get("front") else "", "fail" if r not in ok else "", "ctl" if r.get("control") else "") if c)
            body.append('<tr class="%s">%s%s%s<td class=ax>%s</td><td>%s</td><td>%s</td></tr>' % (
                cls, "".join("<td>%s</td>" % ("control" if r.get("control") and k == vk[0] else cell(r["v"].get(k, ""))) for k in vk),
                "".join("<td>%s</td>" % cell(r.get(c)) for c in cols),
                "".join("<td class=ax>%g</td>" % r[a] if r in ok else "<td class=ax>—</td>" for a in axes),
                "%g" % r["total"] if r in ok else "—", "★" if r.get("front") else "", ("control · " if r.get("control") else "") + gate))
        axis_line = "; ".join("<b>%s</b> = rank-sum of %s" % (a, ", ".join(k.lstrip("-") + (" (more is better)" if k.startswith("-") else "") for k in ks)) for a, ks in axes.items())
        verdict = ("<b>Control lost:</b> off the front; %d of %d passing variants have a lower sum." % (worse, len(ok) - 1)) if lost[p] else "<b>CONTROL DID NOT LOSE.</b>"
        doc_ = ""
        out.append('<h2 id="%s">%s</h2><p class=dim>%d variants and the control · %d pass the gate · %d on the front (★).</p>%s<p class=dim>Axes, lower is better: %s.</p>'
                   '<p>Control: %s. %s</p><div class=wrap><table><tr>%s</tr>%s</table></div>' % (
                       p, TITLES[p], len(rows) - 1, len(ok), sum(1 for r in ok if r.get("front")), doc_, axis_line, H.escape(ctl["why"]), verdict, head, "".join(body)))
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Toast Score Tables</title>
<style>:root{--bg:#fafafa;--fg:#1c1c1c;--dim:#777;--line:#ddd;--fr:#f0f0f0}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121212;--fg:#eee;--dim:#999;--line:#333;--fr:#1f1f1f}}
:root[data-theme=dark]{--bg:#121212;--fg:#eee;--dim:#999;--line:#333;--fr:#1f1f1f}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1500px}
.dim{color:var(--dim)}.wrap{overflow-x:auto}table{border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid var(--line);padding:4px 7px;text-align:left;white-space:nowrap}
.ax{border-left:1px solid var(--line)}tr.ctl td{font-style:italic;border-top:2px dashed var(--dim)}tr.fr{background:var(--fr)}tr.fail td{color:var(--dim)}</style></head><body>
<h1>T1.8 toasts and dialogs: score tables</h1>
<p>Every variant scored by <code>python tools/screens/toast_opt.py</code>, from drawings measured in headless Edge (360×740 phone, 1100×660 Windows). Axes are rank sums within a part, lower is better; ★ marks the Pareto front; each part's control (italics, dashed rule) was built to lose, and the run fails if it reaches the front. Grey rows failed the gate (a target under 48 dp).</p>
<p class=dim>Reference distance joins the axes once the reference apps are captured (toast-references.json).</p>
%s</body></html>""" % "".join(out)
    with open(os.path.join(OUT, "toasts-scores.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(page)
    print("controls lost:", lost)
    if not all(lost.values()):
        sys.exit(1)


# ==== the way-back screens (part B), drawn for the page ==================================================================
def b_way_doc(way, theme="light"):
    if way == "menu":
        phone = b_doc({"timing": 7, "stack": "replace", "way": "menu"}, theme)
        menu = ('<div class="menu3"><div class="mi2" data-tap="Undo last"><span class="t">Undo: deleted %s</span></div>'
                '<div class="mi2" data-tap="History"><span class="t">History</span><span class="d">›</span></div></div>') % kit.ud("Books")
        phone = re.sub(r'<div class="toast".*?</div>', "", phone, count=1, flags=re.S)
        return phone.replace("</body>", "") .replace('<div class="bar">', menu + '<div class="bar">', 1) + "</body>"
    if way == "recent":
        rows = "".join('<div class="mi2"><span class="t">%s %s</span><span class="btn text" data-tap="Undo %d">Undo</span></div>' % (a, kit.ud(n), i) for i, (a, n) in enumerate(
            (("Deleted", "Books"), ("Deleted", "Body"), ("Deleted", "Calm"), ("Moved to Tue:", "Call the bank"), ("Done:", "Walk"), ("Skipped:", "Water"))))
        return doc(kit.phone(kit.header("Recently done", (), ("‹", "Back")), '<div class="c2"><div class="kbd" style="padding:8px 14px">Today</div>%s</div>' % rows, ""), theme)
    return doc(c_base("trash"), theme)


def options_page():
    """docs/screens/t1/toasts-options.html: each part's front (up to four, lowest sum first) and its control, drawn, with
    their numbers; images inlined as greyscale WebP."""
    import base64
    import io
    import html as H
    from PIL import Image

    def img(d, w=360, h=740, show=240):
        im = Image.open(ss.render(d, w, h)).convert("L")
        im = im.resize((show, round(im.height * show / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=60)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    def fig(cap, d, w=360, h=740, show=240):
        return '<figure><img src="%s" width="%d"><figcaption>%s</figcaption></figure>' % (img(d, w, h, show), show, cap)

    def label(r):
        return H.escape(", ".join("%s" % x for k, x in r["v"].items() if k not in ("control", "limit")))

    def nums(r, axes):
        return " · ".join("%s %g" % (a, r[a]) for a in axes) + " · sum %g" % r["total"] if "total" in r else "failed the gate"

    secs = []
    for p in "abcdef":
        rows, ok, axes = ranked(p)
        fr = sorted([r for r in ok if r.get("front") and not r.get("control")], key=lambda r: r["total"])[:4]
        ctl = next(r for r in rows if r.get("control"))
        figs = []
        for r in fr + [ctl]:
            v = r["v"]
            cap = ("<b>Control</b>: " if r.get("control") else "") + label(r) + "<br><span class=dim>" + nums(r, axes) + "</span>"
            if p == "a":
                d = a_docs(v)
                figs.append(fig(cap + " · Today", d["today"]) + fig("…with the capture sheet open", d["capture"]) + fig("…on Windows", a_desk(v), 1100, 660, 420))
            elif p == "b":
                figs.append(fig(cap, b_doc(v)))
            elif p == "c":
                figs.append(fig(cap + " · empty Trash", c_doc(v, "trash")) + fig("…discard changes", c_doc(v, "page")))
            elif p == "d":
                figs.append(fig(cap + " · Today", doc(d_today(v))) + ("" if v["form"] == "dialog" else fig("…the answer", doc(d_page(v)))))
            elif p == "e":
                figs.append(fig(cap, e_doc(v)))
            else:
                figs.append(fig(cap, f_doc(v)))
        if p == "b":
            figs.append(fig("Way back: ⋯ in the header, Undo and History", b_way_doc("menu")) + fig("Way back: ⚙ › Recently done", b_way_doc("recent")) +
                        fig("Way back: ⚙ › Trash", b_way_doc("trash")))
        secs.append('<h2>%s</h2><p class=dim>The front, lowest sum first (up to four), and the control. Every row is in <a href="toasts-scores.html#%s">the tables</a>.</p><div class=flex>%s</div>' % (
            TITLES[p], p, "".join(figs)))
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Toast Options</title>'
            '<style>:root{--bg:#f4f4f2;--fg:#1d1d1b;--dim:#6b6b66}@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141414;--fg:#eee;--dim:#9a9a94}}'
            ':root[data-theme=dark]{--bg:#141414;--fg:#eee;--dim:#9a9a94}body{background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif;margin:0;padding:16px}'
            '.dim{color:var(--dim)}.flex{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}figure{margin:0}figcaption{font-size:12px;max-width:420px}</style></head><body>'
            '<h1 style="font-size:20px">T1.8 toasts and dialogs: the options</h1>%s</body></html>') % "".join(secs)
    with open(os.path.join(OUT, "toasts-options.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(page)
    print(len(page))


if __name__ == "__main__":
    for p in "abcdef":
        if p in sys.argv[1:]:
            run_part(p)
    if "scores" in sys.argv[1:]:
        scores_page()
    if "page" in sys.argv[1:]:
        options_page()
