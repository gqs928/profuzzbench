#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
if ! docker image inspect "$PYNETDICOM_IMAGE" >/dev/null 2>&1; then
  docker pull "$PYNETDICOM_IMAGE"
fi
docker image tag "$PYNETDICOM_IMAGE" pynetdicom-runtime-base:3.12.16
if ! docker image inspect "$AFL_BUILDER_IMAGE" >/dev/null 2>&1; then
  docker pull "$AFL_BUILDER_IMAGE"
fi
docker image tag "$AFL_BUILDER_IMAGE" rockylinux-bench-builder:9.8
docker compose --env-file images.env -f compose.yaml build 2>&1 | tee build-logs/build.log
docker image inspect pynetdicom-aflnet-bench:3.0.4 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect pynetdicom-runtime-base:3.12.16 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/runtime-base-identity.txt
printf 'builder_image=%s\nruntime_base=%s\n' "$AFL_BUILDER_IMAGE" "$PYNETDICOM_IMAGE" | tee build-logs/build-base-identities.txt
