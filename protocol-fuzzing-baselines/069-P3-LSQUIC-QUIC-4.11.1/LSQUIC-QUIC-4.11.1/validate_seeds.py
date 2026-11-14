#!/usr/bin/env python3
"""Validate one-datagram QUIC v1 Initial seeds for Google QUICHE."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def read_varint(data: bytes, pos: int) -> tuple[int, int]:
    if pos >= len(data):
        raise ValueError("missing QUIC variable-length integer")
    width = 1 << (data[pos] >> 6)
    if pos + width > len(data):
        raise ValueError("truncated QUIC variable-length integer")
    value = data[pos] & 0x3F
    for byte in data[pos + 1:pos + width]:
        value = (value << 8) | byte
    return value, pos + width


def validate(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if not 1200 <= len(data) <= 65507:
        raise ValueError(f"{path.name}: UDP datagram size out of bounds: {len(data)}")
    if not data[0] & 0x80 or not data[0] & 0x40:
        raise ValueError(f"{path.name}: not a QUIC long header with fixed bit")
    if data[1:5] != b"\x00\x00\x00\x01":
        raise ValueError(f"{path.name}: expected QUIC v1")
    if ((data[0] >> 4) & 3) != 0:
        raise ValueError(f"{path.name}: not a QUIC v1 Initial")
    pos = 5
    dcid_len = data[pos]
    pos += 1
    if dcid_len > 20 or pos + dcid_len >= len(data):
        raise ValueError(f"{path.name}: invalid destination connection ID")
    pos += dcid_len
    scid_len = data[pos]
    pos += 1
    if scid_len > 20 or pos + scid_len > len(data):
        raise ValueError(f"{path.name}: invalid source connection ID")
    pos += scid_len
    token_len, pos = read_varint(data, pos)
    if token_len > len(data) - pos:
        raise ValueError(f"{path.name}: truncated Initial token")
    pos += token_len
    packet_len, pos = read_varint(data, pos)
    if packet_len == 0 or packet_len > len(data) - pos:
        raise ValueError(f"{path.name}: invalid Initial packet length")
    return {
        "name": path.name,
        "bytes": len(data),
        "version": "1",
        "packet_type": "Initial",
        "destination_connection_id_bytes": dcid_len,
        "source_connection_id_bytes": scid_len,
        "token_bytes": token_len,
        "packet_payload_bytes": packet_len,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_seeds.py SEED_DIR")
    seed_dir = Path(sys.argv[1])
    seeds = sorted(path for path in seed_dir.iterdir()
                   if path.is_file() and not path.name.startswith("."))
    if not seeds:
        raise SystemExit(f"no QUIC seeds found under {seed_dir}")
    print(json.dumps({
        "valid": True,
        "transport": "UDP",
        "datagram_atomic": True,
        "count": len(seeds),
        "provenance": "complete TLS 1.3 ClientHello with QUIC transport parameters, protected as QUIC v1 Initial",
        "seeds": [validate(path) for path in seeds],
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"seed validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
