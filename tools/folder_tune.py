"""Contest 13: tune each device-owned layout's knobs, and test how the ranking holds when the workload
changes. The space is small, so every point is scored (no sampling); the front is by dominance.

    python tools/folder_tune.py [--days 7 --seeds 2]
Writes decisions/options/13-folder.tune.json.
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import folder_sim as fs  # noqa: E402

OBJECTIVES = ["written_MB_per_day", "sent_MB_per_day", "join_MB", "file_creates_per_day", "p95_delay_min"]   # all lower is better
GRID = {
    "device-log": {"debounce_s": [30, 120], "segment_bytes": [16384, 65536], "snapshot_every": [16, 64, 256]},
    "device-chunks": {"debounce_s": [30, 120], "chunks_before_compaction": [256, 1024, 4096]},
    "device-chunks-area": {"debounce_s": [30, 120], "chunks_before_compaction": [256, 1024, 4096]},
}
WORKLOADS = {
    "typical": {},
    "light-pages": {"block": 50},
    "heavy-pages": {"block": 1000},
    "three-devices": {"tablet": True},
}


def variant(base, change):
    w = json.loads(json.dumps(base))
    for k, v in change.items():
        if k == "tablet":
            w["devices"]["tablet"] = {"share": 0.2, "from": 1080, "to": 1380, "writes_offline": False}
            w["devices"]["phone"]["share"] = 0.5
        else:
            w["kinds"][k]["per_day"] = v
    return w


def measure(layout, w, days, seeds):
    runs = []
    for s in range(seeds):
        sim = fs.Sim(layout, json.loads(json.dumps(w)), s, days, list(w["devices"]))
        sim.preseed(365)
        runs.append(sim.run())
    return {k: round(sum(r[k] for r in runs) / len(runs), 3) for k in runs[0]}


def front(points):
    def dominated(p, q):
        return all(q[o] <= p[o] for o in OBJECTIVES) and any(q[o] < p[o] for o in OBJECTIVES)
    return [p for p in points if not any(dominated(p, q) for q in points if q is not p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--seeds", type=int, default=1)
    a = ap.parse_args()
    base = fs.load_workload(os.path.join(fs.ROOT, "decisions", "options", "13-folder.workload.json"))
    out = {"tuning": {}, "sensitivity": {}}
    for layout, grid in GRID.items():
        pts = []
        for values in itertools.product(*grid.values()):
            w = json.loads(json.dumps(base))
            knobs = dict(zip(grid, values))
            w["app"].update(knobs)
            pts.append(dict(measure(layout, w, a.days, a.seeds), layout=layout, **knobs))
        out["tuning"][layout] = {"all": pts, "front": front(pts)}
        print(layout, "front:", [({k: p[k] for k in grid}, p["written_MB_per_day"], p["sent_MB_per_day"], p["join_MB"], p["file_creates_per_day"]) for p in out["tuning"][layout]["front"]], flush=True)
    for name, change in (WORKLOADS.items() if a.sensitivity else []):
        w = variant(base, change)
        res = {lay: measure(lay, w, a.days, a.seeds) for lay in ("per-area+copies", "device-snapshot", "device-area", "device-log", "device-chunks", "device-chunks-area")}
        out["sensitivity"][name] = res
        print(name, {lay: (r["written_MB_per_day"], r["sent_MB_per_day"], r["files"], r["conflict_copies"]) for lay, r in res.items()}, flush=True)
    path = os.path.join(fs.ROOT, "decisions", "options", "13-folder.tune%s.json" % ("" if a.sensitivity else "-knobs"))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
