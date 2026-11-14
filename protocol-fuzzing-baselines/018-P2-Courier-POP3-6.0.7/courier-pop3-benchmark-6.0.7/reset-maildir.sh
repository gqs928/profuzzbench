#!/usr/bin/env bash
set -euo pipefail
MAILDIR=/home/fuzzuser/Maildir
rm -rf "${MAILDIR}"
mkdir -p "${MAILDIR}"
cp -a /opt/benchmark/maildir-seed/. "${MAILDIR}/"
chown -R fuzzuser:fuzzuser "${MAILDIR}"
chmod -R u+rwX,go-rwx "${MAILDIR}"
