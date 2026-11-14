#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
CONTAINER=vitess-bench-vttestserver
docker rm -fv "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --restart unless-stopped --network host --name "$CONTAINER" \
  -e PORT="$VITESS_PORT" -e KEYSPACES=unsharded -e NUM_SHARDS=1 \
  -e MYSQL_BIND_HOST=127.0.0.1 -e VTCOMBO_BIND_HOST=127.0.0.1 \
  "$VITESS_IMAGE" >/dev/null
ready=0
for _ in $(seq 1 360); do
  if "$ROOT/build/mysql-ready-check" --once && curl -fsS "http://127.0.0.1:$VITESS_PORT/debug/status" >/dev/null 2>&1; then ready=1; break; fi
  sleep .5
done
[[ $ready == 1 ]] || { docker logs --tail 120 "$CONTAINER" >&2 || true; exit 1; }
if [[ -f "$ROOT/build/proxy.pid" ]]; then
  old=$(cat "$ROOT/build/proxy.pid")
  if ps -p "$old" -o args= 2>/dev/null | grep -Fq "$ROOT/mysql_auth_proxy.py"; then kill "$old" || true; fi
fi
python3 "$ROOT/mysql_auth_proxy.py" --listen-host 127.0.0.1 --listen-port "$MYSQL_PROXY_PORT" \
  --backend-host 127.0.0.1 --backend-port "$MYSQL_BACKEND_PORT" --user "$BENCHMARK_USER" \
  --password "$BENCHMARK_PASSWORD" >"$ROOT/build/proxy.log" 2>&1 &
proxy_pid=$!
echo "$proxy_pid" >"$ROOT/build/proxy.pid"
cleanup_proxy() { kill "$proxy_pid" 2>/dev/null || true; wait "$proxy_pid" 2>/dev/null || true; rm -f "$ROOT/build/proxy.pid"; }
trap cleanup_proxy EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
proxy_ready=0
for _ in $(seq 1 80); do
  if python3 "$ROOT/protocol_smoke.py" --port "$MYSQL_PROXY_PORT" --quiet; then proxy_ready=1; break; fi
  sleep .5
done
[[ $proxy_ready == 1 ]] || { tail -100 "$ROOT/build/proxy.log" >&2 || true; exit 1; }
runtime_version=$(docker exec "$CONTAINER" /vt/bin/vttestserver --version 2>&1)
[[ "$runtime_version" == *"${TARGET_VERSION#v}"* ]] || { echo "runtime version mismatch: $runtime_version" >&2; exit 1; }
image_digest=$(docker image inspect "$VITESS_IMAGE" --format '{{index .RepoDigests 0}}')
{
  printf 'target_version=%s\nruntime_version=%s\n' "$TARGET_VERSION" "$runtime_version"
  printf 'image_tag=%s\nimage_digest=%s\n' "$VITESS_IMAGE_TAG" "$image_digest"
  printf 'vtgate_port=%s\nproxy_port=%s\n' "$MYSQL_BACKEND_PORT" "$MYSQL_PROXY_PORT"
  printf 'topology=single unsharded keyspace; one shard\n'
} >"$ROOT/build/target-version-runtime.txt"
echo "Vitess $TARGET_VERSION runtime and vtgate MySQL endpoint are ready; proxy smoke SELECT 1 passed. Keep this terminal open while fuzzing."
wait "$proxy_pid"
