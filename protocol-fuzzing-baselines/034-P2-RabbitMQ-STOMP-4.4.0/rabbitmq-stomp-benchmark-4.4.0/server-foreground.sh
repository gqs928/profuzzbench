#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/rabbit-home
export RABBITMQ_HOME=/opt/rabbitmq/rabbitmq_server-4.4.0
export RABBITMQ_CONFIG_FILE=/opt/benchmark/configs/rabbitmq
export RABBITMQ_ENABLED_PLUGINS_FILE=/tmp/rabbitmq/enabled_plugins
export RABBITMQ_MNESIA_BASE=/tmp/rabbitmq/mnesia
export RABBITMQ_LOG_BASE=/tmp/rabbitmq/log
export RABBITMQ_PID_FILE=/tmp/rabbitmq/rabbitmq.pid
export RABBITMQ_NODENAME=rabbit@localhost
export ERL_EPMD_ADDRESS=127.0.0.1
exec "$RABBITMQ_HOME/sbin/rabbitmq-server"
