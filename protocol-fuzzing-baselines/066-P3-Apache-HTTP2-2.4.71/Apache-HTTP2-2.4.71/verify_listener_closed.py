#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=20240)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    rows = subprocess.run(["ss", "-ltnpH", f"sport = :{args.port}"], capture_output=True,
                          text=True, check=False).stdout.splitlines()
    pids = subprocess.run(["pgrep", "-x", "httpd"], capture_output=True, text=True,
                          check=False).stdout.splitlines()
    result = {"port": args.port, "tcp_listener_rows": rows,
              "httpd_process_pids": pids, "listener_closed": not rows and not pids}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["listener_closed"]:
        raise SystemExit(f"Apache target still active: {result}")
    print(f"PASS: TCP/{args.port} listener and httpd processes closed")


if __name__ == "__main__":
    main()
