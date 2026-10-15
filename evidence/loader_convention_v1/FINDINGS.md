# Loader convention probe (V0)

Probes the relationship between `bolge19`'s loader and the two image
conventions that coexist in this line of work, and records the regression
check for the claims that depend on the raw convention.

Status vocabulary is the one in `docs/CLAIMS.md`.

## What was changed in the source

`src/bolge19/main.zig` gained `--loader raw|canonical` (default `raw`) and a
whitespace warning on the raw path. The canonical loader implements the strict
Unshackled rule: `' ' \t \r \n` are not cells; a byte is accepted only when
`33 <= v < 127` and `mod(v + pos, 94)` is one of `{4,5,23,39,40,62,68,81}`;
`pos` advances only on accepted cells and wraps at 564; anything else aborts
the load. The default path is untouched, so every existing claim keeps its
numbers. Build on Linux: `zig build-exe -O ReleaseFast main.zig -lc` (`-lc` is
needed here; the documented Windows command does not use it).

## The two conventions (DEMONSTRATED)

Same VM, same source, only the loader differs:

| specimen | bytes | loader | result | capture |
|---|---|---|---|---|
| `init_module.mb` | 19,392 | raw (default) | HALT steps=**19,337** `c=19435 d=19 a=710270897` | `raw/02` |
| `init_module.mb` | 19,392 | canonical | HALT steps=**19,301** `c=19399 d=387450038 a=182815712` | `raw/03` |
| external `artifact.mu` | 2,888,171 | raw | HALT steps=20,163, `pat=[10,581130723,10...]`, garbage output | `raw/04` |
| external `artifact.mu` | 2,888,171 | canonical | 5/5 correct outputs, deterministic (`raw/06`) | `raw/05` |
| `core.mb` | 371,312,023 | canonical | rejects at `byte=7 v=99 instr=12` | `raw/07` |
| `lisp.mb` | 371,331,415 | canonical | rejects at `byte=19392 v=40 instr=67` | `raw/08` |

`opcode-aligned text` (`init_module.mb`, and `.mu` products of the HeLL/LMFAO
line) is what the canonical loader reads. `raw cell dumps` (`core.mb`,
`lisp.mb`) are what the default loader reads. Neither convention is a superset
of the other, and this is why one engine cannot load both:

* `lisp.mb` carries exactly one whitespace byte, at position 19,391 — the
  newline that ends `init_module.mb` and therefore lands **mid-file** after
  `concat(init_module.mb, core.mb)`. A mid-file whitespace byte displaces every
  later cell, so no post-hoc trimming repairs it: only a loader choice does.
* `init_module.mb`'s single whitespace byte is the trailing newline, i.e. at
  the end. It is the one case where trimming and a loader port agree, and both
  are recorded above (19,337 vs 19,301 — different programs by the loader's
  choice, both legitimate).

The `artifact.mu` rows also reproduce the epochal-chain seeding effect: under
raw loading the two spacing cells corrupt the pattern past the image
(`pat=[10,581130723,10...]`, intolerant) and the machine halts after 20,163
steps with garbage instead of failing loudly. The warning line in `raw/04` and
`raw/02` exists to disarm exactly that silent failure.

## Whitespace census (raw/12)

| specimen | bytes | ws count | ws offsets | where |
|---|---|---|---|---|
| `init_module.mb` | 19,392 | 1 | 19,391 | last byte (trailing) |
| `core.mb` | 371,312,023 | 0 | — | clean raw dump |
| `lisp.mb` | 371,331,415 | 1 | 19,391 | **mid-file** |
| external `artifact.mu` | 2,888,171 | 2 | 2,888,169 · 2,888,170 | last two bytes (trailing) |

Position, not count, decides the repair. A **trailing** spacing byte displaces
nothing, so deleting it and changing the loader are two routes to the same
image — that is why `init_module.mb` and `artifact.mu` can be pre-trimmed. A
**mid-file** byte shifts every later cell by one, so only the loader choice is
correct: `lisp.mb`'s single newline is the last byte of the `init_module.mb`
prefix and therefore sits 19,391 bytes inside a 371 MB tape. Nothing that keeps
the tape intact can fix that, and the canonical loader's right answer on
`lisp.mb` is to refuse the load (`raw/08`), not to guess.

## External specimen (not redistributed)

`artifact.mu`, SHA-256
`3b9bdf37eb708ec751d10f0dea32edde4375e526ce56fd2dd440f5a22819ba10`,
2,888,171 bytes, is a 3^19 product authored in the **MALDOOM** evidence set
(`evidence/M0_KILLER_UNSHACKLED_V0/`), not MalbolgeLISP and not upstream work.
It is referenced by hash here and is not copied into this repository, per
`AGENTS.md` rule 6. It is a 3^19 Translator-product-class specimen: it does not
say anything about MalbolgeLISP's semantics.

## Regression check on the flagship session (A1–A4)

Run with the patched binary on the **default** path, so this is a check that
nothing moved. See `raw/09_lisp_session_reproduce.txt` and
`raw/09_lisp_session_telemetry.txt`.

* stdout is **byte-identical** to the published transcript
  (`b3214e29…`, the hash in `evidence/hashes/evidence.sha256` for
  `bolge19_lisp_session_stdout.txt`). DEMONSTRATED, `[CURRENT]`, Linux.
* the header line and the periodic telemetry agree with the published stderr
  line-for-line through **2,200,000,000 steps** (same `c`, `d`, `a`,
  `overlay`); the published log's 2,400,000,000 line differs. DEMONSTRATED.
* the published `HALT steps=2408246381` was **not** reproduced: this run
  halted at `2401426208` with the **same final state** `c=581143360 d=581861866
  a=10`. Adding one stdin byte (`0x1A`) moves it again to `2686077407`, again
  with the identical final state. So the step count of the full session is a
  function of the exact stdin byte stream, while the transcript and the halt
  state are not — and the original interactive transcript is not pinned in the
  published evidence. NOT_DEMONSTRATED: reproducing 2,408,246,381 from recorded
  inputs. This is a provenance gap in the input, not a divergence in the
  machine, and no claim in either direction is made here about A4's number.
* `elapsed=75s` (published) vs `35s` here is a machine difference, recorded as
  measured, no claim attached.

## This repository's own published manifest does not describe HEAD

`scripts/verify_evidence.py` fails. Cause classification in
`raw/10_manifest_cause.txt` (tool: `tools/manifest_cause.py`):

```
hashed_entries=150  recorded_hash_matches_head=87  line_ending_only=57  content_change=6
content_change: .gitignore  README.md  docs/REPRODUCTION.md
                scripts/run_validation.py  src/bolge19/main.zig  src/patches/fast20_fixed.c
```

* **57** mismatched entries reproduce their recorded hash exactly after
  converting lone LF back to CRLF: content intact, manifest published against
  a CRLF checkout. This is consistent with the Windows-era migration; it is a
  re-sealing question, not a data-loss question.
* **6** differ in content. `src/bolge19/main.zig` was already in that set
  **before** this probe (HEAD's copy did not match either), so this patch
  neither caused nor fixed it.
* Nothing here was rewritten. `evidence/hashes/evidence.sha256` is left exactly
  as published (append-or-add-only), and this probe ships its own manifest.
* Whether the 6 content changes are legitimate post-publication edits or
  accidental is NOT_DEMONSTRATED: it needs the release history of each file,
  and this repository was published in two squashed-looking initial commits.

## Exit statuses

`raw/11_exit_statuses.txt`: unknown `--loader` value → 2; canonical rejection →
2; successful load → 0. The pre-existing error paths (unreadable file, bad
size, short read) still return 0, unchanged — recorded because "exit 0" is not
evidence of a good load on those paths.

## Sanitization rules

Applied by `capture.sh` before writing anything to `raw/`:
`$LISP_RUNTIME_DIR` → `<LISP_RUNTIME_DIR>`, `$EXT_SPECIMEN_DIR` →
`<EXT_SPECIMEN_DIR>`, the evidence directory → `<EVIDENCE_DIR>`, the repository
root → `<REPO>`. Probes `cd` into the specimen directory and pass a bare
filename, so the VM's own path echo is already relative. `grep -rn '/home'`
over `raw/` returns nothing.

## Reproduce

```
LISP_RUNTIME_DIR=<dir with init_module.mb core.mb lisp.mb> \
EXT_SPECIMEN_DIR=<dir with artifact.mu> \
bash evidence/loader_convention_v1/capture.sh
sha256sum -c evidence/hashes/loader_convention_v1.sha256
```

Each probe re-verifies its specimen's SHA-256 first and prints `SKIP …
drifted` instead of producing a number if it moved.

## Scope

This probe is about loaders. It does not decompile anything, does not extend
the 3^10 classic-agreement claims, and does not change any MalbolgeLISP
semantic claim. The canonical loader's accept set is the classic opcode set
read from `vendor/Unshackled.c` in the MALDOOM working tree; it is recorded
here as an observed rule with an observed effect, not as a re-derivation of
MalbolgeLISP's semantics.
