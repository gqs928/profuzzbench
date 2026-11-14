#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/target.env"
PD=tidb-bench-pd
TIKV=tidb-bench-tikv
TIDB=tidb-bench-tidb
for c in "$PD" "$TIKV" "$TIDB"; do docker rm -fv "$c" >/dev/null 2>&1 || true; done
docker run -d --restart unless-stopped --network host --name "$PD" "$PD_IMAGE" \
  --name="$PD" --data-dir=/data/pd --client-urls=http://127.0.0.1:2379 \
  --peer-urls=http://127.0.0.1:2380 --advertise-client-urls=http://127.0.0.1:2379 \
  --advertise-peer-urls=http://127.0.0.1:2380 --initial-cluster="$PD=http://127.0.0.1:2380" >/dev/null
pd_ready=0
for _ in $(seq 1 120); do
  if curl -fsS http://127.0.0.1:2379/pd/api/v1/health >/dev/null 2>&1; then pd_ready=1; break; fi
  sleep .5
done
[[ $pd_ready == 1 ]] || { docker logs --tail 100 "$PD" >&2 || true; exit 1; }
docker run -d --restart unless-stopped --network host --name "$TIKV" "$TIKV_IMAGE" \
  --addr=127.0.0.1:20160 --advertise-addr=127.0.0.1:20160 --data-dir=/data/tikv --pd=127.0.0.1:2379 >/dev/null
sleep 8
docker run -d --restart unless-stopped --network host --name "$TIDB" "$TIDB_IMAGE" \
  --store=tikv --path=127.0.0.1:2379 --host=127.0.0.1 --advertise-address=127.0.0.1 \
  -P=4000 --status=10080 >/dev/null
for _ in $(seq 1 240); do
  if "$ROOT/build/mysql-ready-check" --once; then
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
        if runtime_version=$(docker exec "$TIDB" tidb-server -V 2>/dev/null); then
          :
        else
          runtime_version=$(docker exec "$TIDB" /tidb-server -V 2>&1)
        fi
        if [[ "$runtime_version" != *"$TARGET_VERSION"* ]]; then
          echo "runtime TiDB version does not match $TARGET_VERSION: $runtime_version" >&2
          exit 1
        fi
        pd_digest=$(docker image inspect "$PD_IMAGE" --format '{{index .RepoDigests 0}}')
        tikv_digest=$(docker image inspect "$TIKV_IMAGE" --format '{{index .RepoDigests 0}}')
        tidb_digest=$(docker image inspect "$TIDB_IMAGE" --format '{{index .RepoDigests 0}}')
        {
          printf 'target_version=%s\n' "$TARGET_VERSION"
          printf 'runtime_version=%s\n' "$runtime_version"
          printf 'pd_image=%s\npd_digest=%s\n' "$PD_IMAGE" "$pd_digest"
          printf 'tikv_image=%s\ntikv_digest=%s\n' "$TIKV_IMAGE" "$tikv_digest"
          printf 'tidb_image=%s\ntidb_digest=%s\n' "$TIDB_IMAGE" "$tidb_digest"
          printf 'sql_port=%s\nproxy_port=%s\n' "$MYSQL_BACKEND_PORT" "$MYSQL_PROXY_PORT"
        } >"$ROOT/build/target-version-runtime.txt"
        echo "TiDB $TARGET_VERSION (runtime $runtime_version) PD/TiKV/TiDB cluster ready; loopback MySQL proxy verified with SELECT 1. Keep this terminal open while fuzzing."
        wait "$proxy_pid"
        exit 0
      fi
      sleep .5
    done
    tail -80 "$ROOT/build/proxy.log" >&2 || true
    exit 1
  fi
  sleep .5
done
for c in "$TIDB" "$TIKV" "$PD"; do docker logs --tail 100 "$c" >&2 || true; done
exit 1
