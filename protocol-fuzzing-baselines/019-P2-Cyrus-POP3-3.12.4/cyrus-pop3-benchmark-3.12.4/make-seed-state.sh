#!/usr/bin/env bash
set -euo pipefail

WORKDIR=/home/ubuntu/experiments
ARCHIVE="$WORKDIR/pop3-seed-state.tar.gz"
LOG="$WORKDIR/pop3-mailbox-bootstrap.log"
rm -f "$ARCHIVE" "$LOG"
mkdir -p /tmp/cyrus-benchmark-state/{config/socket,proc,lock,mail,sieve,saslauthd}
export CYRUS_PREFIX="$WORKDIR/cyrus-reference"
"$WORKDIR/start-imap-bootstrap.sh" >"$LOG" 2>&1 &
# This service is started only in the isolated Docker build layer. The builder
# reaps its process namespace when the RUN step completes; avoid global pkill.
if ! python3 "$WORKDIR/bootstrap_mailbox.py"; then
  echo 'Cyrus IMAP bootstrap service log:' >&2
  cat "$LOG" >&2 || true
  exit 1
fi
sleep 0.2
tar -czf "$ARCHIVE" -C /tmp \
  --exclude='cyrus-benchmark-state/proc/*' \
  --exclude='cyrus-benchmark-state/config/socket/*' \
  --exclude='cyrus-benchmark-state/saslauthd/*' \
  --exclude='cyrus-benchmark-state/lock/*' \
  cyrus-benchmark-state
test -s "$ARCHIVE"
tar -tzf "$ARCHIVE" | head -30
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
echo "Created POP3 mailbox snapshot: $ARCHIVE"
