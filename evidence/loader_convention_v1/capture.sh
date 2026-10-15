#!/usr/bin/env bash
# Loader-convention probe: two image conventions, one VM.
#
# What is stored here is sanitized: every absolute path that would identify a
# workstation is replaced by a placeholder before it is written (rules listed in
# FINDINGS.md, "Sanitization rules"). Specimens are never copied into this
# repository; they are pinned by SHA-256 and each probe SKIPS if the local copy
# has drifted, so a later edit elsewhere cannot silently invalidate this record.
#
# Inputs (env):
#   LISP_RUNTIME_DIR  directory holding init_module.mb, core.mb, lisp.mb
#   EXT_SPECIMEN_DIR  directory holding an external 3^19 .mu product (provenance
#                     and hash in FINDINGS.md; not redistributed here)
#   LC_OUT            output directory (default: ./raw next to this script)
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SRC_DIR="$REPO/src/bolge19"
OUT="${LC_OUT:-$HERE/raw}"
RT="${LISP_RUNTIME_DIR:?set LISP_RUNTIME_DIR}"
EXT="${EXT_SPECIMEN_DIR:-}"
mkdir -p "$OUT"
BIN="$OUT/lc_bolge19"

sedargs=(-e "s|$RT|<LISP_RUNTIME_DIR>|g" -e "s|$HERE|<EVIDENCE_DIR>|g" -e "s|$REPO|<REPO>|g")
[ -n "$EXT" ] && sedargs+=(-e "s|$EXT|<EXT_SPECIMEN_DIR>|g")
san() { sed "${sedargs[@]}"; }

expect() { # expect <sha> <path> <label>
  [ "$(sha256sum "$2" | cut -d' ' -f1)" = "$1" ] || { echo "SKIP $3: drifted from $1"; return 1; }
}

INIT_SHA=4b3080fd250a4193030ec647e6c496f90540c1546f717b923284ea31b411e812
CORE_SHA=70e9155bbe44b58a0a44795cf0c614b214c8f31f82270f4913394e07f1f3e53a
LISP_SHA=092df5cdc240de33a355d3cf82bdf09e0859c5827ee57a65bf93dfc37e8f3256
MU_SHA=3b9bdf37eb708ec751d10f0dea32edde4375e526ce56fd2dd440f5a22819ba10

# --- 01: build the committed source, record exactly what was built ------------
( cd "$SRC_DIR" || exit 1
  { printf 'zig=%s\nsource=%s\nsource_sha256=%s\n' "$(zig version)" "src/bolge19/main.zig" "$(sha256sum main.zig | cut -d' ' -f1)"
    printf 'build_cmd=zig build-exe -O ReleaseFast main.zig -lc -femit-bin=<EVIDENCE_DIR>/lc_bolge19\n'
    zig build-exe -O ReleaseFast main.zig -lc -femit-bin="$BIN" 2>&1
    printf 'binary_sha256=%s\n' "$(sha256sum "$BIN" | cut -d' ' -f1)"; } | san > "$OUT/01_build.txt" 2>&1 )

# --- 02/03: the standalone module under both loaders --------------------------
if expect "$INIT_SHA" "$RT/init_module.mb" init_module; then
  ( cd "$RT" && printf '0\n' | "$BIN" init_module.mb 2>&1 ) | san > "$OUT/02_init_module_raw.txt"
  ( cd "$RT" && printf '0\n' | "$BIN" init_module.mb --loader canonical 2>&1 ) | san > "$OUT/03_init_module_canonical.txt"
fi

# --- 04..06: external 3^19 product under both loaders -------------------------
if [ -n "$EXT" ] && expect "$MU_SHA" "$EXT/artifact.mu" artifact.mu; then
  ( cd "$EXT" && printf '0\n' | "$BIN" artifact.mu 2>&1 ) | san > "$OUT/04_mu_raw_silent_corruption.txt"
  { for i in 0 1 2 3 4; do
      o=$( cd "$EXT" && printf '%s\n' "$i" | "$BIN" artifact.mu --loader canonical 2>/dev/null | xxd -p | tr -d '\n')
      e=$( cd "$EXT" && printf '%s\n' "$i" | "$BIN" artifact.mu --loader canonical 2>&1 >/dev/null | sed -n 's/.*HALT steps=\([0-9]*\).*/\1/p')
      printf 'canonical  in=%s  stdout=%s  steps=%s\n' "$i" "${o:-none}" "${e:-no-halt}"
    done; } > "$OUT/05_mu_canonical_matrix.txt" 2>&1
  { for r in 1 2 3; do
      o=$( cd "$EXT" && printf '0\n' | "$BIN" artifact.mu --loader canonical 2>/dev/null | xxd -p | tr -d '\n')
      e=$( cd "$EXT" && printf '0\n' | "$BIN" artifact.mu --loader canonical 2>&1 >/dev/null | sed -n 's/.*HALT steps=\([0-9]*\).*/\1/p')
      printf 'rep=%s  stdout=%s  steps=%s\n' "$r" "${o:-none}" "${e:-no-halt}"
    done; } > "$OUT/06_mu_canonical_reps.txt" 2>&1
fi

# --- 07/08: raw cell dumps are not loadable by the canonical loader -----------
if expect "$CORE_SHA" "$RT/core.mb" core; then
  ( cd "$RT" && "$BIN" core.mb --loader canonical 2>&1 ) | san > "$OUT/07_core_canonical_reject.txt"
fi
expect "$LISP_SHA" "$RT/lisp.mb" lisp || exit 0

( cd "$RT" && "$BIN" lisp.mb --loader canonical 2>&1 ) | san > "$OUT/08_lisp_canonical_reject.txt"

# --- 09: full Lisp session on the raw default path, against the published
#         transcript in evidence/selected_logs/
(
  cd "$RT" || exit 1
  LOG="$REPO/evidence/selected_logs/bolge19_lisp_session_stdout.txt"
  ERR="$REPO/evidence/selected_logs/bolge19_lisp_session_stderr.txt"
  { printf 'published_stdout_sha256=%s\n' "$(sha256sum "$LOG" | cut -d' ' -f1)"
    printf 'published_halt=%s\n' "$(grep -o 'HALT steps=[0-9]*.*' "$ERR")"
    printf 'published_image_line=%s\n' "$(grep -o 'imagen=.*' "$ERR" | san)"
    printf '(+ 1 2)\n' | "$BIN" lisp.mb > "$OUT/.r1.out" 2>"$OUT/.r1.err"; st=$?
    printf 'run1_status=%s\n' "$st"
    printf 'run1_stdout_sha256=%s\n' "$(sha256sum "$OUT/.r1.out" | cut -d' ' -f1)"
    printf 'run1_stdout_vs_published=%s\n' "$(cmp -s "$OUT/.r1.out" "$LOG" && echo IDENTICAL || echo DIFFERS)"
    printf 'run1_image_line=%s\n' "$(grep -o 'imagen=.*' "$OUT/.r1.err" | san)"
    printf 'run1_halt=%s\n' "$(grep -o 'HALT steps=[0-9]*.*' "$OUT/.r1.err")"
    printf 'one_extra_stdin_byte_0x1A_halt='
    printf '(+ 1 2)\n\032\n' | "$BIN" lisp.mb 2>&1 >/dev/null | grep -o 'HALT steps=[0-9]*.*'
    } | san > "$OUT/09_lisp_session_reproduce.txt" 2>&1
  grep 'imagen=\|steps=\|HALT\|AVISO' "$OUT/.r1.err" | san > "$OUT/09_lisp_session_telemetry.txt"
  rm -f "$OUT/.r1.out" "$OUT/.r1.err"
)

# --- 10: integrity of this repository's own published hash manifest -----------
( cd "$REPO" && python3 "$HERE/tools/manifest_cause.py" ) 2>&1 | san > "$OUT/10_manifest_cause.txt"

# --- 11: argument handling and exit statuses ----------------------------------
# bolge19 has always returned 0 on its pre-existing error paths; the two paths
# added by the loader flag report 2 so automation can detect a convention
# mismatch. Recorded explicitly because "exit 0" is not proof of a good load.
( cd "$RT"
  { printf '0\n' | "$BIN" init_module.mb --loader bogus 2>&1
    printf 'exit_unknown_flag=%s\n' "${PIPESTATUS[1]}"
    "$BIN" core.mb --loader canonical 2>&1
    printf 'exit_canonical_reject=%s\n' "$?"
    printf '0\n' | "$BIN" init_module.mb --loader canonical 2>&1 >/dev/null | grep -o 'HALT steps=.*'
    printf 'exit_good_load=%s\n' "${PIPESTATUS[1]}"
  } ) | san > "$OUT/11_exit_statuses.txt"

# --- 12: whitespace census - the observable difference between conventions ----
CENSUS=(init_module.mb core.mb lisp.mb)
[ -n "$EXT" ] && CENSUS+=("artifact.mu=$EXT/artifact.mu")
( cd "$REPO" && python3 "$HERE/tools/census.py" "${CENSUS[@]}" ) 2>&1 | san > "$OUT/12_whitespace_census.txt"

for f in lc_bolge19 lc_bolge19.o lc_bolge19.d lc_bolge19.dwarf lc_bolge19.pdb; do
  [ -e "$OUT/$f" ] && rm -f "$OUT/$f"
done
ls -1 "$OUT"
