#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-gstreamer-rtsp-aflnet:1.28.8}"
MAKE_JOBS="${MAKE_JOBS:-2}"
mkdir -p "${ROOT}/results/build"
docker build --progress=plain --build-arg "MAKE_JOBS=${MAKE_JOBS}" \
  -t "${IMAGE}" "${ROOT}" 2>&1 | tee "${ROOT}/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "${IMAGE}" > "${ROOT}/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "${IMAGE}" > "${ROOT}/results/build/image-digests.json"
docker run --rm --network none -v "${ROOT}/results:/work/results" "${IMAGE}" \
  -lc '/work/capture-build.sh'
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -e PREFLIGHT_ROOT=/work/results/preflight-live \
  -e PREFLIGHT_OUT=/work/results/preflight-live/aflnet-60s-final6 \
  -v "${ROOT}/results:/work/results" "${IMAGE}" \
  -lc 'bash /work/validate.sh'
printf 'built and preflight passed: %s\n' "${IMAGE}"
