#!/usr/bin/env python3
"""Generate deterministic DHCPv4 BOOTREQUEST datagrams for Kea."""

import struct
import sys
from pathlib import Path

COOKIE = b"\x63\x82\x53\x63"


def option(code, value):
    return bytes((code, len(value))) + value


def packet(message_type, xid, mac, ciaddr=b"\0" * 4,
           giaddr=bytes((127, 0, 0, 1)), extra=(), end=True):
    header = struct.pack(
        "!BBBBIHH4s4s4s4s16s64s128s",
        1, 1, 6, 0, xid, 0, 0,
        ciaddr, b"\0" * 4, b"\0" * 4, giaddr,
        mac + b"\0" * 10, b"\0" * 64, b"\0" * 128,
    )
    options = bytearray(COOKIE)
    options += option(53, bytes((message_type,)))
    options += option(61, b"\x01" + mac)
    options += option(55, b"\x01\x03\x06\x33\x36")
    for code, value in extra:
        options += option(code, value)
    if end:
        options.append(255)
    return header + options


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_seeds.py OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    mac = bytes.fromhex("020000000001")
    discover = packet(1, 0x4B454131, mac)
    request = packet(
        3, 0x4B454132, mac,
        extra=[(50, bytes((127, 0, 0, 100))), (54, bytes((127, 0, 0, 1)))],
    )
    inform = packet(8, 0x4B454133, mac, ciaddr=bytes((127, 0, 0, 50)))
    release = packet(
        7, 0x4B454134, mac, ciaddr=bytes((127, 0, 0, 100)),
        extra=[(54, bytes((127, 0, 0, 1)))],
    )
    decline = packet(
        4, 0x4B454135, mac,
        extra=[(50, bytes((127, 0, 0, 100))), (54, bytes((127, 0, 0, 1)))],
    )
    truncated = discover[:-2]
    malformed_option = discover[:240] + b"\x35\x08\x01\xff"
    short_bootp = b"\x01\x01\x06\x00\x4b\x45\x41"
    samples = {
        "discover.bin": discover,
        "request.bin": request,
        "inform.bin": inform,
        "release.bin": release,
        "decline.bin": decline,
        "truncated.bin": truncated,
        "malformed-option.bin": malformed_option,
        "short-bootp.bin": short_bootp,
    }
    for name, data in samples.items():
        (out / name).write_bytes(data)
    print(f"generated {len(samples)} DHCPv4 seeds in {out}")


if __name__ == "__main__":
    main()
