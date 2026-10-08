"""T1.6 round 4 (owner, 2026-10-08): the sentence sheet made tidy and not redundant.

The owner's review of round 3's B: the presets and a unit chooser repeated the same options, an "every [n]" row
repeated the sentence, and the monthly chooser drew "day 16" and "3rd Friday" together when a monthly rule is one or
the other. Owner's design and answers:
  chips      presets Day, Week, Month, Year; additional Minutes, Hours, Weekdays, Weekend. They set the unit; the
             sentence's words edit the rest. Layouts scored: block (all 8, two rows of four), more (4 + "More"),
             rows (two labelled rows), swapA and swapB (the 4 presets on top; tapping the sentence swaps in the
             additional 4, above the sentence or below it)
  number     tapping the unit word ("Every [2 weeks]") changes the number: inline (typed in place), stepper (− n +),
             quick (chips of common values, "Other" typed)
  month day  a switch first, Day of the month | Weekday of the month, then only that picker: grid (1-31 and Last),
             typed (a number, and Last day), list (rows); the weekday of the month is 1st-4th, Last, then Mo-Su
  random     Random and After done: words (a tappable qualifier "[exactly]" → at random / after it's done), chips
             (two more additional chips), typed (on the capture line and the full page only)
  time       "at [09:00]": typed (a field with suggestions, "+ time", "Random time") or dialtyped (T1.5's dial and
             field); minutes and hours read "from [09:00] to [21:00]"
  ends       "[forever]": chips (Never, After n, Until), list (rows), typed ("6 times", "until 31 Dec")
  cron line  readonly, toggle ("as cron"), mirror (an editable field), tapedit (read only until tapped, then edited in
             place, not another sheet); blank when cron cannot express the rule
  container  sheet, page
The sheet opens with nothing repeating ("Does not repeat"): the chips are the presets.

Stage 1 scores the opening (chips × random × cron × container) with the choosers at a default (number inline, month
day grid, time typed, ends chips); stage 2 scores the 54 chooser combinations on stage 1's best sheet and page.
Axes as round 3, less the ones that no longer separate: harmony, ease, clutter, density, rules in the sheet,
distance from the references. Legibility is fixed by the type rule (Major Second: sentence 17.5, small 12.5 px).
Without cron only T10 is lost (the OR rule; the owner: a monthly rule is the day or the weekday, not both).

    PYTHONUTF8=1 python tools/screens/repeat4_opt.py stage1|stage2|page [--workers 4]
"""
import concurrent.futures
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import picker_opt as P  # noqa: E402
import repeat3_opt as Q  # noqa: E402
import repeat_opt as R  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

ch, b, field, row = R.ch, R.b, R.field, R.row
STAGE1 = {"chips": ["block", "more", "rows", "swapA", "swapB"], "random": ["words", "chips", "typed"], "cron": ["readonly", "toggle", "mirror", "tapedit"],
          "container": ["sheet", "page"]}
STAGE2 = {"number": ["inline", "stepper", "quick"], "monthday": ["grid", "typed", "list"], "time": ["typed", "dialtyped"], "ends": ["chips", "list", "typed"]}
DEFAULTS = {"number": "inline", "monthday": "grid", "time": "typed", "ends": "chips"}
PRESET4 = ["Day", "Week", "Month", "Year"]
EXTRA4 = ["Minutes", "Hours", "Weekdays", "Weekend"]
QUICK = {"day": [1, 2, 3, 4, 5, 6], "week": [1, 2, 3, 4, 6, 8], "month": [1, 2, 3, 4, 6, 12], "year": [1, 2, 3, 5],
         "minutes": [5, 10, 15, 30, 45, 60, 90], "hours": [1, 2, 3, 4, 6, 8, 12]}
FIELDS = {"Num field", "Num2 field", "Dom field", "Time field", "From field", "To field", "End field", "Cron field", "Cron line", "Tok cron"}
CSS = R.CSS + Q.type_css("MS-xl") + """
.pk .sent .tok.nf{display:inline-flex;width:auto;padding:0 10px;box-shadow:inset 0 0 0 1px var(--zone2);border-radius:10px;font-weight:600}
.pk .lst .prow{min-height:48px;display:flex;align-items:center;font-size:15px;border-bottom:1px solid var(--zone2)}
.pk .lst{max-height:192px;overflow:hidden}
.pk .dg{display:grid;grid-template-columns:repeat(7,1fr);margin:0 -12px}.pk .dg .tg{min-width:0}
.pk .rl{font-size:12.5px;color:var(--dim);font-weight:600;min-height:20px;display:flex;align-items:flex-end}
"""

# ---- the rule's sentence ---------------------------------------------------------------------------------------
UNIT_WORD = {"day": "day", "week": "week", "month": "month", "year": "year", "minutes": "30 minutes", "hours": "2 hours", "weekdays": "weekday",
             "weekend": "weekend day", "random": "1–3 days", "done": "1 day"}


def tok(name, text, inline_field=False):
    if inline_field:
        return '<span class="tok nf" data-tap="%s">%s</span>' % (name, text)
    return '<span class="tok" data-tap="%s"><b>%s</b></span>' % (name, text)


def sentence(v, rule, chooser):
    if rule == "none":
        words = tok("Tok sentence", "Does not repeat") if v["chips"] in ("swapA", "swapB") else "Does not repeat"
        return '<div class="sent">%s</div>' % words
    inline = v["number"] == "inline" and chooser == "num"
    unit = tok("Tok unit", "2" if inline else UNIT_WORD[rule], inline)
    qual = (" " + tok("Tok qual", {"random": "at random", "done": "exactly"}.get(rule, "exactly")) + ",") if v["random"] == "words" and rule in ("day", "week", "random") else ""
    at = "at " + tok("Tok at", "a random time" if chooser == "atrand" else "09:00")
    if rule in ("minutes", "hours"):
        when = "from " + tok("Tok from", "09:00") + " to " + tok("Tok to", "21:00")
    else:
        when = at
    on = {"week": " on " + tok("Tok on", "Fri"), "month": " on " + tok("Tok on", "day 16"), "year": " on " + tok("Tok on", "16 Oct")}.get(rule, "")
    if rule == "done":
        head = tok("Tok unit", "1 day", inline) + " after it is done,"
    else:
        head = "Every " + unit + qual + on
    end = tok("Tok end", "forever")
    cron = " " + tok("Tok cron", "as cron") if v["cron"] == "toggle" else ""
    return '<div class="sent">%s %s, %s%s</div>' % (head, when, end, cron)


def chips_html(v, rule, chooser):
    extra = EXTRA4 + (["Random", "After done"] if v["random"] == "chips" else [])
    sel = {"day": "Day", "week": "Week", "month": "Month", "year": "Year", "minutes": "Minutes", "hours": "Hours", "weekdays": "Weekdays", "weekend": "Weekend",
           "random": "Random", "done": "After done"}.get(rule)
    mk = lambda names: "".join(ch("Chip %s" % n, n, n == sel) for n in names)
    c = v["chips"]
    if c == "block":
        return '<div class="row">%s</div>' % mk(PRESET4 + extra), ""
    if c == "rows":
        return '<div class="rl">Repeats</div><div class="row">%s</div><div class="rl">Also</div><div class="row">%s</div>' % (mk(PRESET4), mk(extra)), ""
    if c == "more":
        if chooser == "more":
            return '<div class="row">%s</div>' % (mk(PRESET4) + mk(extra)), ""
        return '<div class="row">%s%s</div>' % (mk(PRESET4), b("Chip More", "More ▾")), ""
    # swap: the 4 presets on top; the sentence tapped swaps in the additional ones, above it or below it
    if chooser == "more":
        return ('<div class="row">%s</div>' % mk(extra), "") if c == "swapA" else ("", '<div class="row">%s</div>' % mk(extra))
    return '<div class="row">%s</div>' % mk(PRESET4), ""


def time_chooser(v, which="Time"):
    sug = ch("Sug 09:00", "09:00") + ch("Sug 21:00", "21:00")
    head = row(field("%s field" % which if which != "Time" else "Time field", "21:00" if which == "To" else "09:00", "tf"), sug)
    extra = row(b("Add time", "+ time"), ch("Random time", "Random time")) if which == "Time" else ""
    if v["time"] == "dialtyped":
        spots = "".join('<span data-tap="Hour %d" style="left:%.0fpx;top:%.0fpx">%d</span>' % (
            h, 116 + 92 * math.sin(math.radians(h * 30)), 116 - 92 * math.cos(math.radians(h * 30)), h) for h in range(12))
        return head + '<div class="dial">%s</div>' % spots + extra
    return head + extra


def chooser_html(v, rule, chooser):
    n = v["number"]
    if chooser == "num":
        if rule in ("random",):
            if n == "stepper":
                return row(b("Num minus", "−"), '<span class="txt">1</span>', b("Num plus", "+"), '<span class="txt">to</span>', b("Num2 minus", "−"), '<span class="txt">3</span>', b("Num2 plus", "+"))
            return row(field("Num field", "1"), '<span class="txt">to</span>', field("Num2 field", "3"), '<span class="txt">days</span>')
        if n == "inline":
            return ""
        if n == "stepper":
            return row(b("Num minus", "−"), '<span class="txt">%s</span>' % UNIT_WORD.get(rule, "1"), b("Num plus", "+"))
        vals = QUICK.get(rule if rule in QUICK else "day", QUICK["day"])
        return '<div class="row">%s%s</div>' % ("".join(ch("Q %d" % x, str(x)) for x in vals), field("Num field", "…"))
    if chooser == "on":
        return R.weekdays({"Fri"}, "Wd")
    if chooser in ("dom", "wom"):
        seg = '<div class="seg">%s%s</div>' % (ch("Dom switch", "Day of the month", chooser == "dom"), ch("Wom switch", "Weekday of the month", chooser == "wom"))
        if chooser == "wom":
            return seg + row(*[ch("Ord %s" % o, o, o == "3rd") for o in ("1st", "2nd", "3rd", "4th", "Last")]) + R.weekdays({"Fri"}, "Ow")
        if v["monthday"] == "grid":
            return seg + '<div class="dg">%s%s</div>' % ("".join(ch("Dom %d" % d, str(d), d == 16) for d in range(1, 32)), ch("Dom Last", "Last"))
        if v["monthday"] == "typed":
            return seg + row(field("Dom field", "16"), ch("Dom Last", "Last day"))
        return seg + '<div class="lst">%s</div>' % ('<div class="prow" data-tap="Dom Last">Last day</div>' + "".join('<div class="prow" data-tap="Dom %d">%d</div>' % (d, d) for d in range(1, 32)))
    if chooser in ("at", "atrand"):
        if chooser == "atrand":
            return row(field("From field", "09:00", "tf"), '<span class="txt">to</span>', field("To field", "21:00", "tf"), label="Between") + row(ch("Random time", "Random time", True))
        return time_chooser(v)
    if chooser in ("to", "from"):
        return time_chooser(v, "To" if chooser == "to" else "From")
    if chooser == "end":
        e = v["ends"]
        if e == "chips":
            return row(ch("End never", "Never", True), ch("End after", "After"), field("End field", "6"), ch("End until", "Until…"))
        if e == "list":
            return '<div class="plist"><div class="prow" data-tap="End never">Never</div><div class="prow" data-tap="End after">After a number of times</div><div class="prow" data-tap="End until">Until a date</div></div>'
        return row(field("End field", "6 times, or until 31 Dec", "field"))
    if chooser == "qual":
        return row(ch("Qual exactly", "Exactly", True), ch("Qual random", "At random"), ch("Qual done", "After it is done"))
    if chooser == "endafter":
        return row(ch("End never", "Never"), ch("End after", "After", True), field("End field", "6"), '<span class="txt">times</span>')
    return ""


def cron_html(v, rule, chooser):
    expressible = rule not in ("random", "done", "none") and not (rule == "week" and chooser == "num")
    # the rule's own cron (the measures ran with "0 9 * * 5" in every view, the same length to within a few characters)
    expr = {"day": "0 9 * * *", "week": "0 9 * * 5", "month": "0 9 16 * *", "year": "0 9 16 10 *", "minutes": "*/30 9-20 * * *",
            "hours": "0 9-21/2 * * *", "weekdays": "0 9 * * 1-5", "weekend": "0 9 * * 0,6"}.get(rule, "0 9 * * 5")
    line = "As cron: " + expr if expressible else ""
    c = v["cron"]
    if c == "readonly":
        return '<div class="calc">%s</div>' % line if line else ""
    if c == "mirror":
        return row(field("Cron field", "0 9 * * 5" if line else "", "field"), label="Cron")
    if c == "tapedit":
        if chooser == "cronedit":
            return row(field("Cron field", "0 9 * * 5", "field"))
        return '<div class="calc" data-tap="Cron line" style="min-height:48px;display:flex;align-items:center">%s</div>' % (line or "As cron: none")
    return ""  # toggle: "as cron" is a word of the sentence


def body(v, state):
    rule, chooser = state.split("|")
    if v["cron"] == "toggle" and chooser == "ascron":
        return (R.header(v) + row(field("Cron field", "0 9 * * 5", "field")) + '<div class="calc">Every week on Fri at 09:00</div>'
                + '<div class="row">%s</div>' % b("Tok words", "‹ as words") + R.preview_sec("words", "Next"))
    top, below = chips_html(v, rule, chooser)
    nxt = R.preview_sec("words", "Next") if rule != "none" else ""
    return R.header(v) + top + sentence(v, rule, chooser) + below + chooser_html(v, rule, chooser) + cron_html(v, rule, chooser) + nxt


def phone(v, state, kb=False):
    orig = R.body
    try:
        R.body = lambda _v, s: body(v, s)
        return R.phone(v, state, kb)
    finally:
        R.body = orig


def doc(v, state, kb=False, theme="light", score=True):
    return kit.document(phone(v, state, kb), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + CSS, score)


# ---- the tasks ----------------------------------------------------------------------------------------------------
def tap(state, *names):
    return [(state, "tap", n) for n in names]


def typ(state, n):
    return [(state, "type", n)]


def pick(v, chip):
    """Reach a chip from the opening: direct, through More, or through the sentence (swap)."""
    if chip in PRESET4 or v["chips"] in ("block", "rows"):
        return tap("none|", "Chip %s" % chip)
    if v["chips"] == "more":
        return tap("none|", "Chip More") + tap("none|more", "Chip %s" % chip)
    return tap("none|", "Tok sentence") + tap("none|more", "Chip %s" % chip)


def number(v, rule, value, frm):
    """Set the unit's number from frm to value, in the number chooser."""
    s = "%s|num" % rule
    if v["number"] == "inline":
        return tap("%s|" % rule, "Tok unit") + typ(s, len(str(value)))
    if v["number"] == "stepper":
        step = {"minutes": 15}.get(rule, 1)
        return tap("%s|" % rule, "Tok unit") + tap(s, *["Num plus"] * ((value - frm) // step))
    if value in QUICK.get(rule, QUICK["day"]):
        return tap("%s|" % rule, "Tok unit") + tap(s, "Q %d" % value)
    return tap("%s|" % rule, "Tok unit") + tap(s, "Num field") + typ(s, len(str(value)))


def set_time(v, rule, chooser, value):
    s = "%s|%s" % (rule, chooser)
    name = {"at": "Time field", "to": "To field", "from": "From field"}[chooser]
    hh, mm = value
    if v["time"] == "dialtyped" and chooser == "at" and hh < 12 and mm == 0:
        return tap(s, "Hour %d" % hh)
    return tap(s, name) + typ(s, 4)


def walk(v):
    T = {}
    T[1] = pick(v, "Weekdays") + tap("weekdays|", "Done")
    T[2] = pick(v, "Week") + number(v, "week", 2, 1) + tap("week|", "Tok on") + tap("week|on", "Wd Tue", "Wd Thu", "Wd Fri", "Done")
    T[3] = pick(v, "Month") + tap("month|", "Tok on") + tap("month|dom", "Wom switch") + tap("month|wom", "Ord 2nd", "Ow Tue", "Done")
    last = tap("month|dom", "Dom Last")
    if v["ends"] == "chips":
        ends = tap("month|", "Tok end") + tap("month|end", "End after", "End field") + typ("month|end", 1)
    elif v["ends"] == "list":
        ends = tap("month|", "Tok end") + tap("month|end", "End after") + tap("month|endafter", "End field") + typ("month|endafter", 1)
    else:
        ends = tap("month|", "Tok end") + tap("month|end", "End field") + typ("month|end", len("6 times"))
    T[4] = pick(v, "Month") + tap("month|", "Tok on") + last + ends + tap("month|end" if v["ends"] != "list" else "month|endafter", "Done")
    T[5] = pick(v, "Day") + tap("day|", "Tok at") + set_time(v, "day", "at", (8, 30)) + tap("day|at", "Add time") + typ("day|at", 4) + tap("day|at", "Done")
    T[6] = pick(v, "Minutes") + number(v, "minutes", 90, 30) + tap("minutes|", "Tok to") + set_time(v, "minutes", "to", (17, 0)) + tap("minutes|to", "Done")
    rng = (tap("random|", "Tok unit") + (tap("random|num", "Num plus", "Num2 plus") if v["number"] == "stepper"
                                         else tap("random|num", "Num field") + typ("random|num", 1) + tap("random|num", "Num2 field") + typ("random|num", 1)))
    if v["random"] == "words":
        T[7] = pick(v, "Day") + tap("day|", "Tok qual") + tap("day|qual", "Qual random") + rng + tap("random|num", "Done")
        T[9] = pick(v, "Day") + tap("day|", "Tok qual") + tap("day|qual", "Qual done") + number(v, "done", 3, 1) + tap("done|num", "Done")
    elif v["random"] == "chips":
        T[7] = pick(v, "Random") + rng + tap("random|num", "Done")
        T[9] = pick(v, "After done") + number(v, "done", 3, 1) + tap("done|num", "Done")
    T[8] = pick(v, "Day") + tap("day|", "Tok at") + tap("day|at", "Random time") + tap("day|atrand", "To field") + typ("day|atrand", 4) + tap("day|atrand", "Done")
    c = v["cron"]
    if c == "toggle":
        T[10] = pick(v, "Week") + tap("week|", "Tok cron") + typ("week|ascron", 9) + tap("week|ascron", "Done")
    elif c == "mirror":
        T[10] = tap("none|", "Cron field") + typ("none|", 9) + tap("none|", "Done")
    elif c == "tapedit":
        T[10] = tap("none|", "Cron line") + typ("none|cronedit", 9) + tap("none|cronedit", "Done")
    return T


OUTSIDE = {7: len("random 2-4 days") + 1, 9: len("3 days after done") + 1, 10: 9 + 1}  # typed on the capture line instead


def score(v):
    T = walk(v)
    states = sorted({s for p in T.values() for s, _, _ in p} | {"none|", "week|"})
    views = {}
    for s in states:
        for kb in (False, True):
            m = ss.measure(doc(v, s, kb), 360, 740)
            views[(s, kb)] = ({x["name"]: x for x in m["taps"]}, m)
    kbnames = FIELDS | {"Tok unit"} if v["number"] == "inline" else FIELDS

    def sim(k, task):
        kb, n, miss, tids = False, 0, set(), []
        for state, kind, x in task:
            if kind == "type":
                n += x
                continue
            seen = lambda kbv: views[(state, kbv)][0].get(x, {}).get("seen")
            if kb and not seen(True):
                if seen(False):
                    n += 1
                    kb = False
                else:
                    miss.add("T%d %s: %s" % (k, state, x))
            elif not kb and not seen(False):
                miss.add("T%d %s: %s" % (k, state, x))
            tp = views[(state, kb)][0].get(x)
            if tp and tp.get("seen"):
                tids.append(math.log2(math.hypot(P.THUMB[0] - tp["x"], P.THUMB[1] - tp["y"]) / min(tp["w"], tp["h"]) + 1))
            n += 1
            if x in kbnames or x.startswith("Cron "):
                kb = True
            if x == "Done" or x.startswith("Chip ") or x.startswith("Q "):
                kb = False
        return n, miss, tids

    actions, ids, unseen, per, outside = 0, [], set(), {}, []
    for k in range(1, 11):
        if k in T:
            n, miss, tids = sim(k, T[k])
            unseen |= miss
            ids += tids
        else:
            n = OUTSIDE[k]
            outside.append(k)
        per[k] = n
        actions += n
    base_t, base_m = views[("week|", False)]  # measured on a set rule (the opening is "Does not repeat")
    pk = base_m["boxes"].get("picker")
    in_pk = [x for x in base_m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen") and not x["name"].startswith("Readout")]
    small = sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for (s, kb), (tp, m) in views.items() if not kb for x in tp.values()
                    if x.get("seen") and not x["name"].startswith("Readout") and (x["w"] < 48 or x["h"] < 48)})
    tallest = max((views[(s, False)][1]["boxes"].get("picker") or [0, 0, 0, 0])[3] for s in states)
    png = ss.render(doc(v, "week|"), 360, 740)
    clutter = sum(ss.edge_density(ss.render(doc(v, "week|", False, th), 360, 740)) for th in ("light", "dark")) / 2
    height = min(740, pk[3]) if pk else 740
    return {"actions": actions, "per_task": per, "outside": outside, "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": len(unseen),
            "unseen_names": sorted(unseen), "small": small, "heights": max(1, len({x[4] for x in base_m["vis"]})), "clutter": round(clutter, 4),
            "covered": 1.0 if v["container"] == "page" else round(height / 740, 3), "tallest": 1.0 if v["container"] == "page" else round(min(740, tallest) / 740, 3),
            "controls": len(in_pk), "crowding": round(len(in_pk) / (height / 100), 2), "heavy": P.masses(png, base_m), "rules_outside": len(outside)}


def full(v):
    r = score(v)
    path = os.path.join(ss.CACHE, "r4-%s.html" % "-".join(str(x) for x in v.values()))
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(doc(v, "week|"))
    import subprocess
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    r["sprawl"] = sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast", "type-sizes")) and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))
    return r


def ref_distance(v, refs):
    f = {"presets_first": False, "unit_control": "chips", "weekday_chips": True, "page": v["container"] == "page", "readout": True, "next_dates": True,
         "modes": v["random"] == "chips"}
    return round(sum(sum(f[k] != ref[k] for k in R.FEATURES) / len(R.FEATURES) for ref in refs) / len(refs), 3)


AXES = {"H": ("heights", "sprawl", "heavy"), "U": ("actions", "reach"), "C": ("clutter", "covered", "tallest", "controls"), "Density": ("crowding",),
        "Rules": ("rules_outside",), "Refs": ("ref_distance",)}


def run(vs, out):
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    rows = []
    with concurrent.futures.ProcessPoolExecutor(workers) as ex:
        for v, r in zip(vs, ex.map(full, vs)):
            rows.append(dict(v=v, **r))
            print(len(rows), v, {k: r[k] for k in ("actions", "unseen", "small", "clutter", "covered", "tallest", "controls", "crowding")}, flush=True)
    with open(R.REFS, encoding="utf-8") as fh:
        refs = json.load(fh)["apps"]
    for r in rows:
        r["ref_distance"] = ref_distance(r["v"], refs)
    ok = [r for r in rows if not r["small"] and r["unseen"] == 0]
    for axis, keys in AXES.items():
        cols = [v2.ranks(ok, k, 1) for k in keys]
        for i, r in enumerate(ok):
            r[axis] = sum(c[i] for c in cols)
    ax = list(AXES)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)]
    with open(os.path.join(v2.OUT, out), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump({"rows": rows, "passed": len(ok), "front": [rows.index(r) for r in front]}, fh, indent=1, ensure_ascii=False)
    print("passed", len(ok), "of", len(rows), "front", len(front))


def stage1():
    run([dict(dict(zip(STAGE1, c)), **DEFAULTS) for c in itertools.product(*STAGE1.values())], "repeat4-stage1.json")


def stage2(bases):
    vs = []
    for base in bases:
        vs += [dict(base, **dict(zip(STAGE2, c))) for c in itertools.product(*STAGE2.values())]
    run(vs, "repeat4-stage2.json")


PAGE_STATES = [
    ("none|", "Opens: nothing repeats yet; the four presets on top"), ("none|more", "The sentence tapped: the four more, under it"),
    ("week|", "Week tapped: the rule reads as a sentence"), ("week|num", "\"week\" tapped: how many weeks (quick values, … types any)"),
    ("week|on", "\"Fri\" tapped: the weekdays"), ("month|", "Month tapped"), ("month|dom", "\"day 16\" tapped: day of the month (typed, or Last day)"),
    ("month|wom", "…or weekday of the month: 1st–4th or Last, then the day"), ("day|", "Day tapped"), ("day|at", "\"09:00\" tapped: the time, + time, Random time"),
    ("day|atrand", "Random time: between two times"), ("day|qual", "\"exactly\" tapped: at random, or after it is done"),
    ("random|num", "At random: every 1 to 3 days"), ("done|num", "After it is done: how many days"), ("minutes|", "Minutes (from the four more)"),
    ("minutes|num", "\"30 minutes\" tapped"), ("minutes|to", "\"21:00\" tapped: the window's end"), ("month|end", "\"forever\" tapped: the end"),
]


def page(v):
    """Every state of the chosen design, so each chooser is seen (round 3's redundancy went unseen in its mockups)."""
    with open(os.path.join(v2.OUT, "repeat4-stage2.json"), encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    r = [x for x in rows if x["v"] == v][0]
    meas = ("Actions over the 10 tasks %d · reach %.2f · clutter %.3f · the tallest view covers %.0f%% · controls on the rule's view %d · "
            "per task %s") % (r["actions"], r["reach"], r["clutter"], 100 * r["tallest"], r["controls"], ", ".join("T%s %s" % kv for kv in r["per_task"].items()))
    phones = "".join('<div><div class="cap2">%s</div>%s</div>' % (cap, phone(v, s)) for s, cap in PAGE_STATES)
    head = ('<h1 style="font-size:20px">T1.6 round 4: the sentence sheet, tidied</h1><p class="dim">%s. Chips set the unit; the sentence\'s '
            'words edit the rest; each word opens one chooser. Type: Major Second (sentence 17.5 px, small 12.5 px). Scores: '
            '<code>tools/screens/repeat4_opt.py</code>.</p><p class="cap2" style="max-width:none">%s</p>') % (
        " · ".join("%s %s" % kv for kv in v.items()), meas)
    css = t.EXTRA + t.T12_CSS + t.T13_CSS + CSS + ".cap2{font-size:12px;color:var(--dim);max-width:360px;margin:0 0 6px}.grid4{display:grid;grid-template-columns:repeat(3,362px);gap:14px}"
    with open(os.path.join(v2.OUT, "repeat4-options.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(kit.document(head + '<div class="grid4">%s</div>' % phones, "light", css, False))


if __name__ == "__main__":
    if "page" in sys.argv:
        page(json.loads(sys.argv[sys.argv.index("page") + 1]))
    elif "stage1" in sys.argv:
        stage1()
    elif "stage2" in sys.argv:
        stage2(json.loads(sys.argv[sys.argv.index("stage2") + 1]))
