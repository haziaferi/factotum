"""The purpose map (owner, 2026-10-13): Factotum's screens by what they do, not by the app they came from.

    python tools/screens/purpose_map.py        writes docs/screens/purpose-map.md; exit 1 if a check fails

Checks:
  - every screen in the navigation scoring (nav_score2.SCREENS) is placed on a screen of the map;
  - every Hub entry (tier_t1.FEATURES) is placed on a screen of the map;
  - every screen names a known purpose, and every overlap names a known screen;
  - a screen with no source app says what is new about it.
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
                s["name"], "; ".join(s["sources"]) or "**none**", s.get("new", ""), s["tier"], s["status"],
                ", ".join(name[o] for o in s.get("overlaps", []))))
    out += ["", "## Screens with no parent app", ""]
    out += ["- **%s** (%s): %s" % (s["name"], s["purpose"], s["new"]) for s in m["screens"] if not s["sources"]]
    out += ["", "## Screens whose purposes overlap", "", "| | Strength | Screens | Why |", "|---|---|---|---|"]
    out += ["| %s | %s | %s | %s |" % (g["id"], g["strength"], ", ".join(name[o] for o in g["screens"]), g["why"]) for g in m["overlap_groups"]]
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
