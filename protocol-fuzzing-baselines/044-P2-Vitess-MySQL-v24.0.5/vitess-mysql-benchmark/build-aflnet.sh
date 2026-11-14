#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
WORK="$ROOT/build/aflnet-src"
BACKEND_PORT=${MYSQL_BACKEND_PORT:-3306}
mkdir -p "$ROOT/build"
rm -rf "$WORK"
mkdir -p "$WORK"
tar -xzf "$ROOT/source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" -C "$WORK"
sed -i 's/\r$//' "$WORK/Makefile" "$WORK/aflnet.h" "$WORK/afl-fuzz.c" "$WORK/afl-replay.c" "$WORK/aflnet-replay.c"
git -C "$WORK" init -q
for patch in aflnet-mysql.patch aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch aflnet-graph-close.patch; do
  git -C "$WORK" apply --check "$ROOT/$patch"
  git -C "$WORK" apply "$ROOT/$patch"
done
cp "$ROOT/mysql_aflnet.c" "$ROOT/graphviz_stub.c" "$ROOT/graphviz_stub.h" "$WORK/"
python3 "$ROOT/headless-aflnet.py" "$WORK"
AFL_NO_X86=1 make -C "$WORK" clean
AFL_NO_X86=1 make -C "$WORK" -j2 afl-fuzz
AFL_NO_X86=1 make -C "$WORK" mysql_aflnet.o
cc -O2 -Wall -Wextra -Werror -I"$WORK" "$ROOT/parser-test.c" "$WORK/mysql_aflnet.o" -o "$ROOT/build/mysql-parser-test"
"$ROOT/build/mysql-parser-test"
cp "$WORK/afl-fuzz" "$ROOT/build/afl-fuzz"
sha256sum "$ROOT/build/afl-fuzz" | tee "$ROOT/build/afl-fuzz.sha256"
cc -O2 -Wall -Wextra -Werror -DMYSQL_PORT="$BACKEND_PORT" "$ROOT/mysql-ready-check.c" -o "$ROOT/build/mysql-ready-check"
chmod 0755 "$ROOT/build/afl-fuzz" "$ROOT/build/mysql-ready-check" "$ROOT/fuzz.sh" "$ROOT/start-server.sh" "$ROOT/stop-server-and-remove-image.sh" "$ROOT/server-recover.sh"
