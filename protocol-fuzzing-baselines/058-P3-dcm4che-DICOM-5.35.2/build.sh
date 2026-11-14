#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
if ! docker image inspect "$DCM4CHE_IMAGE" >/dev/null 2>&1; then
  docker pull "$DCM4CHE_IMAGE"
fi
docker image tag "$DCM4CHE_IMAGE" dcm4che-target-bench:5.35.2
if ! docker image inspect "$AFL_BUILDER_IMAGE" >/dev/null 2>&1; then
  docker pull "$AFL_BUILDER_IMAGE"
fi
docker image tag "$AFL_BUILDER_IMAGE" rockylinux-bench-builder:9.8
docker compose --env-file images.env -f compose.yaml build 2>&1 | tee build-logs/build.log
docker image inspect dcm4che-aflnet-bench:5.35.2 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect dcm4che-target-bench:5.35.2 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/dcm4che-image-identity.txt
printf 'builder_image=%s\nruntime_base=%s\n' "$AFL_BUILDER_IMAGE" "$DCM4CHE_IMAGE" | tee build-logs/build-base-identities.txt
