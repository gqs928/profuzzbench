#!/usr/bin/env python3
"""Validate raw DTLS 1.2 records used by AFLNet's built-in DTLS12 parser."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

def records(data: bytes) -> list[dict[str, int]]:
    result = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 13:
            raise ValueError(f"truncated DTLS record header at offset {offset}")
        content_type = data[offset]
        version = int.from_bytes(data[offset + 1:offset + 3], "big")
        size = int.from_bytes(data[offset + 11:offset + 13], "big")
        if version != 0xFEFD:
            raise ValueError(f"record at {offset} is 0x{version:04x}, expected DTLS 1.2")
        if content_type not in (20, 21, 22, 23, 25):
            raise ValueError(f"record at {offset} has unexpected content type {content_type}")
        end = offset + 13 + size
        if end > len(data):
            raise ValueError(f"record at {offset} declares {size} bytes beyond input")
        result.append({"offset": offset, "content_type": content_type,
                       "version": version, "payload_bytes": size})
        offset = end
    return result

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prepare_seeds.py SEED_DIR", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    entries = []
    for path in sorted(root.glob("*.raw")):
        data = path.read_bytes()
        parsed = records(data)
        if not parsed or parsed[0]["content_type"] != 22:
            raise SystemExit(f"{path.name}: first record is not a handshake")
        if parsed[0]["payload_bytes"] < 12 or data[parsed[0]["offset"] + 13] != 1:
            raise SystemExit(f"{path.name}: first handshake record is not a complete ClientHello fragment")
        entries.append({"file": path.name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(), "records": parsed})
    if not entries:
        raise SystemExit("no .raw DTLS seeds found")
    report = {"protocol": "DTLS 1.2", "parser_input": "concatenated DTLS record bytes",
              "seed_count": len(entries), "seeds": entries}
    (root.parent / "seeds-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: validated {len(entries)} DTLS 1.2 client-handshake seed(s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
