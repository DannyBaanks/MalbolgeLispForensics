#!/usr/bin/env python3
"""Classify every mismatch in evidence/hashes/evidence.sha256 by cause.

For each hashed file compare three things: the hash recorded in the published
manifest, the SHA-256 of the file as committed in HEAD, and the SHA-256 of the
file on disk. A mismatch whose HEAD bytes reproduce the recorded hash after
lone-LF -> CRLF conversion is a LINE-ENDING change only: the content is intact
and the manifest was published against a CRLF checkout. Anything else is a
CONTENT change.

Run from the repository root. Prints relative paths only.
"""
import hashlib
import pathlib
import subprocess

root = pathlib.Path(".")
manifest = root / "evidence" / "hashes" / "evidence.sha256"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def to_crlf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


rows = [line.split("  ", 1) for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")]

tally = {"recorded_hash_matches_head": 0, "line_ending_only": 0, "content_change": 0, "missing_in_head": 0}
content, drift = [], []
for recorded, rel in rows:
    try:
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        tally["missing_in_head"] += 1
        content.append(f"  NO_BLOB {rel}")
        continue
    disk = sha((root / rel).read_bytes()) if (root / rel).is_file() else None
    if disk is not None and disk != sha(blob):
        drift.append(f"  WORKTREE_DIFFERS_FROM_HEAD {rel}")
    if sha(blob) == recorded:
        tally["recorded_hash_matches_head"] += 1
    elif sha(to_crlf(blob)) == recorded:
        tally["line_ending_only"] += 1
    else:
        tally["content_change"] += 1
        content.append(f"  {rel}")

print(f"hashed_entries={len(rows)}")
for key, val in tally.items():
    print(f"  {key}={val}")
print("content_change_paths:")
print("\n".join(content) if content else "  (none)")
print("worktree_vs_head:")
print("\n".join(drift) if drift else "  (tree matches HEAD)")
