#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-vernemq-mqtt-aflnet:2.2.1}"
MAKE_JOBS="${MAKE_JOBS:-2}"

mkdir -p "${ROOT}/results/build"
chmod 0777 "${ROOT}/results" "${ROOT}/results/build"
docker build --progress=plain --build-arg "MAKE_JOBS=${MAKE_JOBS}" \
  -t "${IMAGE}" "${ROOT}" 2>&1 | tee "${ROOT}/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "${IMAGE}" > "${ROOT}/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "${IMAGE}" > "${ROOT}/results/build/image-digests.json"
docker run --rm --network none -v "${ROOT}/results:/work/results" "${IMAGE}" \
  -lc 'cp /work/build-lock.txt /work/results/build/build-lock.txt; cp /work/container-packages.txt /work/results/build/container-packages.txt; cp /work/vernemq-version.txt /work/results/build/vernemq-version.txt; cp /work/fuzzer/* /work/results/build/; /opt/aflnet/afl-fuzz -h > /work/results/build/aflnet-help.txt 2>&1 || test "$?" -eq 1; nm /work/aflnet-lifecycle | grep -c __afl_area_ptr > /work/results/build/afl-instrumentation-symbol-count.txt; sha256sum /work/aflnet-lifecycle > /work/results/build/lifecycle-binary.sha256'
printf 'built %s\n' "${IMAGE}"
