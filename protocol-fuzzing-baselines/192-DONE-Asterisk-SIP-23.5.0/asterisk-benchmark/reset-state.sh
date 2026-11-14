#!/usr/bin/env bash
set -euo pipefail

# AFLNet 的 -K 会回收本轮目标子进程；此回调只重置可写状态，保留 forkserver。
RUN_ROOT=${ASTERISK_RUN_ROOT:-/tmp/asterisk-run}
rm -rf "${RUN_ROOT}"
PACKAGE_DIR=${PACKAGE_DIR:-$(cd "$(dirname "$0")" && pwd)}
"${PACKAGE_DIR}/prepare-run.sh"
