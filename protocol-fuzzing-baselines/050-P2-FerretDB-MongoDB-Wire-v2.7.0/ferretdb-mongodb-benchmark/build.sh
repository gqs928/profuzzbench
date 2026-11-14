#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
sha256sum -c source-checksums.sha256
set -a
source ./images.env
set +a
IMAGE=ferretdb-mongodb-fuzz-bench:2.7.0
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 \
  --build-arg "FERRETDB_IMAGE=${FERRETDB_IMAGE}" \
  --build-arg "DEBIAN_IMAGE=${DEBIAN_IMAGE}" \
  --tag "${IMAGE}" . 2>&1 | tee build-logs/docker-build.log
docker image inspect "${IMAGE}" --format '{{.Id}}' > build-logs/image-id.txt
docker image inspect "${IMAGE}" --format '{{json .RepoDigests}}' > build-logs/repo-digests.json
docker run --rm --entrypoint /usr/local/bin/ferretdb "${IMAGE}" --version \
  | tee build-logs/ferretdb-version.txt
