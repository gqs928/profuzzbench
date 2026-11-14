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
mkdir -p "$HOME" /tmp/rabbitmq/mnesia /tmp/rabbitmq/log
nohup "$RABBITMQ_HOME/sbin/rabbitmq-server" >/tmp/rabbitmq/server.log 2>&1 </dev/null &
for _ in $(seq 1 120); do
  if "$RABBITMQ_HOME/sbin/rabbitmqctl" await_startup >/dev/null 2>&1; then break; fi
  sleep .5
done
"$RABBITMQ_HOME/sbin/rabbitmqctl" add_user admin admin || true
"$RABBITMQ_HOME/sbin/rabbitmqctl" set_user_tags admin administrator
"$RABBITMQ_HOME/sbin/rabbitmqctl" set_permissions -p / admin '.*' '.*' '.*'
ready=0
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/61613 ) >/dev/null 2>&1; then ready=1; break; fi
  sleep .5
done
[[ $ready == 1 ]] || { cat /tmp/rabbitmq/server.log >&2; exit 1; }
exec sleep infinity
