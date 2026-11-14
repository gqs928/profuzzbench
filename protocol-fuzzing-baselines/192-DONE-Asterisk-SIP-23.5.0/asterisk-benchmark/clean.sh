#!/usr/bin/env bash
set -euo pipefail

# 清理 AFLNet 上一轮终止后残留的 Asterisk 进程和注册/对话状态。
if command -v pkill >/dev/null 2>&1; then
	pkill -TERM -x asterisk 2>/dev/null || true
	for _ in $(seq 1 20); do
		pgrep -x asterisk >/dev/null 2>&1 || break
		sleep 0.05
	done
	pkill -KILL -x asterisk 2>/dev/null || true
fi
rm -rf "${ASTERISK_RUN_ROOT:-/tmp/asterisk-run}"
PACKAGE_DIR=${PACKAGE_DIR:-$(cd "$(dirname "$0")" && pwd)}
"${PACKAGE_DIR}/prepare-run.sh"
