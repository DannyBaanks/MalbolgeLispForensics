# AGENTS.md — malbolge-lisp-forensics

Contract for agents touching this repository. Read before editing.

## Nature

This is a **forensics/publication repository**: curated evidence + minimal
source needed to reproduce the claims in docs/CLAIMS.md. It is NOT a lab.
Experiments happen elsewhere; only frozen, hashed results enter here.

## Hard rules

1. Evidence files under `evidence/` are append-or-add-only. Never rewrite a
   recorded artifact to match a new narrative; add corrections as new files.
2. Every claim in `docs/CLAIMS.md` must cite at least one file under
   `evidence/` (or an exact command in docs/REPRODUCTION.md).
3. Labels: DEMONSTRATED / OBSERVED / NOT_DEMONSTRATED. Never upgrade a label
   without a fresh probe stored in evidence.
4. Keep the 3^10 vs 3^19 boundary explicit everywhere. Walbolge decompiles
   3^10 Translator products; it does not decompile MalbolgeLISP. Never blur.
5. No absolute workstation paths anywhere: manifests use relative paths;
   logs are included only if path-free or sanitized with documented rules.
6. Large specimens (`*.mb`, normalized dumps) are referenced by SHA-256, not
   committed. Do not redistribute them from this repository; consult upstream
   for provenance and the licensing terms that apply to the complete distribution.
7. Upstream attribution is non-negotiable: MalbolgeLISP/fast20 are upstream work
   by their author; the bundled fast20 snapshot carries its upstream CC0 license,
   while our patches/VM are separate and marked.

## Reproduction entry points

- `scripts/run_validation.py` — cheap suite (classic agreement, roundtrip,
  autobolge container check) writing raw output under
  `evidence/validation/`.
- `docs/REPRODUCTION.md` — full pipeline including the 75 s / 2.4B-step run.

## Known traps

- Cygwin `mmap(MAP_FIXED)` over PROT_NONE returns EINVAL here; never "fix"
  code by trusting mmap return-value-less patterns (see src/diagnostics).
- Do not point Walbolge at `lisp.mb`; wrong-model tooling produces plausible
  garbage (documented in docs/CLAIMS.md, section F).
- `init_module.mb` alone is not the Lisp; it is a fragment. Only
  `concat(init_module.mb, core.mb) == lisp.mb` boots a REPL.
