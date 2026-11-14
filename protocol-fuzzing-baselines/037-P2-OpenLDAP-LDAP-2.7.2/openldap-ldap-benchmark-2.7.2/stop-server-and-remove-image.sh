#!/usr/bin/env bash
set -Eeuo pipefail
docker rm -f openldap-ldap-272 >/dev/null 2>&1 || true
docker image rm profuzzbench-openldap-ldap:2.7.2
