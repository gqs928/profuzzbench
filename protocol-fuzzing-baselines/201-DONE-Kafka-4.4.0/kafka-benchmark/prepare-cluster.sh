#!/usr/bin/env bash
set -euo pipefail

# Docker 构建阶段格式化确定性单节点集群，并预建协议回放用主题。
KAFKA_HOME=${KAFKA_HOME:-/home/ubuntu/experiments/kafka}
CONFIG=${KAFKA_CONFIG:-/home/ubuntu/experiments/kafka-broker.properties}
DATA_DIR=${KAFKA_DATA:-/home/ubuntu/experiments/kafka-data}
SNAPSHOT_DIR=${KAFKA_SNAPSHOT:-/home/ubuntu/experiments/kafka-data-snapshot}
CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk
BROKER_LOG=${WORKDIR:-/home/ubuntu/experiments}/build-logs/cluster-bootstrap.log

mkdir -p "$(dirname "${BROKER_LOG}")"
rm -rf -- "${DATA_DIR}" "${SNAPSHOT_DIR}"
mkdir -p "${DATA_DIR}"
"${KAFKA_HOME}/bin/kafka-storage.sh" format --standalone \
	-t "${CLUSTER_ID}" -c "${CONFIG}"

ENABLE_AFL_AGENT=0 ENABLE_JACOCO=0 KAFKA_OPTS= \
	"${KAFKA_HOME}/bin/kafka-server-start.sh" "${CONFIG}" \
	>"${BROKER_LOG}" 2>&1 &
broker_pid=$!
cleanup() {
	if kill -0 "${broker_pid}" 2>/dev/null; then
		kill -TERM "${broker_pid}" 2>/dev/null || true
		for _ in $(seq 1 100); do
			kill -0 "${broker_pid}" 2>/dev/null || break
			sleep 0.1
		done
		kill -KILL "${broker_pid}" 2>/dev/null || true
	fi
	wait "${broker_pid}" 2>/dev/null || true
}
trap cleanup EXIT

python3 - <<'PY'
import socket
import time

deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    try:
        with socket.create_connection(("127.0.0.1", 9092), timeout=0.2):
            break
    except OSError:
        time.sleep(0.1)
else:
    raise SystemExit("Kafka Broker 未在 90 秒内监听 127.0.0.1:9092")
PY

"${KAFKA_HOME}/bin/kafka-topics.sh" --create --if-not-exists \
	--topic fuzz-topic --partitions 1 --replication-factor 1 \
	--bootstrap-server 127.0.0.1:9092 >>"${BROKER_LOG}" 2>&1
cleanup
trap - EXIT
cp -a "${DATA_DIR}" "${SNAPSHOT_DIR}"
test -s "${SNAPSHOT_DIR}/meta.properties"
