#!/usr/bin/env bash
set -euo pipefail
exec "$QUICHE_SERVER" \
  --listen "127.0.0.1:${QUICHE_PORT:-4433}" \
  --cert "$QUICHE_CERT" \
  --key "$QUICHE_KEY" \
  --root "$QUICHE_ROOT" \
  --no-retry \
  --disable-gso \
  --disable-pacing
