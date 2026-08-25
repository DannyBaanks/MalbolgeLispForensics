# MalbolgeLISP Forensics

Reproducible forensics for **MalbolgeLISP v1.2** — an unusually large program
written in the Malbolge-family esoteric language, targeting a **3^19 memory
model** (Malbolge "Unshackled" style, fixed rotation width 19) — plus a
cross-implementation validation suite for classic 3^10 Malbolge.

This repository answers three questions with runnable evidence:

1. Why does the upstream-bundled `fast20` interpreter hang on some Windows
   configurations, and what exactly is the defect?
2. How can the full 371 MB MalbolgeLISP image be executed natively on Windows,
   and what does a correct run look like?
3. Can independent implementations agree on classic Malbolge semantics down to
   identical step counts?

## The pipeline we validated

```
ordinary text
    |  Translator (anchor harness)
    v
Malbolge program (.mal)
    |  multiple distinct backends: C engine / Python oracle /
   |   Python toolkit / Zig VM
    v
exact output (byte-identical, identical step counts)
    |  Walbolge (inverse translation)
    v
reconstructed representation == original text (roundtrip verified)
```

Two worlds are kept strictly separate throughout:

| World | Word size | Memory | Specimens here |
|---|---|---|---|
| CLASSIC MALBOLGE | 10 trits (3^10 = 59,049 cells) | tiny | hello world, Quijote ch. I |
| MALBOLGELISP | 19 trits (3^19 = 1,162,261,467 cells) | ~371 MB image | `lisp.mb` (see below) |

**Walbolge does NOT decompile the 3^19 monster.** It decompiles
Translator-produced 3^10 programs; that boundary is demonstrated and enforced
by design.

## Headline results (all reproducible, see docs/CLAIMS.md)

- The upstream `fast20.c` hangs because Cygwin's `mmap(MAP_FIXED)` returns
  `EINVAL` over its own `PROT_NONE` reservation on this platform, and fast20
  ignores the return value. A 25-line reproducer is included
  (`src/diagnostics/mmap_repro.c`).
- A one-call fix (`mprotect` instead of `mmap(MAP_FIXED)`) makes fast20 load
  the 371 MB image in ~2 s and execute at ~5.7e8 steps/s on the test machine.
- `bolge19`, a from-scratch native Windows VM written in Zig (no Cygwin, no
  mmap tricks), boots the complete MalbolgeLISP v1.2 REPL, evaluates
  `(+ 1 2)` -> `3`, prints its farewell verse on EOF, and terminates cleanly:
  **HALT at 2,408,246,381 steps in 75 s** (single core).
- Classic Malbolge agreement across four distinct backends:
  hello world = `"Hello World!"` at exactly **40 steps**;
  Quijote chapter I heading at exactly **2632 steps**.
- Translator -> Walbolge roundtrip: all four verification flags True.

## Repository layout

```
docs/          claims, architecture, reproduction, honesty ledger
src/bolge19/   native Zig VM for the 3^19 model
src/patches/   minimal patch to upstream fast20.c (+ rationale)
src/diagnostics/mmap_repro.c            minimal Cygwin bug reproducer
src/validation/ cross-backend test drivers
third_party/upstream/  snapshot of upstream fast20.c (CC0) used as patch base
specimens/     hello world + Quijote chapter I (Translator product + manifest)
evidence/      curated logs, anchors, manifests, hashes (relative paths only)
scripts/       one-shot local validation runner
```

The giant specimens (`lisp.mb` 371,331,415 bytes; normalized form, same size)
are **not redistributed here by default**, but they are CC0 too — see
`docs/REPRODUCTION.md` for provenance and verification instructions.

## Provenance & attribution

MalbolgeLISP, `fast20.c`, the manual and `lisp.zip` are work by the upstream
author (iczelia / kspalaiologos), released CC0. Everything in `src/patches`
derives from their public source; our modifications are clearly marked.
Autobolge/Walbolge/Translator/engine/oracle/toolkit belong to the ISyCo
research workspace and are referenced, not republished, beyond the small
specimen/manifest snapshots needed for reproduction.

## License

Our additions: MIT (see `LICENSE`). Upstream snapshot: CC0 1.0
(`third_party/upstream/LICENSE.upstream`).
