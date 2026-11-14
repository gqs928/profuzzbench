#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
  echo "AFLNet 需要以容器 root 身份启动 Dovecot forkserver；请使用 docker run --user root" >&2
  exit 2
fi

# 用法：run.sh 输出目录 运行时长 [AFLNet 额外参数]
OUTDIR=${1:-/results/imap-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
INPUTS=${INPUTS:-${WORKDIR}/seeds}
DICT=${DICT:-/workspace/imap.dict}
PREFIX=${DOVECOT_AFL_PREFIX:-${WORKDIR}/dovecot-afl}
PORT=${IMAP_PORT:-1143}
AFL_FAST=${AFL_FAST:-1}
STARTUP_DELAY=${IMAP_STARTUP_DELAY:-500000}
CONFIG=${DOVECOT_CONFIG:-/workspace/dovecot.conf}

[[ -x ${FUZZER_BIN} ]] || { echo "缺少 AFLNet：${FUZZER_BIN}" >&2; exit 2; }
[[ -d ${INPUTS} ]] || { echo "缺少 IMAP 种子：${INPUTS}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "缺少 IMAP 字典：${DICT}" >&2; exit 2; }
[[ ${AFL_FAST} == 0 || ${AFL_FAST} == 1 ]] || { echo "AFL_FAST 只能设置为 0 或 1" >&2; exit 2; }
[[ -x /workspace/clean.sh ]] || { echo "缺少复位脚本" >&2; exit 2; }
grep -a -q 'IMAP' "${FUZZER_BIN}" || { echo "AFLNet 未包含 IMAP 状态解析器" >&2; exit 2; }
mkdir -p "$(dirname "${OUTDIR}")"
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
  echo "结果目录非空，请选择新目录：${OUTDIR}" >&2
  exit 2
fi
mkdir -p "${OUTDIR}"

export PATH="${PREFIX}/bin:${PREFIX}/sbin:${PREFIX}/libexec:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export DOVECOT_AFL_PREFIX=${PREFIX}
FUZZ_MODE_ARGS=()
if [[ ${AFL_FAST} == 1 ]]; then
  FUZZ_MODE_ARGS+=(-d)
fi

# 每次启动 AFLNet 前清理旧套接字，再以 ubuntu 身份重建可写邮箱目录。
/usr/local/sbin/dovecot-root-launcher afl reset
runuser -u ubuntu -- /workspace/reset-state.sh

read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
START_EPOCH=$(date -u +%s)
{
  printf 'started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'duration_requested=%s\n' "${TIMEOUT}"
  printf 'protocol=IMAP\nport=%s\n' "${PORT}"
  printf 'seed_dir=%s\n' "${INPUTS}"
  printf 'seed_count=%s\n' "$(find "${INPUTS}" -maxdepth 1 -type f | wc -l)"
  printf 'server_prefix=%s\n' "${PREFIX}"
  printf 'aflnet=%s\n' "${FUZZER_BIN}"
  printf 'deterministic_stages=%s\n' "$([[ ${AFL_FAST} == 1 ]] && echo skipped || echo enabled)"
  printf 'startup_delay_us=%s\n' "${STARTUP_DELAY}"
  printf 'config=%s\n' "${CONFIG}"
} > "${OUTDIR}/run-parameters.txt"

echo "开始 AFLNet IMAP 状态反馈运行：回环 TCP/${PORT}，结果目录 ${OUTDIR}"
set +e
timeout --signal=INT --kill-after=15s "${TIMEOUT}" "${FUZZER_BIN}" \
  "${FUZZ_MODE_ARGS[@]}" -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
  -N "tcp://127.0.0.1/${PORT}" -P IMAP -E -q 3 -s 3 -R -K \
  -D "${STARTUP_DELAY}" -W 100 -w 100000 -m none -t 10000+ -c /usr/local/sbin/dovecot-clean-maildir \
  "${EXTRA_OPTIONS[@]}" "${PREFIX}/sbin/dovecot" -F -c "${CONFIG}" \
  2>&1 | tee "${OUTDIR}/fuzz.log"
STATUS=${PIPESTATUS[0]}
set -e
END_EPOCH=$(date -u +%s)
{
  printf 'ended_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'elapsed_seconds=%s\n' "$((END_EPOCH - START_EPOCH))"
  printf 'fuzzer_exit_status=%s\n' "${STATUS}"
} >> "${OUTDIR}/run-parameters.txt"

if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
  grep -E '^(start_time|last_update|run_time|execs_done|paths_total|paths_favored|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
    "${OUTDIR}/fuzzer_stats" || true
fi
chmod -R a+rX "${OUTDIR}"
echo "AFLNet 退出状态：${STATUS}"
if [[ ${STATUS} -eq 124 || ${STATUS} -eq 0 ]]; then exit 0; fi
exit "${STATUS}"
