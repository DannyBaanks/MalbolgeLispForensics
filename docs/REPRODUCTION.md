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

## 5. fast20 patch (Windows and Linux)

We provide both a production clean interpreter (`src/patches/fast20_clean.c`), an
instrumented diagnostic version (`src/patches/fast20_fixed.c`), and a unified patch
(`src/patches/fast20.patch`) applicable against `third_party/upstream/fast20.c`.

Two defects are repaired:
1. **Windows / Cygwin `EINVAL`:** Upstream used `mmap(MAP_FIXED)` inside `sigsegvh`, which
   fails with `EINVAL` over a `PROT_NONE` reservation on Cygwin, causing an infinite retry loop
   at 100% CPU. Fixed by using `mprotect(PROT_READ|PROT_WRITE)`.
   Reproduce the original Cygwin defect with `src/diagnostics/mmap_repro.c`: expected output
   contains `flip-fixed r=0xffffffffffffffff` (MAP_FAILED) and `Invalid argument`.
2. **Linux `.rodata` read overflow:** Upstream indexed the 135-byte encryption table directly
   (`xlat[mem[c]]`). When `mem[c] >= 135` after `crz`/`rot`, Linux ELF throws `SIGSEGV` when reading
   outside `.rodata`. Fixed with the bounds check `if (mem[c] < 135)`.

Build clean production interpreter:
```
gcc -O3 src/patches/fast20_clean.c -o fast20
```

Build instrumented diagnostic interpreter:
```
gcc -O3 src/patches/fast20_fixed.c -o src/patches/fast20_fixed
```

## 6. Translator/Walbolge roundtrip

Use the Translator to compile any text into `.mal` + manifest + word files,
execute the `.mal` with any 3^10 backend, then run Walbolge with
`--manifest/--words-dir` and require all four roundtrip flags True. The
committed Quijote specimen already satisfies this end-to-end.

## 7. Loader convention probe

Two image conventions exist for 3^19 tapes and `bolge19` can read either. The
default (`raw`) is what every claim in `docs/CLAIMS.md` A1–A5 was measured
under; `--loader canonical` implements the strict Unshackled reader for
opcode-aligned text images.

```
bolge19.exe <image>                              # raw cell dump (default)
bolge19.exe <image> --loader canonical           # opcode-aligned text
```

On Linux the build needs `-lc`, which the Windows command in section 1 does not:

```
zig build-exe -O ReleaseFast src/bolge19/main.zig -lc -femit-bin=bolge19
```

Spot checks, relative to this repository root, with the specimens in a sibling
directory:

```
printf '0\n' | ./bolge19 <dir>/init_module.mb                        # HALT steps=19337
printf '0\n' | ./bolge19 <dir>/init_module.mb --loader canonical     # HALT steps=19301
./bolge19 <dir>/lisp.mb --loader canonical                           # rejects: byte=19392
```

Full probe (sanitized captures, specimens pinned by hash, each probe SKIPs on
drift), executed here on Linux with zig 0.16.0:

```
LISP_RUNTIME_DIR=<dir with init_module.mb core.mb lisp.mb> \
EXT_SPECIMEN_DIR=<dir with artifact.mu> \
bash evidence/loader_convention_v1/capture.sh
sha256sum -c evidence/hashes/loader_convention_v1.sha256
python3 evidence/loader_convention_v1/tools/manifest_cause.py
```

`scripts/verify_evidence.py` currently reports 63 mismatches out of 150 for
reasons that predate this probe: 57 are line-ending-only (the manifest was
published against a CRLF checkout) and 6 are content changes. The cause
classification is reproducible with the last command above and is recorded in
`evidence/loader_convention_v1/raw/10_manifest_cause.txt`.
