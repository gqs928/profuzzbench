#!/usr/bin/env python3
"""Create small valid h2c request transcripts for Apache mod_http2."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


def frame(frame_type: int, flags: int, stream_id: int, payload: bytes = b"") -> bytes:
    if len(payload) > 0xFFFFFF:
        raise ValueError("HTTP/2 frame payload is too large")
    header = len(payload).to_bytes(3, "big") + bytes((frame_type, flags))
    header += (stream_id & 0x7FFFFFFF).to_bytes(4, "big")
    return header + payload


def string(value: bytes) -> bytes:
    if len(value) >= 127:
        raise ValueError("seed strings must be short")
    return bytes((len(value),)) + value


def request_headers(path: bytes, authority: bytes = b"localhost") -> bytes:
    # HPACK static indexes: :method GET=2, :scheme http=6, :path /=4,
    # and :authority=1. Other paths are literals without indexing.
    block = b"\x82\x86"
    block += b"\x84" if path == b"/" else b"\x04" + string(path)
    block += b"\x01" + string(authority)
    return frame(1, 0x5, 1, block)  # HEADERS, END_STREAM | END_HEADERS


def main() -> None:
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")
    out.mkdir(parents=True, exist_ok=True)
    settings = frame(4, 0, 0)
    seeds = {
        "h2c-get-root.raw": PREFACE + settings + request_headers(b"/"),
        "h2c-get-path.raw": PREFACE + settings + request_headers(b"/not-found"),
        "h2c-two-streams.raw": PREFACE + settings + request_headers(b"/") +
        frame(1, 0x5, 3, b"\x82\x86\x84\x01\x09localhost"),
    }
    rows = []
    for name, payload in seeds.items():
        path = out / name
        path.write_bytes(payload)
        rows.append({"file": name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    (out.parent / "seeds-manifest.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"created {len(rows)} HTTP/2 seeds in {out}")


if __name__ == "__main__":
    main()
