#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
if "$ROOT/build/mysql-ready-check" --once; then exit 0; fi
docker restart tidb-bench-tidb >/dev/null
for _ in $(seq 1 240); do
  if "$ROOT/build/mysql-ready-check" --once; then exit 0; fi
  sleep .25
done
echo 'TiDB SQL layer did not recover' >&2
docker logs --tail 100 tidb-bench-tidb >&2 || true
exit 1
