#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
IMAGE='questdb/questdb:10.1.0'
docker rm -f questdb-pg-1010 >/dev/null 2>&1 || true
docker run -d --restart unless-stopped --name questdb-pg-1010 -p 127.0.0.1:8812:8812 "$IMAGE" >/dev/null
for _ in $(seq 1 120); do
  if "$ROOT/build/pgwire-ready-check" --once; then
    printf 'image=questdb/questdb:10.1.0\n' | tee "$ROOT/build/target-version-runtime.txt"
    echo 'QuestDB is responding to PostgreSQL protocol StartupMessage.'
    exit 0
  fi
  sleep .25
done
docker logs --tail 100 questdb-pg-1010 >&2 || true
exit 1
