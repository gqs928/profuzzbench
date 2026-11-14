#!/usr/bin/env bash
set -euo pipefail
/bin/bash /opt/benchmark/stop-bgpd.sh
/bin/bash /opt/benchmark/start-bgpd.sh
