"""Extracts every named palette pair from visual-craft's design lexicon into
docs/screens/t0/palette-sources.json (decision 15, Q4). Only names, a few words of character, the
roles and their hex values are kept; nothing is retyped by hand.

A pair in the lexicon reads:  1. *Name* — character. Light: surface `#..`, text `#..`, primary `#..` (...).
Dark: surface `#..`, ...   Roles other than these are kept under their own names.

    python tools/screens/lexicon_pairs.py <path to visual-craft/references/lexicon>
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "screens", "t0", "palette-sources.json")

PAIR = re.compile(r"^\s*\d+\.\s+\*([^*]+)\*\s*(?:[—-]+|(?=\())\s*(.*)$")  # "*Name* — …" or "*Name* (…)"
ROLE = re.compile(r"([A-Za-z][A-Za-z /-]*?)\s*(?:\([^)]*\)\s*)?`(#[0-9A-Fa-f]{6})`")  # "primary (gold) `#..`" too


def registers(text):
    """Splits a pair's text into its Light and Dark parts, each a {role: hex} map."""
    out = {}
    for reg in ("Light", "Dark"):
        m = re.search(reg + r"[^:]*:\s*(.*?)(?=(?:Light|Dark)[^:]*:|$)", text, re.S)
        if m:
            roles = {}
            for role, hexv in ROLE.findall(m.group(1)):
                role = role.strip().strip(",").strip().split(",")[-1].strip()
                roles[role] = hexv.upper()
            if roles:
                out[reg.lower()] = roles
    return out


def parse(path):
    entries, entry = [], None
    lines = open(path, encoding="utf-8").read().splitlines()
    for line in lines:
        if line.startswith("### "):
            entry = {"entry": line[4:].strip(), "shard": os.path.basename(path), "pairs": []}
            entries.append(entry)
            continue
        m = PAIR.match(line)
        if entry is not None and m:
            name, rest = m.group(1).strip(), m.group(2)
            character = rest.split(".")[0].split(" Light")[0].strip()
            regs = registers(rest)
            if regs:
                entry["pairs"].append({"name": name, "character": character[:120], **regs})
    return [e for e in entries if e["pairs"]]


def main(lexicon_dir):
    entries = []
    for path in sorted(glob.glob(os.path.join(lexicon_dir, "*.md"))):
        entries += parse(path)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"source": "visual-craft references/lexicon (creative-design-suite)", "entries": entries}, fh, indent=1, ensure_ascii=False)
    return entries


if __name__ == "__main__":
    es = main(sys.argv[1])
    print(len(es), "entries,", sum(len(e["pairs"]) for e in es), "pairs ->", OUT)
    for e in es:
        print("%-45s %s" % (e["entry"][:45], " | ".join("%s %s" % (p["name"], p.get("light", {}).get("primary", p.get("dark", {}).get("primary", "?"))) for p in e["pairs"])))
