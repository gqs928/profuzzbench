#!/usr/bin/env bash
set -u

# 用法：run.sh 输出目录 时长 [AFLNet 附加选项]
OUTDIR=${1:-/results/postgres-smoke}
TIMEOUT_VALUE=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
TARGET=${TARGET:-${POSTGRES_AFL_BIN:-${WORKDIR}/postgres-afl/bin/postgres}}
TARGET_LAUNCHER=${TARGET_LAUNCHER:-${WORKDIR}/target-launcher}
INITDB=${POSTGRES_INITDB_BIN:-${WORKDIR}/postgres-reference/bin/initdb}
PG_CTL=${POSTGRES_PG_CTL_BIN:-${WORKDIR}/postgres-reference/bin/pg_ctl}
PGDATA=${PGDATA:-/tmp/postgres-fuzz/data}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-/workspace/postgres.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-/workspace/clean.sh}
PORT=${PORT:-5432}
SERVER_WAIT_US=${SERVER_WAIT_US:-1000000}
RESPONSE_POLL_MS=${RESPONSE_POLL_MS:-1000}
SOCKET_TIMEOUT_US=${SOCKET_TIMEOUT_US:-100000}
TARGET_TIMEOUT=${TARGET_TIMEOUT:-10000+}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -x ${TARGET} ]] || { echo "缺少 PostgreSQL AFL 插桩程序：${TARGET}" >&2; exit 2; }
[[ -x ${TARGET_LAUNCHER} ]] || { echo "缺少 PostgreSQL 目标启动器：${TARGET_LAUNCHER}" >&2; exit 2; }
[[ -x ${INITDB} && -x ${PG_CTL} ]] || {
	echo "缺少 PostgreSQL 集群初始化或复位工具。" >&2
	exit 2
}
[[ -d ${INPUTS} ]] || { echo "缺少 PostgreSQL 种子目录：${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "缺少 PostgreSQL 字典：${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "复位脚本不可执行：${CLEAN_SCRIPT}" >&2; exit 2; }
if ! grep -a -q 'POSTGRES' "${FUZZER_BIN}"; then
	echo "AFLNet 二进制没有编入 PostgreSQL 请求/响应适配器。" >&2
	exit 2
fi
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "结果目录非空，请选择新目录：${OUTDIR}" >&2
	exit 2
fi

PARAMETERS_FILE="${OUTDIR}-run-parameters.txt"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export PGDATA POSTGRES_INITDB_BIN=${INITDB} POSTGRES_PG_CTL_BIN=${PG_CTL}
export POSTGRES_AFL_BIN=${TARGET} POSTGRES_CLEAN_SCRIPT=${CLEAN_SCRIPT}
export POSTGRES_PG_ISREADY_BIN=${POSTGRES_PG_ISREADY_BIN:-${WORKDIR}/postgres-reference/bin/pg_isready}
export POSTGRES_PORT=${PORT} POSTGRES_READY_TIMEOUT_SEC=${POSTGRES_READY_TIMEOUT_SEC:-10}
echo "开始 PostgreSQL 前后端协议状态模糊测试：127.0.0.1/${PORT}，时长=${TIMEOUT_VALUE}"
cat > "${PARAMETERS_FILE}" <<EOF
protocol=PostgreSQL Frontend/Backend Protocol 3.0 and 3.2
endpoint=tcp://127.0.0.1/${PORT}
target=${TARGET}
target_launcher=${TARGET_LAUNCHER}
pgdata=${PGDATA}
initdb=${INITDB}
input_seeds=${INPUTS}
dictionary=${DICT}
cleanup=${CLEAN_SCRIPT}
timeout=${TIMEOUT_VALUE}
fuzzer=${FUZZER_BIN}
state_feedback=-E -q 3 -s 3 -R
target_reset=每轮由目标启动器重建数据目录并启动独立服务进程；AFLNet -K 结束该进程
forkserver=disabled (AFL_NO_FORKSRV=1)
server_start_wait_us=${SERVER_WAIT_US}
response_poll_ms=${RESPONSE_POLL_MS}
socket_timeout_us=${SOCKET_TIMEOUT_US}
memory_limit=none
execution_timeout=${TARGET_TIMEOUT}
additional_options=${OPTIONS}
EOF

set +e
timeout --signal=INT --kill-after=10s "${TIMEOUT_VALUE}" env AFL_NO_FORKSRV=1 "${FUZZER_BIN}" -d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" -N "tcp://127.0.0.1/${PORT}" -P POSTGRES -E -q 3 -s 3 -R -K -D "${SERVER_WAIT_US}" -W "${RESPONSE_POLL_MS}" -w "${SOCKET_TIMEOUT_US}" -m none -t "${TARGET_TIMEOUT}" "${EXTRA_OPTIONS[@]}" "${TARGET_LAUNCHER}" -D "${PGDATA}" -p "${PORT}" -c listen_addresses=127.0.0.1 -c unix_socket_directories= -c fsync=off -c full_page_writes=off -c synchronous_commit=off
STATUS=$?
set -e

echo "AFLNet 退出状态：${STATUS}"
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
	grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' "${OUTDIR}/fuzzer_stats" || true
fi
if [[ -f ${OUTDIR}/plot_data ]]; then
	cp "${OUTDIR}/plot_data" "${OUTDIR}/fuzz-stats.csv"
fi
if [[ -d ${OUTDIR} ]]; then
	mv "${PARAMETERS_FILE}" "${OUTDIR}/run-parameters.txt"
fi
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 130 ]]; then exit 0; fi
exit "${STATUS}"
