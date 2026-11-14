#!/usr/bin/env bash
set -euo pipefail
jobs=${MAKE_JOBS:-2}
docker build --build-arg MAKE_JOBS="$jobs" -t kea-dhcp4-aflnet:3.2.1 .
