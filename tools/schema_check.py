"""Fails when a committed Room schema file differs from HEAD: an exported schema is what installed
databases were made from, and a build that rewrites one (KSP run before SCHEMA_VERSION was bumped)
makes the next AutoMigration skip the columns it should add, so upgrades crash."""
import subprocess
import sys

changed = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "data/schemas"], capture_output=True, text=True, check=True).stdout.split()
if changed:
    print("committed schema files changed:", *changed, sep="\n  ")
    sys.exit(1)
print("schema files: committed ones unchanged")
