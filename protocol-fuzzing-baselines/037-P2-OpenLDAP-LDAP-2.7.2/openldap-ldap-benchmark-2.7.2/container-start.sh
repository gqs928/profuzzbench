#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p /var/lib/openldap-data /run/openldap
chown openldap:openldap /run/openldap
chown -R openldap:openldap /var/lib/openldap-data
if [[ ! -f /var/lib/openldap-data/data.mdb ]]; then
  /opt/openldap/sbin/slapadd -f /opt/benchmark/configs/slapd.conf -l /opt/benchmark/configs/base.ldif
  chown -R openldap:openldap /var/lib/openldap-data
fi
exec /opt/openldap/libexec/slapd -f /opt/benchmark/configs/slapd.conf -h 'ldap://0.0.0.0:3389' -u openldap -g openldap -d 0
