#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
if ! docker image inspect "$KNOT_BASE_IMAGE" >/dev/null 2>&1; then
  docker pull "$KNOT_BASE_IMAGE"
fi
docker image tag "$KNOT_BASE_IMAGE" knot-runtime-base:24.04
docker compose --env-file images.env -f compose.yaml build 2>&1 | tee build-logs/build.log
docker image inspect knot-dns-aflnet-bench:3.6.2 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect knot-runtime-base:24.04 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/runtime-base-identity.txt
printf 'runtime_base=%s\n' "$KNOT_BASE_IMAGE" | tee build-logs/build-base-identities.txt
