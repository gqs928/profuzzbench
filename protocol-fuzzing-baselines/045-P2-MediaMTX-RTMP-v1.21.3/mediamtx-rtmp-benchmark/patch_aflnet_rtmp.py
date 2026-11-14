#!/usr/bin/env python3
"""Apply the profile's RTMP request/response adapter to the pinned AFLNet source."""
from pathlib import Path
import sys

root = Path(sys.argv[1])

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one patch site in {path.name}, found {count}")
    path.write_text(text.replace(old, new, 1))

replace_once(
    root / "aflnet.h",
    "extern unsigned int* (*extract_response_codes)",
    "unsigned int* extract_response_codes_rtmp(unsigned char* buf, unsigned int buf_size, unsigned int* state_count_ref);\n"
    "region_t* extract_requests_rtmp(unsigned char* buf, unsigned int buf_size, unsigned int* region_count_ref);\n"
    "extern unsigned int* (*extract_response_codes)",
)
replace_once(
    root / "afl-fuzz.c",
    '        if (!strcmp(optarg, "RTSP")) {',
    '        if (!strcmp(optarg, "RTMP")) {\n'
    '          extract_requests = &extract_requests_rtmp;\n'
    '          extract_response_codes = &extract_response_codes_rtmp;\n'
    '        } else if (!strcmp(optarg, "RTSP")) {',
)
for filename in ("afl-replay.c", "aflnet-replay.c"):
    replace_once(
        root / filename,
        '  if (!strcmp(argv[2], "RTSP")) extract_response_codes = &extract_response_codes_rtsp;',
        '  if (!strcmp(argv[2], "RTMP")) extract_response_codes = &extract_response_codes_rtmp;\n'
        '  else if (!strcmp(argv[2], "RTSP")) extract_response_codes = &extract_response_codes_rtsp;',
    )

makefile = root / "Makefile"
text = makefile.read_text()
for target in ("afl-fuzz", "afl-replay", "aflnet-replay"):
    old = f"{target}: {target}.c $(COMM_HDR) aflnet.o aflnet.h | test_x86"
    new = f"{target}: {target}.c $(COMM_HDR) aflnet.o rtmp_aflnet.o aflnet.h | test_x86"
    if text.count(old) != 1:
        raise SystemExit(f"expected one {target} Makefile target")
    text = text.replace(old, new, 1)
text = text.replace(
    "$(CC) $(CFLAGS) $@.c aflnet.o -o $@ $(LDFLAGS)",
    "$(CC) $(CFLAGS) $@.c aflnet.o rtmp_aflnet.o -o $@ $(LDFLAGS)",
)
if text.count("rtmp_aflnet.o") != 6:
    # Three targets and their matching link commands.
    raise SystemExit("unexpected RTMP adapter Makefile patch result")
marker = "afl-showmap: afl-showmap.c"
if text.count(marker) != 1:
    raise SystemExit("could not find Makefile insertion point")
text = text.replace(
    marker,
    "rtmp_aflnet.o: rtmp_aflnet.c $(COMM_HDR) aflnet.h | test_x86\n"
    "\t$(CC) $(CFLAGS) -c rtmp_aflnet.c -o rtmp_aflnet.o\n\n"
    + marker,
    1,
)
makefile.write_text(text)

print("Applied RTMP request segmentation and response-state adapter to pinned AFLNet.")
