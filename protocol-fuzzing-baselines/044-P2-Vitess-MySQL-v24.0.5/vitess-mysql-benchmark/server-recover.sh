#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
CONTAINER=vitess-bench-vttestserver
if "$ROOT/build/mysql-ready-check" --once && curl -fsS "http://127.0.0.1:$VITESS_PORT/debug/status" >/dev/null 2>&1; then exit 0; fi
if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then echo "missing container: $CONTAINER" >&2; exit 1; fi
docker restart "$CONTAINER" >/dev/null
for _ in $(seq 1 360); do
  if "$ROOT/build/mysql-ready-check" --once && curl -fsS "http://127.0.0.1:$VITESS_PORT/debug/status" >/dev/null 2>&1; then exit 0; fi
  sleep .5
done
echo 'Vitess vtgate did not recover' >&2
docker logs --tail 120 "$CONTAINER" >&2 || true
exit 1
