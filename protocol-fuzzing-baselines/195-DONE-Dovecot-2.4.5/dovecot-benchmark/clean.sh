#!/usr/bin/env bash
set -euo pipefail

# AFLNet 每次发送测试输入前只重建邮件数据，保留仍在监听的 Dovecot master。
python3 /workspace/prepare_maildir.py
