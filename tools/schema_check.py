"""Fails when a committed Room schema file differs from HEAD: an exported schema is what installed
databases were made from, and a build that rewrites one (KSP run before SCHEMA_VERSION was bumped)
makes the next AutoMigration skip the columns it should add, so upgrades crash. A file moved with its
bytes unchanged (R100, e.g. the package rename) is not a change."""
import subprocess
import sys

lines = subprocess.run(["git", "diff", "--name-status", "-M100%", "HEAD", "--", "data/schemas"],
                       capture_output=True, text=True, check=True).stdout.splitlines()
changed = [line for line in lines if not line.startswith("R100")]
if changed:
    print("committed schema files changed:", *changed, sep="\n  ")
    sys.exit(1)
print("schema files: committed ones unchanged")
