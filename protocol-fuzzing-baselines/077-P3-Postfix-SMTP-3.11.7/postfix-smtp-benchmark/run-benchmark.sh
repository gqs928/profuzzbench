#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
tag=${IMAGE_TAG:-postfix-smtp-aflnet-bench:3.11.7}
seconds=${1:-1800}
label=${2:-postfix-smtp-30m-20261113}
[[ $seconds =~ ^[0-9]+$ ]] || exit 2
out="$root/results/$label"
mkdir -p "$out"
[[ -z "$(find "$out" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "run output directory must be empty: $out" >&2
  exit 2
}
docker run --rm --network none --cpus 2 --memory 4g \
  -v "$root/results:/work/results" "$tag" \
  /work/run-container.sh "/work/results/$label" "$seconds"
