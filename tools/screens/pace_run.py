r"""The running-timer trial page (T3b.4g): where the Paced timer lives while running, with a simulated clock.

Reads the scored part (t3-pacerun.json, through toast_opt's ranking); fills pace_run.tmpl.html; writes
docs/screens/t3/run-try.html. The sheets: the best option, its variant on each dimension, and the control.
"""
import json
import os

import t3_opt as M

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ("view", "today", "rest_end", "stop")
STOP = {"undo": "Stop at once, with Undo", "long": "Stop by holding", "confirm": "Stop asks first"}


def label(v):
    if v.get("control"):
        return "Break Down Timer (control)", "its own screen; no strips; Stop at once, no Undo; no skip, +5 or edit"
    return ("%s · %s" % ("the activity's page" if v["view"] == "page" else "its own screen", "Today strip" if v["today"] == "strip" else "no Today strip"),
            "%s; %s" % ("work resumes after a rest" if v["rest_end"] == "auto" else "a tap starts work after a rest", STOP[v["stop"]]))


def main():
    rows, ok, _ = M.T.ranked("pacerun")
    order = sorted((r for r in ok if not r["v"].get("control")), key=lambda r: r["total"])
    rank = {id(r): i + 1 for i, r in enumerate(order)}
    best = order[0]["v"]
    want = [dict(best)] + [dict(best, **{k: x}) for k in KEYS for x in M.PACERUN_SPACE[k] if x != best[k]]
    by = {json.dumps({k: r["v"][k] for k in KEYS}, sort_keys=True): r for r in order}
    picked = [by[json.dumps({k: w[k] for k in KEYS}, sort_keys=True)] for w in want]
    ctl = next(r for r in rows if r["v"].get("control"))
    sheets = []
    for r in picked[:1]:   # the approved sheet only (owner, 2026-10-16: the unpicked sheets and the control are discarded)
        v = r["v"]
        lab, sub = label(v)
        sheets.append({"id": "bdt" if v.get("control") else "-".join(v[k] for k in KEYS), "label": lab, "sub": sub,
                       "cfg": {k: v[k] for k in KEYS}, "est": {"taps": r["taps"], "total": r.get("total"), "rank": rank.get(id(r))}})
    with open(os.path.join(HERE, "pace_run.tmpl.html"), encoding="utf-8") as fh:
        page = fh.read()
    data = json.dumps({"sheets": sheets}, ensure_ascii=False).replace("</", "<\\/")
    out = os.path.join(M.T.OUT, "run-try.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page.replace("__DATA__", data, 1))
    print(out, [s["id"] for s in sheets])


if __name__ == "__main__":
    main()
