#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
docker pull "$NATS_IMAGE"
docker image tag "$NATS_IMAGE" nats-target-bench:2.15.3
docker pull "$DEBIAN_IMAGE"
docker image tag "$DEBIAN_IMAGE" debian-bench:bookworm-slim
docker pull "$AFL_BUILDER_IMAGE"
docker image tag "$AFL_BUILDER_IMAGE" rockylinux-bench-builder:9.8
docker build --pull \
  --build-arg NATS_IMAGE="$NATS_IMAGE" \
  --build-arg DEBIAN_IMAGE="$DEBIAN_IMAGE" \
  --build-arg AFL_BUILDER_IMAGE="$AFL_BUILDER_IMAGE" \
  --tag nats-aflnet-bench:2.15.3 . 2>&1 | tee build-logs/build.log
docker image inspect nats-aflnet-bench:2.15.3 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect nats-target-bench:2.15.3 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/nats-image-identity.txt
printf 'builder_image=%s\nruntime_base=%s\n' "$AFL_BUILDER_IMAGE" "$DEBIAN_IMAGE" | tee build-logs/build-base-identities.txt
