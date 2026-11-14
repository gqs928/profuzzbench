#!/usr/bin/env python3
"""Build small, self-contained MongoDB OP_MSG request-sequence seeds."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"


def cstring(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if b"\0" in encoded:
        raise ValueError("BSON cstring cannot contain NUL")
    return encoded + b"\0"


def bson_value(value: object) -> tuple[int, bytes]:
    if isinstance(value, bool):
        return 0x08, bytes([1 if value else 0])
    if isinstance(value, str):
        encoded = value.encode("utf-8") + b"\0"
        return 0x02, struct.pack("<i", len(encoded)) + encoded
    if isinstance(value, int):
        if -(1 << 31) <= value < (1 << 31):
            return 0x10, struct.pack("<i", value)
        return 0x12, struct.pack("<q", value)
    if isinstance(value, dict):
        return 0x03, bson_document(value.items())
    if isinstance(value, list):
        return 0x04, bson_document((str(i), item) for i, item in enumerate(value))
    if value is None:
        return 0x0A, b""
    raise TypeError(f"unsupported BSON type: {type(value).__name__}")


def bson_document(items: object) -> bytes:
    elements = bytearray()
    for key, value in items:  # type: ignore[union-attr]
        kind, encoded = bson_value(value)
        elements.append(kind)
        elements.extend(cstring(key))
        elements.extend(encoded)
    length = 4 + len(elements) + 1
    return struct.pack("<i", length) + elements + b"\0"


def op_msg(request_id: int, command: dict[str, object]) -> bytes:
    document = bson_document(command.items())
    body = struct.pack("<iB", 0, 0) + document
    message_length = 16 + len(body)
    return struct.pack("<iiii", message_length, request_id, 0, 2013) + body


def hello(request_id: int = 1) -> bytes:
    return op_msg(request_id, {"hello": 1, "helloOk": True, "$db": "admin"})


def sequence(*commands: dict[str, object]) -> bytes:
    return b"".join(op_msg(i + 1, command) for i, command in enumerate(commands))


def parse_messages(raw: bytes) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    offset = 0
    while offset < len(raw):
        if len(raw) - offset < 16:
            raise ValueError("truncated MongoDB wire header")
        length, request_id, response_to, opcode = struct.unpack_from("<iiii", raw, offset)
        if length < 16 or length > len(raw) - offset:
            raise ValueError("invalid MongoDB message length")
        result.append({"length": length, "request_id": request_id,
                       "response_to": response_to, "opcode": opcode})
        offset += length
    return result


def main() -> int:
    SEEDS.mkdir(parents=True, exist_ok=True)
    samples: dict[str, bytes] = {
        "hello.bin": hello(),
        "hello-ping.bin": sequence(
            {"hello": 1, "helloOk": True, "$db": "admin"},
            {"ping": 1, "$db": "admin"},
        ),
        "hello-buildinfo.bin": sequence(
            {"hello": 1, "helloOk": True, "$db": "admin"},
            {"buildInfo": 1, "$db": "admin"},
        ),
        "hello-list-databases.bin": sequence(
            {"hello": 1, "helloOk": True, "$db": "admin"},
            {"listDatabases": 1, "nameOnly": True, "$db": "admin"},
        ),
        "hello-collection-roundtrip.bin": sequence(
            {"hello": 1, "helloOk": True, "$db": "admin"},
            {"create": "fuzz_seed", "$db": "fuzz"},
            {"insert": "fuzz_seed", "documents": [{"_id": 1, "value": "seed"}], "$db": "fuzz"},
            {"find": "fuzz_seed", "filter": {}, "$db": "fuzz"},
            {"delete": "fuzz_seed", "deletes": [{"q": {"_id": 1}, "limit": 1}], "$db": "fuzz"},
        ),
        "truncated-header.bin": struct.pack("<i", 24) + b"\x01\x00\x00\x00",
        "invalid-opcode.bin": struct.pack("<iiii", 16, 1, 0, 0x7FFFFFFF),
    }
    entries = []
    for name, data in samples.items():
        (SEEDS / name).write_bytes(data)
        entries.append({"name": name, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "frames": parse_messages(data) if len(data) >= 16 and name not in {
                            "truncated-header.bin", "invalid-opcode.bin"} else []})
    manifest = {
        "protocol": "MongoDB Wire Protocol OP_MSG",
        "framing": "16-byte little-endian message header; OP_MSG opcode 2013",
        "sequence": "hello handshake followed by command messages on one TCP connection",
        "backend": "FerretDB with PostgreSQL DocumentDB extension; in-memory/ephemeral benchmark data",
        "seeds": entries,
    }
    (ROOT / "seeds-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for entry in entries:
        print(f"{entry['name']} {entry['bytes']} {entry['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
