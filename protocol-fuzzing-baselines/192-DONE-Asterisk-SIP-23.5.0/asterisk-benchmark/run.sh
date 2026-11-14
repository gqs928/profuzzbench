#!/usr/bin/env bash
set -u

# 用法：run.sh 输出目录 运行时长 [AFLNet 额外参数]
OUTDIR=${1:-/results/sip-smoke}
TIMEOUT=${2:-60s}
OPTIONS=${3:-}
PACKAGE_DIR=${PACKAGE_DIR:-/workspace}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
INPUTS_SOURCE=${INPUTS:-${PACKAGE_DIR}/seeds}
DICT=${DICT:-${PACKAGE_DIR}/sip.dict}
CLEAN_SCRIPT=${CLEAN_SCRIPT:-${PACKAGE_DIR}/clean.sh}
RESET_SCRIPT=${RESET_SCRIPT:-${PACKAGE_DIR}/reset-state.sh}
ASTERISK_PREFIX=${ASTERISK_AFL_PREFIX:-/home/ubuntu/asterisk-afl}
ASTERISK_TARGET=${ASTERISK_TARGET:-${ASTERISK_PREFIX}/sbin/asterisk}
RUN_ROOT=${ASTERISK_RUN_ROOT:-/tmp/asterisk-run}
START_WAIT_US=${ASTERISK_FUZZ_START_WAIT_US:-1000000}
POLL_WAIT_MS=${ASTERISK_FUZZ_POLL_WAIT_MS:-100}
SOCKET_TIMEOUT_US=${ASTERISK_FUZZ_SOCKET_TIMEOUT_US:-100000}

[[ -x ${FUZZER_BIN} ]] || { echo "AFLNet 缺失：${FUZZER_BIN}" >&2; exit 2; }
[[ -d ${INPUTS_SOURCE} ]] || { echo "SIP 种子目录缺失：${INPUTS_SOURCE}" >&2; exit 2; }
[[ -f ${DICT} ]] || { echo "SIP 字典缺失：${DICT}" >&2; exit 2; }
[[ -x ${CLEAN_SCRIPT} ]] || { echo "清理脚本不可执行：${CLEAN_SCRIPT}" >&2; exit 2; }
[[ -x ${RESET_SCRIPT} ]] || { echo "状态复位脚本不可执行：${RESET_SCRIPT}" >&2; exit 2; }
[[ -x ${ASTERISK_TARGET} ]] || { echo "Asterisk 目标程序缺失：${ASTERISK_TARGET}" >&2; exit 2; }
grep -a -q 'SIP' "${FUZZER_BIN}" || { echo "AFLNet 未包含 SIP 协议入口" >&2; exit 2; }
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "输出目录非空，请使用新目录：${OUTDIR}" >&2
	exit 2
fi

SEED_STAGING_DIR=$(mktemp -d /tmp/asterisk-aflnet-seeds.XXXXXX)
python3 - "${INPUTS_SOURCE}" "${SEED_STAGING_DIR}" <<'PY'
import pathlib
import shutil
import sys

source = pathlib.Path(sys.argv[1])
staging = pathlib.Path(sys.argv[2])
seeds = sorted(source.glob("*.bin"))
if not seeds:
	raise SystemExit("种子目录中没有 .bin 协议样本")
priority = next(
	(seed for seed in seeds if seed.name == "06-register-invite-cancel.bin"),
	seeds[0],
)
shutil.copyfile(priority, staging / "00-stateful-flow.bin")
for seed in seeds:
	if seed != priority:
		shutil.copyfile(seed, staging / seed.name)
PY
INPUTS=${SEED_STAGING_DIR}

mkdir -p "$(dirname "${OUTDIR}")"
read -r -a EXTRA_OPTIONS <<< "${OPTIONS}"
export ASAN_OPTIONS=${ASAN_OPTIONS:-abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1}
export ASTERISK_VARIANT=afl
export ASTERISK_RUN_ROOT=${RUN_ROOT}
export LD_LIBRARY_PATH="${ASTERISK_PREFIX}/lib:${LD_LIBRARY_PATH:-}"
cleanup_run() {
	"${CLEAN_SCRIPT}" >/dev/null 2>&1 || true
	rm -rf -- "${SEED_STAGING_DIR}"
}
trap cleanup_run EXIT
"${CLEAN_SCRIPT}" >/dev/null
{
	printf 'protocol=SIP/TCP\nlisten=127.0.0.1:5060\nvariant=afl+asan\n'
	printf 'timeout=%s\nstart_wait_us=%s\npoll_wait_ms=%s\nsocket_timeout_us=%s\n' \
		"${TIMEOUT}" "${START_WAIT_US}" "${POLL_WAIT_MS}" "${SOCKET_TIMEOUT_US}"
	printf 'seed_source=%s\nseed_dir=%s\nseed_count=%s\ndictionary=%s\n' \
		"${INPUTS_SOURCE}" "${INPUTS}" "$(find "${INPUTS}" -maxdepth 1 -type f -name '*.bin' | wc -l)" "${DICT}"
	printf 'fuzzer=%s\ntarget=%s\ntarget_args=-f -n -C %s/asterisk.conf\nreset_script=%s\n' \
		"${FUZZER_BIN}" "${ASTERISK_TARGET}" "${RUN_ROOT}" "${RESET_SCRIPT}"
	printf 'extra_options=%s\n' "${OPTIONS}"
} > "${OUTDIR}.parameters.txt"
echo "开始 AFLNet SIP/TCP 状态模糊测试；输出目录：${OUTDIR}"

set +e
timeout --signal=INT --kill-after=15s "${TIMEOUT}" "${FUZZER_BIN}" \
	-d -i "${INPUTS}" -x "${DICT}" -o "${OUTDIR}" \
	-N tcp://127.0.0.1/5060 -P SIP -E -q 3 -s 3 -R -K \
	-D "${START_WAIT_US}" -W "${POLL_WAIT_MS}" -w "${SOCKET_TIMEOUT_US}" \
	-m none -t 10000+ -c "${RESET_SCRIPT}" \
	"${EXTRA_OPTIONS[@]}" "${ASTERISK_TARGET}" -f -n -C "${RUN_ROOT}/asterisk.conf"
STATUS=$?
set -e

if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
	grep -E '^(execs_done|paths_total|variable_paths|stability|bitmap_cvg|unique_crashes|unique_hangs)[[:space:]]*:' \
		"${OUTDIR}/fuzzer_stats" || true
	python3 "${PACKAGE_DIR}/fuzz-stats-to-csv.py" \
		"${OUTDIR}/fuzzer_stats" "${OUTDIR}/fuzz-stats.csv"
fi
if [[ ${STATUS} -eq 124 ]]; then exit 0; fi
exit "${STATUS}"
