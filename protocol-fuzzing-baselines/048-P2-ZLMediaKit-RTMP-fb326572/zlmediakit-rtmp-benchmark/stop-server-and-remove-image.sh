#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONTAINER=zlmediakit-rtmp-30m
IMAGE=zlmediakit-rtmp-aflnet:fb326572
IMAGE_ID_FILE="$ROOT/results/build/image-id.txt"
OUT="$ROOT/results/cleanup.txt"

test -s "$IMAGE_ID_FILE" || { echo 'Missing image identity evidence.' >&2; exit 2; }
test -s "$ROOT/results/rtmp-30m/ACCEPTANCE.txt" || { echo 'Formal campaign has not completed.' >&2; exit 2; }
bash "$ROOT/validate.sh" "$ROOT/results/rtmp-30m"
IMAGE_ID="$(cat "$IMAGE_ID_FILE")"
mkdir -p "$(dirname "$OUT")"

if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
  CONTAINER_IMAGE="$(docker container inspect --format '{{.Image}}' "$CONTAINER")"
  [[ "$CONTAINER_IMAGE" == "$IMAGE_ID" ]] || {
    echo "Refusing to remove $CONTAINER: image id $CONTAINER_IMAGE differs from benchmark image $IMAGE_ID." >&2
    exit 2
  }
  STATE="$(docker container inspect --format '{{.State.Status}}' "$CONTAINER")"
  [[ "$STATE" != running ]] || { echo "Refusing cleanup while $CONTAINER is still running." >&2; exit 2; }
  docker rm "$CONTAINER" >/dev/null
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
