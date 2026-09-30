"""Run each brief against each case through `claude -p` in parallel, then write a
promptlab-compatible results file (one promptlab case per check, sharing one output).

promptlab's own `run` is sequential with a 120 s timeout, too short for a model that
reads source; scoring and the frontier still go through promptlab.

    python run_briefs.py [--model claude-sonnet-5-5] [--jobs 6]
    python promptlab.py score results.json
    python promptlab.py frontier results.json
"""
import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def run_one(model, system, case):
    cmd = ["claude", "-p", "--model", model, "--setting-sources", "",
           "--allowedTools", "Read,Grep,Glob", "--append-system-prompt", system]
    env = dict(os.environ, PYTHONUTF8="1")
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, input=case["input"], capture_output=True, text=True,
                              encoding="utf-8", cwd=case["cwd"], timeout=900, env=env)
        out, err = proc.stdout, (proc.stderr[:400] if proc.returncode else "")
    except subprocess.TimeoutExpired:
        out, err = "", "timeout"
    return out, err, round(time.time() - t0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", default="", help="comma-separated prompt ids")
    args = ap.parse_args()
    with open(os.path.join(HERE, "prompts.json"), encoding="utf-8") as fh:
        prompts = json.load(fh)
    if args.only:
        prompts = {k: v for k, v in prompts.items() if k in args.only.split(",")}
    with open(os.path.join(HERE, "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)

    jobs = [(pid, p, c) for pid, p in prompts.items() for c in cases]
    with ThreadPoolExecutor(args.jobs) as pool:
        futs = {pool.submit(run_one, args.model, p["system"], c): (pid, c["id"])
                for pid, p, c in jobs}
        raw = {}
        for f, key in futs.items():
            raw[key] = f.result()
            print("%-22s %-18s %4ss %s" % (key[0], key[1], raw[key][2],
                                          raw[key][1] or "%d chars" % len(raw[key][0])))

    case_specs, case_ids = {}, []
    for c in cases:
        for chk_id, chk in c["checks"].items():
            cid = "%s/%s" % (c["id"], chk_id)
            case_ids.append(cid)
            case_specs[cid] = {"id": cid, "check": chk}
    results = {"model": args.model, "runner": "claude -p (run_briefs.py)",
               "cases": case_ids, "case_specs": case_specs, "prompts": []}
    for pid, p in prompts.items():
        entry = {"id": pid, "system": p["system"], "user": p["user"], "outputs": {},
                 "raw": {}, "errors": {}}
        for c in cases:
            out, err, secs = raw[(pid, c["id"])]
            entry["raw"][c["id"]] = out
            if err:
                entry["errors"][c["id"]] = err
            for chk_id in c["checks"]:
                entry["outputs"]["%s/%s" % (c["id"], chk_id)] = out
        results["prompts"].append(entry)
    path = os.path.join(HERE, "results.json")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(results, fh, indent=2)
    print("wrote", path)


if __name__ == "__main__":
    main()
