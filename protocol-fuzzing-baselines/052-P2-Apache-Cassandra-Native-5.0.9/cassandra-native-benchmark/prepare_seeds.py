#!/usr/bin/env python3
"""Build deterministic Cassandra Native Protocol v4 streams."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
VERSION = 0x04


def cql_string(value: str) -> bytes:
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def frame(opcode: int, body: bytes = b"", stream: int = 0) -> bytes:
    return struct.pack(">BBhBI", VERSION, 0, stream, opcode, len(body)) + body


def startup() -> bytes:
    body = struct.pack(">H", 1) + cql_string("CQL_VERSION") + cql_string("3.0.0")
    return frame(0x01, body, 1)


def query(text: str, stream: int) -> bytes:
    body = struct.pack(">I", len(text.encode("utf-8"))) + text.encode("utf-8")
    body += struct.pack(">HB", 0x0001, 0)  # CONSISTENCY ONE, no query flags
    return frame(0x07, body, stream)


def flow(queries: list[str]) -> bytes:
    frames = [frame(0x05, b"", 0), startup()]
    frames.extend(query(text, stream) for stream, text in enumerate(queries, start=2))
    return b"".join(frames)


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    for old in SEEDS.iterdir():
        if old.is_file():
            old.unlink()
    cases = {
        "options-startup.bin": flow([]),
        "system-release-version.bin": flow(["SELECT release_version FROM system.local"]),
        "system-cluster-name.bin": flow(["SELECT cluster_name FROM system.local"]),
        "create-keyspace.bin": flow([
            "CREATE KEYSPACE IF NOT EXISTS afl_fuzz WITH replication = "
            "{'class':'SimpleStrategy','replication_factor':'1'}"
        ]),
        "multi-query-read.bin": flow([
            "SELECT release_version FROM system.local",
            "SELECT cluster_name FROM system.local"
        ]),
        "invalid-opcode.bin": frame(0x7f, b"", 0),
        "truncated-frame.bin": bytes([0x04, 0, 0, 0, 0x07, 0, 0, 0, 8, 0x00, 0x01]),
    }
    manifest = []
    for name, data in sorted(cases.items()):
        path = SEEDS / name
        path.write_bytes(data)
        manifest.append({"name": name, "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
    (ROOT / "seeds-manifest.json").write_text(
        json.dumps({"protocol": "Cassandra Native Protocol v4", "seeds": manifest},
                   indent=2) + "\n", encoding="utf-8")
    print(f"created {len(manifest)} deterministic Cassandra v4 seeds")


if __name__ == "__main__":
    main()
