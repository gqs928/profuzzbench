#!/usr/bin/env bash
set -euo pipefail

# 每个目标进程都先恢复 KRaft 快照，然后让 AFLNet 直接监控 Kafka JVM。
KAFKA_HOME=${KAFKA_HOME:-/home/ubuntu/experiments/kafka}
CONFIG=${KAFKA_CONFIG:-/home/ubuntu/experiments/kafka-broker.properties}
RESET_SCRIPT=${KAFKA_CLEAN_SCRIPT:-/home/ubuntu/experiments/clean.sh}
JAVA_AGENT=${KAFKA_AFL_AGENT:-/home/ubuntu/agents/libkafka_afl_agent.so}
JACOCO_AGENT=${JACOCO_AGENT:-/home/ubuntu/agents/jacoco-agent.jar}
JACOCO_DESTFILE=${JACOCO_DESTFILE:-/home/ubuntu/experiments/results/kafka.exec}
ENABLE_AFL_AGENT=${ENABLE_AFL_AGENT:-1}
ENABLE_JACOCO=${ENABLE_JACOCO:-1}

export KAFKA_HEAP_OPTS=${KAFKA_HEAP_OPTS:-"-Xms256m -Xmx768m"}
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -XX:ActiveProcessorCount=1"
agent_options=${KAFKA_OPTS:-}
if [[ ${ENABLE_AFL_AGENT} == 1 ]]; then
	[[ -f ${JAVA_AGENT} ]] || { echo "JVMTI 代理不存在：${JAVA_AGENT}" >&2; exit 2; }
	agent_options+=" -agentpath:${JAVA_AGENT}"
fi
if [[ ${ENABLE_JACOCO} == 1 ]]; then
	[[ -f ${JACOCO_AGENT} ]] || { echo "JaCoCo 代理不存在：${JACOCO_AGENT}" >&2; exit 2; }
	mkdir -p "$(dirname "${JACOCO_DESTFILE}")"
	# JaCoCo 的类名筛选列表用冒号分隔；只插桩 Kafka 请求处理入口，避免扫描整套依赖。
	agent_options+=" -javaagent:${JACOCO_AGENT}=destfile=${JACOCO_DESTFILE},append=true,dumponexit=true,includes=kafka/server/KafkaApis*"
fi
export KAFKA_OPTS=${agent_options# }
"${RESET_SCRIPT}"
exec "${KAFKA_HOME}/bin/kafka-server-start.sh" "${CONFIG}"
