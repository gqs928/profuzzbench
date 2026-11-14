#!/usr/bin/env bash
set -euo pipefail

VARIANT=afl
if (($#)); then
	VARIANT=$1
	shift
fi
case "$VARIANT" in
	reference) PREFIX=$(printenv GANESHA_REFERENCE_PREFIX) ;;
	afl) PREFIX=$(printenv GANESHA_AFL_PREFIX) ;;
	gcov) PREFIX=$(printenv GANESHA_GCOV_PREFIX) ;;
	*) echo "未知 Ganesha 构建类型：$VARIANT" >&2; exit 2 ;;
esac

export LD_LIBRARY_PATH="$PREFIX/lib:$PREFIX/lib64:$PREFIX/lib/ganesha:$PREFIX/lib/x86_64-linux-gnu:$PREFIX/lib/x86_64-linux-gnu/ganesha"
GANESHA_LOG=${GANESHA_LOG:-/tmp/ganesha-fuzz.log}
exec "$PREFIX/bin/ganesha.nfsd" \
	-F -f /workspace/ganesha.conf -p /tmp/ganesha.pid -L "$GANESHA_LOG" -N NIV_CRIT "$@"
