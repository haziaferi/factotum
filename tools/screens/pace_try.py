r"""The Paced timer trial page (T3b.4d): the best sheet of each way of dividing the run ring, the sentence typed with the
phone's keyboard (the owner's baseline), and Break Down Timer with its presets, working, with the scores beside them.

Reads the scored part (t3-pace4.json, through toast_opt's ranking) and the drawings (pace-imgs.json, from pace_imgs.py);
fills pace_try.tmpl.html; writes docs/screens/t3/pace-try.html.  Run pace_imgs.py first when the drawings change.
"""
import json
import os

import t3_opt as M

HERE = os.path.dirname(os.path.abspath(__file__))
DIV = {"snap": "ring · snapping drag", "chosen": "ring · split into N", "presets": "ring · fraction presets"}
KEYS = ("time", "pauses", "division", "rest", "words", "face")


def label(v):
    if v.get("control"):
        return "Break Down Timer (control)", "with its fraction presets (‹ ›); the clock picker; 60 slices; no later start, no rests"
    if v["pauses"] == "sentence":
        return "sentence only", "times %s; numbers typed with the phone's keyboard" % ("on the dial" if v["time"] == "dial" else "typed")
    parts = ["times on the dial" if v["time"] == "dial" else "times typed", "a rest as a span" if v["rest"] == "span" else "a rest as a point + length",
             "words beside" if v["words"] == "beside" else "ring alone", "ring shown" if v["face"] == "shown" else "ring as a chooser"]
    return DIV[v["division"]], ", ".join(parts)


def main():
    rows, ok, axes = M.T.ranked("pace4")
    order = sorted((r for r in ok if not r["v"].get("control")), key=lambda r: r["total"])
    rank = {id(r): i + 1 for i, r in enumerate(order)}
    picked = []
    for div in ("snap", "chosen", "presets"):   # the best of each way of dividing the ring
        picked.append(next(r for r in order if r["v"]["pauses"] == "ring" and r["v"]["division"] == div))
    picked.append(next(r for r in order if r["v"]["pauses"] == "sentence" and r["v"]["time"] == "typed"))   # the owner's baseline
    picked.sort(key=lambda r: r["total"])
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in picked + [ctl]:
        v = r["v"]
        lab, sub = label(v)
        est = {k: r[k] for k in ("taps", "keyboards", "drags", "reach")}
        est.update(total=r.get("total"), rank=rank.get(id(r)))
        sheets.append({"id": "bdt" if v.get("control") else "-".join(v[k] for k in KEYS), "label": lab, "sub": sub, "cfg": {k: v[k] for k in KEYS}, "est": est})
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
    data = json.dumps({"sheets": sheets, "imgs": imgs}, ensure_ascii=False).replace("</", "<\\/")
    out = os.path.join(M.T.OUT, "pace-try.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("__DATA__", data, 1))
    print(out, [s["id"] for s in sheets])


if __name__ == "__main__":
    main()
