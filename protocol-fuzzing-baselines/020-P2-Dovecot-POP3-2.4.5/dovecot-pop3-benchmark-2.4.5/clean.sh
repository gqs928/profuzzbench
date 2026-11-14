#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
  echo "Mailbox reset hook must run as container root" >&2
  exit 2
fi
exec runuser -u ubuntu -- python3 /workspace/prepare_maildir.py
