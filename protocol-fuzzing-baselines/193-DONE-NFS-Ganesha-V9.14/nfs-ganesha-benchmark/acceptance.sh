#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
IMAGE=${IMAGE:-nfs-ganesha-fuzz}
FUZZ_SECONDS=${1:-1800}
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
RESULTS=${RESULTS_DIR:-"$ROOT/results/$RUN_ID"}
mkdir -p "$RESULTS"
NETWORK="nfs-ganesha-acceptance-$(date -u +%Y%m%d%H%M%S)-$$"
network_created=0
cleanup_network() {
	if ((network_created)); then
		docker network rm "$NETWORK" >/dev/null
	fi
}
trap cleanup_network EXIT INT TERM

"$ROOT/build.sh" "$IMAGE"
cp "$ROOT/build-logs/image-id.txt" "$RESULTS/image-id.txt"
cp "$ROOT/build-logs/image-digests.json" "$RESULTS/image-digests.json"
cp "$ROOT/build-logs/docker-build.log" "$RESULTS/docker-build.log"
if [[ -f "$ROOT/build-logs/docker-build-noasan-fullcompile.log" ]]; then
	cp "$ROOT/build-logs/docker-build-noasan-fullcompile.log" \
		"$RESULTS/docker-build-full-compile.log"
fi
docker network create --internal --driver bridge "$NETWORK" \
	> "$RESULTS/docker-network-id.txt"
network_created=1
docker run --rm --network "$NETWORK" \
	-v "$ROOT:/workspace:ro" \
	-v "$RESULTS:/results" \
	"$IMAGE" /workspace/acceptance-inner.sh "$FUZZ_SECONDS"
printf '完整验收证据：%s\n' "$RESULTS"
