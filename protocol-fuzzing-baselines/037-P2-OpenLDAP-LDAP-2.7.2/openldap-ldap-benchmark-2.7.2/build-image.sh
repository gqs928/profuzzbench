#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OPENLDAP_SECURITY_CDN_IPV4=${OPENLDAP_SECURITY_CDN_IPV4:-185.125.190.82}
docker build --add-host="security.ubuntu.com:${OPENLDAP_SECURITY_CDN_IPV4}" \
  -t profuzzbench-openldap-ldap:2.7.2 "$ROOT"
