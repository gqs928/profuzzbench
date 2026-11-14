#!/usr/bin/env bash
set -euo pipefail

if (($# != 1)); then
  echo "需要且只接受一个服务端变体名称" >&2
  exit 2
fi

case "$1" in
  reference) prefix=/home/ubuntu/experiments/dovecot-reference ;;
  afl) prefix=/home/ubuntu/experiments/dovecot-afl ;;
  gcov) prefix=/home/ubuntu/experiments/dovecot-gcov ;;
  *) echo "未知服务端变体：$1" >&2; exit 2 ;;
esac

export LD_LIBRARY_PATH="${prefix}/lib"
exec "${prefix}/sbin/dovecot" -F -c /workspace/dovecot.conf
