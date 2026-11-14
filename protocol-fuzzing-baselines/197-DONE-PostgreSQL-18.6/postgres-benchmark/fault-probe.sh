#!/usr/bin/env bash
set -euo pipefail

# 用一个可控测试服务验证 AFLNet 异常记录与独立重放链路。
OUTDIR=${1:?用法：fault-probe.sh 输出目录}
WORKDIR=/home/ubuntu/experiments
AFLNET=/home/ubuntu/aflnet
SERVER=${WORKDIR}/postgres-fault-probe-server
SEEDS=${WORKDIR}/fault-probe-seeds
PORT=12059

ulimit -c 0
rm -rf -- "${OUTDIR:?}"
mkdir -p "${OUTDIR}"
rm -rf -- "${SEEDS}"
mkdir -p "${SEEDS}"
printf '\000\000\000\010\000\003\000\000\121\000\000\000\015SELECT 1\000' \
	> "${SEEDS}/postgres-startup-query"
"${AFLNET}/afl-clang-fast" -O0 -g \
	/workspace/fault_probe_server.c -o "${SERVER}"
cat > "${OUTDIR}/parameters.txt" <<EOF
purpose=验证 AFLNet 崩溃记录和独立回放链路
not_a_postgresql_bug=true
seed=${SEEDS}/postgres-startup-query
target=${SERVER}
endpoint=tcp://127.0.0.1:${PORT}
forkserver=disabled
expected_signal=SIGABRT
EOF

set +e
AFL_NO_FORKSRV=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 \
	timeout --signal=INT --kill-after=5s 20s "${AFLNET}/afl-fuzz" \
	-i "${SEEDS}" -o "${OUTDIR}/aflnet" \
	-N "tcp://127.0.0.1/${PORT}" -P POSTGRES -E -q 3 -s 3 -R \
	-D 10000 -W 100 -w 100000 -m none -t 1500 \
	"${SERVER}" "${PORT}" > "${OUTDIR}/aflnet.log" 2>&1
fuzz_status=$?
set -e
if [[ ${fuzz_status} -ne 0 && ${fuzz_status} -ne 124 && ${fuzz_status} -ne 130 ]]; then
	cat "${OUTDIR}/aflnet.log" >&2
	exit "${fuzz_status}"
fi

crash=$(find "${OUTDIR}/aflnet/replayable-crashes" -maxdepth 1 -type f \
	! -name README.txt -print -quit 2>/dev/null || true)
if [[ -z ${crash} ]]; then
	echo "AFLNet 未记录故障探针的 replayable-crashes 样本。" >&2
	cat "${OUTDIR}/aflnet.log" >&2
	exit 1
fi
cp "${crash}" "${OUTDIR}/crash-sample"
python3 /workspace/fault_probe_replay.py \
	"${OUTDIR}/crash-sample" "${SERVER}" "${PORT}" \
	"${OUTDIR}/independent-replay" | tee "${OUTDIR}/replay.log"
test -s "${OUTDIR}/aflnet/fuzzer_stats"
grep -q '故意触发 SIGABRT' "${OUTDIR}/independent-replay/server.log"
grep -q 'unique_crashes[[:space:]]*:[[:space:]]*[1-9]' \
	"${OUTDIR}/aflnet/fuzzer_stats"
echo "通过：AFLNet 记录的故障探针样本能独立触发并记录 SIGABRT。"
