#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
if [[ -f "$ROOT/build/proxy.pid" ]]; then
  pid=$(cat "$ROOT/build/proxy.pid")
  args=$(ps -p "$pid" -o args= 2>/dev/null || true)
  if [[ "$args" == *"$ROOT/mysql_auth_proxy.py"* && "$args" == *"$MYSQL_PROXY_PORT"* ]]; then
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 40); do ps -p "$pid" >/dev/null 2>&1 || break; sleep .1; done
    ps -p "$pid" >/dev/null 2>&1 && kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$ROOT/build/proxy.pid"
fi
docker rm -fv "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker image rm "$IMAGE" >/dev/null
if docker image inspect "$IMAGE" >/dev/null 2>&1; then echo "image still present: $IMAGE" >&2; exit 1; fi
if docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then echo "container still present: $CONTAINER_NAME" >&2; exit 1; fi
echo "removed_container=$CONTAINER_NAME"
echo "removed_image=$IMAGE"
