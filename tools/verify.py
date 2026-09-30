"""Run the measured verification brief (tools/brief/prompts.json, B-structured: 21/21 on
Sonnet 5.5, 2026-09-30) over one contest's per-repo claim sets, in parallel.

    python tools/verify.py decisions/verify/<contest>/inputs.json [--model claude-sonnet-5-5]

inputs.json: [{"repo": "tendril", "cwd": "<abs path>", "input": "<claims text>"}]
Writes decisions/verify/<contest>/<repo>.json (the raw JSON the brief returns) and
prints any output that does not parse, so a failed run is never read as "no findings".
"""
import argparse
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = "B-structured"
ALLOWED_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5"}


def run(model, system, item):
    cmd = ["claude", "-p", "--model", model, "--setting-sources", "",
           "--allowedTools", "Read,Grep,Glob", "--append-system-prompt", system]
    proc = subprocess.run(cmd, input=item["input"], capture_output=True, text=True,
                          encoding="utf-8", cwd=item["cwd"], timeout=1500,
                          env=dict(os.environ, PYTHONUTF8="1"))
    return proc.stdout, proc.stderr[:400] if proc.returncode else ""


def parse(text):
    text = re.sub(r"^\s*```[a-zA-Z]*\s*|\s*```\s*$", "", text.strip())
    try:
        return json.loads(text)
    except ValueError:
        pass
    # A prose preface despite "JSON only" (seen once in 7 runs, 2026-09-30): take the
    # outermost object rather than lose the run.
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    args = ap.parse_args()
    if args.model not in ALLOWED_MODELS:
        raise SystemExit("model floor is Sonnet 5.5: use one of %s" % sorted(ALLOWED_MODELS))
    with open(os.path.join(ROOT, "tools", "brief", "prompts.json"), encoding="utf-8") as fh:
        system = json.load(fh)[BRIEF]["system"]
    with open(args.inputs, encoding="utf-8") as fh:
        items = json.load(fh)
    out_dir = os.path.dirname(os.path.abspath(args.inputs))
    with ThreadPoolExecutor(len(items)) as pool:
        results = list(pool.map(lambda it: run(args.model, system, it), items))
    for item, (out, err) in zip(items, results):
        data = parse(out)
        path = os.path.join(out_dir, item["repo"] + ".json")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            if data is None:
                fh.write(out)
            else:
                json.dump(data, fh, indent=1, ensure_ascii=False)
        status = "UNPARSED " + (err or "%d chars" % len(out)) if data is None else \
            "%d claims, %d missed" % (len(data.get("claims", [])), len(data.get("missed", [])))
        print("%-10s %s" % (item["repo"], status))


if __name__ == "__main__":
    main()
