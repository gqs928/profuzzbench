#!/usr/bin/env bash
set -euo pipefail

variant=${1:-afl}
case "${variant}" in
  reference) prefix=${DOVECOT_REFERENCE_PREFIX:-/home/ubuntu/experiments/dovecot-reference} ;;
  afl) prefix=${DOVECOT_AFL_PREFIX:-/home/ubuntu/experiments/dovecot-afl} ;;
  gcov) prefix=${DOVECOT_GCOV_PREFIX:-/home/ubuntu/experiments/dovecot-gcov} ;;
  *) echo "未知服务端构建类型：${variant}" >&2; exit 2 ;;
esac

export PATH="${prefix}/bin:${prefix}/sbin:${prefix}/libexec:${PATH}"
export LD_LIBRARY_PATH="${prefix}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
/workspace/reset-state.sh
if [[ ${EUID} -eq 0 ]]; then
  exec "${prefix}/sbin/dovecot" -F -c "${DOVECOT_CONFIG:-/workspace/dovecot.conf}"
fi
exec sudo -n /usr/local/sbin/dovecot-root-launcher "${variant}"
