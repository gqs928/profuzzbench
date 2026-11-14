#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
tag=${1:-pjsip-native-fuzz-bench:2.17}
mkdir -p "$root/build-logs"
(
  cd "$root"
  find . -type f ! -path './results/*' ! -path './build-logs/*' -print0 | sort -z | xargs -0 sha256sum > build-logs/build-inputs.sha256
)
docker build --progress=plain -t "$tag" "$root" 2>&1 | tee "$root/build-logs/docker-build.log"
docker image inspect "$tag" --format '{{.Id}} {{.Size}}' > "$root/build-logs/image-id-size.txt"
printf 'image=%s
' "$tag" > "$root/build-logs/image-tag.txt"
