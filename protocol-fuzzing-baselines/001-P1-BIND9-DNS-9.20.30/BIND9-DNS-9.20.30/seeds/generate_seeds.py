#!/usr/bin/env python3
"""Generate deterministic DNS wire seeds for BIND's UDP listener."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


def name_wire(name: str) -> bytes:
    if name == ".":
        return b"\0"
    return b"".join(bytes([len(label)]) + label.encode("ascii") for label in name.rstrip(".").split(".")) + b"\0"


def query(name: str, qtype: int, *, ident: int, flags: int = 0x0100, edns: bool = False) -> bytes:
    arcount = 1 if edns else 0
    header = struct.pack("!HHHHHH", ident, flags, 1, 0, 0, arcount)
    body = name_wire(name) + struct.pack("!HH", qtype, 1)
    if edns:
        body += b"\0" + struct.pack("!HHIH", 41, 1232, 0x00008000, 0)
    return header + body


def write_seeds(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    payloads = {
        "a-www.bin": query("www.example.test", 1, ident=0x1001),
        "aaaa-www.bin": query("www.example.test", 28, ident=0x1002),
        "txt-zone.bin": query("txt.example.test", 16, ident=0x1003),
        "mx-zone.bin": query("example.test", 15, ident=0x1004),
        "soa-zone.bin": query("example.test", 6, ident=0x1005),
        "ns-zone.bin": query("example.test", 2, ident=0x1006),
        "edns-do.bin": query("www.example.test", 1, ident=0x1007, edns=True),
        "recursion-desired.bin": query("outside.test", 1, ident=0x1008),
        "unknown-type.bin": query("www.example.test", 0xFFFE, ident=0x1009),
        "authority-query.bin": query("example.test", 255, ident=0x1010, flags=0x0000),
    }
    for filename, data in payloads.items():
        (destination / filename).write_bytes(data)
    (destination / "truncated-header.bin").write_bytes(b"\x10\x11\x01\x00\x00\x01")
    (destination / "truncated-qname.bin").write_bytes(
        struct.pack("!HHHHHH", 0x1012, 0x0100, 1, 0, 0, 0) + b"\x03www\x07example"
    )
    (destination / "compression-loop.bin").write_bytes(
        struct.pack("!HHHHHH", 0x1013, 0x0100, 1, 0, 0, 0)
        + b"\xc0\x0c" + struct.pack("!HH", 1, 1)
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} DESTINATION")
    write_seeds(Path(sys.argv[1]))
