#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
IMAGE='cockroachdb/cockroach:v26.2.11@sha256:811e5001de2f003ca4539b03853d98e1fd79f70bf929393b17a645673f8d5f47'
docker rm -f cockroachdb-pg-2611 >/dev/null 2>&1 || true
docker run -d --network host --restart unless-stopped --name cockroachdb-pg-2611 "$IMAGE" \
  start-single-node --insecure --listen-addr=localhost:26257 --http-addr=localhost:8080 \
  --store=/cockroach/cockroach-data >/dev/null
for _ in $(seq 1 120); do
  if "$ROOT/build/pgwire-ready-check" --once; then
    docker exec cockroachdb-pg-2611 /cockroach/cockroach version | tee "$ROOT/build/target-version-runtime.txt"
    echo 'CockroachDB is responding to PostgreSQL protocol StartupMessage.'
    exit 0
  fi
  sleep .25
done
docker logs --tail 100 cockroachdb-pg-2611 >&2 || true
exit 1
