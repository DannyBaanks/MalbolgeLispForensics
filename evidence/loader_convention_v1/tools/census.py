#!/usr/bin/env python3
"""Whitespace census for 3^19 specimens: which convention is each file in?

Streams each file once (the dumps are 371 MB) and prints, per specimen: the
label, SHA-256, byte count, the number of `' ' \t \r \n` bytes and up to the
first 8 of their offsets. Prints labels only, never paths.

Run from the repository root with the specimen labels as arguments and
LISP_RUNTIME_DIR pointing at the directory that holds them.
"""
import hashlib
import os
import pathlib
import sys

WS = {ord(" "), ord("\t"), ord("\r"), ord("\n")}
base = pathlib.Path(os.environ.get("LISP_RUNTIME_DIR", "."))
pin = {
    "init_module.mb": "4b3080fd250a4193030ec647e6c496f90540c1546f717b923284ea31b411e812",
    "core.mb": "70e9155bbe44b58a0a44795cf0c614b214c8f31f82270f4913394e07f1f3e53a",
    "lisp.mb": "092df5cdc240de33a355d3cf82bdf09e0859c5827ee57a65bf93dfc37e8f3256",
}

for spec in (sys.argv[1:] or sorted(pin)):
    label, _, explicit = spec.partition("=")
    path = pathlib.Path(explicit) if explicit else base / label
    h = hashlib.sha256()
    n = total = 0
    hits = []
    try:
        with path.open("rb") as fh:
            while True:
                buf = fh.read(1 << 22)
                if not buf:
                    break
                for b in WS:
                    c = buf.count(bytes([b]))
                    total += c
                    if c and len(hits) < 8:
                        start, base_n = 0, n
                        while len(hits) < 8:
                            j = buf.find(bytes([b]), start)
                            if j < 0:
                                break
                            hits.append(base_n + j)
                            start = j + 1
                n += len(buf)
                h.update(buf)
    except OSError as exc:
        print(f"{label}\tUNREADABLE\t{type(exc).__name__}")
        continue
    dig = h.hexdigest()
    state = "pinned-ok" if pin.get(label) == dig else ("DRIFT" if label in pin else "unpinned")
    hits.sort()
    print(f"{label}\tbytes={n}\tsha256={dig}\t{state}\tws_count={total}\tws_offsets={hits[:8]}")
