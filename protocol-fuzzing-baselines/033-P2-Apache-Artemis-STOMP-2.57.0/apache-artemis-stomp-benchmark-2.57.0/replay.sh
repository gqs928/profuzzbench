#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONTAINER=${1:-artemis-stomp-2570}
OUTDIR=${2:-/results/stomp-30m}
docker cp "$ROOT/replay_queue_container.sh" "$CONTAINER:/tmp/replay_queue_container.sh"
docker exec "$CONTAINER" bash /tmp/replay_queue_container.sh "$OUTDIR"
