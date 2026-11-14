#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/openfire-home
export OPENFIRE_HOME=/opt/openfire
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export OPENFIRE_OPTS="-Xms128m -Xmx768m -XX:+UseSerialGC"
mkdir -p "$HOME"
cd "$OPENFIRE_HOME"
exec "$OPENFIRE_HOME/bin/openfire.sh" -demoboot
