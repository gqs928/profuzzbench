#!/usr/bin/env python3
"""Generate immutable, frame-aligned ZooKeeper protocol seeds."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from zookeeper_client import (connect_request, create_request, delete_request,
                              jute_string, path_request, request,
                              set_data_request)

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"


def sequence(*messages: bytes) -> bytes:
    return b"".join((connect_request(), *messages))


def main() -> None:
    SEEDS.mkdir(exist_ok=True)
    cases = {
        "connect-ping.bin": sequence(request(-2, 11)),
        "connect-exists-root.bin": sequence(request(1, 3, path_request("/"))),
        "connect-read-root.bin": sequence(request(1, 4, path_request("/"))),
        "connect-children-root.bin": sequence(request(1, 8, path_request("/"))),
        "connect-create-delete.bin": sequence(
            request(1, 1, create_request("/fuzz", b"seed")),
            request(2, 2, delete_request("/fuzz"))),
        "connect-create-update-read-delete.bin": sequence(
            request(1, 1, create_request("/fuzz", b"seed")),
            request(2, 5, set_data_request("/fuzz", b"updated")),
            request(3, 4, path_request("/fuzz")),
            request(4, 2, delete_request("/fuzz"))),
        "connect-sync-root.bin": sequence(request(1, 9, jute_string("/"))),
        "connect-invalid-opcode.bin": sequence(request(1, 999)),
    }
    for name, data in cases.items():
        (SEEDS / name).write_bytes(data)
    manifest = {
        "target": "Apache ZooKeeper 3.9.7",
        "protocol": "ZooKeeper client Jute binary protocol over TCP/2181",
        "frame": "4-byte big-endian body length followed by Jute-encoded body",
        "connect": "ConnectRequest begins each isolated TCP stream; operation frames follow on the same connection",
        "cases": [{"name": name, "bytes": len(data),
                   "sha256": hashlib.sha256(data).hexdigest(),
                   "frames": 0}
                  for name, data in cases.items()],
    }
    # Frame count is intentionally recomputed from packet prefixes below.
    for row in manifest["cases"]:
        data = (SEEDS / row["name"]).read_bytes()
        offset = 0
        count = 0
        while offset < len(data):
            if len(data) - offset < 4:
                count += 1
                break
            size = int.from_bytes(data[offset:offset + 4], "big")
            count += 1
            if size > len(data) - offset - 4:
                break
            offset += 4 + size
        row["frames"] = count
    (ROOT / "seeds-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                               encoding="utf-8")
    print(f"prepared {len(cases)} ZooKeeper seeds")


if __name__ == "__main__":
    main()
