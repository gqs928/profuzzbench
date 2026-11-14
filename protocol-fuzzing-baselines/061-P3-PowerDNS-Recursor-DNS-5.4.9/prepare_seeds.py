#!/usr/bin/env python3
"""Generate deterministic, framed DNS/TCP request seeds."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


def qname(name: str) -> bytes:
    labels = name.rstrip(".").split(".")
    return b"".join(bytes([len(label)]) + label.encode("ascii") for label in labels) + b"\0"


def query(name: str, qtype: int, ident: int) -> bytes:
    message = struct.pack("!HHHHHH", ident, 0x0100, 1, 0, 0, 0)
    message += qname(name) + struct.pack("!HH", qtype, 1)
    return struct.pack("!H", len(message)) + message


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")
    out.mkdir(parents=True, exist_ok=True)
    definitions = [
        ("www.fuzz.test", 1), ("www.fuzz.test", 28), ("fuzz.test", 2),
        ("fuzz.test", 6), ("mail.fuzz.test", 15), ("text.fuzz.test", 16),
        ("missing.fuzz.test", 1), ("fuzz.test", 255),
    ]
    manifest = []
    for index, (name, qtype) in enumerate(definitions, 1):
        payload = query(name, qtype, 0x5100 + index)
        filename = f"dns-tcp-{index:02d}-type-{qtype}.bin"
        (out / filename).write_bytes(payload)
        manifest.append({"file": filename, "qname": name, "qtype": qtype,
                         "frame_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    (out.parent / "seeds-manifest.json").write_text(
        json.dumps({"transport": "DNS/TCP", "seed_count": len(manifest), "seeds": manifest},
                   indent=2) + "\n", encoding="utf-8")
    print(f"PASS: generated {len(manifest)} DNS/TCP seeds in {out}")


if __name__ == "__main__":
    main()
