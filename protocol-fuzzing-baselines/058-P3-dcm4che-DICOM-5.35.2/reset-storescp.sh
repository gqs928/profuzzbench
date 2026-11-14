#!/usr/bin/env bash
set -euo pipefail
/bin/bash /opt/benchmark/stop-storescp.sh
DICOM_RECEIVE_DIR=${DICOM_RECEIVE_DIR:-/tmp/dcm4che-receive}
rm -rf "$DICOM_RECEIVE_DIR"
mkdir -p "$DICOM_RECEIVE_DIR"
/bin/bash /opt/benchmark/start-storescp.sh
