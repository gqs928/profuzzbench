#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
OUTDIR=${1:-/results/dicom-smoke-post-20261112}
docker compose --env-file "$ROOT/images.env" -f "$ROOT/compose.yaml" run --rm --no-deps \
  -v "$ROOT:/src:ro" -e "OUTDIR=$OUTDIR" --entrypoint /bin/bash fuzz -lc '
set -euo pipefail
export DICOM_PORT=11112
export DICOM_LOG_FILE="$OUTDIR/storescp.log"
export DICOM_RECEIVE_DIR=/tmp/dcm4che-post-smoke-receive
mkdir -p "$OUTDIR"
/bin/bash /opt/benchmark/start-storescp.sh
trap "/bin/bash /opt/benchmark/stop-storescp.sh" EXIT
status=0
python3 /opt/benchmark/protocol_smoke.py --passes 3 \
  --output "$OUTDIR/protocol-smoke.json" || status=$?
/bin/bash /opt/benchmark/stop-storescp.sh
trap - EXIT
if [[ "$status" -ne 0 ]]; then exit "$status"; fi
python3 /src/verify_listener_closed.py --port "$DICOM_PORT" \
  --output "$OUTDIR/listener-closed.json"
chmod -R a+rX "$OUTDIR" 2>/dev/null || true
'
