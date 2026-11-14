#!/usr/bin/env python3
"""Validate seed framing and HPACK semantics with the Python h2 server parser."""
from __future__ import annotations

import json
import pathlib
import sys

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import RequestReceived
from replay_queue import split_regions

PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


def frame_types(data: bytes) -> list[int]:
    if not data.startswith(PREFACE):
        raise ValueError("HTTP/2 connection preface is missing")
    offset = len(PREFACE)
    types = []
    while offset < len(data):
        if len(data) - offset < 9:
            raise ValueError("truncated frame header")
        size = int.from_bytes(data[offset:offset + 3], "big")
        if offset + 9 + size > len(data):
            raise ValueError("truncated frame payload")
        types.append(data[offset + 3])
        offset += 9 + size
    return types


def main() -> None:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")
    expected = {"h2c-get-root.raw": ["/"], "h2c-get-path.raw": ["/not-found"],
                "h2c-two-streams.raw": ["/", "/"]}
    rows = []
    for name, paths in expected.items():
        data = (root / name).read_bytes()
        types = frame_types(data)
        connection = H2Connection(H2Configuration(client_side=False, header_encoding="utf-8"))
        events = connection.receive_data(data)
        requests = [event for event in events if isinstance(event, RequestReceived)]
        actual = [dict(event.headers).get(":path") for event in requests]
        regions, preface_valid, frames, malformed = split_regions(data)
        if (actual != paths or types.count(1) != len(paths) or types[0] != 4
                or not preface_valid or frames != len(types) or malformed or len(regions) != len(paths) + 1):
            raise SystemExit(f"invalid seed {name}: frame_types={types}, paths={actual}, regions={len(regions)}")
        rows.append({"file": name, "size": len(data), "frame_types": types,
                     "request_paths": actual, "fuzzer_regions": len(regions), "valid": True})
    initial_settings = b"\x00\x00\x00\x04\x00\x00\x00\x00\x00"
    regions, preface_valid, frames, malformed = split_regions(PREFACE + initial_settings + b"\x00\x00")
    if not preface_valid or frames != 1 or malformed != 2 or len(regions) != 2:
        raise SystemExit("truncated HTTP/2 frame tail was not preserved as a final region")
    empty_extension = b"\x00\x00\x00\x0b\x00\x00\x00\x00\x00"
    regions, preface_valid, frames, malformed = split_regions(PREFACE + initial_settings + empty_extension)
    if not preface_valid or frames != 2 or malformed or len(regions) != 2:
        raise SystemExit("empty HTTP/2 frame boundary was not recognized")
    print(json.dumps({"valid": True, "seeds": rows}, indent=2))


if __name__ == "__main__":
    main()
