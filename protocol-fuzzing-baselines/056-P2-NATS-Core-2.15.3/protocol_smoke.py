#!/usr/bin/env python3
"""Repeat valid NATS Core INFO/CONNECT/SUB/PUB/HPUB/PING flows."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from nats_client import smoke_flow


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: protocol_smoke.py OUTDIR [repetitions]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else 3
    if not 1 <= repetitions <= 20:
        raise ValueError("repetitions must be between 1 and 20")
    if outdir.exists() and any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)
    host = os.environ.get("NATS_HOST", "127.0.0.1")
    port = int(os.environ.get("NATS_PORT", "4222"))
    flows = [smoke_flow(host, port, i) for i in range(1, repetitions + 1)]
    events = sum(int(flow["event_count"]) for flow in flows)
    result = {
        "target": "NATS Server 2.15.3",
        "protocol": "NATS Core client protocol v1 over plaintext TCP",
        "endpoint": f"{host}:{port}",
        "scope": "Core NATS only; no TLS, WebSocket, JetStream, cluster, leafnode or accounts",
        "repetitions": repetitions,
        "flows": len(flows),
        "all_flows_passed": all(bool(flow["success"]) for flow in flows),
        "server_events": events,
        "flows_detail": flows,
    }
    (outdir / "protocol-smoke.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["all_flows_passed"]:
        raise RuntimeError(json.dumps(result, sort_keys=True))
    print(f"PASS: {repetitions} NATS Core flows, {events} server events")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
