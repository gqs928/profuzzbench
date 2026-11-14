#!/usr/bin/env bash
set -euo pipefail

kea_libdirs=$(cat /opt/kea/build-libdirs)
export LD_LIBRARY_PATH="${kea_libdirs}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ $# -eq 0 ]]; then
  set -- -c /work/kea.conf -p 6767
fi
exec /src/kea/build/src/bin/dhcp4/kea-dhcp4 "$@"
