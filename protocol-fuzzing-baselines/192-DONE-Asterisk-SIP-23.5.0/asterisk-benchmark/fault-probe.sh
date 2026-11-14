#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:-/results/fault-probe}
PROBE_TIMEOUT=${ASTERISK_FAULT_PROBE_TIMEOUT:-120s}
TMP_DIR=$(mktemp -d /tmp/asterisk-sip-fault.XXXXXX)
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
PROBE_BIN=${TMP_DIR}/sip-fault-probe
INPUT_DIR=${TMP_DIR}/seeds
FUZZ_DIR=${TMP_DIR}/fuzz

cleanup_tmp() { rm -rf -- "${TMP_DIR}"; }
trap cleanup_tmp EXIT
if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "故障探针输出目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}" "${INPUT_DIR}"
ulimit -c 0

# 临时构建只用于验证异常捕获的 SIP 服务，不改动 Asterisk 上游源码。
cat > "${TMP_DIR}/sip-fault-probe.c" <<'EOF'
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int contains_trigger(const uint8_t *data, size_t size)
{
	static const uint8_t trigger[] = "X:yes";
	size_t i;
	for (i = 0; i + sizeof(trigger) - 1 <= size; ++i) {
		if (memcmp(data + i, trigger, sizeof(trigger) - 1) == 0) return 1;
	}
	return 0;
}

int main(void)
{
	int server_fd = socket(AF_INET, SOCK_STREAM, 0);
	int reuse = 1;
	struct sockaddr_in address;
	uint8_t request[65536];
	static const char response[] = "SIP/2.0 200 OK\r\nContent-Length: 0\r\n\r\n";
	if (server_fd < 0) return 2;
	(void)setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
	memset(&address, 0, sizeof(address));
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	address.sin_port = htons(5060);
	if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0 ||
	    listen(server_fd, 8) < 0) return 3;
	for (;;) {
		int client_fd = accept(server_fd, NULL, NULL);
		size_t used = 0;
		if (client_fd < 0) continue;
		while (used < sizeof(request)) {
			ssize_t count = recv(client_fd, request + used,
					     sizeof(request) - used, 0);
			if (count <= 0) break;
			used += (size_t)count;
			if (contains_trigger(request, used)) abort();
			if (used >= 4 && memmem(request, used, "\r\n\r\n", 4)) {
				(void)send(client_fd, response, sizeof(response) - 1, 0);
				break;
			}
		}
		close(client_fd);
	}
}
EOF

python3 - "${INPUT_DIR}/seed.bin" <<'PY'
import pathlib
import sys

packet = (
	# 触发字段靠近请求开头，单比特变异即可到达故障分支。
	b"OPTIONS sip:a SIP/2.0\r\n"
	b"X:yeS\r\n\r\n"
)
pathlib.Path(sys.argv[1]).write_bytes(packet)
PY

sha256sum "${TMP_DIR}/sip-fault-probe.c" > "${OUTDIR}/temporary-probe-source.sha256"
AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g \
	"${TMP_DIR}/sip-fault-probe.c" -o "${PROBE_BIN}"
set +e
timeout --signal=INT --kill-after=5s "${PROBE_TIMEOUT}" "${FUZZER_BIN}" \
	-i "${INPUT_DIR}" -x /workspace/sip.dict -o "${FUZZ_DIR}" \
	-N tcp://127.0.0.1/5060 -P SIP -E -q 3 -s 3 -R -K \
	-D 100000 -W 100 -w 100000 -m none -t 2000+ -c /workspace/clean.sh \
	"${PROBE_BIN}"
STATUS=$?
set -e
printf 'fuzzer_exit_status=%s\n' "${STATUS}" > "${OUTDIR}/probe-status.txt"

if [[ -f ${FUZZ_DIR}/fuzzer_stats ]]; then
	cp "${FUZZ_DIR}/fuzzer_stats" "${OUTDIR}/fuzzer_stats"
	grep -E '^(execs_done|unique_crashes|unique_hangs|paths_total)[[:space:]]*:' \
		"${FUZZ_DIR}/fuzzer_stats" > "${OUTDIR}/probe-counters.txt" || true
fi
crash_sample=$(find "${FUZZ_DIR}/replayable-crashes" -maxdepth 1 -type f \
	-name 'id:*' -print -quit 2>/dev/null || true)
if [[ -z ${crash_sample} ]]; then
	echo "AFLNet 未记录到探针崩溃样本" >&2
	exit 1
fi
cp "${crash_sample}" "${OUTDIR}/intentional-crash-sample.aflnet"
python3 - "${crash_sample}" "${OUTDIR}/intentional-crash-sample.bin" <<'PY'
import pathlib
import sys

stored = pathlib.Path(sys.argv[1]).read_bytes()
messages = []
cursor = 0
while cursor < len(stored):
	if cursor + 4 > len(stored):
		raise SystemExit("异常样本长度前缀不完整")
	size = int.from_bytes(stored[cursor : cursor + 4], sys.byteorder)
	cursor += 4
	if size == 0 or cursor + size > len(stored):
		raise SystemExit(f"异常样本 SIP 消息长度无效：{size}")
	messages.append(stored[cursor : cursor + size])
	cursor += size
if not messages:
	raise SystemExit("异常样本不含可回放 SIP 消息")
pathlib.Path(sys.argv[2]).write_bytes(b"".join(messages))
PY

python3 - "${PROBE_BIN}" "${OUTDIR}/intentional-crash-sample.bin" \
	"${OUTDIR}/probe-status.txt" <<'PY'
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time

server = pathlib.Path(sys.argv[1])
sample = pathlib.Path(sys.argv[2]).read_bytes()
status_path = pathlib.Path(sys.argv[3])
process = subprocess.Popen(
	[str(server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
	start_new_session=True,
)
try:
	deadline = time.monotonic() + 5
	sock = None
	while time.monotonic() < deadline:
		if process.poll() is not None:
			raise SystemExit(f"独立回放服务提前退出：{process.returncode}")
		try:
			sock = socket.create_connection(("127.0.0.1", 5060), timeout=0.2)
			break
		except OSError:
			time.sleep(0.05)
	if sock is None:
		raise SystemExit("独立回放服务启动超时")
	with sock:
		sock.sendall(sample)
		sock.shutdown(socket.SHUT_WR)
	deadline = time.monotonic() + 3
	while time.monotonic() < deadline and process.poll() is None:
		time.sleep(0.05)
	if process.poll() in (None, 0):
		raise SystemExit("独立回放没有重现异常退出")
	with status_path.open("a", encoding="utf-8") as stream:
		stream.write(f"independent_replay_exit={process.returncode}\n")
finally:
	if process.poll() is None:
		os.killpg(process.pid, signal.SIGKILL)
		process.wait(timeout=3)
PY

crash_count=$(awk -F: '/^unique_crashes[[:space:]]*:/ { gsub(/[[:space:]]/, "", $2); print $2 }' \
	"${OUTDIR}/fuzzer_stats")
rm -rf -- "${TMP_DIR}"
if [[ -e ${TMP_DIR} ]]; then
	echo "临时故障探针未清理：${TMP_DIR}" >&2
	exit 1
fi
printf 'unique_crashes=%s\ntemporary_injection_removed=true\n' \
	"${crash_count:-0}" >> "${OUTDIR}/probe-status.txt"
[[ ${crash_count:-0} -gt 0 ]]
echo "通过：AFLNet 保存故意崩溃样本并由独立回放复现；临时探针已删除。"
