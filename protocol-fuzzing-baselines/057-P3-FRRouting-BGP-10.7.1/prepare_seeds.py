#!/usr/bin/env python3
"""Generate BGP-4 message sequences for the FRR loopback peer profile."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
MARKER = bytes([0xFF]) * 16
LOCAL_AS = 65000
REMOTE_AS = 65001


def message(kind: int, body: bytes = b"") -> bytes:
    length = 19 + len(body)
    if length > 65535:
        raise ValueError("BGP message exceeds extended-message limit")
    return MARKER + struct.pack(">HB", length, kind) + body


def open_message(version: int = 4, asn: int = REMOTE_AS,
                 hold_time: int = 90, router_id: str = "192.0.2.2") -> bytes:
    import ipaddress
    body = struct.pack(">BHH", version, asn, hold_time)
    body += ipaddress.IPv4Address(router_id).packed + b"\x00"
    return message(1, body)


def keepalive() -> bytes:
    return message(4)


def route_refresh(afi: int = 1, safi: int = 1) -> bytes:
    return message(5, struct.pack(">HBB", afi, 0, safi))


def update() -> bytes:
    origin = bytes((0x40, 1, 1, 0))
    as_path = bytes((0x40, 2, 4, 2, 1)) + struct.pack(">H", REMOTE_AS)
    next_hop = bytes((0x40, 3, 4, 198, 51, 100, 1))
    attrs = origin + as_path + next_hop
    nlri = bytes((24, 203, 0, 113))
    body = struct.pack(">H", 0) + struct.pack(">H", len(attrs)) + attrs + nlri
    return message(2, body)


def build_seeds() -> dict[str, tuple[str, bytes]]:
    opened = open_message()
    ka = keepalive()
    upd = update()
    rr = route_refresh()
    invalid_version = open_message(version=3)
    bad_length = MARKER + struct.pack(">HB", 18, 4)
    return {
        "open.bin": ("BGP OPEN", opened),
        "open-keepalive.bin": ("OPEN followed by KEEPALIVE", opened + ka),
        "open-keepalive-update.bin": ("OPEN, KEEPALIVE, IPv4 UPDATE, KEEPALIVE", opened + ka + upd + ka),
        "open-route-refresh.bin": ("OPEN followed by ROUTE-REFRESH", opened + rr),
        "invalid-open-version.bin": ("OPEN with unsupported version", invalid_version),
        "invalid-short-length.bin": ("BGP header declares length below 19", bad_length),
    }


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, (description, data) in build_seeds().items():
        (SEEDS / name).write_bytes(data)
        manifest.append({"file": name, "description": description,
                         "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
    (ROOT / "seeds-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} BGP sequences to {SEEDS}")


if __name__ == "__main__":
    main()
