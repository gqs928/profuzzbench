#!/usr/bin/env bash
set -euo pipefail

# 每个 AFLNet 样本从同一份 KRaft 单节点快照恢复，清除进程和持久消息状态。
DATA_DIR=${KAFKA_DATA:-/home/ubuntu/experiments/kafka-data}
SNAPSHOT_DIR=${KAFKA_SNAPSHOT:-/home/ubuntu/experiments/kafka-data-snapshot}
if [[ ! -d ${SNAPSHOT_DIR} ]]; then
	echo "缺少 Kafka 初始状态快照：${SNAPSHOT_DIR}" >&2
	exit 2
fi
rm -rf -- "${DATA_DIR}"
mkdir -p "$(dirname "${DATA_DIR}")"
cp -a "${SNAPSHOT_DIR}" "${DATA_DIR}"
