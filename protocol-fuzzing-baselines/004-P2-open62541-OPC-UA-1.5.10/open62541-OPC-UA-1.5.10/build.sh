#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c source-checksums.sha256
sha256sum -c patch-checksums.sha256
docker build --pull=false --tag open62541-opcua:1.5.10 . 2>&1 | tee results/build/docker-build.log
docker image inspect --format '{{.Id}}' open62541-opcua:1.5.10 > results/build/image-id.txt
docker run --rm --network none --entrypoint dpkg-query open62541-opcua:1.5.10 \
  -W -f='${binary:Package} ${Version}\n' | sort > results/build/dpkg-versions.txt
