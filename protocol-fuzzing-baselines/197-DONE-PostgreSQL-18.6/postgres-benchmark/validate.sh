#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-postgres-protocol-fuzz}
RESULTS_DIR=${2:-"$(pwd)/postgres-validation"}
FUZZ_DURATION=${3:-90s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "验收结果目录非空，请指定新目录：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh
"${PACKAGE_DIR}/parser-check.sh" 2>&1 | tee "${RESULTS_DIR}/parser-check.log"
docker run --rm --network none -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" -e "POSTGRES_SMOKE_REPETITIONS=${POSTGRES_SMOKE_REPETITIONS:-10}" "${IMAGE}" python3 /workspace/protocol_smoke.py /results/protocol-smoke 2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
python3 - "${RESULTS_DIR}/protocol-smoke/protocol-smoke.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
if not report.get("all_transcripts_match"):
    raise SystemExit("普通版与 AFL 插桩版协议 transcript 不一致")
if len(report.get("comparisons", [])) != report["repetitions_per_build"]:
    raise SystemExit("协议回放轮数与报告不一致")
PY
docker run --rm --network none -v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" "${IMAGE}" bash /workspace/run.sh /results/fuzz-smoke "${FUZZ_DURATION}" 2>&1 | tee "${RESULTS_DIR}/fuzz-smoke.log"

test -s "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
test -s "${RESULTS_DIR}/fuzz-smoke/ipsm.dot"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' "${RESULTS_DIR}/fuzz-smoke/fuzzer_stats"
docker run --rm -i "${IMAGE}" dot -Tplain < "${RESULTS_DIR}/fuzz-smoke/ipsm.dot" > "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "node" { n++ } END { exit !(n >= 2) }' "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
awk '$1 == "edge" { e++ } END { exit !(e >= 1) }' "${RESULTS_DIR}/fuzz-smoke/ipsm.plain"
for state in 10 20 21 22; do
	if ! awk '$1 == "node" { print $2 }' "${RESULTS_DIR}/fuzz-smoke/ipsm.plain" | grep -Fxq "${state}"; then
		echo "状态图缺少预期 PostgreSQL 响应状态：${state}" >&2
		exit 1
	fi
done
docker run --rm "${IMAGE}" cat /home/ubuntu/experiments/build-versions.txt > "${RESULTS_DIR}/build-versions.txt"
(cd "${RESULTS_DIR}" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
echo "通过：10 轮正常与异常流程回放、AFLNet 冒烟运行及 PostgreSQL 状态图；证据位于 ${RESULTS_DIR}"
