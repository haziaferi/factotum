"""The purpose map (owner, 2026-10-13): Factotum's screens by what they do, not by the app they came from.

    python tools/screens/purpose_map.py        writes docs/screens/purpose-map.md; exit 1 if a check fails

Checks:
  - every screen in the navigation scoring (nav_score2.SCREENS) is placed on a screen of the map;
  - every Hub entry (tier_t1.FEATURES) is placed on a screen of the map;
  - every screen names a known purpose, and every overlap names a known screen;
  - a screen with no source app says what is new about it;
  - the what-where table (owner, 2026-10-16): every thing names a known home (or "undecided") and known places. Repeats outside
    Today are listed as redundancy until scored (Today is a master board: shortcuts there are not redundancy); a new place for a
    thing goes in this table, so it shows here before it is added.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nav_score2  # noqa: E402
import tier_t1  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "docs", "screens", "purpose-map.json")
OUT = os.path.join(ROOT, "docs", "screens", "purpose-map.md")


def checks(m):
    bad = []
    ids = {s["id"] for s in m["screens"]}
    purposes = {p["id"] for p in m["purposes"]}
    nav = {n for s in m["screens"] for n in s.get("nav", [])}
    hub = {h for s in m["screens"] for h in s.get("hub", [])}
    for name, *_ in nav_score2.SCREENS:
        if name not in nav:
            bad.append("navigation screen not placed: %s" % name)
    for f in tier_t1.FEATURES:
        if f not in hub:
            bad.append("Hub entry not placed: %s" % f)
    for s in m["screens"]:
        if s["purpose"] not in purposes:
            bad.append("%s: unknown purpose %s" % (s["id"], s["purpose"]))
        for o in s.get("overlaps", []):
            if o not in ids:
                bad.append("%s: overlaps an unknown screen %s" % (s["id"], o))
        if not s["sources"] and not s.get("new"):
            bad.append("%s: no source app and nothing said new" % s["id"])
    for g in m["overlap_groups"]:
        for o in g["screens"]:
            if o not in ids:
                bad.append("%s: unknown screen %s" % (g["id"], o))
    for w in m.get("where", []):
        if w["home"] not in ids and not w["home"].startswith("undecided"):
            bad.append("where %s: unknown home %s" % (w["thing"], w["home"]))
        for place, _ in w["repeats"]:
            if place not in ids:
                bad.append("where %s: unknown place %s" % (w["thing"], place))
            if place == w["home"]:
                bad.append("where %s: its home listed as a repeat" % w["thing"])
    return bad


def render(m):
    by = {p["id"]: [] for p in m["purposes"]}
    for s in m["screens"]:
        by[s["purpose"]].append(s)
    name = {s["id"]: s["name"] for s in m["screens"]}
    out = ["# Purpose map", "", m["about"], "",
           "Generated from `purpose-map.json` by `tools/screens/purpose_map.py`; edit the JSON, not this page.", ""]
    out += ["## Purposes", "", "| | Purpose | Its job | Screens |", "|---|---|---|---|"]
    out += ["| %s | **%s** | %s | %d |" % (p["id"], p["name"], p["job"], len(by[p["id"]])) for p in m["purposes"]]
    for p in m["purposes"]:
        out += ["", "## %s %s" % (p["id"], p["name"]), "", "_%s_" % p["job"], "",
                "| Screen | Comes from | New in Factotum | Tier | Status | Overlaps |", "|---|---|---|---|---|---|"]
        for s in by[p["id"]]:
            out.append("| %s | %s | %s | %s | %s | %s |" % (
                s["name"] + (" _(%s)_" % s["merged"] if s.get("merged") else ""), "; ".join(s["sources"]) or "**none**", s.get("new", ""), s["tier"], s["status"],
                ", ".join(name[o] for o in s.get("overlaps", []))))
    out += ["", "## Screens with no parent app", ""]
    out += ["- **%s** (%s): %s" % (s["name"], s["purpose"], s["new"]) for s in m["screens"] if not s["sources"]]
    out += ["", "## Screens whose purposes overlap", "", "| | Strength | Screens | Why |", "|---|---|---|---|"]
    out += ["| %s | %s | %s | %s |" % (g["id"], g["strength"], ", ".join(name[o] for o in g["screens"]), g["why"]) for g in m["overlap_groups"] if not g.get("wrapped")]
    wrapped = [g for g in m["overlap_groups"] if g.get("wrapped")]
    if wrapped:   # resolved; re-consulted if something relevant arises (owner, 2026-10-16)
        out += ["", "### Wrapped", "", "Resolved overlaps, kept to re-consult if something relevant arises.", "",
                "| | Screens | Why | Wrapped |", "|---|---|---|---|"]
        out += ["| %s | %s | %s | %s |" % (g["id"], ", ".join(name[o] for o in g["screens"]), g["why"], g["wrapped"]) for g in wrapped]
    if m.get("where"):
        out += ["", "## What, and where (owner, 2026-10-16)", "", m["where_rule"], "",
                "| What | Home | On Today (not counted) | Repeats | Elsewhere | Scored |", "|---|---|---|---|---|---|"]
        for w in m["where"]:
            sh = {x["id"]: x.get("short", x["name"]) for x in m["screens"]}
            reps = "; ".join("%s (%s)" % (sh[pl], why) for pl, why in w["repeats"])
            out.append("| %s | %s | %s | %s | %s | %s |" % (w["thing"], sh.get(w["home"], "**" + w["home"] + "**"), w["today"] or "—",
                                                            reps or "—", w["elsewhere"] or "—", w["scored"] or "**to score**"))
        n = sum(len(w["repeats"]) for w in m["where"])
        out += ["", "_%d repeats outside Today, in %d things; %d things with no home decided._" % (
            n, sum(1 for w in m["where"] if w["repeats"]), sum(1 for w in m["where"] if w["home"].startswith("undecided")))]
    out += ["", "## The owner's answers", ""] + ["- %s" % a for a in m["owner_answers"]]
    counts = (len(m["screens"]), sum(1 for s in m["screens"] if not s["sources"]), sum(1 for s in m["screens"] if s["status"].startswith("approved")))
    out += ["", "_%d screens; %d with no parent app; %d approved._" % counts, ""]
    return "\n".join(out)


def main():
    with open(SRC, encoding="utf-8") as fh:
        m = json.load(fh)
    bad = checks(m)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(m))
    print(OUT)
    for b in bad:
        print("FAIL", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
