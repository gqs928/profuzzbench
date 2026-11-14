#!/usr/bin/env bash
set -Eeuo pipefail

MODE=${1:-afl}
case "$MODE" in
  reference|afl|cover) ;;
  *) echo "usage: run.sh {reference|afl|cover}" >&2; exit 2 ;;
esac

PREFIX="/opt/ejabberd-$MODE"
WORK="/tmp/ejabberd-benchmark/$MODE"
export HOME="$WORK/home"
export EJABBERD_CONFIG_PATH=/opt/benchmark/configs/ejabberd.yml
export LOGS_DIR="$WORK/logs"
export EJABBERD_LOG_PATH="$WORK/ejabberd.log"
export SPOOL_DIR="$WORK/data"
export EJABBERD_PID_PATH="$WORK/ejabberd.pid"
export EJABBERDCTL_CONFIG_PATH="$PREFIX/conf/ejabberdctl.cfg"
export ERL_EPMD_ADDRESS=127.0.0.1
rm -rf "$WORK"
mkdir -p "$HOME" "$WORK/data" "$WORK/logs"
cd "$WORK"
trap 'trap - TERM INT; kill -TERM -- "-$$" 2>/dev/null || true' TERM INT
"$PREFIX/bin/ejabberdctl" foreground &
server_pid=$!
wait "$server_pid"
