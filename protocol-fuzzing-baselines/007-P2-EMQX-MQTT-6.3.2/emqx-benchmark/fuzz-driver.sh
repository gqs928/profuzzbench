#!/usr/bin/env bash
set -euo pipefail

REL=/tmp/emqx-release
mkdir -p "${REL}"
tar -xzf /opt/emqx-release/emqx-6.3.2.tar.gz -C "${REL}"
exec "${REL}/bin/emqx" foreground --config /work/emqx.conf
