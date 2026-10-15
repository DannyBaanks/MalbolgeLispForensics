# CLAIMS ledger

Status vocabulary: DEMONSTRATED (probe + artifact here), OBSERVED (measured
once, artifact present, not re-run), NOT_DEMONSTRATED.

## A. MalbolgeLISP v1.2 execution (3^19)

| id | claim | status | evidence |
|---|---|---|---|
| A1 | `lisp.mb == concat(init_module.mb, core.mb)`, 371,331,415 bytes | DEMONSTRATED | size identity + load logs (`selected_logs/bolge19_lisp_session_stderr.txt`) |
| A2 | Native VM boots the full REPL banner | DEMONSTRATED | `selected_logs/bolge19_lisp_session_stdout.txt` |
| A3 | `(+ 1 2)` evaluates to `3` | DEMONSTRATED | same transcript |
| A4 | EOF farewell verse then clean HALT at exactly 2,408,246,381 steps in 75 s | DEMONSTRATED | stderr line `HALT steps=2408246381 ... elapsed=75s` |
| A5 | Standalone `init_module.mb` halts at 19,337 steps (0.03 s CPU) under 19-trit semantics | DEMONSTRATED | validation run (see scripts) |

## B. fast20 defect and patch

| id | claim | status | evidence |
|---|---|---|---|
| B1 | Upstream fast20 spins at 100% CPU executing zero instructions on Cygwin/Windows here | DEMONSTRATED | telemetry CSVs referenced by lab manifest; behavior summarized in docs |
| B2 | Root cause: `mmap(MAP_FIXED)` over PROT_NONE returns EINVAL/MAP_FAILED; return value ignored; handler refaults forever | DEMONSTRATED | `src/diagnostics/mmap_repro.c` output captured in validation |
| B3 | mprotect-based flip restores loading (~2 s for 371 MB) and ~5.7e8 steps/s execution | OBSERVED | delta-telemetry captured during session; single machine |

## C. Normalization / translation

| id | claim | status | evidence |
|---|---|---|---|
| C1 | 371,331,415 mnemonics emitted; SHA-256 `bef2a63fc92d28f582c2426d1e61d6c942d89006e3676ce2949d2df78270d794` | DEMONSTRATED | `evidence/selected_logs/normalize_lisp_anchors_stderr.txt` FINAL anchor |
| C2 | Anchor checkpoints every 100M cells / 75 s with rolling hash; dual-formula checks 7/7 PASS | DEMONSTRATED | ANCHOR lines in same file |
| C3 | Census: '/' 150,761,408 · '<' 98,369,120 · '*' 73,798,229 · 'p' 47,934,035 · 'D' 468,609 · 'J' 8 · 'i' 4 · 'v' 1 | DEMONSTRATED | HIST lines in same file |

## D. Classic agreement (3^10), distinct backends

| id | claim | status | evidence |
|---|---|---|---|
| D1 | hello world = "Hello World!", halt_opcode @40 steps on C engine, Python oracle, Python toolkit, Zig Autobolge | DEMONSTRATED | `selected_logs/showdown/*hello*`, `autobolge_hello.out.bin` parse in scripts log |
| D2 | Quijote ch. I heading reproduced byte-exact @2632 steps on the same backends | DEMONSTRATED | showdown outputs + autobolge quijote bin |
| D3 | Walbolge trace independently reports 2632 steps for the same program | DEMONSTRATED | `selected_logs/walbolge_quijote_ch001.json` |

Note: "distinct" means separate codebases/tools; we do not claim their
authors never read each other's work.

## E. Translator / Walbolge roundtrip

| id | claim | status | evidence |
|---|---|---|---|
| E1 | Translator product executes back to its exact source text | DEMONSTRATED | toolkit/engine runs of committed specimen |
| E2 | Walbolge roundtrip flags processed/original/words/opcodes all True; bootstrap recognized; 35 words; 101-char output | DEMONSTRATED | walbolge json report |

## F. Boundary conditions (negative space)

| id | claim | status | evidence |
|---|---|---|---|
| F1 | 3^10 tools produce architecturally meaningless results on 3^19 tapes (engine "HALT" after a few thousand steps is bogus) | DEMONSTRATED | showdown init_module rows + analysis in docs/EXPERIMENT_SUMMARY.md |
| F2 | Walbolge does not decompile MalbolgeLISP | BY DESIGN | tool contract; see AGENTS.md trap list |

## G. Loader conventions (added 2026-10-15)

Two image conventions coexist for 3^19 tapes and one loader cannot read both.
`bolge19` keeps the raw convention as its default; `--loader canonical` adds
the strict Unshackled rule. Full probe: `evidence/loader_convention_v1/`.

| id | claim | status | evidence |
|---|---|---|---|
| G1 | `init_module.mb` + `core.mb` are raw cell dumps (byte per cell); `.mu` Translator products are opcode-aligned text where `' ' \t \r \n` are not cells | DEMONSTRATED | `loader_convention_v1/raw/02`–`08`, `raw/12` |
| G2 | A canonical loader rejects the raw dumps loudly (`core.mb` at offset 7, `lisp.mb` at offset 19,392) instead of executing them | DEMONSTRATED | `raw/07`, `raw/08` |
| G3 | `lisp.mb` has exactly one whitespace byte, at offset 19,391 (0-based) — the newline that terminates `init_module.mb` — so the first `core.mb` byte is read at 19,392 with `pos` off by one; trimming cannot repair a mid-file byte, only the loader choice can | DEMONSTRATED | `raw/08`, `raw/12` |
| G4 | Raw-loading an opcode-aligned text image silently corrupts the epochal chain pattern past the image (`pat=[10,581130723,10...]`) and the machine halts with garbage rather than failing | DEMONSTRATED | `raw/04` |
| G5 | `bolge19 --loader canonical` executes an external 3^19 opcode-aligned product correctly, 5/5 and deterministic | DEMONSTRATED | `raw/05`, `raw/06` |
| G6 | bolge19 builds and runs on Linux (zig 0.16.0, `-lc`) and its REPL-session stdout is **byte-identical** to the Windows-recorded transcript; periodic telemetry matches line-for-line through 2,200,000,000 steps | DEMONSTRATED | `raw/01`, `raw/09_lisp_session_*` |
| G7 | What decides whether an image is trim-repairable is the **position** of its whitespace, not its count: trailing bytes displace nothing (`init_module.mb` 1 at 19,391 = its last byte; `artifact.mu` 2 at 2,888,169–170 = its last two bytes), a mid-file byte shifts every later cell (`lisp.mb`) | DEMONSTRATED | `raw/12` with `raw/02`–`05`, `raw/08` |

Note on A5 (2026-10-15): the "exactly 19,337 steps" figure is a
**raw-convention** result — it counts `init_module.mb`'s trailing newline as a
cell. The same bytes under `--loader canonical` halt at 19,301 (`raw/03`). Both
numbers are correct for their loader; citing 19,337 without naming the
convention is now ambiguous, and any cross-engine comparison must state which
loader produced it. A5's label is unchanged.

Note on the published manifest (2026-10-15): `scripts/verify_evidence.py`
currently fails on 63 of 150 entries. Cause classification: 57 entries
reproduce their recorded hash after converting lone LF back to CRLF (content
intact; manifest published against a CRLF checkout), 6 differ in content. This
was true **before** the loader patch and is recorded, not repaired, in
`raw/10_manifest_cause.txt`.

