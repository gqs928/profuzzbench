#!/usr/bin/env bash
set -euo pipefail

VARIANT=${ASTERISK_VARIANT:-afl}
case "${VARIANT}" in
	reference) PREFIX=${ASTERISK_REFERENCE_PREFIX:-/home/ubuntu/asterisk-reference} ;;
	afl) PREFIX=${ASTERISK_AFL_PREFIX:-/home/ubuntu/asterisk-afl} ;;
	gcov) PREFIX=${ASTERISK_GCOV_PREFIX:-/home/ubuntu/asterisk-gcov} ;;
	*) echo "未知 Asterisk 构建变体：${VARIANT}" >&2; exit 2 ;;
esac

RUN_ROOT=${ASTERISK_RUN_ROOT:-/tmp/asterisk-run}
export ASTERISK_VARIANT=${VARIANT}
export ASTERISK_RUN_ROOT=${RUN_ROOT}
export LD_LIBRARY_PATH="${PREFIX}/lib:${LD_LIBRARY_PATH:-}"
ulimit -c 0

"$(dirname "$0")/clean.sh"

exec "${PREFIX}/sbin/asterisk" -f -n -C "${RUN_ROOT}/asterisk.conf"
