#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")" && pwd)
TMP_DIR=$(mktemp -d /tmp/asterisk-sip-parser.XXXXXX)
trap 'rm -rf -- "${TMP_DIR}"' EXIT

tar -xzf "${PACKAGE_DIR}/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz" \
	-C "${TMP_DIR}"
sed -i 's/\r$//' "${TMP_DIR}/aflnet.c" "${TMP_DIR}/aflnet.h" \
	"${TMP_DIR}/afl-fuzz.c"
cp "${PACKAGE_DIR}/aflnet-sip.patch" "${PACKAGE_DIR}/sip_aflnet.c" \
	"${PACKAGE_DIR}/parser-test.c" "${TMP_DIR}/"
git -C "${TMP_DIR}" apply --check "${TMP_DIR}/aflnet-sip.patch"
git -C "${TMP_DIR}" apply "${TMP_DIR}/aflnet-sip.patch"
cc -O2 -w -I"${TMP_DIR}" -c "${TMP_DIR}/aflnet.c" -o "${TMP_DIR}/aflnet-parser.o"
cc -O2 -Wall -Wextra -Werror -I"${TMP_DIR}" \
	"${TMP_DIR}/parser-test.c" "${TMP_DIR}/aflnet-parser.o" \
	-o "${TMP_DIR}/parser-test"
"${TMP_DIR}/parser-test"
