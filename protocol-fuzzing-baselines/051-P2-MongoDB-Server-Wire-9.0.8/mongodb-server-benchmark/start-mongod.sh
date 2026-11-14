#!/usr/bin/env bash
set -euo pipefail

PORT=${MONGODB_PORT:-27017}
DATA_ROOT=${MONGODB_DATA_ROOT:-/tmp/mongodb-aflnet/run}
DBPATH=${DATA_ROOT}/db

rm -rf -- "${DATA_ROOT}"
mkdir -p "${DBPATH}"
exec /usr/bin/mongod \
  --dbpath "${DBPATH}" \
  --bind_ip 127.0.0.1 \
  --port "${PORT}" \
  --logpath "${DATA_ROOT}/mongod.log" \
  --logappend \
  --quiet \
  --wiredTigerCacheSizeGB 0.25
