#!/usr/bin/env bash
set -euo pipefail

OUTDIR="${1:-/work/results/rtsp-30m}"
GO=/usr/local/go/bin/go
[[ -x "${GO}" ]] || { echo "Go toolchain is missing at ${GO}." >&2; exit 2; }
mkdir -p "${OUTDIR}/coverage-scope-breakdown"

for scope in campaign post-smoke; do
  input="${OUTDIR}/go-coverdata"
  [[ "${scope}" == post-smoke ]] && input="${OUTDIR}/post-smoke/go-coverdata"
  test -n "$(find "${input}" -type f -name 'covcounters.*' -print -quit)"
  raw="${OUTDIR}/coverage-scope-breakdown/${scope}.out"
  summary="${OUTDIR}/coverage-scope-breakdown/${scope}-summary.txt"
  "${GO}" tool covdata textfmt -i="${input}" -o="${raw}"
  (cd /src/mediamtx && "${GO}" tool cover -func="${raw}") > "${summary}"
done

printf 'campaign_coverage_data=%s\npost_smoke_coverage_data=%s\nmerged_coverage_data=%s\n' \
  "${OUTDIR}/go-coverdata" "${OUTDIR}/post-smoke/go-coverdata" "${OUTDIR}/go-coverdata-merged" \
  > "${OUTDIR}/coverage-scope-breakdown/README.txt"
