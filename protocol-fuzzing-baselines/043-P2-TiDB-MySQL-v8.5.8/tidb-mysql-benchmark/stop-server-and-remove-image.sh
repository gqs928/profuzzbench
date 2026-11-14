#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
if [[ -f "$ROOT/build/proxy.pid" ]]; then
  pid=$(cat "$ROOT/build/proxy.pid"); args=$(ps -p "$pid" -o args= 2>/dev/null || true)
  if [[ "$args" == *"$ROOT/mysql_auth_proxy.py"* && "$args" == *"$MYSQL_PROXY_PORT"* ]]; then
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 40); do ps -p "$pid" >/dev/null 2>&1 || break; sleep .1; done
    ps -p "$pid" >/dev/null 2>&1 && kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$ROOT/build/proxy.pid"
fi
for c in tidb-bench-tidb tidb-bench-tikv tidb-bench-pd; do docker rm -fv "$c" >/dev/null 2>&1 || true; done
for image in "$TIDB_IMAGE" "$TIKV_IMAGE" "$PD_IMAGE"; do
  docker image rm "$image" >/dev/null
  if docker image inspect "$image" >/dev/null 2>&1; then echo "image still present: $image" >&2; exit 1; fi
done
for c in tidb-bench-tidb tidb-bench-tikv tidb-bench-pd; do
  if docker ps -a --filter "name=^/${c}$" --format '{{.Names}}' | grep -Fxq "$c"; then echo "container still present: $c" >&2; exit 1; fi
done
echo 'removed_containers=tidb-bench-tidb,tidb-bench-tikv,tidb-bench-pd'
echo 'removed_images=pingcap/tidb:v8.5.8,pingcap/tikv:v8.5.8,pingcap/pd:v8.5.8'
