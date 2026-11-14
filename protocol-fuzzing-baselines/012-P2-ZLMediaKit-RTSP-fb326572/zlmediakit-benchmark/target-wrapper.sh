#!/usr/bin/env bash
set -euo pipefail
exec /opt/zlmediakit/MediaServer -c /work/config.ini -l 2 -t 2
