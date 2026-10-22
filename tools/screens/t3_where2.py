"""T3b.6b One home per thing, settled against the item's page (owner, 2026-10-18; decision 19).

Registered into t3_opt's parts by t3_opt itself (register(globals()) at its end):
    python tools/screens/t3_opt.py where2 page_html scores

The owner's answers (2026-10-18):
  - the item's page is the fixed home of what T3b.7f gave it (the tracking panel: Log, the timer, today's amount; the goal
    line, the graph, the statistics, History); only the repeats elsewhere are scored;
  - drawn and measured, not counted by hand; This week, Saved charts and Review's day are not designed yet (T3c), so they
    are drawn as minimal frames from their sources (Tendril's Review, Chronicle's Charts) with only the repeat varying;
    Harmony and Hierarchy are measured on the designed screens only (Measuring, T3b.1d; the Hub sheet, T1.4 A0);
  - axes: the 16 Oct six (redundancy, customization, taps, glance, mental load, consistency), Harmony, Hierarchy and a
    settings burden; Redundancy leads; Taps 2, Consistency 2, the rest 1.
  Shortcuts on Today are not redundancy (owner, 2026-10-16): Today is not varied.

The repeats, each a dimension:
  strip       Measuring's running strip: kept / a doorway ("2 running ›") / removed (the rows' own ■) / the person's choice
  row_amount  Measuring's row says "last" (approved) / today's amount and last
  row_goal    Measuring's row goal line (approved, T3b.5c): shown / the person's choice (shown by default) / removed
  review      Review's day: the item's sessions kept (editable) / a doorway line per item / removed
  week        This week: the items' charts kept / totals with doorways / removed
  saved       Saved charts (comparing items): kept / removed
  shortcut    the Hub's Pinned and recent: kept (approved) / pins only / the person's choice / dropped (Today is the board)

Measured from the drawings (headless Edge, the kept-open browser): the walk's taps (with a scroll for a target below the
fold and a tap for a folded label), what reads without opening anything, the numbers on Measuring's first screen,
Harmony (as T3b.7d) and Hierarchy on Measuring and the Hub. Counted from the variant (rules, flagged): redundancy (a kept
repeat 1, a doorway 0.5, a choice its default), customization (things the person can set), the settings burden (a
setting per item 1.5, one for the app 1), consistency (a doorway reads unlike its thing: 1), mental load's places.
Hierarchy here (HAND-SET, flagged): a screen's own function outranks a repeat of another screen's thing; so a repeat
drawn above the screen's own rows is an inversion, and the share of the screen's own rows on the first screen counts.

The walk (from Today; the constant Hub-Measuring hops left out):
  pause   pause a running timer from Measuring        amount  read Water's amount today from Measuring
  goal    read Water's goal progress from Measuring    edit    edit yesterday's Reading session from Review's day
  week    this week's Reading total                     compare Reading against Language practice this month
  recent  reach Language practice, used yesterday, not pinned (folded under its label: a tap to open it)
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SPACE = {"strip": ["keep", "doorway", "remove", "choice"], "row_amount": ["last", "today_last"], "row_goal": ["shown", "choice", "removed"],
         "review": ["keep", "doorway", "remove"], "week": ["charts", "doorways", "remove"], "saved": ["keep", "remove"],
         "shortcut": ["pin_recent", "pin_only", "pin_choice", "no_hub_list"]}
SPACE3 = {k: SPACE[k] for k in ("strip", "row_amount", "row_goal", "shortcut")}   # T3b.6c: Review one screen
REDUNDANCY = {"strip": {"keep": 1, "doorway": 0.5, "remove": 0, "choice": 1}, "row_amount": {"last": 0, "today_last": 1},
              "row_goal": {"shown": 1, "choice": 1, "removed": 0}, "review": {"keep": 1, "doorway": 0.5, "remove": 0},
              "week": {"charts": 1, "doorways": 0.5, "remove": 0}, "saved": {"keep": 1, "remove": 0},
              # the Hub's pins repeat Today's (0.5); its Recent repeats Measuring's most-used-first order (1)
              "shortcut": {"pin_recent": 1.5, "pin_only": 0.5, "pin_choice": 1.5, "no_hub_list": 0}}
GOALS = {"Water": "3 of 8 glasses today", "Reading": "25 of 30 min today"}   # the items' own amounts today
LOCK = threading.Lock()
_CACHE = {}


_KEY_LOCKS = {}


def _memo(key, make):
    """Each screen measured once: a second thread asking for the same key waits for the first (two threads drawing one
    variant raced for its screenshot file, 2026-10-18)."""
    with LOCK:
        kl = _KEY_LOCKS.setdefault(key, threading.Lock())
    with kl:
        if key not in _CACHE:
            _CACHE[key] = make()
        return _CACHE[key]


def register(ns):
    T, kit, e = ns["T"], ns["kit"], ns["e"]
    G = ns["t3_graphs"]
    import hub_opt
    import tier_t1 as t1

    mv = dict(T.PICKED["measure3"][0])
    ITEMS = ns["ITEMS3_12"]

    # ==== Measuring ===============================================================================================================
    def meas_items(v):
        out = []
        for it in ITEMS:
            it = dict(it)
            g = GOALS.get(it["n"])
            if g and v["row_goal"] != "removed":
                it["last"] = g   # the approved goal line takes the row's sub-line ("drop" layout, T3b.5c)
            out.append(it)
        return out

    def meas_phone(v, control=False):
        mv2 = dict(mv, says="today_last" if (control or v["row_amount"] == "today_last") else "last",
                   running="place" if (not control and v["strip"] in ("remove", "doorway")) else "strip")
        html = ns["measure3_phone"](mv2, meas_items(v if not control else dict(v, row_goal="shown")))
        n_run = sum(1 for it in ITEMS if it["running"])
        if not control and v["strip"] == "doorway":
            line = ('<div class="astrip" data-rep="strip"><div class="sr" data-tap="Running"><span class="t">%d running</span>'
                    '<span style="min-width:48px;min-height:48px;display:grid;place-items:center">›</span></div></div>') % n_run
            html = html.replace('<div class="zone">', '<div class="zone">' + line, 1)
        else:
            html = html.replace('<div class="astrip">', '<div class="astrip" data-rep="strip">', 1)
        if control:   # Chronicle's dashboard over the list: every item's progress again, a streak and a percent
            dash = '<div class="astrip" data-rep="dash"><div class="sr"><span class="t">Today 64% · streak 12 · 7 of 11 goals</span></div></div>'
            html = html.replace('<div class="zone">', '<div class="zone">' + dash, 1)
        if v.get("review") == "one":   # Review's glyph in Measuring's header (T3c.1)
            html = html.replace('<span class="ttl">Measuring</span>', '<span class="ttl">Measuring</span>' + kit.icon_button("\u2197", "Review"), 1)
        return html

    MEAS_JS = r"""(function(){var bar=document.querySelector('.bar').getBoundingClientRect().top;var o={fold:Math.round(bar),rows:{},reps:[],first_row:null,nums:0,rows_seen:0,rows_all:0};
document.querySelectorAll('[data-tr]').forEach(function(r){var b=r.getBoundingClientRect();var n=r.getAttribute('data-tr');o.rows_all++;if(b.bottom<=bar)o.rows_seen++;
 if(o.first_row==null||b.top<o.first_row)o.first_row=Math.round(b.top);if(!o.rows[n]){var st=r.querySelector('[data-tap^="Stop"]');var s=r.querySelector('.bsub');
 o.rows[n]={top:Math.round(b.top),bottom:Math.round(b.bottom),sub:s?s.textContent:''}}});
document.querySelectorAll('[data-rep]').forEach(function(x){var b=x.getBoundingClientRect();if(b.height>0)o.reps.push({k:x.getAttribute('data-rep'),top:Math.round(b.top),bottom:Math.round(b.bottom)})});
var st=[].slice.call(document.querySelectorAll('[data-rep] [data-tap^="Stop"]'));o.strip_stop=st.length?Math.round(st[0].getBoundingClientRect().bottom):null;
var txt='';var w=document.createTreeWalker(document.querySelector('.zone'),NodeFilter.SHOW_TEXT);while(w.nextNode()){var p=w.currentNode.parentElement.getBoundingClientRect();if(p.bottom<=bar)txt+=' '+w.currentNode.textContent}
o.nums=(txt.match(/\d+([.,:]\d+)?/g)||[]).length;return o})()"""
    HARM_JS = G.HARMONY_JS.replace("'[data-row=box],.ipr,.ipt,.ipn,.seg'", "'[data-row=box],.krow,.sr,.fhead'")

    def harmony(d, key):
        h = T.probe(d, key + "-h", HARM_JS)
        hb_, vb_, _ = G.ip5_balance(d, key, h, None)
        fold_area = 360.0 * max(1, h["content"][1] - h["content"][0])
        return {"asym": h["asym"] / fold_area, "balance_h": hb_, "balance_v": vb_,
                "rhythm": len(set(h["gaps"])) + sum(1 for g in h["gaps"] if g % 4), "edges": h["lefts"] + h["rights"] - 2}

    def meas_measure(v, control=False):
        key = "w2-meas-" + ("control" if control else "%s-%s-%s" % (v["strip"], v["row_amount"], v["row_goal"])) + ("-rv" if v.get("review") == "one" else "")

        def make():
            d = ns["m3doc"](meas_phone(v, control))
            m = T.probe(d, key, MEAS_JS)
            m["harm"] = harmony(d, key)
            m["small"] = sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for x in T.taps(d).all if x.get("seen") and (x["w"] < 48 or x["h"] < 48)
                                 and x["name"] in ("Running",)})
            return m
        return _memo(key, make)

    # ==== the Hub sheet (T1.4 A0) ================================================================================================
    def hub_groups(v, control=False):
        out = []
        for name, glyph, feats in hub_opt.NOAPP:
            if v.get("saved") == "review" and name == "Review":   # the card keeps one entry, Review (T3c.1)
                out.append((name, glyph, ["Review"]))
                continue
            fs = []
            for f in feats:
                if f in ("Trackers", "Activities"):
                    if "Measuring" not in fs:
                        fs.append("Measuring")   # one Measuring entry (T3b.6, 2026-10-16)
                    continue
                if f == "Charts" and ((not control and v["saved"] == "remove") or v.get("saved") == "review"):
                    continue
                fs.append(f)
            out.append((name, glyph, fs))
        return out

    def hub_phone(v, control=False):
        sc = "pin_recent" if control else v["shortcut"]
        body = "".join(t1.card(*g) for g in hub_groups(v, control))
        html = hub_opt.phone(body, pinned=sc != "no_hub_list")
        if sc == "pin_only":
            html = html.replace("Pinned and recent</div>", "Pinned</div>", 1)
            html = html.replace(t1.feat(t1.RECENT[0]), "", 1).replace(t1.feat(t1.RECENT[1]), "", 1)
        if control:   # Chronicle's Frequent beside the pins and recent
            html = html.replace('<div class="subl">Pinned and recent</div>', '<div class="subl">Frequent</div><div class="ft" style="margin-bottom:4px">%s</div>'
                                '<div class="subl">Pinned and recent</div>' % "".join(t1.feat(f) for f in ("Water", "Reading", "Coffee")), 1)
        html = html.replace('data-tap="Trackers">Trackers', 'data-tap="Measuring">Measuring')   # one Measuring entry
        return html.replace('<div class="subl">', '<div class="subl" data-rep="shortcut">', 1)

    HUB_JS = r"""(function(){var s=document.querySelector('.hubsheet').getBoundingClientRect(),bar=document.querySelector('.bar').getBoundingClientRect().top;
var o={sheet:[s.left,s.top,s.width,Math.min(s.bottom,bar)-s.top],taps:{},rep_top:null,card_top:null,gaps:[],lefts:{},rights:{},asym:0};
document.querySelectorAll('.hubsheet [data-tap]').forEach(function(x){var b=x.getBoundingClientRect();if(!o.taps[x.getAttribute('data-tap')])o.taps[x.getAttribute('data-tap')]=[Math.round(b.top),Math.round(b.bottom),b.bottom<=bar?1:0]});
var r=document.querySelector('.hubsheet [data-rep]');if(r)o.rep_top=Math.round(r.getBoundingClientRect().top);var c=document.querySelector('.hubsheet .card');if(c)o.card_top=Math.round(c.getBoundingClientRect().top);
var kids=[].slice.call(document.querySelector('.hubsheet').children).map(function(k){return k.getBoundingClientRect()}).filter(function(b){return b.height>0&&b.top<bar});
for(var i=1;i<kids.length;i++)o.gaps.push(Math.round(kids[i].top-kids[i-1].bottom));kids.forEach(function(b){o.lefts[Math.round(b.left/2)*2]=1;o.rights[Math.round(b.right/2)*2]=1});
document.querySelectorAll('.hubsheet .ft').forEach(function(f){var b=f.getBoundingClientRect();if(b.top>=bar||!b.height)return;var L=1e9,R=-1e9;[].slice.call(f.children).forEach(function(x){var q=x.getBoundingClientRect();L=Math.min(L,q.left);R=Math.max(R,q.right)});
 if(L<R){var d=Math.abs((L-b.left)-(b.right-R));if(d>8)o.asym+=(d-8)*b.height}});
o.lefts=Object.keys(o.lefts).length;o.rights=Object.keys(o.rights).length;return o})()"""

    def hub_measure(v, control=False):
        key = "w2-hub-" + ("control" if control else "%s-%s" % (v["shortcut"], v["saved"])) + ("-rv" if v.get("review") == "one" else "")

        def make():
            d = hub_opt.doc(hub_phone(v, control), "light", False)
            m = T.probe(d, key, HUB_JS)
            import headless_browser as hb
            from PIL import Image
            png = os.path.join(HERE, "..", "..", "_screens-sources", "t3", "harmony-shots", key + ".png")
            os.makedirs(os.path.dirname(png), exist_ok=True)
            hb.screenshot(d, png, 660, 1040)
            x, y, w, h = m["sheet"]
            im = Image.open(png).convert("L").crop((int(x), int(y), int(x + w), int(y + h)))
            os.remove(png)
            px = im.load()
            W_, H_ = im.size
            hist = im.histogram()
            ground = max(range(256), key=lambda i: hist[i])
            lft = rgt = up = lo = 0.0
            for j in range(0, H_, 2):
                for i in range(0, W_, 2):
                    a = abs(px[i, j] - ground) / 255.0
                    if a < 0.04:
                        continue
                    if i < W_ / 2:
                        lft += a
                    else:
                        rgt += a
                    if j < H_ / 2:
                        up += a
                    else:
                        lo += a
            tot = (lft + rgt) or 1
            m["harm"] = {"asym": m["asym"] / (360.0 * max(1, h)), "balance_h": abs(lft / tot - 0.5), "balance_v": abs(up / tot - 0.5),
                         "rhythm": len(set(m["gaps"])) + sum(1 for g in m["gaps"] if g % 4), "edges": m["lefts"] + m["rights"] - 2}
            return m
        return _memo(key, make)

    # ==== the minimal frames (T3c later): Review's day, This week, Saved charts =========================================================
    def frame(title, rows, nav="Hub"):
        body = '<div class="zone">%s</div>' % "".join(
            '<div class="prow2"%s><span class="t">%s</span>%s</div>' % (' data-tap="%s"' % tap if tap else "", e(a), e(b)) for a, b, tap in rows)
        return kit.phone(kit.header(title, (), ("‹", "Back")), body, kit.bar(nav))

    def review_phone(v, control=False):
        r = "keep" if control else v["review"]
        rows = [("Habits", "4 of 6 done", None), ("Journal", "1 entry", None)]
        if r == "keep":
            rows += [("Reading 21:00–21:30", "30 min", "Session Reading"), ("Reading +15 min", "15 min", "Session Reading 2"), ("Walk 07:40", "done", "Session Walk")]
        elif r == "doorway":
            rows += [("Reading · 2 sessions", "›", "Open Reading"), ("Walk · done", "›", "Open Walk")]
        return frame("Review · Thursday", rows)

    def week_phone(v, control=False):
        wk = "charts" if control else v["week"]
        rows = [("Habits", "29 of 42", None), ("Check-ins", "6", None)]
        if wk == "charts":
            rows += [("Reading ▁▃▅▂▆▃▅", "3 h 10", "Chart Reading"), ("Water ▅▆▃▇▅▆▄", "41 glasses", "Chart Water"), ("Walk ■■□■■□■", "5 days", "Chart Walk")]
        elif wk == "doorways":
            rows += [("Reading · 3 h 10", "›", "Open Reading"), ("Water · 41 glasses", "›", "Open Water"), ("Walk · 5 days", "›", "Open Walk")]
        if control:
            rows += [("Reading · 3 h 10", "›", "Open Reading")]
        return frame("This week", rows)

    def saved_phone(v, control=False):
        if not control and v["saved"] == "remove":
            return frame("Saved charts", [("(not in the app)", "", None)])
        return frame("Saved charts", [("Reading against Language practice, this month", "›", "Chart compare"), ("Water by weekday", "›", "Chart water")])

    # ==== the score ==================================================================================================================
    def walk(v, M, Hb, control=False):
        """The walk's taps, from the measured positions (a scroll for a target below the fold)."""
        fold = M["fold"]
        reach = lambda bottom: 0 if bottom is None or bottom <= fold else 1
        strip = "keep" if control else v["strip"]
        run_row = M["rows"].get("Work") or M["rows"].get("Cleaning")
        if strip in ("keep", "choice") or control:
            pause = 1 + reach(M["strip_stop"])
        elif strip == "doorway":
            pause = 2
        else:
            pause = 1 + reach(run_row["bottom"] if run_row else None)
        water = M["rows"].get("Water")
        wreach = reach(water["bottom"] if water else None)
        amount = (0 if (control or v["row_amount"] == "today_last") else 1) + wreach
        goal = (0 if (control or v["row_goal"] != "removed") else 1) + wreach
        if v.get("review") == "one":   # T3b.6c: Review is one screen, the same for every option: these three cost the same
            edit = week = compare = 0
        else:
            rv = "keep" if control else v["review"]
            edit = {"keep": 1, "doorway": 3, "remove": 5}[rv]
            wk = "charts" if control else v["week"]
            week = {"charts": 2, "doorways": 2, "remove": 4}[wk]
            sv = "keep" if control else v["saved"]
            charts_seen = (Hb["taps"].get("Charts") or [0, 0, 0])[2]
            compare = (2 + (0 if charts_seen else 1) + 1) if sv == "keep" else 5   # Hub, Charts, the chart; or both pages read one by one
        sc = "pin_recent" if control else v["shortcut"]
        lang = M["rows"].get("Language practice")   # used yesterday, not pinned, in a label folded under the open top
        recent = 2 if sc in ("pin_recent", "pin_choice") else 3 + reach(lang["bottom"] if lang else None) + 1
        return {"pause": pause, "amount": amount, "goal": goal, "edit": edit, "week": week, "compare": compare, "recent": recent}

    def score(v):
        ctl = v.get("control")
        M = meas_measure(v, ctl)
        Hb = hub_measure(v, ctl)
        w = walk(v, M, Hb, ctl)
        one = v.get("review") == "one"
        space = SPACE3 if one else SPACE
        if ctl:
            red = sum(max(REDUNDANCY[k].values()) for k in space) + 2   # Chronicle's dashboard and Frequent: two more copies
            cust, burden, cons, choice_n = 0, 0, 0, 0
        else:
            red = sum(REDUNDANCY[k][v[k]] for k in space)
            choice_n = (v["strip"] == "choice") + (v["row_goal"] == "choice") + (v["shortcut"] == "pin_choice")
            cust = choice_n
            burden = (v["strip"] == "choice") * 1 + (v["row_goal"] == "choice") * 1.5 + (v["shortcut"] == "pin_choice") * 1
            cons = (v["strip"] == "doorway") + (0 if one else (v["review"] == "doorway") + (v["week"] == "doorways"))
        glance = 0
        water = M["rows"].get("Water")
        if water and water["bottom"] <= M["fold"]:
            glance += (1 if (ctl or v["row_amount"] == "today_last") else 0) + (1 if (ctl or v["row_goal"] != "removed") else 0)
        if M["strip_stop"] is not None and M["strip_stop"] <= M["fold"]:
            glance += 1
        places = 1 + red   # the page, and every kept copy
        load = places + M["nums"] / 10 + (1 if (not ctl and not one and v["saved"] == "remove") else 0)   # holding one item's number to compare
        # Hierarchy (flagged): a repeat drawn above the screen's own rows or cards; the screen's own rows on its first screen
        inv = sum(1 for r in M["reps"] if M["first_row"] is not None and r["top"] < M["first_row"])
        inv += 1 if (Hb["rep_top"] is not None and Hb["card_top"] is not None and Hb["rep_top"] < Hb["card_top"]) else 0
        own = M["rows_seen"] / max(1, M["rows_all"])
        hm, hh = M["harm"], Hb["harm"]
        return {"redundancy": red, "custom": cust, "burden": burden, "taps": sum(w.values()), "walk": w, "glance": glance,
                "load": round(load, 2), "inconsistent": cons, "rep_above": inv, "own_rows": round(own, 3),
                "asym": round(hm["asym"] + hh["asym"], 4), "balance_h": round(hm["balance_h"] + hh["balance_h"], 3),
                "balance_v": round(hm["balance_v"] + hh["balance_v"], 3), "rhythm": hm["rhythm"] + hh["rhythm"], "edges": hm["edges"] + hh["edges"],
                "small": M["small"]}

    def draw(v):
        ctl = v.get("control")
        return [ns["m3doc"](meas_phone(v, ctl)), hub_opt.doc(hub_phone(v, ctl), "light", False),
                ns["gdoc"](review_phone(v, ctl)), ns["gdoc"](week_phone(v, ctl)), ns["gdoc"](saved_phone(v, ctl))]

    part = "where2"
    T.SPACES[part] = SPACE
    T.SCORERS[part] = score
    T.VALID[part] = lambda v: True
    T.CONTROLS[part] = [({k: "merged" for k in SPACE} | {"control": True},
                         "the source apps merged as they come: every repeat kept, Chronicle's dashboard over Measuring and its Frequent list on the Hub, This week's charts and totals both")]
    T.TITLES[part] = "T3b.6b One home per thing, settled against the item's page: Measuring's strip and row, Review's day, This week, Saved charts, the Hub's lists"
    T.DRAW[part] = draw
    T.POOL[part] = lambda ok: ([r for r in ok if r.get("front")] +
                               [min((r for r in ok if not r["v"].get("control") and r["v"][k] == x), key=lambda r: r["total"]) for k in SPACE for x in SPACE[k]])
    T.DRAW_MAX[part] = 14
    T.AXES[part] = {"Redundancy": ("redundancy",), "Customization": ("-custom",), "Settings burden": ("burden",), "Taps": ("taps",),
                    "Glance": ("-glance",), "Mental load": ("load",), "Consistency": ("inconsistent",),
                    "Harmony": ("asym", "balance_h", "balance_v", "rhythm", "edges"), "Hierarchy": ("rep_above", "-own_rows")}
    T.WEIGHTS[part] = {"Taps": 2, "Consistency": 2}
    T.LEAD[part] = [("redundancy", 1)]   # HAND-SET: within one kept repeat of the least redundant (owner: Redundancy leads)
    T.REFS_INFO.add(part)
    T.SUPERSEDED["where"] = "settled against the item's page, drawn and measured (owner, 2026-10-18): T3b.6b replaced it"

    # ==== T3b.6c: the same, with Review one screen (T3c.1, owner 2026-10-22) ==========================================================
    # Review's day, This week and Saved charts became one screen, Review (reached from Measuring's header and the Hub's Review
    # card): those three dimensions are fixed, their walk tasks cost the same for every option, and the drawings carry
    # Review's glyph on Measuring and the one-entry Review card on the Hub. The four repeats left are scored as before.
    fill = lambda v: dict(v, review="one", week="review", saved="review")
    part = "where3"
    T.SPACES[part] = SPACE3
    T.SCORERS[part] = lambda v: score(fill(v))
    T.VALID[part] = lambda v: True
    T.CONTROLS[part] = [({k: "merged" for k in SPACE3} | {"control": True},
                         "the source apps merged as they come: every repeat kept, Chronicle's dashboard over Measuring and its Frequent list on the Hub")]
    T.TITLES[part] = "T3b.6c One home per thing, with Review one screen: Measuring's running strip, the row's amount and goal line, the Hub's lists"
    T.DRAW[part] = lambda v: [ns["m3doc"](meas_phone(fill(v), v.get("control"))), hub_opt.doc(hub_phone(fill(v), v.get("control")), "light", False)]
    T.POOL[part] = lambda ok: ([r for r in ok if r.get("front")] +
                               [min((r for r in ok if not r["v"].get("control") and r["v"][k] == x), key=lambda r: r["total"]) for k in SPACE3 for x in SPACE3[k]])
    T.DRAW_MAX[part] = 14
    T.AXES[part] = dict(T.AXES["where2"])
    T.WEIGHTS[part] = {"Taps": 2, "Consistency": 2}
    T.LEAD[part] = [("redundancy", 1)]
    T.REFS_INFO.add(part)
    T.SUPERSEDED["where2"] = "Review became one screen (T3c.1): its Review's day, This week and Saved charts dimensions are moot; T3b.6c re-scored the rest"
