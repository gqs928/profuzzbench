#!/usr/bin/env bash
set -euo pipefail

STATE_DIR=${RADIUS_STATE_DIR:-/home/ubuntu/experiments/state}

# 删除上一轮产生的记账明细，避免报文回放继承持久化状态。
rm -rf -- "${STATE_DIR}"
mkdir -p -- "${STATE_DIR}/radacct"
chmod 700 -- "${STATE_DIR}" "${STATE_DIR}/radacct"
