"""T1.5 on Windows (owner, 2026-10-08: score the options): the date picker from the quick-add window as
  dropdown  a calendar dropping under the line, the usual desktop date field (presets, month, time, end)
  dropdown2 the dropdown in two columns, the month on the left, presets, time and end on the right (a one-column
            picker ran off the 660 px window in both first shapes)
  panel     a side panel opening beside the quick-add window, the same parts in a column
Same parts as picker_opt (presets, month grid, typed time with suggestions, duration presets). A desktop window has
width, not height: in one column both first shapes ran past the 660 px window and cut the time and end; the
two-column dropdown fits. Measures (render and DOM):
  reach     mean Fitts' ID from the line (where the pointer is when the picker opens) to the task set's targets
  unseen    task targets not drawn (hit-tested)
  covered   share of the app window the picker and quick-add hide together
  clutter   edge density of the window
  travel    total pointer distance over the task set, in px
    PYTHONUTF8=1 python tools/screens/picker_desk.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import kit  # noqa: E402
import legend_opt as L  # noqa: E402
import picker_opt as P  # noqa: E402
import screen_score as ss  # noqa: E402
import tier_t1 as t  # noqa: E402

V = {"container": "page", "entry": "typed", "load": True, "end": "duration"}


def body(shape):
    parts = P.picker(V).replace('class="pk page"', 'class="pk"')
    qa = L.sheet("both", "typed").replace('class="sheet" style="position:relative"', 'class="qa" style="position:relative;margin:60px 0 0 150px"')
    if shape == "dropdown2":  # a desktop has width: the month on the left, presets, time and end on the right
        presets = '<div class="row">%s</div>' % "".join(P.chip("Preset %s" % p, p) for p in P.PRESETS)
        right = P.time_entry("typed") + P.end_part(V)  # no presets (owner, 2026-10-08): the calendar opens straight away
        two = ('<div class="pk" data-picker="1" style="display:grid;grid-template-columns:336px 1fr;gap:16px;padding:6px 24px 10px">'
               '<div>%s</div><div>%s</div></div>') % (P.month(True), right)
        drop = '<div style="position:absolute;left:150px;top:190px;width:720px;box-shadow:0 12px 40px rgba(0,0,0,.25);border-radius:14px;overflow:hidden">%s</div>' % two
        return '<div class="c2" style="position:relative">%s%s</div>' % (qa, drop)
    if shape == "dropdown":
        drop = '<div style="position:absolute;left:150px;top:190px;width:360px;box-shadow:0 12px 40px rgba(0,0,0,.25);border-radius:14px;overflow:hidden">%s</div>' % parts
        return '<div class="c2" style="position:relative">%s%s</div>' % (qa, drop)
    panel = '<div style="position:absolute;left:690px;top:60px;width:360px;box-shadow:0 12px 40px rgba(0,0,0,.25);border-radius:14px;overflow:hidden">%s</div>' % parts
    return '<div class="c2" style="position:relative">%s%s</div>' % (qa, panel)


def doc(shape, theme="light", score=True):
    return kit.document(t.cap_desk(body(shape)), theme, t.EXTRA + t.T12_CSS + t.T13_CSS + P.CSS, score)


def score(shape):
    m = ss.measure(doc(shape), 1100, 660)
    taps = {x["name"]: x for x in m["taps"]}
    line = m["boxes"]["line"]
    start = (line[0] + line[2] / 2, line[1] + line[3] / 2)
    ids, travel, unseen = [], 0.0, set()
    for names, _, _ in P.steps(V):
        pos = start
        for n in names:
            x = taps.get(n)
            if n.endswith("(T1.6)"):
                continue
            if not x or not x.get("seen"):
                unseen.add(n)
                continue
            d = math.hypot(pos[0] - x["x"], pos[1] - x["y"])
            ids.append(math.log2(d / min(x["w"], x["h"]) + 1))
            travel += d
            pos = (x["x"], x["y"])
    pk = m["boxes"].get("picker")
    covered = (pk[2] * min(pk[3], 660 - pk[1]) + 520 * 120) / (1100 * 660) if pk else 0
    clutter = sum(ss.edge_density(ss.render(doc(shape, th), 1100, 660)) for th in ("light", "dark")) / 2
    return {"shape": shape, "reach": round(sum(ids) / max(1, len(ids)), 3), "travel": round(travel), "unseen": sorted(unseen),
            "covered": round(covered, 3), "clutter": round(clutter, 4)}


def main():
    rows = [score(s) for s in ("dropdown", "dropdown2", "panel")]
    for r in rows:
        print(r)
    with open(os.path.join(v2.OUT, "picker-desk.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
