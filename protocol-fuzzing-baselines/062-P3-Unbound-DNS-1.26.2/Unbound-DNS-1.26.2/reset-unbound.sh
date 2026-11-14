#!/usr/bin/env bash
set -euo pipefail
/bin/bash /opt/benchmark/stop-unbound.sh
/bin/bash /opt/benchmark/start-unbound.sh
