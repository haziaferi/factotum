"""Re-apply cases.json checks to the raw outputs already in results.json (no model calls)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
res = json.load(open(os.path.join(HERE, "results.json"), encoding="utf-8"))
res["cases"], res["case_specs"] = [], {}
for c in cases:
    for k, chk in c["checks"].items():
        cid = "%s/%s" % (c["id"], k)
        res["cases"].append(cid)
        res["case_specs"][cid] = {"id": cid, "check": chk}
for p in res["prompts"]:
    p["outputs"] = {"%s/%s" % (c["id"], k): p["raw"][c["id"]]
                    for c in cases if c["id"] in p["raw"] for k in c["checks"]}
with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(res, fh, indent=2)
print("rescored", len(res["cases"]), "checks")
