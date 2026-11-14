#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-emqx-mqtt-aflnet:6.3.2}"
MAKE_JOBS="${MAKE_JOBS:-2}"

mkdir -p "${ROOT}/results/build"
chmod 0777 "${ROOT}/results" "${ROOT}/results/build"
docker build --pull --progress=plain --build-arg "MAKE_JOBS=${MAKE_JOBS}" \
  -t "${IMAGE}" "${ROOT}" 2>&1 | tee "${ROOT}/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "${IMAGE}" > "${ROOT}/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "${IMAGE}" > "${ROOT}/results/build/image-digests.json"
docker run --rm --network none -v "${ROOT}/results:/work/results" "${IMAGE}" \
  -lc 'cp /work/build-lock.txt /work/results/build/build-lock.txt; cp /work/container-packages.txt /work/results/build/container-packages.txt; cp /opt/emqx-release/emqx-6.3.2.tar.gz /work/results/build/emqx-6.3.2-ubuntu24.04-amd64.tar.gz; sha256sum /opt/emqx-release/emqx-6.3.2.tar.gz > /work/results/build/emqx-release.sha256; cp -a /work/dependency-locks /work/results/build/; /opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || test "$?" -eq 1'
printf 'built %s\n' "${IMAGE}"
