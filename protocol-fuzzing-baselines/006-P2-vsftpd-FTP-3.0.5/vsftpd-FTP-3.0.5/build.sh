#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${IMAGE:-vsftpd-ftp-aflnet:3.0.5}"
MAKE_JOBS="${MAKE_JOBS:-1}"

mkdir -p "$ROOT/results/build"
chmod 0777 "$ROOT/results" "$ROOT/results/build"
docker build --pull --progress=plain --build-arg MAKE_JOBS="$MAKE_JOBS" -t "$IMAGE" "$ROOT" 2>&1 | tee "$ROOT/results/build/docker-build.log"
docker image inspect --format '{{.Id}}' "$IMAGE" > "$ROOT/results/build/image-id.txt"
docker image inspect --format '{{json .RepoDigests}}' "$IMAGE" > "$ROOT/results/build/image-digests.json"
docker run --rm --network none -v "$ROOT/results:/work/results" "$IMAGE" /work/validate.sh
printf 'built %s\n' "$IMAGE"
