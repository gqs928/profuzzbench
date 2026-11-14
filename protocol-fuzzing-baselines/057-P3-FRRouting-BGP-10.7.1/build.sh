#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
docker pull "$FRR_IMAGE"
docker image tag "$FRR_IMAGE" frr-target-bench:10.7.1
docker compose --env-file images.env -f compose.yaml build --pull 2>&1 | tee build-logs/build.log
docker image inspect frr-bgp-aflnet-bench:10.7.1 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect frr-target-bench:10.7.1 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/frr-image-identity.txt
printf 'frr_image=%s\n' "$FRR_IMAGE" | tee build-logs/build-base-identities.txt
