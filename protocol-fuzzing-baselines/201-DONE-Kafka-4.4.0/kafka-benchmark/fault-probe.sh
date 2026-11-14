#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:-/results/fault-probe}
WORKDIR=${WORKDIR:-/home/ubuntu/experiments}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER=${AFLNET}/afl-fuzz
PROBE_SOURCE=${PROBE_SOURCE:-/workspace/fault_probe_server.c}
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "故障探针输出目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}/input"

# 使用隔离的测试服务触发确定性 abort，不给 Kafka 源码打故意异常补丁。
[[ -f ${PROBE_SOURCE} ]] || { echo "缺少隔离探针源码：${PROBE_SOURCE}" >&2; exit 2; }
"${AFLNET}/afl-clang-fast" -O1 -g -Wall -Wextra -Werror \
	-o "${OUTDIR}/fault-probe-server" "${PROBE_SOURCE}"
python3 - "${OUTDIR}/input/trigger.bin" <<'PY'
import pathlib
import struct
import sys

# 一个字节偏离触发令牌；AFLNet 可先校准正常状态，再经确定性变异找到崩溃。
marker = b"KAFKA-CRASH-PROBD"
body = struct.pack(">HHI", 32767, 0, 99) + marker
pathlib.Path(sys.argv[1]).write_bytes(struct.pack(">I", len(body)) + body)
PY

export AFL_NO_FORKSRV=1
set +e
timeout --signal=INT --kill-after=10s 20s "${FUZZER}" \
	-d -i "${OUTDIR}/input" -x "${WORKDIR}/kafka.dict" -o "${OUTDIR}/aflnet" \
	-N tcp://127.0.0.1/19092 -P KAFKA -E -q 3 -s 3 -R -K \
	-D 1000 -W 20 -w 100000 -m none -t 3000+ \
	-- "${OUTDIR}/fault-probe-server" \
	2>&1 | tee "${OUTDIR}/run.log"
STATUS=$?
set -e
if [[ ${STATUS} -ne 0 && ${STATUS} -ne 124 && ${STATUS} -ne 130 ]]; then
	echo "AFLNet 故障探针退出异常：${STATUS}" >&2
	exit "${STATUS}"
fi

CRASH=$(find "${OUTDIR}/aflnet/crashes" -maxdepth 1 -type f -name 'id:*' -print -quit 2>/dev/null || true)
REPLAYABLE_CRASH=false
if [[ -z ${CRASH} ]]; then
	# ProFuzzBench AFLNet 将可独立重放的异常样本保存在 replayable-crashes/。
	CRASH=$(find "${OUTDIR}/aflnet/replayable-crashes" -maxdepth 1 -type f -name 'id:*' -print -quit 2>/dev/null || true)
	[[ -z ${CRASH} ]] || REPLAYABLE_CRASH=true
fi
if [[ -z ${CRASH} ]]; then
	echo "AFLNet 没有保存故障探针崩溃样本。" >&2
	exit 1
fi
if [[ ${REPLAYABLE_CRASH} == true ]]; then
	# 可回放样本按 4 字节小端长度封装多条消息；解包后保存裸 TCP 字节供独立进程重放。
	python3 - "${CRASH}" "${OUTDIR}/intentional-crash-sample.bin" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_bytes()
cursor = 0
messages = []
while cursor < len(source):
    if len(source) - cursor < 4:
        raise SystemExit("AFLNet 可回放异常样本缺少消息长度头")
    size = int.from_bytes(source[cursor:cursor + 4], "little")
    cursor += 4
    if size == 0 or size > len(source) - cursor:
        raise SystemExit("AFLNet 可回放异常样本消息长度无效")
    messages.append(source[cursor:cursor + size])
    cursor += size
pathlib.Path(sys.argv[2]).write_bytes(b"".join(messages))
PY
else
	cp "${CRASH}" "${OUTDIR}/intentional-crash-sample.bin"
fi
sha256sum "${OUTDIR}/intentional-crash-sample.bin" > "${OUTDIR}/crash-sample-sha256.txt"
python3 /workspace/fault-probe-replay.py \
	"${OUTDIR}/fault-probe-server" "${OUTDIR}/intentional-crash-sample.bin" "${OUTDIR}"
cp "${OUTDIR}/aflnet/fuzzer_stats" "${OUTDIR}/fuzzer_stats"
rm -f "${OUTDIR}/fault-probe-server"
echo "通过：AFLNet 已保存异常样本，独立进程可重复触发；探针二进制已移除。"
