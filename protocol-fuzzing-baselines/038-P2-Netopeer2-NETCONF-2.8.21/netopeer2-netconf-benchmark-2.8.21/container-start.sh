#!/usr/bin/env bash
set -Eeuo pipefail
sysrepo-plugind -d >/tmp/sysrepo-plugind.log 2>&1 &
sysrepo-notifd -d >/tmp/sysrepo-notifd.log 2>&1 &
sleep 1
netopeer2-server -d >/tmp/netopeer2-server.log 2>&1 &
ready=0
for _ in $(seq 1 120); do
  if ( exec 3<>/dev/tcp/127.0.0.1/830 ) >/dev/null 2>&1; then ready=1; break; fi
  sleep .5
done
if [[ $ready != 1 ]]; then
  cat /tmp/sysrepo-plugind.log /tmp/sysrepo-notifd.log /tmp/netopeer2-server.log >&2
  exit 1
fi
python3 /opt/benchmark/netconf_proxy.py >/tmp/netconf-proxy.log 2>&1 &
exec sleep infinity
