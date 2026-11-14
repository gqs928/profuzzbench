#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${1:-/results/fault-probe}
PROBE_TIMEOUT=${FAULT_PROBE_TIMEOUT:-45s}
TMP_DIR=$(mktemp -d /tmp/freeradius-fault-probe.XXXXXX)
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
FUZZER_BIN=${FUZZER_BIN:-${AFLNET}/afl-fuzz}
PROBE_BIN=${TMP_DIR}/fault-probe-server
INPUT_DIR=${TMP_DIR}/in
FUZZ_DIR=${TMP_DIR}/out

cleanup_tmp() {
	rm -rf -- "${TMP_DIR}"
}
trap cleanup_tmp EXIT

if [[ -e ${OUTDIR} ]] && [[ -n $(find "${OUTDIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
	echo "故障探针结果目录非空：${OUTDIR}" >&2
	exit 2
fi
mkdir -p "${OUTDIR}" "${INPUT_DIR}"
ulimit -c 0

# 临时构建一个 RADIUS/TCP 测试服务，在特定测试属性到达时主动异常退出。
cat > "${TMP_DIR}/fault-probe-server.c" <<'EOF'
#include <arpa/inet.h>
#include <signal.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int contains_marker(const uint8_t *data, size_t size)
{
	static const uint8_t marker[] = "FAULT-PROBE";
	size_t i;
	for (i = 0; i + sizeof(marker) - 1 <= size; i++) {
		if (memcmp(data + i, marker, sizeof(marker) - 1) == 0) return 1;
	}
	return 0;
}

int main(void)
{
	int server_fd = socket(AF_INET, SOCK_STREAM, 0);
	struct sockaddr_in address;
	uint8_t request[65536], response[20] = {2, 1, 0, 20};
	int reuse = 1;
	if (server_fd < 0) return 2;
	(void)setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
	memset(&address, 0, sizeof(address));
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	address.sin_port = htons(1812);
	if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0 ||
	    listen(server_fd, 8) < 0) return 3;
	for (;;) {
		int client_fd = accept(server_fd, NULL, NULL);
		size_t used = 0;
		if (client_fd < 0) continue;
		while (used < sizeof(request)) {
			ssize_t count = recv(client_fd, request + used, sizeof(request) - used, 0);
			if (count <= 0) break;
			used += (size_t)count;
			if (used >= 4) {
				size_t length = ((size_t)request[2] << 8) | request[3];
				if (length >= 20 && used >= length) {
					if (contains_marker(request, length)) abort();
					response[1] = request[1];
					(void)send(client_fd, response, sizeof(response), 0);
					break;
				}
			}
		}
		close(client_fd);
	}
}
EOF

python3 - "${INPUT_DIR}/fault-trigger.bin" <<'PY'
import pathlib
import sys

marker = b"GAULT-PROBE"
attribute = bytes((1, len(marker) + 2)) + marker
packet = bytes((1, 1)) + (20 + len(attribute)).to_bytes(2, "big") + bytes(16) + attribute
pathlib.Path(sys.argv[1]).write_bytes(packet)
PY

sha256sum "${TMP_DIR}/fault-probe-server.c" > "${OUTDIR}/temporary-probe-source.sha256"
AFL_USE_ASAN=1 "${AFLNET}/afl-clang-fast" -O1 -g \
	"${TMP_DIR}/fault-probe-server.c" -o "${PROBE_BIN}"

set +e
timeout --signal=INT --kill-after=5s "${PROBE_TIMEOUT}" "${FUZZER_BIN}" \
	-i "${INPUT_DIR}" -o "${FUZZ_DIR}" -N tcp://127.0.0.1/1812 \
	-P RADIUS -E -q 3 -s 3 -R -K -D 1000 -W 100 -w 100000 \
	-m none -t 1000+ -c /workspace/clean.sh \
	"${PROBE_BIN}"
STATUS=$?
set -e
printf 'fuzzer_exit_status=%s\n' "${STATUS}" > "${OUTDIR}/probe-status.txt"

if [[ -f ${FUZZ_DIR}/fuzzer_stats ]]; then
	cp "${FUZZ_DIR}/fuzzer_stats" "${OUTDIR}/fuzzer_stats"
	grep -E '^(execs_done|unique_crashes|unique_hangs|paths_total)[[:space:]]*:' \
		"${FUZZ_DIR}/fuzzer_stats" > "${OUTDIR}/probe-counters.txt" || true
fi
if [[ -f ${FUZZ_DIR}/ipsm.dot ]]; then cp "${FUZZ_DIR}/ipsm.dot" "${OUTDIR}/ipsm.dot"; fi
crash_sample=$(find "${FUZZ_DIR}/replayable-crashes" -maxdepth 1 -type f -name 'id:*' -print -quit 2>/dev/null || true)
if [[ -n ${crash_sample} ]]; then
	cp "${crash_sample}" "${OUTDIR}/intentional-crash-sample.aflnet"
	python3 - "${crash_sample}" "${OUTDIR}/intentional-crash-sample.bin" <<'PY'
import pathlib
import sys

stored = pathlib.Path(sys.argv[1]).read_bytes()
messages = []
cursor = 0
while cursor < len(stored):
	if cursor + 4 > len(stored):
		raise SystemExit("异常样本的 AFLNet 长度前缀不完整")
	size = int.from_bytes(stored[cursor : cursor + 4], sys.byteorder)
	cursor += 4
	if size < 20 or cursor + size > len(stored):
		raise SystemExit(f"异常样本的 RADIUS 报文长度无效：{size}")
	messages.append(stored[cursor : cursor + size])
	cursor += size
if not messages:
	raise SystemExit("异常样本没有可回放的 RADIUS 报文")
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
	[str(server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
)
try:
	deadline = time.monotonic() + 10
	sock = None
	while time.monotonic() < deadline:
		if process.poll() is not None:
			raise SystemExit(f"独立回放服务提前退出：{process.returncode}")
		try:
			sock = socket.create_connection(("127.0.0.1", 1812), timeout=0.2)
			break
		except OSError:
			time.sleep(0.05)
	if sock is None:
		raise SystemExit("独立回放服务启动超时")
	with sock:
		sock.sendall(sample)
		sock.shutdown(socket.SHUT_WR)
	deadline = time.monotonic() + 5
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
fi

crash_count=0
if [[ -f ${OUTDIR}/fuzzer_stats ]]; then
	crash_count=$(awk -F: '/^unique_crashes[[:space:]]*:/ { gsub(/[[:space:]]/, "", $2); print $2 }' \
		"${OUTDIR}/fuzzer_stats")
fi
rm -rf -- "${TMP_DIR}"
if [[ -e ${TMP_DIR} ]]; then
	echo "临时故障注入文件未清理：${TMP_DIR}" >&2
	exit 1
fi
printf 'temporary_injection_removed=true\n' >> "${OUTDIR}/probe-status.txt"
[[ ${crash_count:-0} -gt 0 && -s ${OUTDIR}/intentional-crash-sample.bin ]]
echo "通过：AFLNet 记录到故意异常退出；临时服务和注入源码已删除。"
