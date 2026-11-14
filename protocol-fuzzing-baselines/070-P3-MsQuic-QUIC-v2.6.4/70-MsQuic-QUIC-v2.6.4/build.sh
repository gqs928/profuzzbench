#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs results
docker compose --env-file images.env -f compose.yaml build fuzz 2>&1 | tee build-logs/docker-build.log
docker image inspect --format '{{.Id}}' msquic-aflnet-bench:v2.6.4 | tee build-logs/image-id.txt
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz /opt/benchmark/build-info.sh \
  | tee build-logs/build-info.txt
docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
  python3 /opt/benchmark/validate_seeds.py /opt/benchmark/seeds \
  | tee results/seed-validation.json
