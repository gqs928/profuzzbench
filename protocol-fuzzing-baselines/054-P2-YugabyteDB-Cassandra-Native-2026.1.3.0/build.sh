#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
docker pull "$YUGABYTE_IMAGE"
docker image tag "$YUGABYTE_IMAGE" yugabyte-benchmark-base:2026.1.3.0
docker pull "$AFL_BUILDER_IMAGE"
docker image tag "$AFL_BUILDER_IMAGE" scylla-benchmark-builder:2026.3.5
docker build --pull \
  --build-arg YUGABYTE_IMAGE="$YUGABYTE_IMAGE" \
  --build-arg AFL_BUILDER_IMAGE="$AFL_BUILDER_IMAGE" \
  --tag yugabyte-native-fuzz-bench:2026.1.3.0 . 2>&1 | tee build-logs/build-final.log
docker image inspect yugabyte-native-fuzz-bench:2026.1.3.0 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect "$YUGABYTE_IMAGE" --format '{{.Id}} {{.RepoDigests}}' | tee build-logs/yugabyte-image-identity.txt
printf 'build_stage_image=%s\n' "$AFL_BUILDER_IMAGE" | tee build-logs/afl-builder-image-identity.txt
