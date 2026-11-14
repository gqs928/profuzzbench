#!/usr/bin/env bash
set -euo pipefail
CERT_DIR=${OPENSSL_CERT_DIR:-/run/openssl-dtls-benchmark}
mkdir -p "$CERT_DIR"
if [[ ! -s "$CERT_DIR/server.key" || ! -s "$CERT_DIR/server.crt" ]]; then
  /opt/openssl/bin/openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.crt" \
    -days 2 -subj /CN=localhost \
    -addext 'subjectAltName=IP:127.0.0.1,DNS:localhost' >/dev/null 2>&1
fi
chmod 0600 "$CERT_DIR/server.key"
echo "local self-signed DTLS test certificate ready: $CERT_DIR"
