r"""The Paced timer trial page (T3b.4c): the best sheet of each top placer, the real clock face, and Break Down Timer,
working, with the scores beside them.

Reads the scored part (t3-pace3.json, through toast_opt's ranking) and the drawings (pace-imgs.json, from pace_imgs.py);
fills pace_try.tmpl.html; writes docs/screens/t3/pace-try.html.  Run pace_imgs.py first when the drawings change.
"""
import json
import os

import t3_opt as M

HERE = os.path.dirname(os.path.abspath(__file__))
PLACERS = 4   # the best option of each of the four best placers (owner, 2026-10-15: "best four"), then the clock face asked for
NAME = {"clock": "real clock face", "ring24": "ring of 24 slices", "dragring": "drag ring", "tabs": "segment tabs", "line": "timeline", "sentence": "sentence"}


def label(v):
    if v.get("control"):
        return "Break Down Timer (control)", "length or finish-time icons, the 60-slice ring; no later start, no rests"
    parts = ["run " + v["run"], "words beside" if v["exact"] == "sentence" else "face alone", "rhythm word" if v["rhythm"] == "word" else "no rhythm word",
             "face shown" if v["face"] == "shown" else "face as a chooser"]
    return NAME[v["placer"]], ", ".join(parts)


def main():
    rows, ok, axes = M.T.ranked("pace3")
    order = sorted((r for r in ok if not r["v"].get("control")), key=lambda r: r["total"])
    rank = {id(r): i + 1 for i, r in enumerate(order)}
    picked, seen = [], set()
    for r in order:
        if r["v"]["placer"] not in seen and r["v"]["placer"] != "sentence":
            seen.add(r["v"]["placer"])
            picked.append(r)
        if len(picked) == PLACERS:
            break
    if "clock" not in seen:
        picked.append(next(r for r in order if r["v"]["placer"] == "clock"))
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in picked + [ctl]:
        v = r["v"]
        lab, sub = label(v)
        est = {k: r[k] for k in ("taps", "keyboards", "drags", "reach")}
        est.update(total=r.get("total"), rank=rank.get(id(r)))
        sheets.append({"id": "bdt" if v.get("control") else "-".join(v[k] for k in ("run", "placer", "exact", "rhythm", "face")),
                       "label": lab, "sub": sub, "cfg": {k: v[k] for k in ("run", "placer", "exact", "rhythm", "face")}, "est": est})
    with open(os.path.join(M.T.OUT, "pace-imgs.json"), encoding="utf-8") as fh:
        got = json.load(fh)
    by = {json.dumps(r["v"], sort_keys=True): r for r in rows}
    imgs = []
    for i in got["sheets"]:
        r = by[json.dumps(i["v"], sort_keys=True)]
        lab, sub = label(i["v"])
        note = "total %s%s · %s taps, %s keyboards, %s drags · recovery %s%s" % (r.get("total"), (" · #%d" % rank[id(r)]) if id(r) in rank else " · control",
                                                                              r["taps"], r["keyboards"], r["drags"], r["recover"],
                                                                              " · %d steps impossible (each counted as the worst)" % r["impossible"] if r["impossible"] else "")
        imgs.append({"src": i["src"], "caption": lab, "note": sub + " · " + note})
    prow, _, _ = M.T.ranked("paceplace")
    pby = {(r["v"]["place"], r["v"]["elsewhere"]): r for r in prow}
    PL = {"sheet": "sheet, set and run", "sheet_strip": "sheet to set, strip to run", "page": "the activity's page", "screen": "its own screen",
          "row": "the Measuring row", "bdt": "Break Down Timer's full screen (control)"}
    places = got["places"]
    for pl in places:
        r = pby[(pl["place"], pl["elsewhere"])]
        pl["caption"] = PL[pl["place"]] + ("" if pl["place"] == "bdt" else " · " + ("header mark" if pl["elsewhere"] == "mark" else "no mark"))
        pl["note"] = "total %s%s · app %s · taps %s to reach + %s to return · seen elsewhere %s of 2" % (
            r.get("total"), " · front" if r.get("front") else "", "blocked" if r["app_blocked"] else "free", r["reach_taps"], r["return_taps"], r["seen_elsewhere"])
        pl["total"] = r.get("total")
    places.sort(key=lambda x: (x["total"] is None, x["total"] or 0))
    with open(os.path.join(HERE, "pace_try.tmpl.html"), encoding="utf-8") as fh:
        page = fh.read()
    data = json.dumps({"sheets": sheets, "imgs": imgs, "places": places}, ensure_ascii=False).replace("</", "<\\/")
    out = os.path.join(M.T.OUT, "pace-try.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("__DATA__", data, 1))
    print(out, [s["id"] for s in sheets])


if __name__ == "__main__":
    main()
