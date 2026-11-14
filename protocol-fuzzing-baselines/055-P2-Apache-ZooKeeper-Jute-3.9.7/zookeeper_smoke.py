#!/usr/bin/env python3
"""Validate the ZooKeeper connect and data-operation protocol lifecycle."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from zookeeper_client import smoke_flow


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: zookeeper_smoke.py OUTDIR [repetitions]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else 3
    if not 1 <= repetitions <= 20:
        raise ValueError("repetitions must be in [1, 20]")
    if outdir.exists() and any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)
    host = os.environ.get("ZK_HOST", "127.0.0.1")
    port = int(os.environ.get("ZK_PORT", "2181"))
    flows = [smoke_flow(host, port, iteration) for iteration in range(1, repetitions + 1)]
    replies = sum(len(flow["replies"]) for flow in flows)
    passed = all(bool(flow["success"]) for flow in flows)
    result = {
        "target": "Apache ZooKeeper 3.9.7",
        "protocol": "ZooKeeper client Jute binary protocol",
        "endpoint": f"{host}:{port}",
        "scope": "standalone unauthenticated plaintext client protocol; no quorum/ZAB ports",
        "repetitions": repetitions,
        "flows": len(flows),
        "successful_replies": replies,
        "all_flows_passed": passed,
        "flows_detail": flows,
    }
    (outdir / "protocol-smoke.json").write_text(json.dumps(result, indent=2) + "\n",
                                                 encoding="utf-8")
    if not passed:
        raise RuntimeError(json.dumps(result, sort_keys=True))
    print(f"PASS: {repetitions} ZooKeeper sessions, {replies} successful replies")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, ConnectionError,
            AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
