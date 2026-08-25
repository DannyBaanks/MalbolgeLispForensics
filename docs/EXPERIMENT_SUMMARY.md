# Experiment summary

## Specimen

MalbolgeLISP v1.2 (upstream project; consult upstream for complete licensing).
Distributed as `lisp.zip` containing
`core.mb` (371,312,023 bytes) and `init_module.mb` (19,392 bytes).
Identity: `lisp.mb == concat(init_module.mb, core.mb)`,
size 371,331,415 bytes (verified by byte-concatenation and by execution).

Word model: 19 trits/cell, END = 3^19 = 1,162,261,467 cells; raw-ASCII tape;
position-dependent decode with per-region offsets as implemented by the
bundled interpreter `fast20.c` ("fixed rotation width 19").

## What broke

The bundled Cygwin build of fast20 spins at 100% CPU executing **zero**
instructions on this platform, for any input (even a 19 KB fragment that
terminates in 19,337 steps under a correct VM).

Root cause chain, demonstrated:

1. fast20 reserves 4.65 GB virtual with `mmap(PROT_NONE)`, then flips file
   region to RW using `mmap(MAP_FIXED)` — ignoring mmap's return value.
2. On Cygwin/Windows here, that second mmap fails: `EINVAL` / `MAP_FAILED`
   (`src/diagnostics/mmap_repro.c`, one-shot reproducer).
3. The first store then faults; the SIGSEGV handler calls the same failing
   mmap and writes to the still-unmapped page -> nested fault storm,
   infinite spin, no progress, no I/O.

## What fixed it (patch)

`src/patches/fast20_fixed.c`: replace both protection-flip calls with
`mprotect(..., PROT_READ|PROT_WRITE)`. Result: full 371 MB load in ~2 s,
execution at ~5.7e8 steps/s measured on the test machine (delta-based
telemetry). Telemetry must avoid stdio inside the dispatch path after faults
(see docs/ARCHITECTURE.md).

## What replaced it (native VM)

`src/bolge19/main.zig` — from-scratch Windows-native Zig VM implementing the
same visible semantics (per-region decode offsets, concatenated 135-char
encrypt table, c/d advance each cycle, pattern fill beyond image with
page-phase alignment). No mmap games: flat image + small chain zone +
period-6 page-phased pattern + write overlay.

Result of a full interactive session against `lisp.mb`
(`evidence/selected_logs/bolge19_lisp_session_stdout.txt`):

```
MALBOLGELISP V1.2 (2020-2021, PALAIOLOGOS)
DOT COMMANDS:  .F(eatures)  .A(uthor)  .R(eset)  ...
% ......|....
3
%
There is a sky illuminating us
...
```

Input `(+ 1 2)` evaluated to `3`. EOF produced the interpreter's farewell
verse. Clean termination:

```
HALT steps=2408246381 c=581143360 d=581861866 a=10 elapsed=75s
```

Standalone fragment control: `init_module.mb` alone halts at 19,337 steps in
0.03 s CPU (it is a module, not the Lisp).

## Translation

`bolge19 --normalize` walks all cells applying the runtime decode and emits
one mnemonic character per cell: D(jmp) J(out) i(in) *(rot) <(movd) p(crz)
/(nop) v(halt), '#' otherwise. Over the whole image:
371,331,415 characters, SHA-256
`bef2a63fc92d28f582c2426d1e61d6c942d89006e3676ce2949d2df78270d794`,
anchor checkpoints every 100M cells and every 75 s wall time (rolling hash),
dual-formula cross-checks in region 0: 7 checks, 0 failures.
Instruction census: '/' 150,761,408 · '<' 98,369,120 · '*' 73,798,229 ·
'p' 47,934,035 · 'D' 468,609 · 'J' 8 · 'i' 4 · 'v' 1.

## Classic-side agreement (distinct backends, shared specimen set)

hello world: output `"Hello World!"`, halt_opcode at exactly 40 steps in
all four backends exercised (C engine, Python oracle, Python toolkit, Zig
Autobolge container). Quijote chapter I heading: identical text at exactly
2632 steps in the same four plus Walbolge's independent trace. Details and
raw outputs: `evidence/selected_logs/showdown/`.

## Roundtrip

Translator product (.mal + manifest + word files) executed back to its exact
source text, then Walbolge decompilation reports roundtrip flags
processed/original/words/opcodes all True, bootstrap segment recognized,
35 words, output 101 chars. Raw report: `evidence/selected_logs/walbolge_quijote_ch001.json`.
