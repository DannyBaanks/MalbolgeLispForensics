# Architecture notes

## Three memory regimes in play

| Regime | Cells | Who needs it |
|---|---|---|
| classic 3^10 | 59,049 | engine, oracle, toolkit, Autobolge, Walbolge, Translator |
| image zone | 0 .. S (S = tape bytes) | every 19-trit run: one byte loads as one cell |
| beyond-image | S .. 3^19 | pattern semantics; where MalbolgeLISP data lives |

## fast20 semantics frozen by this study

- decode: `op = (mem[c] + c + offs[c / (END/3)]) % 94` — the per-region
  offsets are NOT decoration; tapes are built for them. Do not substitute
  the textbook single-region formula.
- encrypt: index a concatenated 135-char string directly with `mem[c]`
  (27-char prefix + 94-char table + 14-char suffix).
- both `c` and `d` advance every cycle; `d` is set absolutely by movd.
- fill rules: `[S, szR)` continuous crazy-chain; beyond `szR`, period-6
  pattern with per-page phase `(page_base % (END/3) + k) % 6` under the
  Cygwin page granularity of the reference runs (64 KiB).

## bolge19 design (Zig, Windows-native)

No virtual-memory tricks. Four plain structures:

1. `image`: flat u32 array of the loaded tape (mutated in place).
2. `chain_zone`: eager crazy-chain for `[S, szR)` — at most one page.
3. `pat[6]` + phase formula for everything past `szR`.
4. `overlay`: hashmap for writes landing beyond the image.

I/O is raw Win32 (`CreateFileW/ReadFile/WriteFile/GetStdHandle`), chosen
deliberately against API churn and against stdio-lock interactions with
fault handlers.

## Lessons that cost us hours (do not relearn them)

- Never ignore mmap return values; on Cygwin the failure mode is silent and
  the resulting fault loop burns a core forever.
- Never `fprintf` from inside or right after fault-handling paths in a
  computed-goto interpreter: poisoned stdio locks present as a hang at full
  CPU. Use `write(2)`-style telemetry only.
- Never arm `SIGALRM/setitimer` against these interpreters under Cygwin:
  first tick freezes execution permanently (A/B tested).
- Reinterpreting a byte buffer as u32 cells lies about its span; allocate
  cell arrays properly (this produced a deterministic access violation at
  exactly bytes/4 cells before being fixed).

## Validation topology

Distinct backends, shared specimens, step-count equality as the oracle:

```
        hello.malbolge          quijote_ch001_full.mal
engine C      40 steps               2632 steps
oracle py     40                     2632 (trace via walbolge)
toolkit py    40                     2632
autobolge zig 40                     2632
```

Step counts agree because all four implement the same 3^10 cycle model;
outputs agree byte-for-byte.
