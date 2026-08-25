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
