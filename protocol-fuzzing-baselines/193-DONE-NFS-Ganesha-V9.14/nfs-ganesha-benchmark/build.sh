#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")" && pwd)
IMAGE=nfs-ganesha-fuzz
if (($#)); then IMAGE=$1; fi
MAKE_JOBS=$(printenv MAKE_JOBS || true)
if [[ -z "$MAKE_JOBS" ]]; then MAKE_JOBS=1; fi
mkdir -p "$ROOT/build-logs"

{
	printf 'image=%s\n' "$IMAGE"
	printf 'make_jobs=%s\n' "$MAKE_JOBS"
	docker build --pull --progress=plain \
		--build-arg MAKE_JOBS="$MAKE_JOBS" \
		-t "$IMAGE" "$ROOT"
	docker image inspect --format '{{.Id}}' "$IMAGE" \
		> "$ROOT/build-logs/image-id.txt"
	docker image inspect --format '{{json .RepoDigests}}' "$IMAGE" \
		> "$ROOT/build-logs/image-digests.json"
} 2>&1 | tee "$ROOT/build-logs/docker-build.log"
