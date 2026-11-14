#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
mkdir -p "$ROOT/build"
docker rm -fv "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --restart unless-stopped --name "$CONTAINER_NAME" \
  -p "127.0.0.1:${MYSQL_BACKEND_PORT}:3306" \
  -e "${ROOT_PASSWORD_ENV}=${BENCHMARK_PASSWORD}" \
  -e "${ROOT_HOST_ENV}=%" "$IMAGE" >/dev/null
ready=0
for _ in $(seq 1 240); do
  if "$ROOT/build/mysql-ready-check" --once; then ready=1; break; fi
  sleep .25
done
if [[ $ready != 1 ]]; then docker logs --tail 100 "$CONTAINER_NAME" >&2 || true; exit 1; fi
if [[ -f "$ROOT/build/proxy.pid" ]]; then old=$(cat "$ROOT/build/proxy.pid"); if ps -p "$old" -o args= 2>/dev/null | grep -Fq "$ROOT/mysql_auth_proxy.py"; then kill "$old" || true; fi; fi
python3 "$ROOT/mysql_auth_proxy.py" --listen-host 127.0.0.1 --listen-port "$MYSQL_PROXY_PORT" \
  --backend-host 127.0.0.1 --backend-port "$MYSQL_BACKEND_PORT" --user "$BENCHMARK_USER" \
  --password "$BENCHMARK_PASSWORD" >"$ROOT/build/proxy.log" 2>&1 &
proxy_pid=$!
echo "$proxy_pid" >"$ROOT/build/proxy.pid"
cleanup_proxy() {
  kill "$proxy_pid" 2>/dev/null || true
  wait "$proxy_pid" 2>/dev/null || true
  rm -f "$ROOT/build/proxy.pid"
}
trap cleanup_proxy EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
for _ in $(seq 1 80); do
  if python3 "$ROOT/protocol_smoke.py" --port "$MYSQL_PROXY_PORT" --quiet; then
    runtime_version=$(docker exec -e "MYSQL_PWD=$BENCHMARK_PASSWORD" "$CONTAINER_NAME" "$DATABASE_CLI" \
      -u"$BENCHMARK_USER" -N -e 'SELECT VERSION()')
    image_digest=$(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}')
    cat >"$ROOT/build/target-version-runtime.txt" <<EOF
image=$IMAGE
image_digest=$image_digest
runtime_version=$runtime_version
backend_port=$MYSQL_BACKEND_PORT
proxy_port=$MYSQL_PROXY_PORT
EOF
    echo "$TARGET_NAME runtime $runtime_version ready; authenticated loopback MySQL proxy is accepting SQL packets. Keep this terminal open while fuzzing."
    wait "$proxy_pid"
    exit 0
  fi
  sleep .25
done
tail -80 "$ROOT/build/proxy.log" >&2 || true
docker logs --tail 80 "$CONTAINER_NAME" >&2 || true
exit 1
