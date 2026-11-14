#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORK="$ROOT/build/aflnet-src"
mkdir -p "$ROOT/build"
rm -rf "$WORK"; mkdir -p "$WORK"
tar -xzf "$ROOT/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" -C "$WORK"
sed -i 's/\r$//' "$WORK/Makefile" "$WORK/aflnet.h" "$WORK/afl-fuzz.c" "$WORK/afl-replay.c" "$WORK/aflnet-replay.c"
git -C "$WORK" init -q
git -C "$WORK" apply --unidiff-zero --check "$ROOT/aflnet-ldap.patch"
git -C "$WORK" apply --unidiff-zero "$ROOT/aflnet-ldap.patch"
git -C "$WORK" apply --check "$ROOT/aflnet-dumb-mode-network.patch"
git -C "$WORK" apply "$ROOT/aflnet-dumb-mode-network.patch"
git -C "$WORK" apply --check "$ROOT/aflnet-dumb-mode-state-feedback.patch"
git -C "$WORK" apply "$ROOT/aflnet-dumb-mode-state-feedback.patch"
cp "$ROOT/ldap_ber_aflnet.c" "$ROOT/graphviz_stub.c" "$ROOT/graphviz_stub.h" "$WORK/"
python3 "$ROOT/headless-aflnet.py" "$WORK"
AFL_NO_X86=1 make -C "$WORK" clean
AFL_NO_X86=1 make -C "$WORK" -j1 afl-fuzz
AFL_NO_X86=1 make -C "$WORK" ldap_ber_aflnet.o
cc -O2 -I"$WORK" "$ROOT/parser-test.c" "$WORK/ldap_ber_aflnet.o" -o "$ROOT/build/ldap-parser-test"
"$ROOT/build/ldap-parser-test"
cp "$WORK/afl-fuzz" "$ROOT/build/afl-fuzz"
cc -O2 -Wall -Wextra -static "$ROOT/ldap-ready-check.c" -o "$ROOT/build/ldap-ready-check"
(cd "$ROOT" && sha256sum build/afl-fuzz > build/afl-fuzz.sha256)
(cd "$ROOT" && sha256sum build/ldap-ready-check > build/ldap-ready-check.sha256)
