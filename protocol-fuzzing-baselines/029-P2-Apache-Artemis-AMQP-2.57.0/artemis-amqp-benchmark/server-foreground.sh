#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/artemis-home
export ARTEMIS_HOME=/opt/artemis
export JAVA_ARGS="-Xms128M -Xmx768M -XX:+UseSerialGC"
mkdir -p "$HOME"
cd /opt/artemis-instance
exec ./bin/artemis run
