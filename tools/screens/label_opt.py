"""T1.7 Labels (owner, 2026-10-08; decision 17). Four parts, each in its own views, so each is scored on its own:
  A  the chip on rows and cards: look × overflow × placement
  B  the picker (single for an activity, habit or tracker; several for a page)        [label_picker in this file]
  C  the suggestions while typing # on the capture line                                [part C]
  D  management, Settings › Labels behind ⚙                                            [part D]

Part A
  look       text (the name in the dim colour), dot (a dot, which takes the label's colour later, then the name),
             outline (an outlined pill), tint (a filled pill, which takes a light tint later), hash (#name)
  overflow   first (the first label and +n), fit (as many as fit, then +n), wrap (all of them, onto more lines)
  placement  inline (after the title, on its line: width taken from the title) or below (a line under the title:
             height added to the row)
  Rows: T1.2's approved row (decision 17: D, the mark or time left, the action right) in Today's Routines, one label
  each, and a Pages list whose rows carry one to four labels.
Measures, from the render and its DOM (a probe script reads the laid-out page):
  truncated   titles cut short (their text is wider than the room left)
  title_room  the mean width a title has, px
  extra_h     the mean height labels add to a row, px
  lines       label lines beyond the first, over all rows (wrapping)
  hidden      labels not drawn (behind a +n), over all rows
  rows_lost   rows pushed below the bar by the labels' height (the same 8 rows fit without labels)
  min_text    the smallest label text, px
  apart       cues that tell a label from the title without colour: smaller text, dim ink, a boundary (outline or
              fill), a leading mark (dot or #); counted from the design
  clutter     edge density of the render, light and dark averaged

    PYTHONUTF8=1 python tools/screens/label_opt.py a
"""
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

LOOKS = ["text", "dot", "outline", "tint", "hash"]
OVERFLOW = ["first", "fit", "wrap"]
PLACEMENT = ["inline", "below"]
APART = {"text": 2, "dot": 3, "outline": 3, "tint": 3, "hash": 3}  # smaller text and dim ink, plus a mark or a boundary
ROUTINES = [("habit", "Walk", "07:00", ["Health"]), ("habit", "Water", "14:00", ["Health"]), ("habit", "Stretch", "", ["Body"]),
            ("habit", "Read before bed", "22:00", ["Calm"])]
PAGES = [("Garden plan", ["Home", "Outdoors", "Seasonal", "Projects"]), ("Reading notes", ["Books", "Ideas"]),
         ("Trip to Lisbon in the spring with the whole family", ["Travel", "Family", "Planning"]), ("Recipes", ["Home"])]
CSS = """
.lrow{display:flex;align-items:center;gap:8px;min-height:48px;padding:4px 0;border-bottom:1px solid var(--zone2)}
.lrow .lead{width:44px;flex:none;color:var(--dim);font-size:12px;text-align:center}
.lrow .body{flex:1;min-width:0;display:flex;gap:8px}
.lrow.inline .body{flex-direction:row;align-items:center}.lrow.below .body{flex-direction:column;gap:2px}
.lrow .tt{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:48px}
.lrow.inline .tt{flex:1 1 auto}
.lrow .lbs{display:flex;gap:6px;align-items:center;min-width:0;flex:none;max-width:100%}
.lrow.inline .lbs{max-width:60%}
.lrow .lbs.wrap{flex-wrap:wrap;row-gap:4px}.lrow .lbs.nowrap{flex-wrap:nowrap;overflow:hidden}
.lrow .act{flex:none;min-width:48px;height:48px;display:grid;place-items:center;font-size:13px}
.lb{font-size:12.5px;color:var(--dim);white-space:nowrap;display:inline-flex;align-items:center;gap:5px;flex:none}
.lb.outline{box-shadow:inset 0 0 0 1px var(--dim);border-radius:999px;padding:0 8px;height:22px}
.lb.tint{background:var(--zone2);border-radius:999px;padding:0 8px;height:22px;color:var(--ink)}
.lb.dot::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--dim)}
.lb.more{color:var(--dim)}
"""
# "fit": labels that do not fit their row are hidden and counted in +n, measured on the laid-out page
FIT_JS = """<script>(function(){document.querySelectorAll('.lbs.fit').forEach(function(b){var ls=[].slice.call(b.querySelectorAll('.lb:not(.more)')),m=b.querySelector('.more');
for(var k=ls.length;k>=1;k--){ls.forEach(function(x,i){x.style.display=i<k?'':'none'});var hid=ls.length-k;m.style.display=hid?'':'none';m.textContent='+'+hid;if(b.scrollWidth<=b.clientWidth+1)return}})})()</script>"""


def labels_html(names, v):
    look, over = v["look"], v["overflow"]
    one = lambda n: '<span class="lb %s">%s</span>' % (look if look not in ("text", "hash") else "", ("#" + n) if look == "hash" else n)
    if over == "first":
        shown = names[:1]
        more = '<span class="lb more">+%d</span>' % (len(names) - 1) if len(names) > 1 else ""
        return '<span class="lbs nowrap" data-n="%d">%s%s</span>' % (len(names), one(shown[0]), more)
    if over == "fit":
        return '<span class="lbs nowrap fit" data-n="%d">%s<span class="lb more">+0</span></span>' % (len(names), "".join(one(n) for n in names))
    return '<span class="lbs wrap" data-n="%d">%s</span>' % (len(names), "".join(one(n) for n in names))


def row(lead, title, names, v, act=""):
    return '<div class="lrow %s"><span class="lead">%s</span><span class="body"><span class="tt">%s</span>%s</span>%s</div>' % (
        v["placement"], lead, kit.ud(title), labels_html(names, v), '<span class="act">%s</span>' % act if act else "")


def phone(v):
    routines = "".join(row(time or t.KIND_MARK["habit"], title, names, v, "Log") for _, title, time, names in ROUTINES)
    pages = "".join(row("▤", title, names, v) for title, names in PAGES)
    body = kit.zone("Routines", routines) + kit.zone("Pages", pages)
    return kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), body, kit.bar("Today"))


def doc(v, theme="light"):
    return kit.document(phone(v), theme, t.EXTRA + t.T12_CSS + CSS, False).replace("</body>", FIT_JS + "</body>")


PROBE = """<script>(function(){var rows=[].slice.call(document.querySelectorAll('.lrow')),bar=document.querySelector('.bar'),out={rows:[]};
var floor=bar?bar.getBoundingClientRect().top:740;
rows.forEach(function(r){var tt=r.querySelector('.tt'),lbs=r.querySelector('.lbs'),ls=[].slice.call(lbs.querySelectorAll('.lb:not(.more)'));
var shown=ls.filter(function(x){return x.offsetParent!==null&&x.getBoundingClientRect().right<=lbs.getBoundingClientRect().right+1});
var tops={};shown.forEach(function(x){tops[Math.round(x.getBoundingClientRect().top)]=1});
out.rows.push({h:Math.round(r.getBoundingClientRect().height),room:Math.round(tt.clientWidth),cut:tt.scrollWidth>tt.clientWidth+1,
n:+lbs.dataset.n,shown:shown.length,lines:Object.keys(tops).length,seen:r.getBoundingClientRect().bottom<=floor+1})});
document.body.insertAdjacentHTML('beforeend','<pre id="__la'+'bels">'+JSON.stringify(out)+'</pre>')})()</script>"""


def probe(v):
    d = doc(v).replace("</body>", PROBE + "</body>")
    key = "labels-" + "-".join(v.values())
    res = ss._edge(["--dump-dom"], True, key, d, 360 + 300, 740 + 300)
    return json.loads(re.search(r'<pre id="__labels">(.*?)</pre>', res.stdout, re.S).group(1).replace("&quot;", '"'))


def score_a(v):
    p = probe(v)["rows"]
    # a row is 56 px without labels (48 px of target and 4 px above and below); what is over that, labels added
    clutter = sum(ss.edge_density(ss.render(doc(v, th), 360, 740)) for th in ("light", "dark")) / 2
    return {"truncated": sum(r["cut"] for r in p), "title_room": round(sum(r["room"] for r in p) / len(p), 1),
            "extra_h": round(sum(max(0, r["h"] - 56) for r in p) / len(p), 1), "lines": sum(max(0, r["lines"] - 1) for r in p),
            "hidden": sum(r["n"] - r["shown"] for r in p), "rows_lost": sum(not r["seen"] for r in p), "min_text": 12.5, "apart": APART[v["look"]], "clutter": round(clutter, 4)}


def run_a():
    rows = []
    for c in itertools.product(LOOKS, OVERFLOW, PLACEMENT):
        v = dict(zip(("look", "overflow", "placement"), c))
        r = dict(v=v, **score_a(v))
        rows.append(r)
        print(r, flush=True)
    with open(os.path.join(v2.OUT, "labels-a.json"), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1)


# ==== shared: measured views and walked tasks (as repeat4_opt) ==========================================================
import math  # noqa: E402

import picker_opt as P  # noqa: E402
import repeat_opt as R  # noqa: E402

LABELS = ["Health", "Body", "Calm", "Home", "Outdoors", "Seasonal", "Books", "Ideas", "Travel", "Family", "Planning", "Projects"]
KB = '<div class="kb" style="height:290px">keyboard</div>'


def views_of(docs):
    """{state: {False: taps, True: taps}} from {state: (doc without keyboard, doc with it)}."""
    out = {}
    for s, (d0, d1) in docs.items():
        out[s] = {kb: {x["name"]: x for x in ss.measure(d, 360, 740)["taps"]} for kb, d in ((False, d0), (True, d1))}
    return out


def walk(views, task, fields, closers=("Done",)):
    """Actions for a task [(state, 'tap', name) | (state, 'type', n)], the keyboard closed first when it hides a target."""
    kb, n, miss, ids = False, 0, set(), []
    for state, kind, x in task:
        if kind == "type":
            n += x
            continue
        seen = lambda k: views[state][k].get(x, {}).get("seen")
        if kb and not seen(True):
            if seen(False):
                n += 1
                kb = False
            else:
                miss.add("%s: %s" % (state, x))
        elif not kb and not seen(False):
            miss.add("%s: %s" % (state, x))
        tp = views[state][kb].get(x)
        if tp and tp.get("seen"):
            ids.append(math.log2(math.hypot(P.THUMB[0] - tp["x"], P.THUMB[1] - tp["y"]) / min(tp["w"], tp["h"]) + 1))
        n += 1
        if x in fields:
            kb = True
        if x in closers or x.startswith("Lb ") and x != "Lb keep":
            kb = False
    return n, miss, ids


def tap(state, *names):
    return [(state, "tap", x) for x in names]


def typ(state, n):
    return [(state, "type", n)]


def clutter_of(make_doc):
    return round(sum(ss.edge_density(ss.render(make_doc(th), 360, 740)) for th in ("light", "dark")) / 2, 4)


def small_of(views):
    return sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for st in views.values() for x in st[False].values()
                   if x.get("seen") and (x["w"] < 48 or x["h"] < 48)})


# ==== Part B: the picker ==============================================================================================
"""
  container  sheet (as the When sheet: over the screen, grows upward), page (a full page), keyboard (in the keyboard's
             place, the capture line above it), popover (above the line, the keyboard kept)
  shape      list (one row a label, a check on the chosen) or grid (chips that wrap)
  The search field on top filters, and its last row (or chip) creates: "Create "Sample label"". One label (an
  activity, habit or tracker) closes on the pick; several (a page) end with Done. Tasks, each opened from ⋯ › Label
  (not counted): (a) put Health on Walk; (b) create "Sample label" and put it on Walk; (c) take Walk's label off;
  (d) put Home, Outdoors and Seasonal on a page.
"""
B_SPACE = {"container": ["sheet", "page", "keyboard", "popover"], "shape": ["list", "grid"]}
B_CSS = R.CSS + """
.pk .lrow2{min-height:48px;display:flex;align-items:center;gap:10px;font-size:15px;border-bottom:1px solid var(--zone2)}
.pk .lrow2 .ck2{margin-left:auto;width:24px;text-align:center}
.pk .lrow2 .dt{width:8px;height:8px;border-radius:50%;background:var(--dim)}
.pk .lrow2.mk{color:var(--dim)}
"""


def picker_body(v, state, multi):
    chosen = {"Home"} if multi else {"Health"}
    field = R.row(R.field("Search field", "Sample label" if state == "typed" else "Search or create", "field"))
    names = [] if state == "typed" else LABELS
    create = state == "typed"
    if v["shape"] == "list":
        rows = "" if multi or create else '<div class="lrow2 mk" data-tap="Lb none">No label</div>'
        rows += "".join('<div class="lrow2" data-tap="Lb %s"><span class="dt"></span>%s<span class="ck2">%s</span></div>' % (n, n, "✓" if n in chosen else "") for n in names)
        if create:
            rows += '<div class="lrow2" data-tap="Create">Create “Sample label”</div>'
        items = rows
    else:
        chips = ("" if multi or create else R.ch("Lb none", "No label")) + "".join(R.ch("Lb %s" % n, n, n in chosen) for n in names)
        if create:
            chips += R.ch("Create", "Create “Sample label”")
        items = '<div class="row">%s</div>' % chips
    head = ('<div class="row" style="justify-content:space-between"><span></span><span class="ttl">Label</span>%s</div>' % (R.b("Done", "Done") if multi else "<span></span>")) if v["container"] != "page" else ""
    return head + field + items


def picker_phone(v, state, kb, multi):
    c = v["container"]
    cls = {"keyboard": "pk", "sheet": "pk sheet", "popover": "pk pop", "page": "pk page"}[c]
    style = {"keyboard": ' style="height:290px;overflow:hidden"', "sheet": ' style="max-height:704px"', "popover": ' style="max-height:440px"', "page": ""}[c]
    if c == "page" and kb:
        style = ' style="bottom:290px"'
    pk = '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, picker_body(v, state, multi))
    if c == "page":
        return kit.phone(kit.header("Label", (("✓", "Done"),) if multi else (), ("‹", "Back")),
                         '<div class="c2" style="position:relative;height:100%%">%s</div>' % pk, KB.replace('class="kb"', 'class="kb" style="position:absolute;left:0;right:0;bottom:0;height:290px"') if kb else "")
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    if c == "keyboard":
        overlay = '<div class="sheet c2" style="position:relative">%s</div>%s' % (P.line_html(), KB if kb else pk)
    elif c == "popover":
        overlay = '<div class="sheet c2" style="position:relative">%s%s</div>%s' % (pk, P.line_html(), KB)
    else:
        overlay = '<div class="c2">%s</div>%s' % (pk, KB if kb else "")
    overlay = '<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s</div>' % overlay
    return today[:-len("</div>")] + overlay + "</div>"


def picker_doc(v, state, kb=False, multi=False, theme="light"):
    return kit.document(picker_phone(v, state, kb, multi), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + B_CSS, True)


def score_b(v):
    docs = {s: (picker_doc(v, s, False, s == "multi"), picker_doc(v, s, True, s == "multi")) for s in ("base", "typed", "multi")}
    docs = {("base" if s == "base" else s): (picker_doc(v, "typed" if s == "typed" else "base", False, s == "multi"),
                                              picker_doc(v, "typed" if s == "typed" else "base", True, s == "multi")) for s in ("base", "typed", "multi")}
    views = views_of(docs)
    tasks = {
        "a": tap("base", "Lb Health"),
        "b": tap("base", "Search field") + typ("typed", len("Sample label")) + tap("typed", "Create"),
        "c": tap("base", "Lb none"),
        "d": tap("multi", "Lb Home", "Lb Outdoors", "Lb Seasonal", "Done"),
    }
    if v["shape"] == "grid":
        tasks["c"] = tap("base", "Lb none")
    actions, ids, miss, per = 0, [], set(), {}
    for k, task in tasks.items():
        n, m, i = walk(views, task, {"Search field"})
        actions += n
        ids += i
        miss |= m
        per[k] = n
    base = ss.measure(docs["base"][0], 360, 740)
    pk = base["boxes"].get("picker")
    covered = 1.0 if v["container"] == "page" else round(min(740, pk[3] if pk else 0) / 740, 3)
    in_pk = [x for x in base["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen")]
    return {"actions": actions, "per_task": per, "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": sorted(miss), "small": small_of(views),
            "covered": covered, "controls": len(in_pk), "labels_seen": sum(1 for x in in_pk if x["name"].startswith("Lb ") and x["name"] != "Lb none"),
            "clutter": clutter_of(lambda th: picker_doc(v, "base", False, False, th))}


# ==== Part C: suggestions while typing # =============================================================================
"""
  place  chips (matching labels as chips in the hint line's place, above the keyboard), list (rows over the line, the
         create row last), inline (the best match completes the word in grey; tapping it accepts)
  Tasks on the capture line (T1.3 v4), the keyboard up: (a) "#he" then Health; (b) "#h" then Home, the second match;
  (c) "#garden", a new label, kept by typing on (the line creates it when the item is added). Counted: the taps and
  keys after the #.
"""
C_SPACE = {"place": ["chips", "list", "inline"]}
C_CSS = """
.sug{display:flex;gap:6px;flex-wrap:nowrap;overflow:hidden;padding:0 2px}
.slist{background:var(--zone);border-radius:14px 14px 0 0;box-shadow:0 -6px 18px rgba(0,0,0,.12)}
.slist .sr{min-height:48px;display:flex;align-items:center;padding:0 14px;font-size:15px;border-bottom:1px solid var(--zone2)}
.ghost{color:var(--dim)}
.c2 .acc{display:inline-flex;align-items:center;min-height:48px;padding:0 2px}
"""


def c_sheet(v, typed):
    matches = [n for n in LABELS if n.lower().startswith(typed[1:].lower())]
    more = v2.control("More", "⋯", 32, "ghost")
    if v["place"] == "inline" and matches:
        word = '<span class="hl">%s</span><span class="acc" data-tap="Accept"><span class="ghost">%s</span></span>' % (typed, matches[0][len(typed) - 1:])
    else:
        word = '<span class="hl">%s</span>' % typed
    line = '<div class="line"><span class="in">%s</span>%s</div>' % (kit.ud("water plants " + word) + '<span class="caret"></span>', more)
    if v["place"] == "chips":
        hint = '<div class="sug">%s%s</div>' % ("".join(R.ch("Sug %s" % n, n) for n in matches), R.ch("Create", "+ " + typed) if typed not in ("#he", "#h") else "")
        return '<div class="sheet" style="position:relative">%s%s</div>' % (line, hint)
    if v["place"] == "list":
        rows = "".join('<div class="sr" data-tap="Sug %s">%s</div>' % (n, n) for n in matches[:4]) + '<div class="sr" data-tap="Create">Create %s</div>' % typed
        return '<div class="slist">%s</div><div class="sheet" style="position:relative">%s<div class="hint">Task · # label</div></div>' % (rows, line)
    return '<div class="sheet" style="position:relative">%s<div class="hint">Task · # label</div></div>' % line


def c_doc(v, typed, theme="light"):
    today = kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="cap">+ <span>Add…</span></div>' + t.rows_today(t.row_d), kit.bar("Today"))
    today = today.replace("data-tap=", "data-behind=")
    overlay = ('<div class="scrim" style="background:rgba(0,0,0,.16)"></div><div class="c2" style="position:absolute;left:0;right:0;bottom:0">%s%s</div>') % (c_sheet(v, typed), KB)
    import legend_opt as L
    return kit.document(today[:-len("</div>")] + overlay + "</div>", theme, t.EXTRA + t.T12_CSS + t.T13_CSS + L.CSS + C_CSS, True)


def score_c(v):
    he = {x["name"]: x for x in ss.measure(c_doc(v, "#he"), 360, 740)["taps"]}
    h = {x["name"]: x for x in ss.measure(c_doc(v, "#h"), 360, 740)["taps"]}
    seen = lambda m, n: bool(m.get(n, {}).get("seen"))
    if v["place"] == "inline":
        a = 3 + (1 if seen(he, "Accept") else 3)          # accept, or type "alth"
        b = 2 + 1 + (1 if seen(he, "Accept") else 2)       # #h, then "o" narrows to Home, accept (or type "me")
    else:
        a = 3 + (1 if seen(he, "Sug Health") else 3)
        b = 2 + (1 if seen(h, "Sug Home") else 3)
    c = len("#garden")
    d = ss.measure(c_doc(v, "#h"), 360, 740)
    shown = sum(1 for x in d["taps"] if x["name"].startswith("Sug ") and x.get("seen"))
    covered_line = d.get("line_covered", False)
    return {"actions": a + b + c, "per_task": {"a": a, "b": b, "c": c}, "shown": shown, "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in d["taps"] if x.get("seen") and (x["w"] < 48 or x["h"] < 48)}),
            "clutter": clutter_of(lambda th: c_doc(v, "#h", th)), "line_covered": covered_line}


# ==== Part D: management, Settings › Labels ==========================================================================
"""
  form  direct (each row: a drag handle, a colour dot, the name (tap to rename in place), a scope word that cycles,
        a delete ×, and the count of what carries it), menu (each row: handle, name, count, and ⋯ opening Rename,
        Colour, Scope, What carries it, Delete), detail (each row: handle, name, count, ›; the label's page holds the
        rest)
  Deleting shows an undo toast (no confirmation), as everywhere in Factotum (T1.8). Tasks: (a) rename Health to
  Wellbeing; (b) scope Books to activities; (c) delete Calm; (d) move Projects to the top; (e) see what carries
  Health; (f) change Home's colour (to the first suggested).
"""
D_SPACE = {"form": ["direct", "menu", "detail"]}
D_CSS = """
.mrow{min-height:48px;display:flex;align-items:center;gap:4px;border-bottom:1px solid var(--zone2);font-size:15px}
.mrow .nm{flex:1;min-height:48px;display:flex;align-items:center}
.mrow .cnt{font-size:12.5px;color:var(--dim);min-width:48px;min-height:48px;display:inline-flex;align-items:center;justify-content:center}
.mrow .ic{min-width:48px;min-height:48px;display:inline-flex;align-items:center;justify-content:center;color:var(--dim)}
.mrow .dt{width:12px;height:12px;border-radius:50%;background:var(--dim)}
.menu2{position:absolute;right:12px;top:120px;width:220px;background:var(--bg);border-radius:12px;box-shadow:0 8px 28px rgba(0,0,0,.22);padding:4px 0}
.menu2 div{min-height:48px;display:flex;align-items:center;padding:0 16px;font-size:15px}
"""
COUNTS = {"Health": 12, "Body": 3, "Calm": 2, "Home": 7, "Outdoors": 4, "Seasonal": 1, "Books": 5, "Ideas": 2, "Travel": 3, "Family": 6, "Planning": 2, "Projects": 4}


def d_list(v, state):
    rows = ""
    for n in LABELS:
        handle = '<span class="ic" data-tap="Handle %s">≡</span>' % n
        if v["form"] == "direct":
            rows += ('<div class="mrow">%s<span class="ic" data-tap="Colour %s"><span class="dt"></span></span><span class="nm" data-tap="Name %s">%s</span>'
                     '<span class="cnt" data-tap="Count %s">%d</span><span class="cnt" data-tap="Scope %s">All</span><span class="ic" data-tap="Delete %s">×</span></div>') % (handle, n, n, n, n, COUNTS[n], n, n)
        elif v["form"] == "menu":
            rows += '<div class="mrow">%s<span class="nm">%s</span><span class="cnt">%d</span><span class="ic" data-tap="Menu %s">⋯</span></div>' % (handle, n, COUNTS[n], n)
        else:
            rows += '<div class="mrow" data-tap="Open %s">%s<span class="nm">%s</span><span class="cnt">%d</span><span class="ic">›</span></div>' % (n, handle, n, COUNTS[n])
    body = '<div class="c2" style="padding:0 12px">%s</div>' % rows
    if state == "menu":
        body += '<div class="menu2">%s</div>' % "".join('<div data-tap="M %s">%s</div>' % (x, x) for x in ("Rename", "Colour", "Scope", "What carries it", "Delete"))
    return kit.phone(kit.header("Labels", (("+", "New label"),), ("‹", "Back")), body, "")


def d_detail(state):
    body = ('<div class="c2" style="padding:0 12px">%s<div class="mrow"><span class="nm" data-tap="Colour row">Colour</span><span class="ic"><span class="dt"></span></span></div>'
            '<div class="row"><span class="lab">For</span>%s%s%s</div><div class="mrow"><span class="nm" data-tap="Carries">Carried by 12 · Walk, Water, …</span></div>'
            '<div class="row">%s</div></div>') % (R.row(R.field("Name field", "Health", "field")), R.ch("Scope all", "Everything", True), R.ch("Scope act", "Activities"),
                                                   R.ch("Scope trk", "Trackers"), R.b("Delete label", "Delete"))
    if state == "colours":
        body += '<div class="c2" style="padding:0 12px"><div class="row">%s</div></div>' % "".join(R.ch("Swatch %d" % i, "●") for i in range(6))
    return kit.phone(kit.header("Health", (), ("‹", "Back")), body, "")


def d_doc(v, state, kb=False, theme="light"):
    page = d_detail(state) if state in ("detail", "colours") else d_list(v, state)
    if state == "colours" and v["form"] != "detail":
        page = d_list(v, "list")[:-len("</div>")] + '<div class="c2" style="position:absolute;left:0;right:0;bottom:0;padding:0 12px;background:var(--zone)"><div class="row">%s</div></div></div>' % "".join(R.ch("Swatch %d" % i, "●") for i in range(6))
    if kb:
        page = page[:-len("</div>")] + KB.replace('class="kb"', 'class="kb" style="position:absolute;left:0;right:0;bottom:0;height:290px"') + "</div>"
    return kit.document(page, theme, t.EXTRA + t.T12_CSS + t.T13_CSS + R.CSS + D_CSS, True)


def score_d(v):
    states = ("list", "menu", "detail", "colours")
    views = views_of({s: (d_doc(v, s), d_doc(v, s, True)) for s in states})
    f = v["form"]
    if f == "direct":
        tasks = {"a": tap("list", "Name Health") + typ("list", 9) + tap("list", "Name Health"),
                 "b": tap("list", "Scope Books"), "c": tap("list", "Delete Calm"), "d": tap("list", "Handle Projects"),
                 "e": tap("list", "Count Health"), "f": tap("list", "Colour Home") + tap("colours", "Swatch 0")}
    elif f == "menu":
        tasks = {"a": tap("list", "Menu Health") + tap("menu", "M Rename") + typ("menu", 9) + tap("menu", "M Rename"),
                 "b": tap("list", "Menu Books") + tap("menu", "M Scope") + tap("detail", "Scope act"),
                 "c": tap("list", "Menu Calm") + tap("menu", "M Delete"), "d": tap("list", "Handle Projects"),
                 "e": tap("list", "Menu Health") + tap("menu", "M What carries it"), "f": tap("list", "Menu Home") + tap("menu", "M Colour") + tap("colours", "Swatch 0")}
    else:
        tasks = {"a": tap("list", "Open Health") + tap("detail", "Name field") + typ("detail", 9) + tap("detail", "Back"),
                 "b": tap("list", "Open Books") + tap("detail", "Scope act", "Back"), "c": tap("list", "Open Calm") + tap("detail", "Delete label"),
                 "d": tap("list", "Handle Projects"), "e": tap("list", "Open Health"), "f": tap("list", "Open Home") + tap("detail", "Colour row") + tap("colours", "Swatch 0") + tap("detail", "Back")}
    actions, miss, per = 0, set(), {}
    for k, task in tasks.items():
        n, m, _ = walk(views, task, {"Name field", "Name Health"}, closers=("Back",))
        actions += n
        miss |= m
        per[k] = n
    lst = ss.measure(d_doc(v, "list"), 360, 740)
    rows = len(LABELS)
    return {"actions": actions, "per_task": per, "unseen": sorted(miss), "small": small_of({"list": views["list"]}),
            "controls_per_row": round(len([x for x in lst["taps"] if x.get("seen") and x["name"] not in ("Back", "New label")]) / rows, 1),
            "clutter": clutter_of(lambda th: d_doc(v, "list", False, th))}


def run_part(name, space, fn):
    rows = []
    for c in itertools.product(*space.values()):
        v = dict(zip(space, c))
        r = dict(v=v, **fn(v))
        rows.append(r)
        print(r, flush=True)
    with open(os.path.join(v2.OUT, "labels-%s.json" % name), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    if "a" in sys.argv[1:]:
        run_a()
    if "b" in sys.argv[1:]:
        run_part("b", B_SPACE, score_b)
    if "c" in sys.argv[1:]:
        run_part("c", C_SPACE, score_c)
    if "d" in sys.argv[1:]:
        run_part("d", D_SPACE, score_d)


# ==== ranking: each part on the owner's axes, with the distance from the captured apps ==================================
def ref_distance(v, keys, refs):
    """The share of the reference apps that draw a part differently, over the apps that draw it at all."""
    out = []
    for k in keys:
        have = [r[k] for r in refs if r.get(k)]
        if have:
            out.append(sum(x != v[k] for x in have) / len(have))
    return round(sum(out) / len(out), 3)


def rank():
    with open(os.path.join(v2.OUT, "label-references.json"), encoding="utf-8") as fh:
        refs = json.load(fh)["apps"]
    parts = {
        # A: density is title room (more is better), added height, rows lost and labels hidden
        "a": ({"place": ("placement",), "look": ("look",)}, {"Clutter": ("clutter",), "Apart": ("neg_apart",), "Density": ("neg_title_room", "extra_h", "rows_lost", "hidden", "lines"),
                                                               "Refs": ("ref_distance",)}),
        "b": ({}, {"Ease": ("actions", "reach"), "Clutter": ("clutter", "covered", "controls"), "Shown": ("neg_labels_seen",), "Refs": ("ref_distance",)}),
        "c": ({}, {"Ease": ("actions",), "Clutter": ("clutter",), "Shown": ("neg_shown",), "Refs": ("ref_distance",)}),
        "d": ({}, {"Ease": ("actions",), "Clutter": ("clutter", "controls_per_row"), "Refs": ("ref_distance",)}),
    }
    keys = {"a": ("look", "placement"), "b": ("container", "shape"), "c": ("suggest",), "d": ("manage",)}
    report = {}
    for p, (_, axes) in parts.items():
        with open(os.path.join(v2.OUT, "labels-%s.json" % p), encoding="utf-8") as fh:
            rows = json.load(fh)
        for r in rows:
            v = dict(r["v"])
            v.setdefault("suggest", v.get("place"))
            v.setdefault("manage", v.get("form"))
            r["ref_distance"] = ref_distance(v, keys[p], refs)
            for k in ("apart", "title_room", "labels_seen", "shown"):
                if k in r:
                    r["neg_" + k] = -r[k]
        ok = [r for r in rows if not r.get("small") and not r.get("unseen")]
        for axis, ks in axes.items():
            cols = [v2.ranks(ok, k, 1) for k in ks]
            for i, r in enumerate(ok):
                r[axis] = sum(c[i] for c in cols)
        ax = list(axes)
        front = [r for r in ok if not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)]
        report[p] = {"passed": len(ok), "of": len(rows), "front": [r["v"] for r in front],
                     "rows": [{k: r.get(k) for k in ["v", "ref_distance"] + ax} for r in rows]}
        print(p, "passed", len(ok), "of", len(rows), "front", len(front))
        for r in sorted(front, key=lambda r: sum(r[a] for a in ax)):
            print("  ", r["v"], {a: r[a] for a in ax}, "ref", r["ref_distance"])
    with open(os.path.join(v2.OUT, "labels-rank.json"), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__" and "rank" in sys.argv[1:]:
    rank()


# ==== the options page: the front of each part, drawn ===================================================================
def page():
    """docs/screens/t1/labels-options.html, its images inlined (greyscale WebP) so it renders wherever it is opened."""
    import base64
    import io
    import html as H
    from PIL import Image
    with open(os.path.join(v2.OUT, "labels-rank.json"), encoding="utf-8") as fh:
        rank_ = json.load(fh)

    def img(d, w=300):
        buf = io.BytesIO()
        Image.open(ss.render(d, 360, 740)).convert("L").save(buf, "WEBP", quality=80)
        return '<img width="%d" src="data:image/webp;base64,%s">' % (w, base64.b64encode(buf.getvalue()).decode("ascii"))

    def fig(cap, d):
        return '<figure>%s<figcaption>%s</figcaption></figure>' % (img(d), H.escape(cap))

    def meas(part, v):
        r = [x for x in rank_[part]["rows"] if x["v"] == v][0]
        return " · ".join("%s %s" % (k, r[k]) for k in r if k != "v")

    a = json.load(open(os.path.join(v2.OUT, "labels-a.json"), encoding="utf-8"))
    sec = []
    shown_a = [{"look": "tint", "overflow": "fit", "placement": "inline"}, {"look": "tint", "overflow": "first", "placement": "below"},
               {"look": "hash", "overflow": "first", "placement": "inline"}, {"look": "text", "overflow": "first", "placement": "inline"},
               {"look": "dot", "overflow": "fit", "placement": "inline"}]
    figs = ""
    for v in shown_a:
        r = [x for x in a if x["v"] == v][0]
        cap = "%s, %s, %s: title room %s px, +%s px a row, %d rows lost, %d labels hidden, clutter %s" % (
            v["look"], {"fit": "as many as fit +n", "first": "first +n", "wrap": "wrap"}[v["overflow"]], v["placement"], r["title_room"], r["extra_h"], r["rows_lost"], r["hidden"], r["clutter"])
        figs += fig(cap, doc(v))
    sec.append('<h3>A. The chip on rows</h3><p class="dim">The front holds %d of 30; drawn: its leaders, and the dot for comparison.</p><div class="flex">%s</div>' % (len(rank_["a"]["front"]), figs))
    b = json.load(open(os.path.join(v2.OUT, "labels-b.json"), encoding="utf-8"))
    figs = ""
    for v in ({"container": "sheet", "shape": "grid"}, {"container": "sheet", "shape": "list"}, {"container": "page", "shape": "list"}):
        r = [x for x in b if x["v"] == v][0]
        cap = "%s, %s: %d actions over 4 tasks, covers %d%%, %d labels shown, clutter %s" % (v["container"], v["shape"], r["actions"], 100 * r["covered"], r["labels_seen"], r["clutter"])
        figs += fig(cap, picker_doc(v, "base")) + fig("…typing a new name: Create", picker_doc(v, "typed", True))
    figs += fig("A page's labels, several (sheet, grid)", picker_doc({"container": "sheet", "shape": "grid"}, "base", False, True))
    sec.append('<h3>B. The picker</h3><p class="dim">The keyboard\'s place and the pop-over cut off controls with a list.</p><div class="flex">%s</div>' % figs)
    figs = "".join(fig("%s: typing #h" % p, c_doc({"place": p}, "#h")) for p in ("chips", "list"))
    sec.append('<h3>C. Suggestions while typing #</h3><p class="dim">Chips and a list tie on every measure (14 actions); inline completion fails the 48 dp rule.</p><div class="flex">%s</div>' % figs)
    figs = fig("direct: 17 actions, 6 controls a row", d_doc({"form": "direct"}, "list")) + fig("detail: 23 actions, 2 controls a row (the list)", d_doc({"form": "detail"}, "list")) + \
        fig("detail: a label's page", d_doc({"form": "detail"}, "detail")) + fig("menu: 23 actions (a label's ⋯)", d_doc({"form": "menu"}, "menu"))
    sec.append('<h3>D. Management, Settings › Labels</h3><div class="flex">%s</div>' % figs)
    css = "body{font:14px/1.4 system-ui,sans-serif;padding:16px;background:#f4f4f2;color:#1d1d1b}h3{font-size:15px;margin:20px 0 6px}.dim{color:#6b6b66}.flex{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;max-width:300px}figcaption{font-size:12px;color:#6b6b66}"
    out = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T1.7 label options</title><style>%s</style></head><body>'
           '<h1 style="font-size:20px">T1.7 Labels: the options on each front</h1><p class="dim">Greys only (the dot, the tint and the outline take the label\'s colour later). '
           'Scores: <code>tools/screens/label_opt.py</code>; references: 8 apps captured on the phone.</p>%s</body></html>') % (css, "".join(sec))
    with open(os.path.join(v2.OUT, "labels-options.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(out)
    print(len(out))


if __name__ == "__main__" and "page" in sys.argv[1:]:
    page()
