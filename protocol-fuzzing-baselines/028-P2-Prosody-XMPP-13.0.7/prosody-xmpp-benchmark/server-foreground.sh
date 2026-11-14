#!/usr/bin/env bash
set -Eeuo pipefail
export HOME=/tmp/prosody-home
export PROSODY_SRCDIR=/opt/prosody
export PROSODY_CFGDIR=/opt/benchmark/configs
export PROSODY_PLUGINDIR=/opt/prosody/plugins
export PROSODY_DATADIR=/tmp/prosody-data
mkdir -p "$HOME" "$PROSODY_DATADIR"
cd "$PROSODY_SRCDIR"
exec ./prosody
