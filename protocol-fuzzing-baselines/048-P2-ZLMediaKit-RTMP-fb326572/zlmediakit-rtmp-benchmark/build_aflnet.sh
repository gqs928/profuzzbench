#!/usr/bin/env bash
set -euo pipefail

AFLNET=/opt/aflnet
mkdir -p /work/build-evidence
test -s /tmp/aflnet-commit.txt
python3 /work/patch_aflnet_rtmp.py "$AFLNET"
cp /work/rtmp_aflnet.c "$AFLNET/rtmp_aflnet.c"
(
  cd "$AFLNET"
  AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
    make -j2 afl-fuzz afl-gcc afl-showmap afl-as
  AFL_PATH="$AFLNET" AFL_QUIET=1 ./afl-gcc -O2 -g -Wall -Wextra -Werror \
    /work/rtmp-fuzz-helper.c -o ./rtmp-fuzz-helper
  cc -std=c11 -Wall -Wextra -Werror -I"$AFLNET" \
    /work/rtmp_parser_test.c /work/rtmp_aflnet.c -o /work/rtmp-parser-test
)
/work/rtmp-parser-test
sha256sum "$AFLNET/afl-fuzz" "$AFLNET/rtmp-fuzz-helper" > /work/build-evidence/aflnet-binaries.sha256
sha256sum /work/rtmp_aflnet.c /work/patch_aflnet_rtmp.py /work/rtmp_proxy.py \
  /work/rtmp_protocol.py /work/rtmp_parser_test.c > /work/build-evidence/rtmp-adapter.sha256
printf '%s\n' "$(cat /tmp/aflnet-commit.txt)" > /work/build-evidence/aflnet-commit.txt
