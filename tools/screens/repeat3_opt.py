"""T1.6 round 3 (owner, 2026-10-08): "hiding the full task sheet behind advanced or wrapping everything, including
cron, inside the rule as a sentence of tappable words", scored for density, harmony and text size as well.

Designs
  A  a slim sheet: the presets, one field that takes words or cron with its calculator line, the rule read back,
     and "More options ›", which opens a builder (scored with each of freq, modes, sentence, sentmodes behind it)
  B  everything in the sentence of tappable words, cron included (owner: the cron line goes blank when cron cannot
     express the rule); three ways:
       readonly  the cron line under the sentence, read only
       mirror    the cron line is a field under the sentence; editing either updates the other
       toggle    the sentence ends with a tappable "as cron" that turns it into an editable cron line and back
     The OR rule (T10) is reachable by words too: "on [day 1] or [a weekday]".
Type (owner: "let scoring decide"): seven options from designkit's scale steps on the controls' 14 px base (Major
Second, Minor Third, Major Third, Perfect Fourth; the sentence at the lg or xl step, the small text at sm).
Fonts stay placeholders (decision 15).

Axes (owner, 2026-10-08)
  H        heights, sprawl (craftkit ui findings, colour excluded), heavy (the largest element's share of mass)
  U        actions for someone who knows cron (the quicker path per task), reach
  C        clutter, covered, controls
  Density  controls per 100 px of the sheet (crowding); the empty share is reported beside it
  Legible  the smallest text and the sentence's size (both larger is better)
  Learn    actions without cron syntax: every task has a words, sentence or builder path (owner: "no cron-only
           actually exists"), so this is what a beginner pays
  Refs     the distance from the 17 references
Rules reached without typing and the rule read back are the same for every design here (all reach T2-T9 by taps,
all read the rule back), so they are reported, not ranked.

    PYTHONUTF8=1 python tools/screens/repeat3_opt.py [--workers 4]
"""
import concurrent.futures
import itertools
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import picker_opt as P  # noqa: E402
import repeat_opt as R  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402
from craftkit import imgstat  # noqa: E402

TYPES = {"MS-lg": (16, 12.5), "MS-xl": (17.5, 12.5), "m3-lg": (17, 11.5), "m3-xl": (20, 11.5), "M3-lg": (17.5, 11), "M3-xl": (22, 11), "P4-lg": (18.5, 10.5)}
SPACE_A = {"design": ["A"], "builder": ["freq", "modes", "sentence", "sentmodes"], "start": ["presets", "builder"], "container": ["sheet", "page"], "type": list(TYPES)}
SPACE_B = {"design": ["B"], "cronmode": ["readonly", "mirror", "toggle"], "start": ["presets", "builder"], "container": ["sheet", "page"], "type": list(TYPES)}
FIELDS = R.FIELDS | {"Day field", "Tok cron"}
WORDS_T10 = "the 1st or any monday"  # the beginner's words for the OR rule
CRON = {k: c for k, c in R.CRON_CHARS.items() if k != 4}  # T4's count is not cron


def type_css(name):
    s, x = TYPES[name]
    return ".pk .sent{font-size:%spx}.pk .calc,.pk .lab{font-size:%spx}.pk .calc{line-height:1.45}" % (s, x)


def bv(v):
    """The builder behind A's More options, as repeat_opt draws it."""
    return {"form": v["builder"], "start": "builder", "cron": "advanced", "preview": "words", "container": v["container"]}


def cron_line(state):
    """Every drawn state shows a rule cron can express (weekly on Fri); for a rule it cannot (every 2 weeks, random,
    after done) the line is blank (owner, 2026-10-08), which only shortens the sheet."""
    return '<div class="calc">As cron: 0 9 * * 5</div>'


def b_sentence(v, state):
    """The sentence form with the day-and-weekday chooser (T10 by words) and, for toggle, a tappable "as cron"."""
    st = "onm" if state == "onor" else state
    html = R.sentence(dict(v, form="sentence"), st)
    if state in ("onm", "onor"):
        html += R.row(R.field("Day field", "16"), R.ch("Or weekday", "or a weekday", state == "onor"))
    if v["cronmode"] == "toggle":
        html = html.replace("</div>", ' <span class="tok" data-tap="Tok cron"><b>as cron</b></span></div>', 1)
    return html


def body(v, state):
    pre = R.presets_row() if v["start"] == "builder" else ""
    if state == "presets":
        return R.header(v) + R.preset_list()
    back = v["start"] == "presets"
    if v["design"] == "A":
        if state == "base":
            return R.header(v, back) + pre + R.rule_field() + R.preview_sec("words") + '<div class="row">%s</div>' % R.b("Advanced", "More options ›")
        st = state[4:]
        words = R.WORDS.get(st, "Every week on Fri at 09:00") if v["builder"] not in ("sentence", "sentmodes") else "Next"
        return R.header(v, back=True) + R.FORM[v["builder"]](bv(v), st) + R.preview_sec("words", words)
    if state == "ascron":
        return (R.header(v, back) + R.row(R.field("Cron field", "0 9 * * 5", "field")) + '<div class="calc">Every week on Fri at 09:00</div>'
                + '<div class="row">%s</div>' % R.b("Tok words", "‹ as words") + R.preview_sec("words", "Next"))
    cron = {"readonly": cron_line(state), "mirror": R.row(R.field("Cron field", "0 9 * * 5", "field"), label="Cron"), "toggle": ""}[v["cronmode"]]
    return R.header(v, back) + pre + b_sentence(v, state) + cron + R.preview_sec("words", "Next")


def phone(v, state, kb=False):
    # repeat_opt's frame, with this module's body
    orig = R.body
    try:
        R.body = lambda _v, s: body(v, s)
        return R.phone(dict(v, container=v["container"]), state, kb)
    finally:
        R.body = orig


def doc(v, state, kb=False, theme="light", score=True):
    return kit.document(phone(v, state, kb), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + R.CSS + type_css(v["type"]), score)


def tap(state, *names):
    return [(state, "tap", n) for n in names]


def typ(state, n):
    return [(state, "type", n)]


def paths(v):
    """{task: [(path, uses_cron)]}: every way the design offers, so the quicker one is counted."""
    pre = tap("presets", "Custom") if v["start"] == "presets" else []
    out = {k: [] for k in range(1, 11)}
    out[1].append((tap("presets", "Preset Weekdays") if v["start"] == "presets" else tap("base", "Preset Weekdays", "Done"), False))
    if v["design"] == "A":
        words = {**R.TYPED_CHARS, 10: WORDS_T10}
        for k in range(2, 11):
            out[k].append((pre + tap("base", "Rule field") + typ("base", len(words[k])) + tap("base", "Done"), False))
            if k in CRON:
                out[k].append((pre + tap("base", "Rule field") + typ("base", len(CRON[k])) + tap("base", "Done"), True))
        W = R.walk(bv(v))
        for k in range(2, 10):
            out[k].append((pre + tap("base", "Advanced") + [("adv:" + s, kind, x) for s, kind, x in W[k]], False))
    else:
        W = R.walk({"form": "sentence", "start": "builder", "cron": "advanced", "preview": "words", "container": v["container"]})
        for k in range(2, 10):
            out[k].append((pre + W[k], False))
        out[10].append((pre + tap("base", "Tok unit") + tap("unit", "Unit Months") + tap("unitm", "Tok on") + tap("onm", "Day field") + typ("onm", 1)
                        + tap("onm", "Or weekday") + tap("onor", "Ow Mon", "Ow Fri", "Done"), False))
        for k, c in CRON.items():
            if v["cronmode"] == "mirror":
                out[k].append((pre + tap("base", "Cron field") + typ("base", len(c)) + tap("base", "Done"), True))
            elif v["cronmode"] == "toggle":
                out[k].append((pre + tap("base", "Tok cron") + typ("ascron", len(c)) + tap("ascron", "Done"), True))
    return out


def empty_share(png, m):
    sx, sy, sw, sh = m["boxes"]["picker"]
    crop = png.replace(".png", "-r3-%d.png" % os.getpid())
    Image.open(png).convert("RGB").crop((int(sx), int(max(0, sy)), int(sx + sw), int(min(740, sy + sh)))).save(crop)
    img = imgstat.load(crop)
    lum = imgstat._fast_luma(img.px)
    return round(imgstat._detail_report(imgstat._sobel(lum, img.w, img.h), img.w, img.h).get("empty_share", 0.0), 3)


def score(v):
    P_ = paths(v)
    states = sorted({s for ps in P_.values() for p, _ in ps for s, _, _ in p} | {"base"})
    views = {}
    for s in states:
        for kb in (False, True):
            m = ss.measure(doc(v, s, kb), 360, 740)
            views[(s, kb)] = ({x["name"]: x for x in m["taps"]}, m)

    def sim(k, task):
        kb, n, miss, tids = False, 0, set(), []
        for state, kind, x in task:
            if kind == "type":
                n += x
                continue
            seen = lambda kbv: views[(state, kbv)][0].get(x, {}).get("seen")
            if kb and not seen(True):
                if seen(False):
                    n += 1  # close the keyboard first
                    kb = False
                else:
                    miss.add("T%d %s: %s" % (k, state, x))
            elif not kb and not seen(False):
                miss.add("T%d %s: %s" % (k, state, x))
            tp = views[(state, kb)][0].get(x)
            if tp and tp.get("seen"):
                tids.append(math.log2(math.hypot(P.THUMB[0] - tp["x"], P.THUMB[1] - tp["y"]) / min(tp["w"], tp["h"]) + 1))
            n += 1
            if x in FIELDS or x.startswith("Cron "):
                kb = True
            if x == "Done" or x.startswith("Preset"):
                kb = False
        return n, miss, tids

    expert, beginner, ids, unseen, per = 0, 0, [], set(), {}
    for k, ps in P_.items():
        runs = [(sim(k, p), cron) for p, cron in ps]
        drawn = lambda rs: min(rs, key=lambda r: (len(r[0][1]), r[0][0]))
        (n, miss, tids), _ = drawn(runs)
        (nb, missb, _), _ = drawn([r for r in runs if not r[1]])
        expert += n
        beginner += nb
        unseen |= miss | missb
        ids += tids
        per[k] = (n, nb)
    base_t, base_m = views[("base", False)]
    pk = base_m["boxes"].get("picker")
    in_pk = [x for x in base_m["taps"] if pk and x["box"][1] >= pk[1] - 1 and x.get("seen") and not x["name"].startswith("Readout")]
    small = sorted({"%s %dx%d" % (x["name"], x["w"], x["h"]) for (s, kb), (tp, m) in views.items() if not kb for x in tp.values()
                    if x.get("seen") and not x["name"].startswith("Readout") and (x["w"] < 48 or x["h"] < 48)})
    png = ss.render(doc(v, "base"), 360, 740)
    clutter = sum(ss.edge_density(ss.render(doc(v, "base", False, th), 360, 740)) for th in ("light", "dark")) / 2
    height = min(740, pk[3]) if pk else 740
    return {"actions": expert, "beginner": beginner, "per_task": per, "reach": round(sum(ids) / max(1, len(ids)), 3), "unseen": len(unseen),
            "unseen_names": sorted(unseen), "small": small, "heights": max(1, len({x[4] for x in base_m["vis"]})), "clutter": round(clutter, 4),
            "covered": 1.0 if v["container"] == "page" else round(height / 740, 3), "controls": len(in_pk),
            "crowding": round(len(in_pk) / (height / 100), 2), "empty": empty_share(png, base_m), "heavy": P.masses(png, base_m),
            "min_text": TYPES[v["type"]][1], "main_text": TYPES[v["type"]][0], "neg_min_text": -TYPES[v["type"]][1], "neg_main_text": -TYPES[v["type"]][0]}


def sprawl(v):
    import subprocess
    path = os.path.join(ss.CACHE, "r3-%s.html" % "-".join(str(x) for x in v.values()))
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(doc(v, "base"))
    res = subprocess.run([sys.executable, os.path.join(v2.CRAFT, "craftkit_cli.py"), "ui", "--json", path], capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
    found = json.loads(res.stdout).get("findings", [])
    return sum(1 for f in found if not f.get("code", "").startswith(("colour", "contrast")) and (f.get("severity") in ("warn", "warning", "error") or f.get("code") == "spacing-off-grid"))


def features(v):
    unit = {"freq": "menu", "modes": "chips", "sentence": "words", "sentmodes": "words"}.get(v.get("builder"), "words")
    return {"presets_first": v["start"] == "presets", "unit_control": "text" if v["design"] == "A" else unit, "weekday_chips": True,
            "page": v["container"] == "page", "readout": True, "next_dates": True, "modes": v.get("builder") in ("modes", "sentmodes")}


def full(v):
    r = score(v)
    r["sprawl"] = sprawl(v)
    return r


AXES = {"H": ("heights", "sprawl", "heavy"), "U": ("actions", "reach"), "C": ("clutter", "covered", "controls"), "Density": ("crowding",),
        "Legible": ("neg_min_text", "neg_main_text"), "Learn": ("beginner",), "Refs": ("ref_distance",)}


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    vs = [dict(zip(SPACE_A, c)) for c in itertools.product(*SPACE_A.values())] + [dict(zip(SPACE_B, c)) for c in itertools.product(*SPACE_B.values())]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(workers) as ex:
        for v, r in zip(vs, ex.map(full, vs)):
            rows.append(dict(v=v, **r))
            print(len(rows), v, {k: r[k] for k in ("actions", "beginner", "unseen", "small", "clutter", "covered", "crowding", "empty")}, flush=True)
    with open(R.REFS, encoding="utf-8") as fh:
        refs = json.load(fh)["apps"]
    for r in rows:
        f = features(r["v"])
        r["ref_distance"] = round(sum(sum(f[k] != ref[k] for k in R.FEATURES) / len(R.FEATURES) for ref in refs) / len(refs), 3)
    ok = [r for r in rows if not r["small"] and r["unseen"] == 0]
    for axis, keys in AXES.items():
        cols = [v2.ranks(ok, k, 1) for k in keys]
        for i, r in enumerate(ok):
            r[axis] = sum(c[i] for c in cols)
    ax = list(AXES)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in ax) and any(o[a] < r[a] for a in ax) for o in ok if o is not r)]
    with open(os.path.join(v2.OUT, "repeat3-opt.json"), "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump({"rows": rows, "passed": len(ok), "front": [rows.index(r) for r in front]}, fh, indent=1, ensure_ascii=False)
    print("passed", len(ok), "of", len(rows), "front", len(front))


def page():
    """Mockups of the leading round-3 designs: sheet, builder start, Major Second xl type (the only scale keeping the
    small text at 12 px or more)."""
    with open(os.path.join(v2.OUT, "repeat3-opt.json"), encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    show = [
        ("B, read-only cron line: everything in the sentence", {"design": "B", "cronmode": "readonly"},
         [("base", "Opens on the sentence; cron read back under it"), ("unit", "\"week\" tapped"), ("onor", "\"on\" tapped, monthly: day 1 or a weekday (the OR rule by words)")]),
        ("B, \"as cron\" toggle", {"design": "B", "cronmode": "toggle"}, [("base", "The sentence ends with \"as cron\""), ("ascron", "\"as cron\" tapped: the rule as an editable cron line")]),
        ("A: the field and its calculator, the builder behind More options (schedule types)", {"design": "A", "builder": "modes"},
         [("base", "Opens on the field"), ("adv:base", "More options"), ("adv:random", "More options › Random")]),
    ]
    parts = ['<h1 style="font-size:20px">T1.6 round 3: everything in the sentence, or a slim sheet with the builder behind More options</h1>'
             '<p class="dim">Sheet, opening on the builder with the presets as its first row; type Major Second (sentence 17.5 px, small text 12.5 px). '
             'Scores from <code>tools/screens/repeat3_opt.py</code>.</p>']
    for title, sel, states in show:
        v = dict(sel, start="builder", container="sheet", type="MS-xl")
        r = [x for x in rows if x["v"] == v][0]
        meas = ("Actions over the 10 tasks %d if you know cron, %d if you do not · reach %.2f · clutter %.3f · covers %.0f%% · controls %d · "
                "controls per 100 px %.1f · empty share %.2f · distance from the references %.2f") % (
            r["actions"], r["beginner"], r["reach"], r["clutter"], 100 * r["covered"], r["controls"], r["crowding"], r["empty"], r["ref_distance"])
        phones = "".join('<div><div class="cap2">%s</div>%s</div>' % (cap, phone(v, s)) for s, cap in states)
        parts.append('<h3>%s</h3><p class="cap2" style="max-width:none">%s</p><div class="flex">%s</div>' % (title, meas, phones))
    css = (t.EXTRA + t.T12_CSS + t.T13_CSS + R.CSS + type_css("MS-xl")
           + "h3{font-size:15px;margin:18px 0 6px}.cap2{font-size:12px;color:var(--dim);max-width:360px;margin:0 0 6px}.flex{display:flex;gap:12px;overflow-x:auto}")
    with open(os.path.join(v2.OUT, "repeat3-options.html"), "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(kit.document("".join(parts), "light", css, False))


if __name__ == "__main__":
    page() if "--page" in sys.argv else main()
