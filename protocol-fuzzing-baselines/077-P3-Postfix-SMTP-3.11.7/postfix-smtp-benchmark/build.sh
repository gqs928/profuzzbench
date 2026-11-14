#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
tag=${1:-postfix-smtp-aflnet-bench:3.11.7}
python3 "$root/generate_seeds.py"
(cd "$root"; find . -type f ! -path './results/*' ! -path './build-logs/*' ! -path './__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum > build-logs/build-inputs.sha256)
docker build --progress=plain -t "$tag" "$root" 2>&1 | tee "$root/build-logs/docker-build.log"
docker image inspect "$tag" --format '{{.Id}} {{.Size}}' > "$root/build-logs/image-id-size.txt"
printf 'image=%s\n' "$tag" > "$root/build-logs/image-tag.txt"
container=$(docker create "$tag")
mkdir -p "$root/build-logs/image-evidence"
docker cp "$container:/work/build-evidence/." "$root/build-logs/image-evidence/"
docker cp "$container:/work/source-signature-verification.txt" "$root/build-logs/"
docker rm "$container" >/dev/null
