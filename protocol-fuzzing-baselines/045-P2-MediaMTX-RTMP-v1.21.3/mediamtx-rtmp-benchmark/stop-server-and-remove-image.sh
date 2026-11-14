#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONTAINER=mediamtx-rtmp-30m
IMAGE=mediamtx-rtmp-aflnet:v1.21.3
OUT="$ROOT/results/cleanup.txt"
mkdir -p "$(dirname "$OUT")"
IMAGE_ID="$(cat "$ROOT/results/build/image-id.txt")"

if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
  CONTAINER_IMAGE="$(docker container inspect --format '{{.Image}}' "$CONTAINER")"
  [[ "$CONTAINER_IMAGE" == "$IMAGE_ID" ]] || {
    echo "Refusing to remove $CONTAINER: image id $CONTAINER_IMAGE differs from benchmark image $IMAGE_ID." >&2
    exit 2
  }
  docker rm -f "$CONTAINER" >/dev/null
  container_removed=yes
else
  container_removed=already-absent
fi

if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker image rm "$IMAGE" >/dev/null
  image_removed=yes
else
  image_removed=already-absent
fi

cat > "$OUT" <<EOF
container=$CONTAINER
container_removed=$container_removed
image=$IMAGE
image_id=$IMAGE_ID
image_removed=$image_removed
cleanup_recorded_at_utc=$(date -u +%FT%TZ)
EOF
printf 'Removed successful benchmark container/image: %s / %s\n' "$CONTAINER" "$IMAGE"
