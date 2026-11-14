#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ARCHIVE="$ROOT/source/rabbitmq-server-generic-unix-4.4.0.tar.xz"
SIGNATURE="$ROOT/source/rabbitmq-server-generic-unix-4.4.0.tar.xz.asc"
KEY="$ROOT/source/rabbitmq-release-signing-key.asc"
EXPECTED=68c22d5dafa15c0911463aeca73c362d638cd6fb8e407ad39512959c6cc37f0f
printf '%s  %s\n' "$EXPECTED" "$ARCHIVE" | sha256sum -c -
GNUPGHOME=$(mktemp -d)
trap 'rm -rf "$GNUPGHOME"' EXIT
chmod 700 "$GNUPGHOME"
gpg --homedir "$GNUPGHOME" --batch --import "$KEY"
gpg --homedir "$GNUPGHOME" --batch --verify "$SIGNATURE" "$ARCHIVE"
rm -rf "$ROOT/build/rabbitmq_server-4.4.0"
mkdir -p "$ROOT/build"
tar -xJf "$ARCHIVE" -C "$ROOT/build"
test -x "$ROOT/build/rabbitmq_server-4.4.0/sbin/rabbitmq-server"
echo "RabbitMQ 4.4.0 verified and extracted for the image build."
