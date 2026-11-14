#!/usr/bin/env bash
set -u

# 用法：run.sh 输出目录 时长
OUTDIR=${1:-/results/kafka-smoke}
TIMEOUT=${2:-60s}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${WORKDIR}/kafka-launcher}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-${WORKDIR}/kafka.dict}
PORT=${PORT:-9092}
JACOCO_DESTFILE=${JACOCO_DESTFILE:-${OUTDIR}/kafka-fuzz.exec}
EXEC_TIMEOUT_MS=${AFL_EXEC_TIMEOUT_MS:-120000}
OPTIONS=${3:-}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "Kafka 启动器不可执行：${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "缺少 Kafka 二进制种子：${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "缺少 Kafka 协议字典：${DICT}" >&2; exit 2; }
[[ ${EXEC_TIMEOUT_MS} =~ ^[0-9]+$ ]] && ((EXEC_TIMEOUT_MS > 0)) || {
	echo "AFL_EXEC_TIMEOUT_MS 必须是正整数毫秒：${EXEC_TIMEOUT_MS}" >&2
	exit 2
}
if ! grep -a -q 'KAFKA' "${FUZZER_BIN}"; then
	echo "AFLNet 未包含 Kafka 请求边界/状态解析器。" >&2
	exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")" "$(dirname "${JACOCO_DESTFILE}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "结果目录非空，请选择新路径：${OUTDIR}" >&2
	exit 2
fi

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export AFL_NO_FORKSRV=1
# Kafka JVM 每次独立冷启动；三次快速校准由前置十轮业务回放补足。
export AFL_FAST_CAL=1
export JACOCO_DESTFILE
export ENABLE_AFL_AGENT=1
export ENABLE_JACOCO=0
export KAFKA_HEAP_OPTS=${KAFKA_HEAP_OPTS:-"-Xms128m -Xmx384m"}
PARAMETERS_FILE="${OUTDIR}-run-parameters.txt"
cat > "${PARAMETERS_FILE}" <<EOF
protocol=Kafka native TCP binary protocol
endpoint=tcp://127.0.0.1/${PORT}
target=${TARGET}
target_launcher=ELF 包装器 exec 启动 start-kafka.sh，满足 AFLNet 目标检查
target_source=Apache Kafka 4.4.0 (${KAFKA_COMMIT:-1156b2752aaa28eafc0b4c4d387e63356793268d})
input_seeds=${INPUTS}
dictionary=${DICT}
target_reset=launcher restores kafka-data-snapshot before every target process
server_mode=real Kafka JVM with JVMTI method-edge AFL shared-map agent
forkserver=disabled; AFL_NO_FORKSRV=1
state_feedback=-E -q 3 -s 3 -R
target_termination=-K
connection_retry=up to 60000 fresh TCP sockets at 1ms intervals
startup_deadline=90 seconds
execution_timeout=${EXEC_TIMEOUT_MS}ms hard per-sample limit
docker_cpu_quota=${KAFKA_CPU_LIMIT:-unknown}
docker_memory_limit=${KAFKA_MEMORY_LIMIT:-unknown}
jaCoCo_during_fuzz=disabled; clean queue replay exports JaCoCo line/branch reports
afl_address_space_limit=none
broker_heap_max=384m
container_memory_limit=${KAFKA_MEMORY_LIMIT:-unknown}
additional_options=${OPTIONS}
coverage_calibration=Kafka fast calibration; three executions; long variable-path calibration disabled for Kafka only
socket_poll_wait_milliseconds=1000
socket_send_receive_timeout_microseconds=500000
EOF

echo "开始 Kafka 状态反馈模糊测试：127.0.0.1/${PORT}，时长=${TIMEOUT}，结果=${OUTDIR}"
set +e
# 每个样本硬限 120 秒；150 秒宽限用于回收目标并让 AFLNet 写出统计。
timeout --signal=INT --kill-after=150s "${TIMEOUT}" "${FUZZER_BIN}" \
	-d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
	-N "tcp://127.0.0.1/${PORT}" -P KAFKA -E -q 3 -s 3 -R -K \
	-D 10000 -W 1000 -w 500000 -m none -t "${EXEC_TIMEOUT_MS}" \
	"${EXTRA_OPTIONS[@]}" -- "${TARGET}"
STATUS=$?
set -e
echo "AFLNet 退出状态：${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
	grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
		"${OUTDIR}/fuzzer_stats" || true
fi
if [[ -f ${OUTDIR}/plot_data ]]; then cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"; fi
if [[ -d ${OUTDIR} ]]; then mv "${PARAMETERS_FILE}" "${OUTDIR}/run-parameters.txt"; fi
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 130 ]]; then exit 0; fi
exit "${STATUS}"
