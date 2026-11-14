#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
  echo "AFLNet 邮箱复位需要容器 root 调用固定的 ubuntu 清理程序" >&2
  exit 2
fi

# root 只负责传递权限，固定测试邮箱始终由 ubuntu 用户重建。
exec runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
