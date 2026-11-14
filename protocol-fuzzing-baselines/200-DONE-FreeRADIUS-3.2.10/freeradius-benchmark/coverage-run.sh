#!/usr/bin/env bash
set -euo pipefail

QUEUE=${1:?用法：coverage-run.sh AFL_QUEUE 输出目录 [异常样本目录]}
OUTDIR=${2:?用法：coverage-run.sh AFL_QUEUE 输出目录 [异常样本目录]}
CRASHES=${3:-"$(dirname "${QUEUE}")/replayable-crashes"}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
SOURCE=${RADIUS_GCOV_SOURCE:-${WORKDIR}/src-gcov}
TARGET=${RADIUS_GCOV_BIN:-${WORKDIR}/freeradius-gcov/sbin/radiusd}
CONFIG=${RADIUS_GCOV_CONFIG:-${WORKDIR}/freeradius-gcov/etc/raddb}

[[ -d ${QUEUE} ]] || { echo "AFL 队列目录不存在：${QUEUE}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "覆盖率版 FreeRADIUS 不存在：${TARGET}" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "覆盖率输出目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}"
cat > "${OUTDIR}/coverage-parameters.txt" <<EOF
target=${TARGET}
config=${CONFIG}
queue=${QUEUE}
crashes=${CRASHES}
timeout_seconds_per_sample=1.5
core_files=src/lib/radius.c,src/main/listen.c,src/main/process.c
EOF
find "${SOURCE}" -name '*.gcda' -delete

python3 /workspace/coverage_replay.py \
	--target "${TARGET}" --config "${CONFIG}" --queue "${QUEUE}" \
	--crashes "${CRASHES}" --output "${OUTDIR}" \
	| tee "${OUTDIR}/replay.log"

gcovr --root "${SOURCE}" --object-directory "${SOURCE}" \
	--filter='.*src/(lib/radius|main/listen|main/process)\.c$' \
	--print-summary --output "${OUTDIR}/protocol-core-coverage.txt" \
	| tee "${OUTDIR}/gcovr.log"
gcovr --root "${SOURCE}" --object-directory "${SOURCE}" \
	--filter='.*src/(lib/radius|main/listen|main/process)\.c$' \
	--html-details --output "${OUTDIR}/protocol-core.html"
gcovr --root "${SOURCE}" --object-directory "${SOURCE}" \
	--filter='.*src/(lib/radius|main/listen|main/process)\.c$' \
	--json --output "${OUTDIR}/protocol-core.json"
python3 /workspace/summarize_coverage.py \
	"${OUTDIR}/protocol-core.json" "${OUTDIR}/protocol-core-coverage.csv"
find "${SOURCE}" -name '*.gcda' -printf '%P\n' | sort > "${OUTDIR}/gcda-files.txt"
test -s "${OUTDIR}/protocol-core-coverage.csv"
test -s "${OUTDIR}/queue-replay.jsonl"
grep -Eq 'src/(lib/radius|main/listen|main/process)\.c' "${OUTDIR}/protocol-core-coverage.txt"
echo "通过：AFL 队列与异常样本逐条回放；RADIUS 核心覆盖率已导出。"
