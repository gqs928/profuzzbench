#!/usr/bin/env python3
"""Assert that the target TCP listener is closed after the post-run smoke."""
from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    deadline = time.monotonic() + 3
    last = "no connection attempted"
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((args.host, args.port), timeout=0.25):
                raise SystemExit(f"listener still accepts TCP on {args.host}:{args.port}")
        except OSError as exc:
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(0.1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"listener_closed": True, "host": args.host,
                                      "port": args.port, "probe": last}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"PASS: listener closed on {args.host}:{args.port}; {last}")


if __name__ == "__main__":
    main()
