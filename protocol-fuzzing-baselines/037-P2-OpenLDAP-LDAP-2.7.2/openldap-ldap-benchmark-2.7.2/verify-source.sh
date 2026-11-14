#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GNUPGHOME="$ROOT/build/gnupg"; export GNUPGHOME
mkdir -p "$GNUPGHOME"; chmod 700 "$GNUPGHOME"
gpg --batch --no-autostart --import "$ROOT/source/gpg-pubkey.txt"
gpg --batch --no-autostart --export 7F67D5FD1CE1CBCE > "$ROOT/build/openldap-keyring.gpg"
gpgv --keyring "$ROOT/build/openldap-keyring.gpg" "$ROOT/source/openldap-2.7.2.tgz.asc" "$ROOT/source/openldap-2.7.2.tgz"
echo 'OpenLDAP official source signature verified'
