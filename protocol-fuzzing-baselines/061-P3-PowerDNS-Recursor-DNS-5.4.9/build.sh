#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
set -a
source images.env
set +a
if ! docker image inspect "$PDNS_BASE_IMAGE" >/dev/null 2>&1; then
  docker pull "$PDNS_BASE_IMAGE"
fi
docker image tag "$PDNS_BASE_IMAGE" pdns-runtime-base:24.04
if ! docker image inspect "$AFL_BUILDER_IMAGE" >/dev/null 2>&1; then
  docker pull "$AFL_BUILDER_IMAGE"
fi
docker image tag "$AFL_BUILDER_IMAGE" rockylinux-bench-builder:9.8
docker compose --env-file images.env -f compose.yaml build 2>&1 | tee build-logs/build.log
docker image inspect powerdns-recursor-aflnet-bench:5.4.9 --format '{{.Id}} {{.Size}}' | tee build-logs/image-id.txt
docker image inspect pdns-runtime-base:24.04 --format '{{.Id}} {{.RepoDigests}} {{.Os}}/{{.Architecture}}' | tee build-logs/runtime-base-identity.txt
printf 'runtime_base=%s\nbuilder_base=%s\npackage_version=%s\n' "$PDNS_BASE_IMAGE" "$AFL_BUILDER_IMAGE" "$PDNS_PACKAGE_VERSION" | tee build-logs/build-base-identities.txt
docker run --rm powerdns-recursor-aflnet-bench:5.4.9 cat /opt/benchmark/pdns-version.txt | tee build-logs/pdns-version.txt
docker run --rm powerdns-recursor-aflnet-bench:5.4.9 dpkg-query -W -f='${Version}\n' pdns-recursor | tee build-logs/pdns-package-version.txt
