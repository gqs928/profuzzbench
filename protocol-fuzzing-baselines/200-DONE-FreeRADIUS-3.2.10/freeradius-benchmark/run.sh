#!/usr/bin/env bash
set -u

# 用法：run.sh 输出目录 时长 [AFLNet 附加选项]
OUTDIR=${1:-/results/freeradius-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${RADIUS_AFL_BIN:-${WORKDIR}/freeradius-afl/sbin/radiusd}}
CONFIG=${CONFIG:-${RADIUS_AFL_CONFIG:-${WORKDIR}/freeradius-afl/etc/raddb}}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-/workspace/radius.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
PORT=${PORT:-1812}
SERVER_WAIT_US=${SERVER_WAIT_US:-10000}
RESPONSE_POLL_MS=${RESPONSE_POLL_MS:-1500}
SOCKET_TIMEOUT_US=${SOCKET_TIMEOUT_US:-100000}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "缺少 FreeRADIUS 插桩程序：${TARGET}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "缺少 RADIUS 种子目录：${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "缺少 RADIUS 字典：${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "复位脚本不可执行：${CLEAN_SCRIPT}" >&2; exit 2; }
[[ -d ${CONFIG} ]] || { echo "FreeRADIUS 配置目录不存在：${CONFIG}" >&2; exit 2; }
if ! grep -a -q 'RADIUS' "${FUZZER_BIN}"; then
	echo "AFLNet 未包含 RADIUS 状态解析器。" >&2
	exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "结果目录非空，请选择新目录：${OUTDIR}" >&2
	exit 2
fi
PARAMETERS_FILE="${OUTDIR}-run-parameters.txt"

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
echo "开始 FreeRADIUS RADIUS/TCP 状态模糊测试：127.0.0.1/${PORT}，时长=${TIMEOUT}，结果=${OUTDIR}"
cat > "${PARAMETERS_FILE}" <<EOF
protocol=RADIUS/TCP
endpoint=tcp://127.0.0.1/${PORT}
target=${TARGET}
config=${CONFIG}
input_seeds=${INPUTS}
dictionary=${DICT}
cleanup=${CLEAN_SCRIPT}
timeout=${TIMEOUT}
fuzzer=${FUZZER_BIN}
state_feedback=-E -q 3 -s 3 -R
target_reset=-K
server_start_wait_us=${SERVER_WAIT_US}
response_poll_ms=${RESPONSE_POLL_MS}
socket_timeout_us=${SOCKET_TIMEOUT_US}
memory_limit=none
execution_timeout=5000+
additional_options=${OPTIONS}
EOF

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT}" "${FUZZER_BIN}" \
	-d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
	-N "tcp://127.0.0.1/${PORT}" -P RADIUS -E -q 3 -s 3 -R -K \
	-D "${SERVER_WAIT_US}" -W "${RESPONSE_POLL_MS}" -w "${SOCKET_TIMEOUT_US}" \
	-m none -t 5000+ -c "${CLEAN_SCRIPT}" \
	"${EXTRA_OPTIONS[@]}" "${TARGET}" -f -l /dev/null -d "${CONFIG}"
STATUS=$?
set -e

echo "AFLNet 退出状态：${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
	grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
		"${OUTDIR}/fuzzer_stats" || true
fi
if [[ -f ${OUTDIR}/plot_data ]]; then
	cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
fi
if [[ -d ${OUTDIR} ]]; then
	mv "${PARAMETERS_FILE}" "${OUTDIR}/run-parameters.txt"
fi
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 130 ]]; then exit 0; fi
exit "${STATUS}"
