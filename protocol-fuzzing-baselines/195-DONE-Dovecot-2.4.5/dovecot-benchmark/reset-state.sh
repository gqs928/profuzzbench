#!/usr/bin/env bash
set -euo pipefail

STATE_ROOT=/tmp/dovecot-benchmark-state
if [[ "${STATE_ROOT}" != /tmp/dovecot-benchmark-state ]]; then
  echo "拒绝清理测试目录之外的状态" >&2
  exit 2
fi
rm -rf -- "${STATE_ROOT}"
mkdir -p "${STATE_ROOT}/run" "${STATE_ROOT}/state" "${STATE_ROOT}/log"
python3 /workspace/prepare_maildir.py
