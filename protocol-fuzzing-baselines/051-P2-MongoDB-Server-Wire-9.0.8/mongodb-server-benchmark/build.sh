#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build-logs
sha256sum -c source-checksums.sha256
set -a
source ./images.env
set +a
IMAGE=mongodb-server-aflnet-bench:9.0.8
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 \
  --build-arg "MONGO_IMAGE=${MONGO_IMAGE}" \
  --tag "${IMAGE}" . 2>&1 | tee build-logs/docker-build.log
docker image inspect "${IMAGE}" --format '{{.Id}}' > build-logs/image-id.txt
docker image inspect "${IMAGE}" --format '{{json .RepoDigests}}' > build-logs/repo-digests.json
docker run --rm --network none --entrypoint /usr/bin/mongod "${IMAGE}" --version \
  | tee build-logs/mongod-version.txt
docker run --rm --network none --entrypoint /usr/bin/mongosh "${IMAGE}" --version \
  | tee build-logs/mongosh-version.txt
