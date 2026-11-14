#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/qpid-home
export QPID_HOME=/opt/qpid
export QPID_WORK=/tmp/qpid-work
mkdir -p "$HOME" "$QPID_WORK"
exec /opt/qpid/bin/qpid-server -icp /opt/benchmark/qpid-initial-config.json -prop qpid.amqp_port=5672
