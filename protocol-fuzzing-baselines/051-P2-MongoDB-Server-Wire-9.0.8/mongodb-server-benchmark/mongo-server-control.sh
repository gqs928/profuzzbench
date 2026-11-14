#!/usr/bin/env bash
set -euo pipefail

PORT=${MONGODB_PORT:-27017}
DATA_ROOT=${MONGODB_DATA_ROOT:-/tmp/mongodb-aflnet/run}
DBPATH=${DATA_ROOT}/db
PIDFILE=${MONGODB_PIDFILE:-/tmp/mongodb-aflnet/mongod.pid}
LOGFILE=${DATA_ROOT}/mongod.log
ACTION=${1:-restart}

is_mongod_pid() {
  local pid=$1
  [[ ${pid} =~ ^[0-9]+$ && -r /proc/${pid}/cmdline ]] || return 1
  tr '\0' ' ' < "/proc/${pid}/cmdline" | grep -q '/usr/bin/mongod'
}

stop_server() {
  local pid
  if [[ -r ${PIDFILE} ]]; then
    read -r pid < "${PIDFILE}" || true
    if is_mongod_pid "${pid:-}"; then
      kill -TERM "${pid}" 2>/dev/null || true
      for _ in {1..200}; do
        is_mongod_pid "${pid}" || break
        sleep 0.05
      done
      if is_mongod_pid "${pid}"; then
        kill -KILL "${pid}" 2>/dev/null || true
      fi
    fi
    rm -f -- "${PIDFILE}"
  fi
}

start_server() {
  mkdir -p "$(dirname "${PIDFILE}")"
  rm -rf -- "${DATA_ROOT}"
  mkdir -p "${DBPATH}"
  /usr/bin/mongod \
    --dbpath "${DBPATH}" \
    --bind_ip 127.0.0.1 \
    --port "${PORT}" \
    --pidfilepath "${PIDFILE}" \
    --logpath "${LOGFILE}" \
    --logappend \
    --quiet \
    --wiredTigerCacheSizeGB 0.25 \
    --fork
  for _ in {1..100}; do
    if python3 -c 'import socket,sys; s=socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=0.1); s.close()' "${PORT}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.05
  done
  tail -80 "${LOGFILE}" >&2 || true
  stop_server
  return 1
}

case "${ACTION}" in
  stop)
    stop_server
    ;;
  restart)
    stop_server
    start_server
    ;;
  *)
    echo "usage: $0 [restart|stop]" >&2
    exit 2
    ;;
esac
