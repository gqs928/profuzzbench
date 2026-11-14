#!/usr/bin/env bash
set -euo pipefail
/bin/bash /opt/benchmark/stop-knot.sh
rm -rf /tmp/knot-rundir /tmp/knot-storage
mkdir -p /tmp/knot-rundir /tmp/knot-storage
chown knot:knot /tmp/knot-rundir /tmp/knot-storage
/bin/bash /opt/benchmark/start-knot.sh
