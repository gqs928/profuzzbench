#!/usr/bin/env bash
set -euo pipefail

variant=${1:-afl}
sudo -n /usr/local/sbin/dovecot-root-launcher "${variant}" reset
/workspace/reset-state.sh
exec sudo -n -C 200 /usr/local/sbin/dovecot-root-launcher "${variant}" start
