#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
if "$ROOT/build/pgwire-ready-check" --once; then exit 0; fi
docker restart cockroachdb-pg-2611 >/dev/null
for _ in $(seq 1 120); do
  if "$ROOT/build/pgwire-ready-check" --once; then exit 0; fi
  sleep .25
done
echo 'CockroachDB PostgreSQL-wire service did not recover' >&2
docker logs --tail 100 cockroachdb-pg-2611 >&2 || true
exit 1
