#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE=mediamtx-rtmp-aflnet:v1.21.3
mkdir -p "$ROOT/results/build"
docker build --progress=plain -t "$IMAGE" "$ROOT" 2>&1 | tee "$ROOT/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "$IMAGE" > "$ROOT/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "$IMAGE" > "$ROOT/results/build/image-digests.json"
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$ROOT/results:/work/results" "$IMAGE" -lc '/work/capture-build.sh'
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$ROOT/results:/work/results" "$IMAGE" \
  -lc 'bash /work/run.sh /work/results/preflight/aflnet-60s 60 && bash /work/validate.sh /work/results/preflight/aflnet-60s'
test -s "$ROOT/results/preflight/aflnet-60s/campaign/aflnet-out/fuzzer_stats"
test -s "$ROOT/results/preflight/aflnet-60s/campaign/aflnet-out/ipsm.dot"
printf 'built and RTMP response-state preflight passed: %s\n' "$IMAGE"
