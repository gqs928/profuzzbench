#!/usr/bin/env bash
set -u
ROOT=${1:-/results/stomp-30m}
total=0;responses=0;no_response=0;errors=0
shopt -s nullglob
for f in "$ROOT"/queue/id:*; do
  [[ -f "$f" ]] || continue
  total=$((total+1)); tmp=$(mktemp)
  if ! exec 3<>/dev/tcp/127.0.0.1/61613; then errors=$((errors+1)); rm -f "$tmp"; continue; fi
  if ! cat "$f" >&3 2>/dev/null; then errors=$((errors+1)); fi
  timeout 1 cat <&3 >"$tmp" 2>/dev/null || true
  exec 3>&-; exec 3<&-
  if grep -aEq 'CONNECTED|MESSAGE|RECEIPT|ERROR' "$tmp"; then responses=$((responses+1)); else no_response=$((no_response+1)); fi
  rm -f "$tmp"
done
printf '{"queue_files":%d,"responses":%d,"no_response":%d,"errors":%d}\n' "$total" "$responses" "$no_response" "$errors"
