#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f netopeer2-netconf-2821 2>/dev/null || true
docker image rm profuzzbench-netopeer2-netconf:2.8.21
