r"""The Paced timer trial page (T3b.4): the four best sheets and Break Down Timer, working, with the scores beside them.

Reads the scored part (t3-pace.json, through toast_opt's ranking) and the drawings (pace-imgs.json, from pace_imgs.py);
fills pace_try.tmpl.html; writes docs/screens/t3/pace-try.html.  Run pace_imgs.py first when the drawings change.
"""
import json
import os

import t3_opt as M

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"sentence": "sentence", "fields": "fields", "switch": "switch", "ring": "ring", "line": "line", "presets": "presets",
         "ring_presets": "ring + presets", "line_presets": "line + presets", "bdt": "Break Down Timer"}
KEEP = 4   # the owner's choice: the front's best four and the control (2026-10-14)


def main():
    rows, _, _ = M.T.ranked("pace")
    scored = sorted((r for r in rows if r.get("total") is not None and not r["v"].get("control")), key=lambda r: r["total"])
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in scored[:KEEP] + [ctl]:
        v = r["v"]
        est = {k: r[k] for k in ("taps", "keyboards", "reach", "step_min", "like_when")}
        est["total"] = r.get("total")
        if v.get("control"):
            sheets.append({"id": "bdt", "mode": "bdt", "place": "bdt", "label": "Break Down Timer (control)",
                           "sub": "length or finish-time icons, the 60-slice ring; no later start, no rests", "est": est})
        else:
            sheets.append({"id": "%s-%s" % (v["mode"], v["place"]), "mode": v["mode"], "place": v["place"],
                           "label": "%s · %s" % (NAMES[v["mode"]], NAMES[v["place"]]), "sub": "run by %s, pauses by %s" % (NAMES[v["mode"]], NAMES[v["place"]]), "est": est})
    by_key = {(r["v"]["mode"], r["v"]["place"]): r for r in rows}
    with open(os.path.join(M.T.OUT, "pace-imgs.json"), encoding="utf-8") as fh:
        got = json.load(fh)
    imgs, places = got["sheets"], got["places"]
    prow, _, _ = M.T.ranked("paceplace")
    pby = {(r["v"]["place"], r["v"]["elsewhere"]): r for r in prow}
    PL = {"sheet": "sheet, set and run", "sheet_strip": "sheet to set, strip to run", "page": "the activity's page", "screen": "its own screen",
          "row": "the Measuring row", "bdt": "Break Down Timer's full screen (control)"}
    for pl in places:
        r = pby[(pl["place"], pl["elsewhere"])]
        pl["caption"] = PL[pl["place"]] + ("" if pl["place"] == "bdt" else " · " + ("header mark" if pl["elsewhere"] == "mark" else "no mark"))
        pl["note"] = "total %s%s · app %s · taps %s to reach + %s to return · seen elsewhere %s of 2" % (
            r.get("total"), " · front" if r.get("front") else "", "blocked" if r["app_blocked"] else "free", r["reach_taps"], r["return_taps"], r["seen_elsewhere"])
        pl["total"] = r.get("total")
    places.sort(key=lambda x: (x["total"] is None, x["total"] or 0))
    for i in imgs:
        r = by_key.get((i["mode"], i["place"]), {})
        i["caption"] = NAMES[i["place"]] if i["mode"] == "bdt" else "%s · %s" % (NAMES[i["mode"]], NAMES[i["place"]])
        if r.get("small"):
            i["note"] = "gated: " + ", ".join(r["small"])
        else:
            i["note"] = "total %s · %s taps · step %s min%s" % (r.get("total"), r.get("taps"), r.get("step_min"), " · control" if i["mode"] == "bdt" else "")
    with open(os.path.join(HERE, "pace_try.tmpl.html"), encoding="utf-8") as fh:
        page = fh.read()
    data = json.dumps({"sheets": sheets, "imgs": imgs, "places": places}, ensure_ascii=False).replace("</", "<\\/")
    out = os.path.join(M.T.OUT, "pace-try.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("__DATA__", data, 1))
    print(out, [s["id"] for s in sheets])


if __name__ == "__main__":
    main()
