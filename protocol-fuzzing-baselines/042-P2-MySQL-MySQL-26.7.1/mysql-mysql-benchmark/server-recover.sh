#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
if "$ROOT/build/mysql-ready-check" --once; then exit 0; fi
docker restart "$CONTAINER_NAME" >/dev/null
for _ in $(seq 1 240); do
  if "$ROOT/build/mysql-ready-check" --once; then exit 0; fi
  sleep .25
done
echo "$TARGET_NAME service did not recover" >&2
docker logs --tail 100 "$CONTAINER_NAME" >&2 || true
exit 1
