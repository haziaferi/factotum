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
APART = {"text": 2, "dot": 3, "outline": 3, "tint": 3, "hash": 3, "heavy": 3}  # smaller text and dim ink, plus a mark or a boundary
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
/* control: built to lose */
.lb.heavy{background:var(--ink);color:var(--bg);border-radius:6px;padding:0 10px;height:26px;font-size:14px;font-weight:600}
.lb.heavy::before{content:"\25C6";font-size:10px}
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
        extra = (lambda n: "".join('<span data-tap="%s %s" style="min-width:48px;min-height:48px;display:inline-flex;align-items:center;justify-content:center;color:var(--dim)">%s</span>' % (k, n, g)
                                  for k, g in (("Ren", "✎"), ("Col", "●"), ("Del", "×")))) if v.get("control") else (lambda n: "")
        rows += "".join('<div class="lrow2"><span data-tap="Lb %s" style="flex:1;min-height:48px;display:flex;align-items:center;gap:10px"><span class="dt"></span>%s<span class="ck2">%s</span></span>%s</div>' % (n, n, "✓" if n in chosen else "", extra(n)) for n in names)
        if create:
            rows += '<div class="lrow2" data-tap="Create">Create “Sample label”</div>'
        items = rows
    else:
        chips = ("" if multi or create else R.ch("Lb none", "No label")) + "".join(R.ch("Lb %s" % n, n, n in chosen) for n in names)
        if create:
            chips += R.ch("Create", "Create “Sample label”")
        items = '<div class="row">%s</div>' % chips
    head = ('<div class="row" style="justify-content:space-between"><span></span><span class="ttl">Label</span>%s</div>' % (R.b("Done", "Done") if multi else "<span></span>")) if v["container"] != "page" else ""
    return head + (items + field if v.get("field_below") else field + items)


def picker_phone(v, state, kb, multi):
    c = v["container"]
    cls = {"keyboard": "pk", "sheet": "pk sheet", "popover": "pk pop", "page": "pk page"}[c]
    style = {"keyboard": ' style="height:290px;overflow:hidden"', "sheet": ' style="max-height:704px"', "popover": ' style="max-height:440px"', "page": ""}[c]
    if c == "page" and kb:
        style = ' style="bottom:290px"'
    pk = '<div class="%s"%s data-picker="1">%s</div>' % (cls, style, picker_body(v, state, multi))
    if c == "page":
        return kit.phone(kit.header("Label", (("✓", "Done"),) if multi or v.get("control") else (), ("‹", "Back")),
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
    if v.get("control"):  # every pick is confirmed with Done
        for k in ("a", "b", "c"):
            tasks[k] = tasks[k] + tap("typed" if k == "b" else "base", "Done")
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
C_SPACE = {"place": ["below", "above", "list", "inline"]}  # below was "chips" (owner: score chips above and below the line)
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
    if v["place"] in ("chips", "below", "above"):
        # owner, 2026-10-09: chips below the line (the hint line's place) or above it
        hint = '<div class="sug">%s%s</div>' % ("".join(R.ch("Sug %s" % n, n) for n in matches), R.ch("Create", "+ " + typed) if typed not in ("#he", "#h") else "")
        if v["place"] == "above":
            return '<div class="sheet" style="position:relative">%s%s<div class="hint">Task · # label</div></div>' % (hint, line)
        return '<div class="sheet" style="position:relative">%s%s</div>' % (line, hint)
    if v["place"] == "dialog":
        rows = "".join('<div class="sr" data-tap="Sug %s">%s</div>' % (n, n) for n in matches) + '<div class="sr" data-tap="Create">Create %s</div>' % typed
        dlg = ('<div style="position:absolute;left:20px;right:20px;bottom:0;background:var(--bg);border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,.25);padding:8px 0;z-index:5">'
               '<div style="padding:8px 16px;font-size:17px;font-weight:600">Choose a label</div><div class="slist" style="box-shadow:none;border-radius:0">%s</div>'
               '<div style="display:flex;justify-content:flex-end;gap:8px;padding:4px 8px 0">%s%s</div></div>') % (rows, R.b("Cancel", "Cancel"), R.b("OK", "OK"))
        return '<div class="sheet" style="position:relative">%s<div class="hint">Task · # label</div>%s</div>' % (line, dlg)
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
    if v["place"] == "dialog":  # each pick is confirmed with OK; the new label is created from its row, then OK
        a, b, c = a + 1, b + 1, c + 2
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
        elif v["form"] in ("legend", "legend_menu"):
            rows += ('<div class="mrow" style="min-height:60px">%s<span class="ic"><span class="dt"></span></span><span class="nm" data-tap="Open %s" '
                     'style="flex-direction:column;align-items:flex-start;justify-content:center">%s<span style="font-size:12.5px;color:var(--dim)">%d item%s</span></span>'
                     '%s<span class="ic">›</span></div>') % (handle if state == "edit" else "", n, n, COUNTS[n], "" if COUNTS[n] == 1 else "s",
                                                            '<span class="ic" data-tap="Menu %s">⋯</span>' % n if v["form"] == "legend_menu" else "")
        elif v["form"] == "menu":
            rows += '<div class="mrow">%s<span class="nm">%s</span><span class="cnt">%d</span><span class="ic" data-tap="Menu %s">⋯</span></div>' % (handle, n, COUNTS[n], n)
        else:
            rows += '<div class="mrow" data-tap="Open %s">%s<span class="nm">%s</span><span class="cnt">%d</span><span class="ic">›</span></div>' % (n, handle, n, COUNTS[n])
    body = '<div class="c2" style="padding:0 12px">%s</div>' % rows
    if state == "menu":
        body += '<div class="menu2">%s</div>' % "".join('<div data-tap="M %s">%s</div>' % (x, x) for x in ("Rename", "Colour", "Scope", "What carries it", "Delete"))
    edit = ((("✎", "Edit") if state != "edit" else ("✓", "Done")),) if v["form"] in ("legend", "legend_menu") else ()
    return kit.phone(kit.header("Labels", edit + (("+", "New label"),), ("‹", "Back")), body, "")


SCOPE = True  # the label page's scope row; the approved drawing leaves it out (owner, 2026-10-10: labels are global)


def d_detail(state):
    scope = '<div class="row"><span class="lab">For</span>%s%s%s</div>' % (R.ch("Scope all", "Everything", True), R.ch("Scope act", "Activities"), R.ch("Scope trk", "Trackers")) if SCOPE else ""
    body = ('<div class="c2" style="padding:0 12px">%s<div class="mrow"><span class="nm" data-tap="Colour row">Colour</span><span class="ic"><span class="dt"></span></span></div>'
            '%s<div class="mrow"><span class="nm" data-tap="Carries">Carried by 12 · Walk, Water, …</span></div>'
            '<div class="row">%s</div></div>') % (R.row(R.field("Name field", "Health", "field")), scope, R.b("Delete label", "Delete"))
    if state == "colours":
        body += '<div class="c2" style="padding:0 12px"><div class="row">%s</div></div>' % "".join(R.ch("Swatch %d" % i, "●") for i in range(6))
    return kit.phone(kit.header("Health", (), ("‹", "Back")), body, "")


def d_nested(state):
    """The control: every row opens the label (› or ⋯, both), with its count, scope and use written out; each property
    is a page of its own with Save; reorder sits behind Edit; delete asks first."""
    if state in ("list", "edit"):
        rows = "".join(('<div class="mrow" style="min-height:60px">%s<span class="nm" data-tap="Open %s" style="flex-direction:column;align-items:flex-start;justify-content:center">%s'
                        '<span style="font-size:12.5px;color:var(--dim)">%d item%s · used today</span></span><span class="ic"><span class="dt"></span></span>'
                        '<span class="ic" data-tap="More %s">⋯</span><span class="ic">›</span></div>') % (
                            '<span class="ic" data-tap="Handle %s">≡</span>' % n if state == "edit" else "", n, n, COUNTS[n], "" if COUNTS[n] == 1 else "s", n) for n in LABELS)
        return kit.phone(kit.header("Labels", (("✎", "Edit" if state == "list" else "Done"), ("+", "New label")), ("‹", "Back")),
                         '<div class="c2" style="padding:0 12px">%s</div>' % rows, "")
    if state in ("detail", "confirm"):
        rows = "".join('<div class="mrow" data-tap="Go %s"><span class="nm">%s</span><span class="ic">›</span></div>' % (k, k) for k in ("Rename", "Colour", "Scope", "Carries", "Delete"))
        body = '<div class="c2" style="padding:0 12px">%s</div>' % rows
        if state == "confirm":
            body += ('<div class="scrim" style="background:rgba(0,0,0,.3)"></div><div style="position:absolute;left:24px;right:24px;top:260px;background:var(--bg);border-radius:16px;padding:16px">'
                     '<div style="font-size:17px;font-weight:600">Delete this label?</div><div style="color:var(--dim);font-size:14px;margin:6px 0 10px">It comes off every item.</div>'
                     '<div style="display:flex;justify-content:flex-end;gap:8px">%s%s</div></div>') % (R.b("Cancel", "Cancel"), R.b("Confirm delete", "Delete"))
        return kit.phone(kit.header("Health", (), ("‹", "Back")), body, "")
    body = ('<div class="c2" style="padding:0 12px">%s<div class="row">%s%s%s</div><div class="row">%s</div></div>') % (
        R.row(R.field("Sub field", "Health", "field")), R.ch("Scope all", "Everything", True), R.ch("Scope act", "Activities"), R.ch("Scope trk", "Trackers"),
        "".join(R.ch("Swatch %d" % i, "●") for i in range(6)))
    return kit.phone(kit.header("Rename", (("✓", "Save"),), ("‹", "Back")), body, "")


def d_doc(v, state, kb=False, theme="light"):
    page = d_nested(state) if v["form"] == "nested" else d_detail(state) if state in ("detail", "colours") else d_list(v, state)
    if state == "colours" and v["form"] not in ("detail", "legend", "legend_menu"):
        page = d_list(v, "list")[:-len("</div>")] + '<div class="c2" style="position:absolute;left:0;right:0;bottom:0;padding:0 12px;background:var(--zone)"><div class="row">%s</div></div></div>' % "".join(R.ch("Swatch %d" % i, "●") for i in range(6))
    if kb:
        page = page[:-len("</div>")] + KB.replace('class="kb"', 'class="kb" style="position:absolute;left:0;right:0;bottom:0;height:290px"') + "</div>"
    return kit.document(page, theme, t.EXTRA + t.T12_CSS + t.T13_CSS + R.CSS + D_CSS, True)


def score_d(v):
    states = ("list", "edit", "detail", "sub", "confirm") if v["form"] == "nested" else ("list", "edit", "menu", "detail", "colours") if v["form"].startswith("legend") else ("list", "menu", "detail", "colours")
    views = views_of({s: (d_doc(v, s), d_doc(v, s, True)) for s in states})
    f = v["form"]
    if f == "nested":
        tasks = {"a": tap("list", "Open Health") + tap("detail", "Go Rename") + tap("sub", "Sub field") + typ("sub", 9) + tap("sub", "Save") + tap("detail", "Back"),
                 "b": tap("list", "Open Books") + tap("detail", "Go Scope") + tap("sub", "Scope act", "Save") + tap("detail", "Back"),
                 "c": tap("list", "Open Calm") + tap("detail", "Go Delete") + tap("confirm", "Confirm delete"),
                 "d": tap("list", "Edit") + tap("edit", "Handle Projects", "Done"),
                 "e": tap("list", "Open Health") + tap("detail", "Go Carries"),
                 "f": tap("list", "Open Home") + tap("detail", "Go Colour") + tap("sub", "Swatch 0", "Save") + tap("detail", "Back")}
    elif f == "legend":
        tasks = {"a": tap("list", "Open Health") + tap("detail", "Name field") + typ("detail", 9) + tap("detail", "Back"),
                 "b": tap("list", "Open Books") + tap("detail", "Scope act", "Back"), "c": tap("list", "Open Calm") + tap("detail", "Delete label"),
                 "d": tap("list", "Edit") + tap("edit", "Handle Projects", "Done"), "e": tap("list", "Open Health"),
                 "f": tap("list", "Open Home") + tap("detail", "Colour row") + tap("colours", "Swatch 0") + tap("detail", "Back")}
    elif f == "legend_menu":
        tasks = {"a": tap("list", "Menu Health") + tap("menu", "M Rename") + typ("menu", 9) + tap("menu", "M Rename"),
                 "b": tap("list", "Menu Books") + tap("menu", "M Scope") + tap("detail", "Scope act"),
                 "c": tap("list", "Menu Calm") + tap("menu", "M Delete"), "d": tap("list", "Edit") + tap("edit", "Handle Projects", "Done"),
                 "e": tap("list", "Open Health"), "f": tap("list", "Menu Home") + tap("menu", "M Colour") + tap("colours", "Swatch 0")}
    elif f == "direct":
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
        n, m, _ = walk(views, task, {"Name field", "Name Health", "Sub field"}, closers=("Back", "Save"))
        if f in ("nested", "legend", "legend_menu") and m == {"edit: Handle Projects"}:  # its taller rows put Projects below the fold: one scroll
            n, m = n + 1, set()
        actions += n
        miss |= m
        per[k] = n
    lst = ss.measure(d_doc(v, "list"), 360, 740)
    rows = len(LABELS)
    return {"actions": actions, "per_task": per, "unseen": sorted(miss), "small": small_of({"list": views["list"]}),
            "controls_per_row": round(len([x for x in lst["taps"] if x.get("seen") and x["name"] not in ("Back", "New label", "Edit")]) / rows, 1),
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


# ==== Part E: what tapping a label does, with the chip's target at 28 or 32 dp (owner, 2026-10-09) ====================
"""
  behaviour  view (a screen of everything carrying the label: items, habits, activities, trackers, pages, its time
             total), filter (the current screen filtered by it, with a clear ×), mark (the chip only shows; everything
             with a label is found by searching #name)
  target     28 or 32 dp, the chip's tap area (owner: an exception to 48 dp for this one purpose, as the dial's 32 dp)
  placement  inline or below, as part A; look tint (7 of the 8 captured apps) or text (a mark needs no pill)
Measures
  see_all      actions from Today to see everything carrying Health, and back
  complete     whether that shows everything (a filter shows only the screen it is on: 0)
  reach        Fitts' ID from the thumb to the chip (its target's smaller side as the width)
  exposure     the share of each row's area a chip's target takes from opening the item (0 for a mark)
  title_room, extra_h, rows_lost   as part A, with the chip's target height
"""
E_SPACE = {"behaviour": ["view", "filter", "mark"], "target": [28, 32], "placement": ["inline", "below"], "look": ["tint", "text"]}


def e_doc(v, theme="light"):
    base = dict(look=v["look"], overflow="first", placement=v["placement"])
    d = doc(base, theme)
    if v["behaviour"] != "mark":
        # each chip becomes a target of its own, the given height, its drawn pill unchanged inside
        d = re.sub(r'<span class="lb ([^"]*)">([^<]*)</span>',
                   lambda m: '<span data-tap="Chip %s" style="display:inline-flex;align-items:center;min-height:%dpx;min-width:%dpx;flex:none"><span class="lb %s">%s</span></span>' % (
                       m.group(2), v["target"], v["target"], m.group(1), m.group(2)) if "more" not in m.group(1) else m.group(0), d)
    return d


def score_e(v):
    m = ss.measure(e_doc(v), 360, 740)
    chips = [x for x in m["taps"] if x["name"].startswith("Chip ") and x.get("seen")]
    rows_px = 360 * 56  # a row's area, before labels
    exposure = round(sum(x["w"] * x["h"] for x in chips) / max(1, len(chips)) / rows_px, 3) if chips else 0.0
    reach = round(sum(math.log2(math.hypot(P.THUMB[0] - x["x"], P.THUMB[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in chips) / len(chips), 3) if chips else None
    # see everything carrying Health from Today, and back: view 1 + back 1; filter 1 + clear 1 (this screen only);
    # mark: search (1), "#health" (7 keys), its result (1), back (1)
    see_all = {"view": 2, "filter": 2, "mark": 10, "menu": 3}[v["behaviour"]]
    complete = {"view": 1, "filter": 0, "mark": 1, "menu": 1}[v["behaviour"]]
    d = doc(dict(look=v["look"], overflow="first", placement=v["placement"])).replace("</body>", PROBE + "</body>")
    if v["behaviour"] != "mark":
        d = e_doc(v).replace("</body>", PROBE + "</body>")
    res = ss._edge(["--dump-dom"], True, "labels-e-" + "-".join(str(x) for x in v.values()), d, 660, 1040)
    p = json.loads(re.search(r'<pre id="__labels">(.*?)</pre>', res.stdout, re.S).group(1).replace("&quot;", '"'))["rows"]
    return {"see_all": see_all, "complete": complete, "reach": reach, "exposure": exposure, "chips": len(chips),
            "title_room": round(sum(r["room"] for r in p) / len(p), 1), "extra_h": round(sum(max(0, r["h"] - 56) for r in p) / len(p), 1),
            "rows_lost": sum(not r["seen"] for r in p), "clutter": clutter_of(lambda th: e_doc(v, th))}


if __name__ == "__main__" and "e" in sys.argv[1:]:
    run_part("e", E_SPACE, score_e)


def c_reach(v):
    """Thumb reach to the suggestions (Fitts' ID from the thumb's rest; the keyboard is up, so the thumb rests on it)."""
    m = ss.measure(c_doc(v, "#h"), 360, 740)
    sug = [x for x in m["taps"] if x["name"].startswith("Sug ") and x.get("seen")]
    kb_thumb = (180, 615)  # the keyboard's centre, where a typing thumb is (as T1.3)
    return round(sum(math.log2(math.hypot(kb_thumb[0] - x["x"], kb_thumb[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in sug) / max(1, len(sug)), 3)


if __name__ == "__main__" and "creach" in sys.argv[1:]:
    for v in ({"place": "below"}, {"place": "above"}, {"place": "list"}):
        print(v, c_reach(v))


# ==== Part F: the label as a coloured dot (owner, 2026-10-09) ===========================================================
"""
Owner: "Could the label sit somewhere where it doesn't crowd the screen or increase rows height? Could it become a
colored dot? The label color would then be decided by the user with an advanced color picker." The name is read by a
long press on the row, on the item's page, and in a filter bar of named dots (owner's answers); all of these are drawn
or counted. The dots are grey here; colour comes with the palette (decision 15), from the guided picker that keeps
colours apart for colour-blind vision (T0's series contest).
  place     lead (under the time or kind mark, in the row's left column) or action (beside the right-hand action)
  several   dots (up to 3 side by side, then +n), count (one dot and the number), stack (up to 3 overlapping)
  entry     names (the label view opens from the item's page; the dot is no target) or tap (the dots are a 32 dp
            target opening the label view; owner's exception to 48 dp)
Measures: title_room, extra_h, rows_lost (the filter bar included), clutter, column (how far the dots stray from one
x across rows, px), exposure and reach (tap only), see_all (actions to everything carrying Health, and back).
"""
F_SPACE = {"place": ["lead", "action"], "several": ["dots", "count", "stack"], "entry": ["names", "tap"]}
F_CSS = """
.drow{display:flex;align-items:center;gap:8px;min-height:48px;padding:4px 0;border-bottom:1px solid var(--zone2)}
.drow .lead{width:44px;flex:none;color:var(--dim);font-size:12px;display:flex;flex-direction:column;align-items:center;gap:3px}
.drow .tt{flex:1;min-width:0;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.drow .act{flex:none;min-width:48px;height:48px;display:grid;place-items:center;font-size:13px}
.dots{display:inline-flex;align-items:center;gap:4px;flex:none}
.dots i{width:8px;height:8px;border-radius:50%;background:var(--dim);display:block}
.dots.stack i{margin-left:-4px;box-shadow:0 0 0 1.5px var(--bg)}.dots.stack i:first-child{margin-left:0}
.dots .n{font-size:11px;color:var(--dim)}
/* owner, 2026-10-09: the dots exactly on one vertical line; a count hangs beside its dot without moving it */
.dots.centred{position:relative}.dots.centred .n{position:absolute;left:calc(100% + 3px);top:50%;transform:translateY(-50%);line-height:1}
.dtap{min-width:32px;min-height:32px;display:inline-flex;align-items:center;justify-content:center;flex:none}
.fbar{display:flex;gap:6px;overflow:hidden;padding:0 0 2px}
"""


def dots_html(n, v):
    if v["several"] == "names":  # the control: n is the list of names
        inner = "".join('<span style="display:inline-flex;align-items:center;gap:3px;font-size:11px;color:var(--dim);white-space:nowrap"><i></i>%s</span>' % x for x in n)
        d = '<span class="dots" style="flex-direction:column;align-items:flex-start;gap:1px">%s</span>' % inner
        return '<span class="dtap" data-tap="Dots">%s</span>' % d if v["entry"] == "tap" else d
    if v["several"] == "count":
        inner = "<i></i>" + ('<span class="n">%d</span>' % n if n > 1 else "")
    else:
        inner = "<i></i>" * min(3, n) + ('<span class="n">+%d</span>' % (n - 3) if n > 3 else "")
    d = '<span class="dots %s%s">%s</span>' % ("stack" if v["several"] == "stack" else "", " centred" if v.get("centred") else "", inner)
    return '<span class="dtap" data-tap="Dots">%s</span>' % d if v["entry"] == "tap" else d


def f_row(lead, title, n, v, act=""):
    dots = dots_html(n, v)
    wide = ' style="width:auto;min-width:44px;align-items:flex-start"' if v["several"] == "names" else ""
    lead_html = '<span class="lead"%s><span>%s</span>%s</span>' % (wide, lead, dots if v["place"] == "lead" else "")
    right = (dots if v["place"] == "action" else "") + ('<span class="act">%s</span>' % act if act else ('<span class="act"></span>' if v["place"] == "action" else ""))
    return '<div class="drow" data-tap="Open item">%s<span class="tt">%s</span>%s</div>' % (lead_html, kit.ud(title), right)


def f_phone(v):
    fbar = '<div class="fbar">%s</div>' % "".join(R.ch("Filter %s" % n, '<span class="dots"><i></i></span>&nbsp;' + n) for n in ("Health", "Body", "Calm", "Home", "Books"))
    cnt = (lambda names: names) if v["several"] == "names" else len
    routines = "".join(f_row(time or t.KIND_MARK["habit"], title, cnt(names), v, "Log") for _, title, time, names in ROUTINES)
    pages = "".join(f_row("▤", title, cnt(names), v) for title, names in PAGES)
    return kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), '<div class="c2">%s</div>' % fbar + kit.zone("Routines", routines) + kit.zone("Pages", pages), kit.bar("Today"))


def f_doc(v, theme="light"):
    return kit.document(f_phone(v), theme, t.EXTRA + t.T12_CSS + R.CSS + F_CSS, True)


F_PROBE = """<script>(function(){var bar=document.querySelector('.bar'),floor=bar?bar.getBoundingClientRect().top:740,out={rows:[]};
[].slice.call(document.querySelectorAll('.drow')).forEach(function(r){var tt=r.querySelector('.tt'),d=r.querySelector('.dots');
out.rows.push({h:Math.round(r.getBoundingClientRect().height),room:Math.round(tt.clientWidth),seen:r.getBoundingClientRect().bottom<=floor+1,
dx:d?Math.round(d.getBoundingClientRect().left):null})});
document.body.insertAdjacentHTML('beforeend','<pre id="__do'+'ts">'+JSON.stringify(out)+'</pre>')})()</script>"""


def score_f(v):
    d = f_doc(v).replace("</body>", F_PROBE + "</body>")
    res = ss._edge(["--dump-dom"], True, "labels-f-" + "-".join(str(x) for x in v.values()), d, 660, 1040)
    p = json.loads(re.search(r'<pre id="__dots">(.*?)</pre>', res.stdout, re.S).group(1).replace("&quot;", '"'))["rows"]
    xs = [r["dx"] for r in p if r["dx"] is not None]
    m = ss.measure(f_doc(v), 360, 740)
    chips = [x for x in m["taps"] if x["name"] == "Dots" and x.get("seen")]
    exposure = round(sum(x["w"] * x["h"] for x in chips) / max(1, len(chips)) / (360 * 56), 3) if chips else 0.0
    reach = round(sum(math.log2(math.hypot(P.THUMB[0] - x["x"], P.THUMB[1] - x["y"]) / min(x["w"], x["h"]) + 1) for x in chips) / len(chips), 3) if chips else None
    return {"title_room": round(sum(r["room"] for r in p) / len(p), 1), "extra_h": round(sum(max(0, r["h"] - 56) for r in p) / len(p), 1),
            "rows_lost": sum(not r["seen"] for r in p), "column": max(xs) - min(xs) if xs else 0, "exposure": exposure, "reach": reach,
            "see_all": 2 if v["entry"] == "tap" else 3, "small": sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in m["taps"] if x.get("seen") and (x["w"] < 48 or x["h"] < 48) and x["name"] != "Dots"}),
            "clutter": clutter_of(lambda th: f_doc(v, th))}


if __name__ == "__main__" and "f" in sys.argv[1:]:
    run_part("f", F_SPACE, score_f)


def run_f_centred():
    """The count hung beside its dot (owner's "exactly vertically centred") for every count variant, not only the chosen
    one: added to labels-f.json (the F control first reached the front because no tappable centred variant existed)."""
    path = os.path.join(v2.OUT, "labels-f.json")
    with open(path, encoding="utf-8") as fh:
        rows = [r for r in json.load(fh) if not r["v"].get("centred")]
    for place in F_SPACE["place"]:
        for entry in F_SPACE["entry"]:
            v = {"place": place, "several": "count", "entry": entry, "centred": True}
            rows.append(dict(v=v, **score_f(v)))
            print(rows[-1], flush=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__" and "fcentred" in sys.argv[1:]:
    run_f_centred()


def dots_page():
    """docs/screens/t1/labels-dots.html: part F drawn, images inlined."""
    import base64
    import io
    import html as H
    from PIL import Image
    rows = json.load(open(os.path.join(v2.OUT, "labels-f.json"), encoding="utf-8"))
    figs = ""
    for r in rows:
        v = r["v"]
        buf = io.BytesIO()
        Image.open(ss.render(f_doc(v), 360, 740)).convert("L").save(buf, "WEBP", quality=80)
        cap = "%s · %s · %s: title room %s px, +%s px a row, %d rows lost, dots stray %d px%s, clutter %s" % (
            {"lead": "under the time", "action": "by the action"}[v["place"]], {"dots": "up to 3 dots", "count": "dot + count", "stack": "stacked"}[v["several"]],
            {"names": "view from the item's page", "tap": "dots tap to the view (32 dp)"}[v["entry"]], r["title_room"], r["extra_h"], r["rows_lost"], r["column"],
            ", %.1f%% of a row a target" % (100 * r["exposure"]) if r["exposure"] else "", r["clutter"])
        figs += '<figure><img width="300" src="data:image/webp;base64,%s"><figcaption>%s</figcaption></figure>' % (base64.b64encode(buf.getvalue()).decode("ascii"), H.escape(cap))
    css = "body{font:14px/1.4 system-ui,sans-serif;padding:16px;background:#f4f4f2;color:#1d1d1b}.dim{color:#6b6b66}.flex{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;max-width:300px}figcaption{font-size:12px;color:#6b6b66}"
    out = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T1.7 label dots</title><style>%s</style></head><body>'
           '<h1 style="font-size:20px">T1.7 Labels as coloured dots</h1><p class="dim">Grey here; each dot takes its label\'s colour, chosen in the picker that keeps colours apart '
           'for colour-blind vision. Names: a long press on the row, the item\'s page, and the filter bar of named dots on top.</p><div class="flex">%s</div></body></html>') % (css, figs)
    with open(os.path.join(v2.OUT, "labels-dots.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(out)
    print(len(out))


if __name__ == "__main__" and "dotspage" in sys.argv[1:]:
    dots_page()


# ==== the chosen dot (owner, 2026-10-09: "Under the time, dot + count, all exactly vertically centered") ==============
CHOSEN_DOT = {"place": "lead", "several": "count", "entry": "names", "centred": True}


def rest_page():
    """docs/screens/t1/labels-rest.html: the chosen dots, and the parts still open: the # chips above or below the
    line, and Settings › Labels as direct controls or a page per label (with the dot), images inlined."""
    import base64
    import io
    import html as H
    from PIL import Image

    def fig(cap, d):
        buf = io.BytesIO()
        Image.open(ss.render(d, 360, 740)).convert("L").save(buf, "WEBP", quality=80)
        return '<figure><img width="300" src="data:image/webp;base64,%s"><figcaption>%s</figcaption></figure>' % (base64.b64encode(buf.getvalue()).decode("ascii"), H.escape(cap))

    r = score_f(CHOSEN_DOT)
    sec = '<h3>The chosen dots</h3><p class="dim">Under the time or mark, one dot and its count; every dot on one vertical line (strays %d px), titles %s px, no row height added.</p><div class="flex">%s</div>' % (
        r["column"], r["title_room"], fig("Today and Pages, the chosen dots", f_doc(CHOSEN_DOT)))
    sec += '<h3>The # suggestions: above or below the line</h3><div class="flex">%s%s%s</div>' % (
        fig("Above: the line stays put while you type; reach 2.81", c_doc({"place": "above"}, "#h")),
        fig("Below (the hint line's place): reach 2.49, the line moves up 25 px", c_doc({"place": "below"}, "#h")),
        fig("Control (lost): a dialog over the line, OK after each pick; 18 actions, the line hidden", c_doc({"place": "dialog"}, "#h")))
    sec += '<h3>Settings › Labels</h3><div class="flex">%s%s%s%s%s</div>' % (
        fig("Direct controls: 17 actions, 6 controls a row", d_doc({"form": "direct"}, "list")),
        fig("A page per label: the list (23 actions, 2 controls a row)", d_doc({"form": "detail"}, "list")),
        fig("…a label's page: name, colour, scope, what carries it, Delete", d_doc({"form": "detail"}, "detail")),
        fig("Control (lost): nested pages, a page per property with Save; 33 actions, clutter 0.059", d_doc({"form": "nested"}, "list")),
        fig("…the control's label page: every property one more page away", d_doc({"form": "nested"}, "detail")))
    css = "body{font:14px/1.4 system-ui,sans-serif;padding:16px;background:#f4f4f2;color:#1d1d1b}h3{font-size:15px;margin:20px 0 6px}.dim{color:#6b6b66}.flex{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;max-width:300px}figcaption{font-size:12px;color:#6b6b66}"
    out = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T1.7 labels, the rest</title><style>%s</style></head><body>'
           '<h1 style="font-size:20px">T1.7 Labels: the chosen dots, and the parts still open</h1><p class="dim">Every number is in labels-scores.html, one table per part, with its control.</p>%s</body></html>') % (css, sec)
    with open(os.path.join(v2.OUT, "labels-rest.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(out)
    print(len(out), r)


if __name__ == "__main__" and "rest" in sys.argv[1:]:
    rest_page()


def run_d_legend():
    """The owner's D (the control's list rows as the colour legend, a page per label), with and without the row's ⋯,
    added to labels-d.json."""
    path = os.path.join(v2.OUT, "labels-d.json")
    with open(path, encoding="utf-8") as fh:
        rows = [r for r in json.load(fh) if not r["v"]["form"].startswith("legend")]
    for f in ("legend", "legend_menu"):
        rows.append(dict(v={"form": f}, **score_d({"form": f})))
        print(rows[-1], flush=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__" and "dlegend" in sys.argv[1:]:
    run_d_legend()


# ==== controls: one variant per part built to lose; it must stay off the front ==============================================
CONTROLS = {
    "a": ({"look": "heavy", "overflow": "wrap", "placement": "below"}, "heavy dark chips (bold, 14 px, a mark), every name, wrapped below the title"),
    "b": ({"container": "page", "shape": "list", "control": True}, "a full page, a list, rename/colour/delete on every row, every pick confirmed with Done"),
    "c": ({"place": "dialog"}, "a dialog over the line, every match a row, each pick confirmed with OK"),
    "d": ({"form": "nested"}, "nested pages: list › label › a page per property with Save, reorder behind Edit, delete confirmed, rows written out"),
    "e": ({"behaviour": "menu", "target": 48, "placement": "below", "look": "tint"}, "tinted 48 dp chips below the title; a tap opens a menu (View, Filter, Remove) first"),
    "f": ({"place": "lead", "several": "names", "entry": "tap"}, "every label as a dot and its name, stacked under the time, the stack a target"),
}


def run_controls():
    fns = {"a": score_a, "b": score_b, "c": score_c, "d": score_d, "e": score_e, "f": score_f}
    out = {}
    for p, (v, why) in CONTROLS.items():
        out[p] = dict(v=v, why=why, **fns[p](v))
        print(p, out[p], flush=True)
    with open(os.path.join(v2.OUT, "labels-controls.json"), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__" and "controls" in sys.argv[1:]:
    run_controls()


# ==== the score tables: every variant of every part, its measures, its axes and the front ===============================
SCORE_AXES = {
    # part: {axis: (measure, ...)}; a measure prefixed "-" counts more as better
    "a": {"Clutter": ("clutter",), "Apart": ("-apart",), "Density": ("-title_room", "extra_h", "rows_lost", "hidden", "lines"), "Refs": ("ref_distance",)},
    "b": {"Ease": ("actions", "reach"), "Clutter": ("clutter", "covered", "controls"), "Shown": ("-labels_seen",), "Refs": ("ref_distance",)},
    "c": {"Ease": ("actions", "reach"), "Calm": ("clutter", "line_move", "line_hidden"), "Shown": ("-shown",), "Refs": ("ref_distance",)},
    "d": {"Ease": ("actions",), "Clutter": ("clutter", "controls_per_row"), "Refs": ("ref_distance",)},
    "e": {"Ease": ("see_all", "reach"), "Clutter": ("clutter", "exposure"), "Density": ("-title_room", "extra_h", "rows_lost")},
    "f": {"Density": ("-title_room", "extra_h", "rows_lost"), "Order": ("column",), "Ease": ("see_all",), "Clutter": ("clutter",)},
}
SCORE_COLS = {
    "a": ["title_room", "extra_h", "rows_lost", "hidden", "lines", "truncated", "min_text", "apart", "clutter", "ref_distance"],
    "b": ["actions", "reach", "covered", "controls", "labels_seen", "clutter", "ref_distance"],
    "c": ["actions", "reach", "line_move", "line_hidden", "shown", "clutter", "ref_distance"],
    "d": ["actions", "controls_per_row", "clutter", "ref_distance"],
    "e": ["see_all", "complete", "reach", "exposure", "chips", "title_room", "extra_h", "rows_lost", "clutter"],
    "f": ["title_room", "extra_h", "rows_lost", "column", "see_all", "reach", "exposure", "clutter"],
}
SCORE_HELP = {
    "title_room": "px the title keeps (more is better)", "extra_h": "px added to a row", "rows_lost": "rows pushed off Today",
    "hidden": "labels not shown", "lines": "extra lines", "truncated": "names cut", "min_text": "smallest text px",
    "apart": "label kinds told apart (of 3; more is better)", "clutter": "edge density, light and dark averaged (lower is calmer)",
    "ref_distance": "share of the 8 captured apps that draw it differently", "actions": "taps and keys over the part's tasks",
    "reach": "Fitts ID from the thumb (lower is easier)", "covered": "share of the screen covered", "controls": "controls on screen",
    "labels_seen": "labels visible, of 12", "line_move": "px the capture line moves when suggestions appear",
    "shown": "suggestions visible", "line_hidden": "1 = the capture line is covered while choosing", "controls_per_row": "controls on each Settings row",
    "see_all": "actions to see everything carrying a label, and back",
    "complete": "1 = the view shows every kind (tasks, pages, entries)", "exposure": "tap area per row, share of the row",
    "chips": "chips that are targets", "column": "px the dots stray from one vertical line",
}


def c_line_move(v):
    """How far the capture line moves when the suggestions appear: the line's ⋯ with "#h" typed, against "#zq" (no match)
    on the inline variant, which keeps the line where it is with nothing shown."""
    def y(vv, typed):
        return [x for x in ss.measure(c_doc(vv, typed), 360, 740)["taps"] if x["name"] == "More"][0]["y"]
    return abs(round(y(v, "#h") - y({"place": "inline"}, "#zq")))


def scores_page():
    """docs/screens/t1/labels-scores.html: one table per part, every variant, raw measures, rank-sum axes, the front."""
    import html as H
    with open(os.path.join(v2.OUT, "label-references.json"), encoding="utf-8") as fh:
        refs = json.load(fh)["apps"]
    keys = {"a": ("look", "placement"), "b": ("container", "shape"), "c": ("suggest",), "d": ("manage",)}
    titles = {"a": "A. Chip look × overflow × placement (on Today's rows)", "b": "B. The picker: container × shape",
              "c": "C. # suggestions on the capture line", "d": "D. Settings › Labels",
              "e": "E. What tapping a label does × target size × placement × look",
              "f": "F. The label as a dot: place × several × entry"}
    chosen = {"b": {"container": "sheet", "shape": "grid"}, "c": {"place": "above"}, "d": {"form": "legend"}, "f": dict(CHOSEN_DOT)}
    tasks = {"b": "Tasks: a = add Health; b = add three labels; c = remove one; d = create Garden.",
             "c": "Tasks: a = \"#he\" then Health; b = \"#h\" then Home (the second match); c = \"#garden\", a new label.",
             "d": "Tasks: a = rename Health; b = scope Books; c = delete Calm; d = move Projects up; e = see what carries Health; f = colour Home."}
    out = []
    with open(os.path.join(v2.OUT, "labels-controls.json"), encoding="utf-8") as fh:
        controls = json.load(fh)
    lost = {}
    for p in "abcdef":
        with open(os.path.join(v2.OUT, "labels-%s.json" % p), encoding="utf-8") as fh:
            rows = json.load(fh)
        rows.append(dict(controls[p], control=True))
        if p == "c":
            for r in rows:
                r["reach"] = c_reach(r["v"]) if r["shown"] else None
                r["line_move"] = c_line_move(r["v"])
                r["line_hidden"] = int(not [x for x in ss.measure(c_doc(r["v"], "#h"), 360, 740)["taps"] if x["name"] == "More"][0].get("seen"))
        for r in rows:
            if p in keys:
                v = dict(r["v"])
                v.setdefault("suggest", {"below": "chips", "above": "chips"}.get(v.get("place"), v.get("place")))
                v.setdefault("manage", {"legend": "detail", "legend_menu": "menu"}.get(v.get("form"), v.get("form")))
                r["ref_distance"] = ref_distance(v, keys[p], refs)
        ok = [r for r in rows if not r.get("small") and not r.get("unseen")]
        axes = SCORE_AXES[p]
        for r in ok:  # nothing to reach ranks as no cost in F (the dot is no target), as unreachable elsewhere
            r["_reach"] = r.get("reach") if r.get("reach") is not None else (0 if p == "f" else 99)
        for axis, ks in axes.items():
            for r in ok:
                r[axis] = 0
            for k in ks:
                sign, k2 = (-1, k[1:]) if k.startswith("-") else (1, k)
                k2 = "_reach" if k2 == "reach" else k2
                for r, rk in zip(ok, v2.ranks(ok, k2, sign)):
                    r[axis] += rk
        ax = list(axes)
        for r in ok:
            r["front"] = not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)
            r["total"] = sum(r[a] for a in ax)
        ctl = next(r for r in rows if r.get("control"))
        worse = sum(1 for r in ok if r is not ctl and r.get("total", 0) < ctl.get("total", 1e9))
        lost[p] = ctl in ok and not ctl.get("front")
        order = sorted(rows, key=lambda r: (r not in ok, not r.get("front"), r.get("total", 1e9)))
        vk = [k for k in dict.fromkeys(k for r in rows for k in r["v"]) if k != "control"]
        cols = SCORE_COLS[p]

        def cell(x):
            if x is None:
                return "—"
            if isinstance(x, bool):
                return "yes" if x else "no"
            return "%g" % x if isinstance(x, (int, float)) else H.escape(str(x))
        head = "".join("<th>%s</th>" % k for k in vk) + \
            "".join('<th title="%s">%s</th>' % (H.escape(SCORE_HELP.get(c, "")), c) for c in cols) + \
            "".join("<th class=ax>%s</th>" % a for a in ax) + "<th class=ax>sum</th><th>front</th><th>gate</th>"
        body = []
        for r in order:
            gate = "pass" if r in ok else "fails: " + H.escape(", ".join(r.get("small", []) + r.get("unseen", [])))
            cls = " ".join(c for c in ("ch" if chosen.get(p) == r["v"] else "", "fr" if r.get("front") else "", "fail" if r not in ok else "", "ctl" if r.get("control") else "") if c)
            body.append('<tr class="%s">%s%s%s<td class=ax>%s</td><td>%s</td><td>%s</td></tr>' % (
                cls, "".join("<td>%s</td>" % cell(r["v"].get(k, "")) for k in vk),
                "".join("<td>%s</td>" % cell(r.get(c)) for c in cols),
                "".join("<td class=ax>%g</td>" % r[a] if r in ok else "<td class=ax>—</td>" for a in ax),
                "%g" % r["total"] if r in ok else "—", "★" if r.get("front") else "", ("control · " if r.get("control") else "") + gate))
        axis_line = "; ".join("<b>%s</b> = rank-sum of %s" % (a, ", ".join(k.lstrip("-") + (" (more is better)" if k.startswith("-") else "") for k in ks)) for a, ks in axes.items())
        verdict = ("<b>Control lost:</b> off the front; %d of %d passing variants have a lower sum." % (worse, len(ok) - 1)) if lost[p] else \
            ("<b>CONTROL DID NOT LOSE</b> (%s): the axes cannot tell it from a real option." % ("on the front" if ctl in ok else "it failed the gate instead"))
        out.append('<h2 id="%s">%s</h2><p class=dim>%d variants and the control · %d pass the gate · %d on the Pareto front (★). %s</p>'
                   '<p class=dim>Axes, lower is better: %s.</p><p>Control: %s. %s</p><div class=wrap><table><tr>%s</tr>%s</table></div>' % (
                       p, titles[p], len(rows) - 1, len(ok), sum(1 for r in ok if r.get("front")), tasks.get(p, ""), axis_line,
                       H.escape(ctl["why"]), verdict, head, "".join(body)))
    legend = "".join("<li><b>%s</b>: %s</li>" % (k, H.escape(v)) for k, v in SCORE_HELP.items())
    doc = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Label Score Tables</title>
<style>:root{--bg:#fafafa;--fg:#1c1c1c;--dim:#777;--line:#ddd;--ch:#dcdcdc;--fr:#f0f0f0}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121212;--fg:#eee;--dim:#999;--line:#333;--ch:#3a3a3a;--fr:#1f1f1f}}
:root[data-theme=dark]{--bg:#121212;--fg:#eee;--dim:#999;--line:#333;--ch:#3a3a3a;--fr:#1f1f1f}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1500px}
.dim{color:var(--dim)}.wrap{overflow-x:auto}table{border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid var(--line);padding:4px 7px;text-align:left;white-space:nowrap}th{background:var(--bg)}
.ax{border-left:1px solid var(--line)}tr.ctl td{font-style:italic;border-top:2px dashed var(--dim)}tr.fr{background:var(--fr)}tr.ch{background:var(--ch);font-weight:700}tr.fail td{color:var(--dim)}
li{margin:2px 0}</style></head><body>
<h1>T1.7 labels: score tables</h1>
<p>Every variant scored, generated from the measured files (labels-a…f.json) by <code>python tools/screens/label_opt.py scores</code>.
Measures come from headless Edge at 360×740: targets, reach, row heights, and clutter rendered light and dark. Axes are rank sums within a part (lower is better); ★ marks the Pareto front; <b>bold</b> rows are the owner's choices so far; grey rows failed the gate (a target under 48 dp where no exception was set, or a target that cannot be reached).</p>
<p class=dim>Each part has one control, in italics with a dashed rule: a variant built to be heavier or deeper than anything in its space. It must pass the gate and stay off the front; if it does not, the axes are suspect and the run fails.</p>
%s<h2>Measures</h2><ul>%s</ul></body></html>""" % ("".join(out), legend)
    path = os.path.join(v2.OUT, "labels-scores.html")
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(doc)
    print(path)
    print("controls lost:", lost)
    if not all(lost.values()):
        sys.exit(1)


if __name__ == "__main__" and "scores" in sys.argv[1:]:
    scores_page()


# ==== the approved T1.7 section for screens.html (owner, 2026-10-09) ======================================================
CHOSEN_B = {"container": "sheet", "shape": "grid", "field_below": True}
CHOSEN_C = {"place": "above"}
CHOSEN_D = {"form": "legend"}


def f_filtered_doc(name="Health", theme="light"):
    """Today filtered by one label from the filter bar of named dots: only what carries it, the chip on, Clear beside it."""
    v = CHOSEN_DOT
    names = [name] + [n for n in ("Health", "Body", "Calm", "Home", "Books") if n != name]  # the one on first, Clear beside it
    chip = lambda n: R.ch("Filter %s" % n, '<span class="dots"><i></i></span>&nbsp;' + n, n == name)
    fbar = '<div class="fbar">%s%s%s</div>' % (chip(names[0]), R.ch("Clear", "Clear"), "".join(chip(n) for n in names[1:]))
    routines = "".join(f_row(time or t.KIND_MARK["habit"], title, len(names), v, "Log") for _, title, time, names in ROUTINES if name in names)
    pages = "".join(f_row("▤", title, len(names), v) for title, names in PAGES if name in names)
    body = '<div class="c2">%s</div>' % fbar + kit.zone("Routines", routines) + (kit.zone("Pages", pages) if pages else "")
    return kit.document(kit.phone(kit.header(t.TITLE, t.APPROVED_BUTTONS), body, kit.bar("Today")), theme, t.EXTRA + t.T12_CSS + R.CSS + F_CSS, True)


def labels_desk_doc(theme="light"):
    """Windows: Today's rows with their dots and the filter bar, and Settings › Labels open in the page column."""
    v = CHOSEN_DOT
    fbar = '<div class="c2"><div class="fbar">%s</div></div>' % "".join(R.ch("Filter %s" % n, '<span class="dots"><i></i></span>&nbsp;' + n) for n in ("Health", "Body", "Calm", "Home", "Books"))
    rows = "".join(f_row(time or t.KIND_MARK["habit"], title, len(names), v, "Log") for _, title, time, names in ROUTINES) + \
        "".join(f_row("▤", title, len(names), v) for title, names in PAGES)
    legend = "".join(('<div class="mrow" style="min-height:52px"><span class="ic"><span class="dt"></span></span><span class="nm" style="flex-direction:column;align-items:flex-start;justify-content:center">'
                      '%s<span style="font-size:12.5px;color:var(--dim)">%d item%s</span></span><span class="ic">›</span></div>') % (n, COUNTS[n], "" if COUNTS[n] == 1 else "s") for n in LABELS[:9])
    head = '<div class="hdr"><span class="ttl">%s</span><span class="srch" data-tap="Search" style="width:320px">⌕ Search everything <span class="kbd">Ctrl+K</span></span></div>' % t.TITLE
    page = '<div class="page"><div class="kbd">Settings › Labels</div>%s</div>' % legend
    return kit.document(kit.desk(kit.rail("Today"), head, '<div class="dcol">%s%s</div>%s' % (fbar, rows, page)), theme,
                        t.EXTRA + t.T12_CSS + R.CSS + F_CSS + D_CSS, True)


def labels_section():
    """The T1.7 section, images inlined small (greyscale WebP at the shown width) so screens.html stays under viewers' caps."""
    global SCOPE
    SCOPE = False  # owner, 2026-10-10: labels are global, so a label's page has no scope row
    import base64
    import io
    import html as H
    from PIL import Image

    def img(d, w, h, show):
        im = Image.open(ss.render(d, w, h)).convert("L")
        im = im.resize((show, round(im.height * show / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=50)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    def fig(cap, d):
        return '<figure><img src="%s" width="300" alt="%s"><figcaption>%s</figcaption></figure>' % (img(d, 360, 740, 300), H.escape(cap), H.escape(cap))
    table = [
        ("The label on a row", "A dot under the time or kind mark, one dot and its count, every dot on one vertical line. Titles keep 232 px; no row grows; 0 px stray. Colour from the guided picker; the name is never colour alone (WCAG 1.4.1).", "F, labels-scores.html#f"),
        ("Filtering", "The filter bar of named dots on any screen: a tap shows only what carries that label there; Clear undoes it. 2 actions.", "E, owner 2026-10-09"),
        ("The picker", "A sheet, a grid of every label in alphabetical order, the search-and-create box below them. 20 actions over 4 tasks, reach 2.08, 12 of 12 labels shown.", "B, labels-scores.html#b"),
        ("# on the capture line", "Matching labels as chips above the line, so the line stays put while typing (moves 0 px, against 25 px below). 14 actions, reach 2.81.", "C, labels-scores.html#c"),
        ("Settings › Labels", "Each row is the label's dot, its name and a written line (how many carry it), so the list is the colour legend; each opens one page with name, colour, what carries it and Delete (undo toast). Reorder behind Edit. 26 actions, 0.9 controls a row.", "D, labels-scores.html#d"),
    ]
    rows = "".join("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>" % tuple(H.escape(x) for x in r) for r in table)
    figs = "".join([
        fig("Today: the dots, and the filter bar", f_doc(CHOSEN_DOT)),
        fig("Today filtered by Health", f_filtered_doc()),
        fig("Capture: # suggestions above the line", c_doc(CHOSEN_C, "#h")),
        fig("⋯ › Label: the picker sheet", picker_doc(CHOSEN_B, "base")),
        fig("Settings › Labels: the list is the legend", d_doc(CHOSEN_D, "list")),
        fig("A label's page", d_doc(CHOSEN_D, "detail")),
    ])
    desk = '<figure><img src="%s" width="560" alt="Windows, Today and Labels"><figcaption>Today with its dots beside Settings › Labels</figcaption></figure>' % img(labels_desk_doc(), 1100, 660, 560)
    return ('<section id="t1-7"><h2>T1.7 Labels <span class="tag">approved</span></h2>'
            '<p>A label is a coloured dot, not a chip: it takes no room from titles and adds no height. The name is read in the filter bar, '
            'on the item\'s page, in the picker and in Settings › Labels, whose list doubles as the colour legend. Every variant, its measures '
            'and a control per part: <a href="labels-scores.html">labels-scores.html</a>.</p>'
            '<h3>Decided by</h3><table><tr><th>Part</th><th>Choice and its measure</th><th>Record</th></tr>%s</table>'
            '<h3>Phone</h3><div class="refs">%s</div><h3>Windows</h3><div class="refs">%s</div></section>') % (rows, figs, desk)


if __name__ == "__main__" and "section" in sys.argv[1:]:
    s_ = labels_section()
    print(len(s_))
    with open(os.path.join(v2.OUT, "labels-section-preview.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write('<!doctype html><meta charset="utf-8"><title>T1.7 preview</title>' + s_)
