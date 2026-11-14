#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
NETOPEER2_SECURITY_CDN_IPV4=${NETOPEER2_SECURITY_CDN_IPV4:-185.125.190.82}
docker build --add-host="security.ubuntu.com:${NETOPEER2_SECURITY_CDN_IPV4}" \
  -t profuzzbench-netopeer2-netconf:2.8.21 "$ROOT"
