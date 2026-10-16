r"""The Paced timer trial page (T3b.4e): the best ring sheet for each way of moving a break (the dial, a slowed drag, a
nudge), the sentence alone with the dial and typed with the phone's keyboard, and Break Down Timer with its presets.

Reads the scored part (t3-pace5.json, through toast_opt's ranking) and the drawings (pace-imgs.json, from pace_imgs.py);
fills pace_try.tmpl.html; writes docs/screens/t3/pace-try.html.  Run pace_imgs.py first when the drawings change.
"""
import json
import os

import t3_opt as M

HERE = os.path.dirname(os.path.abspath(__file__))
MOVE = {"dial": "moved on the dial", "nudge": "moved with − / +", "magnify": "moved by a slowed drag"}
KEYS = ("time", "pauses", "move", "drag", "face")


def label(v):
    if v.get("control"):
        return "Break Down Timer (control)", "with its fraction presets (‹ ›); the clock picker; 60 slices; no later start, no rests"
    if v["pauses"] == "sentence":
        return "sentence only", "times %s; N breaks evenly; counts typed" % ("on the dial" if v["time"] == "dial" else "typed with the phone's keyboard")
    return "ring · break " + MOVE[v["move"]], ", ".join(["times on the dial" if v["time"] == "dial" else "times typed",
                                                         "a press on the ring adds a chime (snapping)" if v["drag"] == "rough" else "the ring only shows and selects",
                                                         "ring shown" if v["face"] == "shown" else "ring as a chooser"])


def main():
    rows, ok, axes = M.T.ranked("pace5")
    order = sorted((r for r in ok if not r["v"].get("control")), key=lambda r: r["total"])
    rank = {id(r): i + 1 for i, r in enumerate(order)}
    picked = [next(r for r in order if r["v"]["pauses"] == "ring" and r["v"]["move"] == mv) for mv in ("dial", "magnify", "nudge")]
    picked += [next(r for r in order if r["v"]["pauses"] == "sentence" and r["v"]["time"] == t) for t in ("dial", "typed")]
    picked.sort(key=lambda r: r["total"])
    pick = next(r for r in picked if r["v"]["pauses"] == "sentence" and r["v"]["time"] == "dial")
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in picked + [ctl]:
        v = r["v"]
        lab, sub = label(v)
        est = {k: r[k] for k in ("taps", "keyboards", "drags", "reach")}
        est.update(total=r.get("total"), rank=rank.get(id(r)))
        sheets.append({"id": "bdt" if v.get("control") else "-".join(v[k] for k in KEYS), "label": lab, "sub": sub, "cfg": {k: v[k] for k in KEYS}, "est": est})
    # the owner's pick (2026-10-15): the sentence and the dial, with - / + beside every box (times and lengths 5 min, counts 1)
    est = dict(sheets[[s["id"] for s in sheets].index("-".join(pick["v"][k] for k in KEYS))]["est"], total="the pick", rank=None)
    sheets.insert(0, {"id": "dial-sentence-steps", "label": "the approved sheet (T3b.4f, A + C)", "est": est,
                      "sub": "one part per row; 32 dp − / + (times 5 min, counts 1); evenly ↔ at; Reset breaks",
                      "cfg": dict({k: pick["v"][k] for k in KEYS}, steps=True)})
    with open(os.path.join(M.T.OUT, "pace-imgs.json"), encoding="utf-8") as fh:
        got = json.load(fh)
    by = {json.dumps(r["v"], sort_keys=True): r for r in rows}
    imgs = []
    for i in got["sheets"]:
        r = by[json.dumps(i["v"], sort_keys=True)]
        lab, sub = label(i["v"])
        note = "total %s%s · %s taps, %s keyboards, %s drags · recovery %s · %d%% without the keyboard%s" % (
            r.get("total"), (" · #%d" % rank[id(r)]) if id(r) in rank else " · control", r["taps"], r["keyboards"], r["drags"], r["recover"],
            round(100 * r["adoption"]), " · %d steps impossible (each counted as the worst)" % r["impossible"] if r["impossible"] else "")
        imgs.append({"src": i["src"], "caption": lab, "note": sub + " · " + note})
    with open(os.path.join(HERE, "pace_try.tmpl.html"), encoding="utf-8") as fh:
        page = fh.read()
    sheets, imgs = sheets[:1], []   # the approved sheet only; the unpicked sheets and their images are discarded (owner, 2026-10-16)
    data = json.dumps({"sheets": sheets, "imgs": imgs}, ensure_ascii=False).replace("</", "<\\/")
    out = os.path.join(M.T.OUT, "pace-try.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("__DATA__", data, 1))
    print(out, [s["id"] for s in sheets])


if __name__ == "__main__":
    main()
