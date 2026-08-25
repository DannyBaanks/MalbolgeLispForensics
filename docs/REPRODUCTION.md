# Reproduction

All commands are relative to this repository root. Python is invoked as
`py` (3.12). Zig 0.16.0 was used for the VM. Windows assumed for the native
paths; classic-side tools also run elsewhere.

Before reproducing anything, verify the published artifact set:

```
py scripts/verify_evidence.py
```

## 0. Big-specimen provenance (not redistributed here)

`lisp.mb` — SHA-256 recorded in `evidence/hashes/evidence.sha256`
(371,331,415 bytes). Obtain legitimately from the upstream MalbolgeLISP
repository (`lisp.zip`; consult upstream for applicable licensing), extract
`core.mb` + `init_module.mb`,
verify sizes 371,312,023 and 19,392, concatenate in that order, then check
the hash. The normalized dump has the same byte count; its full digest is
in `evidence/selected_logs/normalize_lisp_anchors_stderr.txt`.

## 1. Build the native VM

```
zig build-exe -O ReleaseFast src/bolge19/main.zig -femit-bin=bolge19.exe
```

## 2. Full MalbolgeLISP session (~75 s single core, ~1.5 GB RAM)

Interactive REPL on stdin/stdout:

```
bolge19.exe <path-to lisp.mb>
```

then type e.g. `(+ 1 2)` and expect `3`; Ctrl-Z/EOF prints the farewell
verse and halts with a telemetry line like
`HALT steps=<N> ... elapsed=<s>` (reference machine: 2,408,246,381 steps,
75 s). Non-interactive smoke: pipe one expression in.

## 3. Normalize the tape

```
bolge19.exe <path-to lisp.mb> --normalize normalized.txt
```

Emits one mnemonic per cell plus ANCHOR lines (rolling SHA-256 every 100M
cells / 75 s) and the final census on stderr. Compare your final digest
with `evidence/selected_logs/normalize_lisp_anchors_stderr.txt`.

## 4. Classic agreement suite (cheap)

```
py scripts/run_validation.py
```

Runs hello world and Quijote chapter I across the available backends
(C engine, Python oracle, Python toolkit, Autobolge Zig container via the
BOLG1/BOLG2 format), plus Walbolge roundtrip when its workspace is
available, writing raw stdout/stderr/exit codes under
`evidence/validation/`. Expected: "Hello World!" at 40 steps everywhere;
Quijote text at 2632 steps.

## 5. fast20 patch (optional)

Apply `src/patches/fast20_fixed.c` logic to any fast20 checkout: the only
semantic-neutral change is replacing both `mmap(MAP_FIXED)` protection
flips with `mprotect`. First reproduce the original defect with
`src/diagnostics/mmap_repro.c` compiled under Cygwin gcc:
expected output contains `flip-fixed r=0xffffffffffffffff` (MAP_FAILED)
and `Invalid argument`.

## 6. Translator/Walbolge roundtrip

Use the Translator to compile any text into `.mal` + manifest + word files,
execute the `.mal` with any 3^10 backend, then run Walbolge with
`--manifest/--words-dir` and require all four roundtrip flags True. The
committed Quijote specimen already satisfies this end-to-end.
