"""Sensitivity of the hand-counted growth figures (contests 09, 11 and 12): does any front or pick flip?

    python tools/sensitivity.py

Growth in these three contests is a hand count, not a measurement of a built schema. Every live
option's growth is multiplied independently by each of MULT, and every combination is enumerated
(6^options), using score_contest.py's own load, score and dominates. For each contest it reports how
often the decided option stays on the front, how often it is the only full-coverage option on the
front, and the exact growth at which each full-coverage rival would displace it.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_contest as sc  # noqa: E402

MULT = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
PICKS = {"09-settings": "scoped-live", "11-occurrence-edits": "edit-log+move", "12-page-merge": "per-row+revive"}


def front(rows, owners):
    return [r for r in rows if not any(sc.dominates(q, r, owners) for q in rows if q is not r)]


def main():
    for contest, pick in PICKS.items():
        cases, spec = sc.load(contest)
        owners, rows = sc.score(cases, spec)
        live = [r for r in rows if not r["violates"] and not r["control"]]
        base = {r["id"]: r["growth"] for r in live}
        full = [r["id"] for r in live if r["all"] == 1.0]
        on, only, total = 0, 0, 0
        fronts = {}
        for ms in itertools.product(MULT, repeat=len(live)):
            for r, m in zip(live, ms):
                r["growth"] = base[r["id"]] * m
            f = [r["id"] for r in front(live, owners)]
            total += 1
            on += pick in f
            only += [x for x in f if x in full] == [pick]
            fronts[tuple(sorted(f))] = fronts.get(tuple(sorted(f)), 0) + 1
        for r in live:
            r["growth"] = base[r["id"]]
        print("%s  pick=%s  full-coverage options=%s" % (contest, pick, full))
        print("  combinations %d: pick on front %d (%.1f%%), pick the only full-coverage front member %d (%.1f%%)"
              % (total, on, 100.0 * on / total, only, 100.0 * only / total))
        for rival in [x for x in full if x != pick]:
            print("  rival %s (growth %s) vs pick (growth %s): the pick stays on the front while its growth <= the rival's"
                  % (rival, base[rival], base[pick]))
        for f, n in sorted(fronts.items(), key=lambda kv: -kv[1])[:4]:
            print("  front %-60s %5.1f%%" % (", ".join(f), 100.0 * n / total))


if __name__ == "__main__":
    main()
