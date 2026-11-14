#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
docker pull "$ZOOKEEPER_IMAGE"
docker image tag "$ZOOKEEPER_IMAGE" zookeeper-bench:3.9.7
docker pull "$AFL_BUILDER_IMAGE"
docker image tag "$AFL_BUILDER_IMAGE" rockylinux-bench-builder:9.8
docker build --pull \
  --build-arg ZOOKEEPER_IMAGE="$ZOOKEEPER_IMAGE" \
  --build-arg AFL_BUILDER_IMAGE="$AFL_BUILDER_IMAGE" \
  --tag zookeeper-aflnet-bench:3.9.7 . 2>&1 | tee build-logs/build-final.log
docker image inspect zookeeper-aflnet-bench:3.9.7 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect zookeeper-bench:3.9.7 --format '{{.Id}} {{.RepoDigests}}' | tee build-logs/zookeeper-image-identity.txt
printf 'build_stage_image=%s\n' "$AFL_BUILDER_IMAGE" | tee build-logs/afl-builder-image-identity.txt
