#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-nanomq-mqtt-aflnet:0.25.6}"
MAKE_JOBS="${MAKE_JOBS:-2}"

mkdir -p "${ROOT}/results/build"
chmod 0777 "${ROOT}/results" "${ROOT}/results/build"
docker build --pull --progress=plain --build-arg "MAKE_JOBS=${MAKE_JOBS}" \
  -t "${IMAGE}" "${ROOT}" 2>&1 | tee "${ROOT}/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "${IMAGE}" > "${ROOT}/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "${IMAGE}" > "${ROOT}/results/build/image-digests.json"
docker run --rm --network none -v "${ROOT}/results:/work/results" "${IMAGE}" \
  -lc 'cp /work/build-lock.txt /work/results/build/build-lock.txt; cp /work/container-packages.txt /work/results/build/container-packages.txt; cp /work/nanomq-help.txt /work/results/build/nanomq-help.txt; /opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || test "$?" -eq 1; nm /opt/nanomq/nanomq | grep -c __afl_area_ptr > /work/results/build/afl-instrumentation-symbol-count.txt; sha256sum /opt/nanomq/nanomq > /work/results/build/nanomq-binary.sha256'
printf 'built %s\n' "${IMAGE}"
