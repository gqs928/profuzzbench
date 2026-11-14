#!/usr/bin/env bash
set -euo pipefail

# 容器内完整验收流程；FUZZ_DURATION 不得低于 1800 秒。
RESULTS=${1:-/results}
FUZZ_DURATION=${2:-1800s}
WORKDIR=/home/ubuntu/experiments
SECONDS_REQUIRED=1800
if [[ ${FUZZ_DURATION} =~ ^([0-9]+)(s)?$ ]]; then
	FUZZ_SECONDS=${BASH_REMATCH[1]}
else
	echo "严格验收时长只接受整数秒，例如 1800s。" >&2
	exit 2
fi
if ((FUZZ_SECONDS < SECONDS_REQUIRED)); then
	echo "图片要求 AFLNet 连续运行至少 1800 秒；本次设置为 ${FUZZ_SECONDS} 秒。" >&2
	exit 2
fi
mkdir -p "${RESULTS}"
(cd /workspace && sha256sum -c source-checksums.sha256) \
	| tee "${RESULTS}/source-checksums.log"

/workspace/parser-check.sh 2>&1 | tee "${RESULTS}/parser-check.log"
python3 "${WORKDIR}/prepare_seeds.py" \
	"${RESULTS}/regenerated-seeds" "${RESULTS}/regenerated-seeds-manifest.json" \
	| tee "${RESULTS}/seed-generation.log"
diff -r "${WORKDIR}/seeds" "${RESULTS}/regenerated-seeds"
cmp "${WORKDIR}/seeds-manifest.json" "${RESULTS}/regenerated-seeds-manifest.json"
python3 "${WORKDIR}/protocol_smoke.py" \
	"${RESULTS}/protocol-smoke" | tee "${RESULTS}/protocol-smoke.log"
python3 "${WORKDIR}/seed_replay.py" \
	"${RESULTS}/seed-replay" | tee "${RESULTS}/seed-replay.log"

echo "先进行 180 秒 AFLNet 目标启动预检，覆盖完整种子校准阶段。"
/workspace/run.sh "${RESULTS}/fuzz-preflight" 180s \
	| tee "${RESULTS}/fuzz-preflight.log"
test -s "${RESULTS}/fuzz-preflight/fuzzer_stats"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
	"${RESULTS}/fuzz-preflight/fuzzer_stats"

FUZZ_START=$(date +%s)
/workspace/run.sh "${RESULTS}/fuzz-run-01" "${FUZZ_SECONDS}s" \
	| tee "${RESULTS}/fuzz-run-01.log"
FUZZ_END=$(date +%s)
FUZZ_ELAPSED=$((FUZZ_END - FUZZ_START))
printf 'started_epoch=%s\nfinished_epoch=%s\nelapsed_seconds=%s\nrequired_seconds=%s\n' \
	"${FUZZ_START}" "${FUZZ_END}" "${FUZZ_ELAPSED}" "${SECONDS_REQUIRED}" \
	> "${RESULTS}/fuzz-duration.txt"
if ((FUZZ_ELAPSED < SECONDS_REQUIRED - 2)); then
	echo "AFLNet 实际运行仅 ${FUZZ_ELAPSED} 秒，未达到 1800 秒。" >&2
	exit 1
fi
test -s "${RESULTS}/fuzz-run-01/fuzzer_stats"
test -s "${RESULTS}/fuzz-run-01/ipsm.dot"
test -s "${RESULTS}/fuzz-run-01/plot_data"
cp "${RESULTS}/fuzz-run-01/plot_data" "${RESULTS}/fuzz-run-01/fuzz-stats.csv"
awk -F: '/^execs_done[[:space:]]*:/ { if ($2+0 > 0) ok=1 } END { exit !ok }' \
	"${RESULTS}/fuzz-run-01/fuzzer_stats"
dot -Tplain "${RESULTS}/fuzz-run-01/ipsm.dot" \
	> "${RESULTS}/fuzz-run-01/ipsm.plain"
awk '$1 == "node" { n++ } $1 == "edge" { e++ } END { exit !(n >= 2 && e >= 1) }' \
	"${RESULTS}/fuzz-run-01/ipsm.plain"
for state in 10 20 21 22; do
	grep -Eq "^[[:space:]]*${state}[[:space:]]+\\[color=" \
		"${RESULTS}/fuzz-run-01/ipsm.dot" || {
		echo "状态图缺少关键状态 ${state}" >&2
		exit 1
	}
done

crashes="${RESULTS}/fuzz-run-01/replayable-crashes"
hangs="${RESULTS}/fuzz-run-01/replayable-hangs"
/workspace/coverage-run.sh "${RESULTS}/fuzz-run-01" \
	"${RESULTS}/coverage" "${crashes}" "${hangs}" \
	| tee "${RESULTS}/coverage.log"
/workspace/fault-probe.sh "${RESULTS}/fault-probe" \
	| tee "${RESULTS}/fault-probe.log"
cp "${WORKDIR}/build-versions.txt" "${RESULTS}/build-versions.txt"
cp "${WORKDIR}/package-manifest.txt" "${RESULTS}/package-manifest.txt"

(cd "${RESULTS}" && find . -type f ! -name SHA256SUMS \
	! -name acceptance-report.md ! -name acceptance-report.json \
	! -name acceptance-report.csv -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
python3 /workspace/acceptance_report.py "${RESULTS}"
python3 - "${RESULTS}" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
report = json.loads((root / "acceptance-report.json").read_text(encoding="utf-8"))
files = []
for path in sorted(root.rglob("*")):
    if path.is_file() and path.name != "evidence-manifest.json":
        files.append({
            "path": str(path.relative_to(root)),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
(root / "evidence-manifest.json").write_text(
    json.dumps({"files": files}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
if not report.get("all_passed"):
    raise SystemExit("8 项验收中存在未通过项，详见 acceptance-report.md")
print(f"已清点 {len(files)} 个验收证据文件，并保存 SHA-256 清单。")
PY
echo "8 项验收全部通过；证据保存在 ${RESULTS}。"
