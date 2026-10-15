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

> Note (2026-10-15): the paragraph above describes the published Windows
> build. The `src/bolge19/main.zig` now in HEAD declares `fopen/fread/fwrite`
> and POSIX `read` and contains no Win32 calls; it builds on Linux with
> `-lc`. The design rationale (do not `fprintf` from fault paths) still
> applies, but the API list is historical. Recorded as `raw/01` and `raw/09`
> in `evidence/loader_convention_v1/`.

### Two image conventions, one loader switch

A 3^19 tape arrives in one of two shapes and they are not interchangeable:

* **Raw cell dump** — one byte per cell, everything counts, including bytes
  `32/9/10/13`. `core.mb`, and therefore `lisp.mb`.
* **Opcode-aligned text** — the strict Unshackled reader: `' ' \t \r \n` are
  not cells, a byte is accepted only when `33 <= v < 127` and
  `mod(v + pos, 94)` is in `{4,5,23,39,40,62,68,81}`, and `pos` advances only
  on accepted cells (wrapping at 564). HeLL/LMFAO `.mu` products are written
  for this reader.

`bolge19` loads raw by default, because that is the convention every claim in
`docs/CLAIMS.md` A1–A5 was measured under. `--loader canonical` implements the
strict rule for text images, and the raw path prints a warning when a tape
contains spacing bytes so that loading a text image by mistake cannot pass
silently: it corrupts `pat[]` past the image and the machine halts with garbage
in ~20k steps instead of failing. See `evidence/loader_convention_v1/`.

Consequence for cross-engine comparison: step counts are only comparable when
the loader convention is named. The same `init_module.mb` bytes halt at 19,337
(raw) or 19,301 (canonical), and `lisp.mb` cannot be canonical-loaded at all
because its one newline sits 19,391 bytes inside the tape.

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
