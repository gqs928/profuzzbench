#!/usr/bin/env bash
set -euo pipefail

if (($# < 1 || $# > 2)); then
  echo "需要变体名称，以及可选的 start/stop 操作" >&2
  exit 2
fi

variant=$1
action=${2:-start}
case "${variant}" in
  reference) prefix=/home/ubuntu/experiments/dovecot-reference ;;
  afl) prefix=/home/ubuntu/experiments/dovecot-afl ;;
  gcov) prefix=/home/ubuntu/experiments/dovecot-gcov ;;
  *) echo "未知服务端变体：${variant}" >&2; exit 2 ;;
esac

case "${action}" in
  start)
    export LD_LIBRARY_PATH="${prefix}/lib"
    exec "${prefix}/sbin/dovecot" -F -c /workspace/dovecot.conf
    ;;
  stop)
    export LD_LIBRARY_PATH="${prefix}/lib"
    exec "${prefix}/sbin/dovecot" -c /workspace/dovecot.conf stop
    ;;
  reset)
    /bin/rm -rf -- /tmp/dovecot-benchmark-state
    ;;
  *) echo "未知启动器操作：${action}" >&2; exit 2 ;;
esac
