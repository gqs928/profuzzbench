#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs results seeds
set -a
source images.env
set +a
docker compose --env-file images.env -f compose.yaml build --pull fuzz 2>&1 | tee build-logs/docker-build.log
docker image inspect "$QUICHE_IMAGE" --format '{{.Id}} {{.RepoTags}}' | tee build-logs/image-id.txt
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/build-info.sh 2>&1 | tee build-logs/build-info.txt
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  bash /opt/benchmark/generate-seeds.sh 2>&1 | tee results/seed-generation-console.log
