#!/usr/bin/env python3
"""Verify hashes for the published artifact set."""
from pathlib import Path
import hashlib, sys

ROOT = Path(__file__).resolve().parents[1]
HASH_FILE = ROOT / "evidence" / "hashes" / "evidence.sha256"
failures = 0
count = 0
for raw in HASH_FILE.read_text(encoding="utf-8").splitlines():
    if not raw.strip() or raw.lstrip().startswith("#"):
        continue
    expected, rel = raw.split("  ", 1)
    path = ROOT / rel
    if not path.is_file():
        print(f"MISSING {rel}")
        failures += 1
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    count += 1
    if actual != expected:
        print(f"MISMATCH {rel}\n  expected {expected}\n  actual   {actual}")
        failures += 1
if failures:
    print(f"FAIL: {failures} problem(s) across {count} hashed files")
    sys.exit(1)
print(f"OK: {count} published files match evidence.sha256")
