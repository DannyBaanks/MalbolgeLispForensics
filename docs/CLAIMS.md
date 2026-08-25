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
