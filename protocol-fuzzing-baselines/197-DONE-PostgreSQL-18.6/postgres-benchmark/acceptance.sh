#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-postgres-protocol-fuzz}
RESULTS_DIR=${2:-"$(pwd)/postgres-benchmark-results"}
FUZZ_DURATION=${3:-1800s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "${RESULTS_DIR}"
RESULTS_DIR=$(cd "${RESULTS_DIR}" && pwd)
if [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
	echo "严格验收结果目录必须为空：${RESULTS_DIR}" >&2
	exit 2
fi
"${PACKAGE_DIR}/build.sh" "${IMAGE}"
mkdir -p "${RESULTS_DIR}/build"
cp -a "${PACKAGE_DIR}/build-logs/." "${RESULTS_DIR}/build/"
docker run --rm --init --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/acceptance-inner.sh /results "${FUZZ_DURATION}" \
	2>&1 | tee "${RESULTS_DIR}/acceptance-console.log"
(cd "${RESULTS_DIR}" && find . -type f ! -name SHA256SUMS \
	! -name evidence-manifest.json -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
echo "严格验收结果已保存：${RESULTS_DIR}"
