#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-/tmp/imap-parser-check.txt}
AFLNET=${AFLNET:-/home/ubuntu/aflnet}
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  /usr/bin/cc -O2 -Wall -Wextra -Werror -I"${AFLNET}" \
  /workspace/parser-test.c "${AFLNET}/imap_aflnet.o" -o /tmp/imap-parser-test
/tmp/imap-parser-test | tee "${OUT}"
python3 /workspace/prepare_seeds.py /tmp/imap-seeds-check \
  --manifest /tmp/imap-seeds-manifest-check.json
diff -r /workspace/seeds /tmp/imap-seeds-check
cmp /workspace/seeds-manifest.json /tmp/imap-seeds-manifest-check.json
echo "通过：解析器边界测试和固定语料哈希清单" | tee -a "${OUT}"
