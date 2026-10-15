# NOT_DEMONSTRATED

Explicit honesty ledger. Nothing here may be promoted to a claim without a
new probe stored under `evidence/`.

1. **fast20-fixed reaching the REPL banner.** After the mprotect patch,
   fast20 loads and executes at full speed, but an observed banner was never
   captured from it on the test machine (telemetry/stdio merge limitations
   of the Cygwin binary). bolge19 is the interpreter whose REPL session is
   DEMONSTRATED.

2. **Formal performance benchmark, bolge19 vs upstream fast20.** We report
   one machine, one session (~5.7e8 steps/s delta-telemetry; 75 s wall for
   2.4e9 steps including I/O). No controlled benchmark suite was run; no
   cross-hardware comparison exists.

3. **bolge19 speaking the BOLG1/BOLG2 container format.** The Autobolge
   container validation used Autobolge's own Zig VM. bolge19's CLI takes a
   raw `.mb` image directly. Container integration is future work.

4. **Walbolge applied to MalbolgeLISP.** Never attempted seriously and not
   expected to be meaningful: Walbolge decompiles Translator-shaped 3^10
   programs. Listed to prevent narrative creep.

5. **Universality / minimality / correctness-proof claims of any kind.**
   Nothing here proves MalbolgeLISP computes everything computable, that
   bolge19 is bug-free, or that any implementation is minimal.

6. **Architectural independence of the classic backends.** They are distinct
   implementations/tools; we did not audit their authorship histories.
   Step-count agreement is reported as-is.

7. **Cross-platform behavior of bolge19.** Developed and validated on
   Windows only (Win32 I/O layer). POSIX portability is unplanned.

8. **Reproduction of the 75 s run on other machines.** Memory pressure,
   storage speed and CPU differ; only the artifact hashes are portable
   promises, not the timings.

9. **Reproducing `HALT steps=2408246381` (A4) from recorded inputs.** The full
   Lisp session's stdout is byte-identical across runs and platforms, and the
   periodic telemetry matches the published log line-for-line through
   2,200,000,000 steps, but the final step count depends on the exact stdin
   byte stream: piping `(+ 1 2)` plus EOF halts at 2,401,426,208, and adding one
   `0x1A` byte halts at 2,686,077,407 — both with the same final machine state
   `c=581143360 d=581861866 a=10`. The original interactive transcript was
   never pinned in evidence, so A4's number cannot be re-derived, only
   respected. No divergence of the machine is claimed either way.
   Probe: `evidence/loader_convention_v1/raw/09_lisp_session_*`.

10. **Whether the 6 content-changed manifest entries are deliberate edits.**
    `evidence/hashes/evidence.sha256` does not describe HEAD for 63 of its 150
    entries; 57 of those are line-ending-only and 6 (`README.md`, `.gitignore`,
    `docs/REPRODUCTION.md`, `scripts/run_validation.py`,
    `src/bolge19/main.zig`, `src/patches/fast20_fixed.c`) differ in content.
    Their hashes were recorded before a Windows-to-Linux transition, and this
    repository's history was published in two initial commits, so intent cannot
    be recovered from it. Nothing was rewritten to make the numbers look right.
    Probe: `evidence/loader_convention_v1/raw/10_manifest_cause.txt`.

Item 7 above (POSIX portability "unplanned") is now partially superseded by
claim G6: the committed source has no Win32 calls and runs on Linux. The
Win32-era rationale in `docs/ARCHITECTURE.md` stays as written history.
