#!/usr/bin/env bash
set -euo pipefail

QUEUE=${1:?用法：coverage-run.sh AFLNet输出目录 覆盖率输出目录}
OUTDIR=${2:?用法：coverage-run.sh AFLNet输出目录 覆盖率输出目录}
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "覆盖率输出目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
REPLAY_LOG="${OUTDIR}.replay.log"

python3 /workspace/coverage_replay.py \
	"${QUEUE}/queue" "${QUEUE}/crashes" "${OUTDIR}" \
	| tee "${REPLAY_LOG}"

test -s "${OUTDIR}/queue-replay.jsonl"
test -s "${OUTDIR}/protocol-core-coverage.csv"
test -s "${OUTDIR}/protocol-core-coverage.txt"
test -s "${OUTDIR}/protocol-core-coverage.json"
test -s "${OUTDIR}/jacoco-html/index.html"
test -s "${OUTDIR}/jacoco-all.xml"
cp "${REPLAY_LOG}" "${OUTDIR}/replay.log"
rm -f "${REPLAY_LOG}"
cat > "${OUTDIR}/coverage-parameters.txt" <<EOF
target=Apache Kafka 4.4.0 reference JVM broker
queue=${QUEUE}/queue
crashes=${QUEUE}/crashes
reset=each sample starts a fresh broker after restoring kafka-data-snapshot
collector=JaCoCo ${JACOCO_VERSION:-0.8.13}
core_packages=kafka.network,org.apache.kafka.common.requests,org.apache.kafka.server
EOF

echo "通过：Kafka 队列/异常样本分别清状态回放；JaCoCo 行与分支报告已导出。"
