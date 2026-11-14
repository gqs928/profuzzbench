#!/usr/bin/env bash
set -Eeuo pipefail
export ACTIVEMQ_HOME=/opt/activemq ACTIVEMQ_BASE=/opt/activemq ACTIVEMQ_CONF=/opt/activemq/conf
export ACTIVEMQ_DATA=/tmp/activemq-data HOME=/tmp/activemq-home
export ACTIVEMQ_OPTS_MEMORY='-Xms128M -Xmx512M'
mkdir -p "$ACTIVEMQ_DATA" "$HOME" "$ACTIVEMQ_HOME/tmp"
exec "$ACTIVEMQ_HOME/bin/activemq" console
