"""Contest 13: score each folder layout on the behaviour cases of decisions/cases/13-folder.jsonl,
measured on top of a year of already-synced data. Writes decisions/options/13-folder.sim.json (case
marks, read by score_contest.py) and decisions/options/13-folder.metrics.json (the measured costs).

    python tools/folder_cases.py [--days 14 --seeds 3 --history 365]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import folder_sim as fs  # noqa: E402

ROOT = fs.ROOT
ANDROID_SLOW_FILES = 10_000   # syncthing-android #1630: scanning slows past 10,000-16,000 files


def tiny_workload(base):
    w = json.loads(json.dumps(base))
    w["kinds"] = {"item": dict(base["kinds"]["item"], per_day=0)}
    return w


def flush(sim, dev, t):
    """Export now, and land any shared-file write that would follow `write_ms` later."""
    sim.export(dev, t)
    for _, _, kind, args in sorted(sim.events):
        if kind == "write_files":
            sim.write_files(args[0], t, args[1], args[2])
    sim.events.clear()


def local_edit(sim, dev, row, group, t):
    s = sim.stamp(dev, t)
    dev.state[(row.id, group)] = s
    sim.truth[(row.id, group)] = max(s, sim.truth.get((row.id, group), (0, "")))
    dev.dirty_rows.add(row.id)
    return s


def retired_loser(layout, base):
    """A and B change the same row at once; B's version loses the file conflict (older mtime), and
    B is wiped before it syncs again. Does B's change survive on the devices that remain?"""
    sim = fs.Sim(layout, tiny_workload(base), 0, 1, ["A", "B"])
    a, b = sim.devs
    sim.write(a, 0, "item")
    flush(sim, a, 1)
    sim.session(a, b, 2)
    sim.import_folder(b, 3)
    row = next(iter(sim.rows.values()))
    s_b = local_edit(sim, b, row, "status", 10)
    local_edit(sim, a, row, "schedule", 20)
    flush(sim, b, 10)
    flush(sim, a, 20)
    sim.session(a, b, 30)
    sim.import_folder(a, 31)
    sim.devs = [a, fs.Device("C")]          # B is wiped before it syncs again
    sim.settle(40)
    return 1 if all(d.state.get((row.id, "status")) == s_b for d in sim.devs) else 0


def run(days, seeds, history, only):
    base = fs.load_workload(os.path.join(ROOT, "decisions", "options", "13-folder.workload.json"))
    d = os.path.join(ROOT, "decisions", "options")
    marks, metrics = {}, {}
    if only:
        marks = json.load(open(os.path.join(d, "13-folder.sim.json"), encoding="utf-8"))
        metrics = json.load(open(os.path.join(d, "13-folder.metrics.json"), encoding="utf-8"))
    for layout in (only or fs.LAYOUTS):
        runs = []
        for seed in range(seeds):
            sim = fs.Sim(layout, json.loads(json.dumps(base)), seed, days, list(base["devices"]))
            sim.preseed(history)
            runs.append(sim.run())
        m = {k: round(sum(r[k] for r in runs) / len(runs), 3) for k in runs[0]}
        m["single_point_worst"] = max(r["single_point_worst"] for r in runs)
        metrics[layout] = m
        copies_cleared = fs.LAYOUTS[layout].get("reads_conflicts", False)
        marks[layout] = {
            "st-no-conflict-copies": 1 if m["conflict_copies"] == 0 else (0.5 if copies_cleared else 0),
            "st-retired-loser": retired_loser(layout, base),
            "android-files-1y": 1 if m["files"] < ANDROID_SLOW_FILES else 0,
            "ff-nothing-lost": 1 if m["lost_versions"] == 0 else 0,
        }
        print("%-20s %s" % (layout, marks[layout]), flush=True)
        print("%-20s %s" % ("", m), flush=True)
    for name, data in (("13-folder.sim.json", marks), ("13-folder.metrics.json", metrics)):
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--history", type=int, default=365, help="days of already-synced data to start from")
    ap.add_argument("--only", default="", help="comma-separated layouts to re-score; the rest are kept")
    a = ap.parse_args()
    run(a.days, a.seeds, a.history, [x for x in a.only.split(",") if x])
