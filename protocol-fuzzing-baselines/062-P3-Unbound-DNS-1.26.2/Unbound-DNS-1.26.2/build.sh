#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
if ! docker image inspect "$UNBOUND_BASE_IMAGE" >/dev/null 2>&1; then
  docker pull "$UNBOUND_BASE_IMAGE"
fi
docker image tag "$UNBOUND_BASE_IMAGE" unbound-runtime-base:24.04
docker compose --env-file images.env -f compose.yaml build 2>&1 | tee build-logs/build.log
docker image inspect unbound-dns-aflnet-bench:1.26.2 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect unbound-runtime-base:24.04 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/runtime-base-identity.txt
printf 'runtime_base=%s\nproduct_version=%s\n' "$UNBOUND_BASE_IMAGE" "$UNBOUND_VERSION" | tee build-logs/build-base-identities.txt
docker run --rm unbound-dns-aflnet-bench:1.26.2 /opt/unbound/sbin/unbound -V | tee build-logs/unbound-version.txt
docker run --rm unbound-dns-aflnet-bench:1.26.2 /opt/unbound/sbin/unbound-checkconf /opt/benchmark/unbound.conf
