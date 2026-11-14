#!/usr/bin/env python3
"""Apply the pinned AFLNet iSCSI request/response adapter extension."""
from __future__ import annotations

from pathlib import Path
import shutil
import sys


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one patch anchor in {path}, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: patch_aflnet.py AFLNET_SOURCE ADAPTER_SOURCE", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    adapter = Path(sys.argv[2])
    if not (root / "afl-fuzz.c").is_file():
        raise SystemExit(f"not an AFLNet source root: {root}")

    makefile = root / "Makefile"
    for target in ("afl-fuzz", "afl-replay", "aflnet-replay"):
        old = f"{target}: {target}.c $(COMM_HDR) aflnet.o aflnet.h | test_x86\n\t$(CC) $(CFLAGS) $@.c aflnet.o -o $@ $(LDFLAGS)"
        new = f"{target}: {target}.c $(COMM_HDR) aflnet.o iscsi_aflnet.o aflnet.h | test_x86\n\t$(CC) $(CFLAGS) $@.c aflnet.o iscsi_aflnet.o -o $@ $(LDFLAGS)"
        replace_once(makefile, old, new)
    replace_once(
        makefile,
        "afl-showmap: afl-showmap.c $(COMM_HDR) | test_x86",
        "iscsi_aflnet.o: iscsi_aflnet.c $(COMM_HDR) aflnet.h\n\t$(CC) $(CFLAGS) -c $< -o $@\n\nafl-showmap: afl-showmap.c $(COMM_HDR) | test_x86",
    )

    header = root / "aflnet.h"
    replace_once(
        header,
        "unsigned int* extract_response_codes_http(unsigned char* buf, unsigned int buf_size, unsigned int* state_count_ref);",
        "unsigned int* extract_response_codes_http(unsigned char* buf, unsigned int buf_size, unsigned int* state_count_ref);\nunsigned int* extract_response_codes_iscsi(unsigned char* buf, unsigned int buf_size, unsigned int* state_count_ref);",
    )
    replace_once(
        header,
        "region_t* extract_requests_http(unsigned char* buf, unsigned int buf_size, unsigned int* region_count_ref);",
        "region_t* extract_requests_http(unsigned char* buf, unsigned int buf_size, unsigned int* region_count_ref);\nregion_t* extract_requests_iscsi(unsigned char* buf, unsigned int buf_size, unsigned int* region_count_ref);",
    )

    fuzz = root / "afl-fuzz.c"
    replace_once(
        fuzz,
        '        } else if (!strcmp(optarg, "HTTP")) {\n          extract_requests = &extract_requests_http;\n          extract_response_codes = &extract_response_codes_http;\n        } else {',
        '        } else if (!strcmp(optarg, "HTTP")) {\n          extract_requests = &extract_requests_http;\n          extract_response_codes = &extract_response_codes_http;\n        } else if (!strcmp(optarg, "ISCSI")) {\n          extract_requests = &extract_requests_iscsi;\n          extract_response_codes = &extract_response_codes_iscsi;\n        } else {',
    )
    replace_once(
        root / "afl-replay.c",
        '  else if (!strcmp(argv[2], "HTTP")) extract_response_codes = &extract_response_codes_http;',
        '  else if (!strcmp(argv[2], "HTTP")) extract_response_codes = &extract_response_codes_http;\n  else if (!strcmp(argv[2], "ISCSI")) extract_response_codes = &extract_response_codes_iscsi;',
    )
    replace_once(
        root / "aflnet-replay.c",
        '  else if (!strcmp(argv[2], "HTTP")) extract_response_codes = &extract_response_codes_http;',
        '  else if (!strcmp(argv[2], "HTTP")) extract_response_codes = &extract_response_codes_http;\n  else if (!strcmp(argv[2], "ISCSI")) extract_response_codes = &extract_response_codes_iscsi;',
    )

    shutil.copy2(adapter, root / "iscsi_aflnet.c")
    print("Applied ISCSI parser declarations, CLI selection, replay selection and build rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
