"""Capture sheet v4 (owner, 2026-10-07): "Is the Task / Event / Reminder chip necessary? Could only text the size of
the hint be left?" The prefix sheet with ⋯ (capture_v3's front), the kind shown as
  chip     a chip, first in the row (as v3)
  inline   hint-sized text (12 px) at the row's start, still a 48 px target that changes it
  row      a hint-sized line where the hint sits while the line is empty; changed by a prefix or ⋯ › Kind
  none     not shown; a prefix or ⋯ › Kind still changes it
crossed with the parse as chips or highlighted, and Enter or a ✓. capture_v3's measures and axes, with
  taps_fix  taps to change the kind without typing: the chip or the inline text 2 (open, pick); row or none 3 (⋯, Kind, pick)
  hidden    adds 1 when the kind is not shown at all (Nielsen: visibility of system status)
  min_text  the smallest text on the sheet (the hint size is the floor the owner asked about)

    PYTHONUTF8=1 python tools/screens/capture_v4.py
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capture_v2 as v2  # noqa: E402
import capture_v3 as v3  # noqa: E402
import screen_score as ss  # noqa: E402

SPACE = {"kind": ["chip", "inline", "row", "none"], "display": ["chips", "highlight"], "add": ["enter", "chips"]}
AXES = {"H": v3.AXES["H"], "U": v3.AXES["U"] + (("taps_fix", 1),), "C": v3.AXES["C"]}


def score(v, control_mode=False):
    agg = v3.score(dict(v, tail="more"), control_mode)
    k = v["kind"]
    agg["taps_fix"] = 2 if k in ("chip", "inline") or control_mode else 3
    agg["hidden"] += 1 if k == "none" and not control_mode else 0
    m = ss.measure(v3.doc(dict(v, tail="more"), v2.INPUTS[0], control_mode=control_mode), 360, 740)
    agg["min_text"] = m["min_text"]
    return agg


def main():
    rows = []
    for c in itertools.product(*SPACE.values()):
        v = dict(zip(SPACE, c))
        rows.append(dict(v=v, control=False, **score(v)))
        print(len(rows), v, {x: rows[-1][x] for x in ("sheet", "empty", "controls", "clutter", "unshown", "hidden", "taps_fix", "min_text")}, flush=True)
    rows.append(dict(v={"kind": "all", "display": "chips", "add": "big"}, control=True,
                     **score({"kind": "chip", "display": "chips", "add": "chips", "tail": "icons+more"}, True)))
    ok = [r for r in rows if r["over_box"] == 0 and not r["small"]]
    for axis, parts in AXES.items():
        rk = [v2.ranks(ok, key, sg) for key, sg in parts]
        for i, r in enumerate(ok):
            r[axis] = sum(col[i] for col in rk)
    front = [r for r in ok if not any(all(o[a] <= r[a] for a in "HUC") and any(o[a] < r[a] for a in "HUC") for o in ok if o is not r)]
    beaten = rows[-1] not in front
    with open(os.path.join(v2.OUT, "capture-v4.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"rows": rows, "front": [rows.index(r) for r in front], "control_beaten": beaten}, fh, indent=1, ensure_ascii=False)
    print("front:", len(front), "control beaten:", beaten)
    for r in sorted(front, key=lambda r: r["H"] + r["U"] + r["C"]):
        print(r["v"], "H %.1f U %.1f C %.1f" % (r["H"], r["U"], r["C"]))
    if not beaten:
        sys.exit(2)


if __name__ == "__main__":
    main()
