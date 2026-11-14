#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-asterisk-sip-fuzz}
RESULTS_DIR=${2:-"$(pwd)/asterisk-validation"}
FUZZ_DURATION=${3:-180s}
PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
REPETITIONS=${ASTERISK_SMOKE_REPETITIONS:-10}

docker image inspect "${IMAGE}" >/dev/null
if [[ -e ${RESULTS_DIR} ]] && [[ -n $(find "${RESULTS_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "验收结果目录非空，请指定全新路径：${RESULTS_DIR}" >&2
	exit 2
fi
mkdir -p "${RESULTS_DIR}"
chmod +x "${PACKAGE_DIR}"/*.sh

docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" python3 /workspace/protocol_smoke.py \
		/results/protocol-smoke "${REPETITIONS}" \
	2>&1 | tee "${RESULTS_DIR}/protocol-smoke.log"
python3 - "${RESULTS_DIR}/protocol-smoke/protocol-smoke.json" "${REPETITIONS}" <<'PY'
import json
import pathlib
import sys

report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = int(sys.argv[2])
checks = (
	report.get("repetitions_per_variant", 0) >= expected,
	report.get("all_sessions_passed") is True,
	report.get("same_transcript_within_each_variant") is True,
	report.get("same_exact_requests_across_all_runs") is True,
	report.get("reference_and_afl_transcripts_match") is True,
)
if not all(checks):
	raise SystemExit("参考版/AFL 版真实 SIP 会话或重复复位检查未通过")
PY

docker run --rm --network none \
	-v "${PACKAGE_DIR}:/workspace:ro" -v "${RESULTS_DIR}:/results" \
	"${IMAGE}" bash /workspace/run.sh /results/fuzz-smoke "${FUZZ_DURATION}" \
	2>&1 | tee "${RESULTS_DIR}/fuzz-smoke.log"

FUZZ_DIR=${RESULTS_DIR}/fuzz-smoke
test -s "${FUZZ_DIR}/fuzzer_stats"
test -s "${FUZZ_DIR}/plot_data"
test -s "${FUZZ_DIR}/ipsm.dot"
test -s "${RESULTS_DIR}/fuzz-smoke.parameters.txt"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
	"${FUZZ_DIR}/fuzzer_stats"
docker run --rm --network none -i "${IMAGE}" dot -Tplain \
	< "${FUZZ_DIR}/ipsm.dot" > "${FUZZ_DIR}/ipsm.plain"
node_count=$(awk '$1 == "node" { n++ } END { print n+0 }' "${FUZZ_DIR}/ipsm.plain")
edge_count=$(awk '$1 == "edge" { e++ } END { print e+0 }' "${FUZZ_DIR}/ipsm.plain")
[[ ${node_count} -ge 2 && ${edge_count} -ge 1 ]]
for state in 100 200; do
	grep -Eq "(^|[^0-9])${state}([^0-9]|$)" "${FUZZ_DIR}/ipsm.dot" || {
		echo "SIP 状态图缺少预期状态码：${state}" >&2
		exit 1
	}
done

docker run --rm --network none "${IMAGE}" \
	cat /home/ubuntu/experiments/build-versions.txt \
	> "${RESULTS_DIR}/build-versions.txt"
docker run --rm --network none "${IMAGE}" \
	cat /home/ubuntu/experiments/package-manifest.txt \
	> "${RESULTS_DIR}/package-manifest.txt"
python3 - "${FUZZ_DIR}/fuzzer_stats" "${FUZZ_DIR}/queue/.state/variable_behavior" \
	"${RESULTS_DIR}/variable-paths-audit.md" <<'PY'
import pathlib
import re
import sys

stats = {}
for line in pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines():
	if ":" in line:
		key, value = line.split(":", 1)
		stats[key.strip()] = value.strip()
variable_paths = int(re.sub(r"[^0-9]", "", stats.get("variable_paths", "0")) or "0")
state_dir = pathlib.Path(sys.argv[2])
examples = sorted(path.name for path in state_dir.iterdir()) if state_dir.is_dir() else []
lines = [
	"# AFLNet variable_paths 排查记录",
	"",
	f"- `variable_paths`: {variable_paths}",
	f"- `stability`: {stats.get('stability', '未提供')}",
	f"- AFLNet 标记的变动队列样本: {len(examples)}",
]
if variable_paths == 0:
	lines.append("- 结论：本轮未发现覆盖轨迹不稳定样本。")
else:
	lines.append("- 结论：存在变动覆盖轨迹；同一组 SIP 请求在参考版/AFL 版重复回放的业务响应仍需结合下列队列项复核。")
	lines.extend(f"- `{name}`" for name in examples[:50])
pathlib.Path(sys.argv[3]).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
cp "${PACKAGE_DIR}/source-checksums.sha256" "${RESULTS_DIR}/source-checksums.sha256"
(
	cd "${PACKAGE_DIR}"
	sha256sum -c source-checksums.sha256
)
(
	cd "${RESULTS_DIR}"
	find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
echo "通过：SIP 业务回放、重复复位、AFLNet 执行和状态反馈；证据目录：${RESULTS_DIR}"
