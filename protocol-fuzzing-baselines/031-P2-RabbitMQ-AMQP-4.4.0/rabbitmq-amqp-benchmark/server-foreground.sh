#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/rabbit-home
export RABBITMQ_NODENAME=rabbit@localhost
export RABBITMQ_USE_LONGNAME=false
export RABBITMQ_CONFIG_FILE=/opt/benchmark/configs/rabbitmq.conf
export RABBITMQ_MNESIA_BASE=/tmp/rabbit-data/mnesia
export RABBITMQ_LOG_BASE=/tmp/rabbit-data/log
export RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="+S 1:1 +A 4"
mkdir -p "$HOME" "$RABBITMQ_MNESIA_BASE" "$RABBITMQ_LOG_BASE"
chmod 0700 "$HOME"
export PATH="/opt/rabbitmq/rabbitmq_server-4.4.0/sbin:$PATH"
exec rabbitmq-server
