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
mkdir -p "${RUN_ROOT}"/{db,keys,data,agi,spool,run,log}
cat > "${RUN_ROOT}/asterisk.conf" <<EOF
[directories]
astetcdir => /workspace/config
astmoddir => ${PREFIX}/lib/asterisk/modules
astvarlibdir => ${RUN_ROOT}/data
astdbdir => ${RUN_ROOT}/db
astkeydir => ${RUN_ROOT}/keys
astdatadir => ${RUN_ROOT}/data
astagidir => ${RUN_ROOT}/agi
astspooldir => ${RUN_ROOT}/spool
astrundir => ${RUN_ROOT}/run
astlogdir => ${RUN_ROOT}/log
astsbindir => ${PREFIX}/sbin

[options]
verbose = 0
debug = 0
language = en
execincludes = no
dontwarn = yes

[files]
astctlpermissions = 0600
EOF
