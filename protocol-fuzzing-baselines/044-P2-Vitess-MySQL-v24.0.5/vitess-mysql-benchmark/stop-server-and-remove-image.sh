#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
if [[ -f "$ROOT/build/proxy.pid" ]]; then
  pid=$(cat "$ROOT/build/proxy.pid"); args=$(ps -p "$pid" -o args= 2>/dev/null || true)
  if [[ "$args" == *"$ROOT/mysql_auth_proxy.py"* ]]; then kill "$pid" 2>/dev/null || true; fi
  rm -f "$ROOT/build/proxy.pid"
fi
docker rm -fv vitess-bench-vttestserver >/dev/null 2>&1 || true
docker image rm "$VITESS_IMAGE" >/dev/null
if docker image inspect "$VITESS_IMAGE" >/dev/null 2>&1; then echo "image still present: $VITESS_IMAGE" >&2; exit 1; fi
if docker ps -a --filter 'name=^/vitess-bench-vttestserver$' --format '{{.Names}}' | grep -Fxq vitess-bench-vttestserver; then echo 'container still present' >&2; exit 1; fi
echo 'removed_containers=vitess-bench-vttestserver'
echo "removed_images=$VITESS_IMAGE"
