"""Score every candidate model of one contest against its behaviour cases.

    python tools/score_contest.py 01-sync [--md decisions/01-sync-scores.md]

Reads decisions/cases/<contest>.jsonl   {id, owner, given, when, then, source}
      decisions/options/<contest>.json  {options: [{id, summary, growth{tables,columns,enum_cases},
                                          expresses{case_id: 0|0.5|1}, violates[], control?,
                                          expect_fail[]}]}
and, if present, decisions/options/<contest>.sim.json ({option_id: {case_id: score}}), which
overrides hand marks: a simulated result beats a stated one.

Objectives, none weighted: coverage per owner (higher), schema growth (lower). An option with
a violation is rejected before the front is built. Every option is scored; the space is small
enough that nothing is sampled. A control option lists cases it must fail (expect_fail); if it
passes one, the scorer cannot tell a loss from a win and the run exits 2.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(contest):
    d = os.path.join(ROOT, "decisions")
    with open(os.path.join(d, "cases", contest + ".jsonl"), encoding="utf-8") as fh:
        cases = [json.loads(l) for l in fh if l.strip() and not l.startswith("#")]
    with open(os.path.join(d, "options", contest + ".json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    sim_path = os.path.join(d, "options", contest + ".sim.json")
    if os.path.exists(sim_path):
        with open(sim_path, encoding="utf-8") as fh:
            sim = json.load(fh)
        for o in spec["options"]:
            o.setdefault("expresses", {}).update(sim.get(o["id"], {}))
            o["simulated"] = o["id"] in sim
    return cases, spec


def score(cases, spec):
    owners = sorted({c["owner"] for c in cases})
    rows = []
    for o in spec["options"]:
        missing = [c["id"] for c in cases if c["id"] not in o.get("expresses", {})]
        if missing:
            raise SystemExit("option %s has no mark for: %s" % (o["id"], ", ".join(missing)))
        cov = {}
        for w in owners:
            mine = [c for c in cases if c["owner"] == w]
            cov[w] = sum(o["expresses"][c["id"]] for c in mine) / len(mine)
        g = o.get("growth", {})
        rows.append({
            "id": o["id"], "summary": o.get("summary", ""), "cov": cov,
            "all": sum(o["expresses"][c["id"]] for c in cases) / len(cases),
            "growth": g.get("tables", 0) + g.get("columns", 0) + g.get("enum_cases", 0),
            "violates": o.get("violates", []), "control": o.get("control", False),
            "lost": [c["id"] for c in cases if o["expresses"][c["id"]] < 1],
            "expect_fail": o.get("expect_fail", []), "simulated": o.get("simulated", False),
        })
    return owners, rows


def dominates(a, b, owners):
    ka = [a["cov"][w] for w in owners] + [-a["growth"]]
    kb = [b["cov"][w] for w in owners] + [-b["growth"]]
    return all(x >= y for x, y in zip(ka, kb)) and any(x > y for x, y in zip(ka, kb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("contest")
    ap.add_argument("--md")
    args = ap.parse_args()
    cases, spec = load(args.contest)
    owners, rows = score(cases, spec)

    bad_controls = [(r["id"], c) for r in rows if r["control"]
                    for c in r["expect_fail"] if c not in r["lost"]]
    live = [r for r in rows if not r["violates"] and not r["control"]]
    front = [r for r in live if not any(dominates(q, r, owners) for q in live if q is not r)]

    out = ["| option | " + " | ".join(owners) + " | all | growth | status | loses |",
           "|---|" + "---|" * (len(owners) + 4)]
    for r in rows:
        status = ("control" if r["control"] else "rejected: " + ", ".join(r["violates"])
                  if r["violates"] else "**front**" if r in front else "dominated")
        out.append("| %s%s | %s | %.2f | %d | %s | %s |" % (
            r["id"], " (sim)" if r["simulated"] else "",
            " | ".join("%.2f" % r["cov"][w] for w in owners), r["all"], r["growth"],
            status, ", ".join(r["lost"]) or "-"))
    text = "\n".join(out)
    text += "\n\n%d cases, %d options, front: %s" % (
        len(cases), len(rows), ", ".join(r["id"] for r in front) or "none")
    if bad_controls:
        text += "\n\nCONTROL FAILED: " + "; ".join("%s passed %s" % x for x in bad_controls)
    print(text)
    if args.md:
        with open(os.path.join(ROOT, args.md), "w", encoding="utf-8", newline="") as fh:
            fh.write(text + "\n")
    sys.exit(2 if bad_controls else 0)


if __name__ == "__main__":
    main()
