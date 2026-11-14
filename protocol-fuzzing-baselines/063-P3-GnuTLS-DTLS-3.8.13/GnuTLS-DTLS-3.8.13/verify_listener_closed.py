#!/usr/bin/env python3
"""Verify that the post-run DTLS UDP listener process has been stopped."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=20220)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ss = subprocess.run(["ss", "-lunH"], capture_output=True, text=True, check=False)
    active = [line for line in ss.stdout.splitlines()
              if len(line.split()) >= 5 and line.split()[4].endswith(f":{args.port}")]
    proc = subprocess.run(["pgrep", "-x", "gnutls-serv"], capture_output=True, text=True, check=False)
    alive_pids = proc.stdout.split()
    result = {"port": args.port, "udp_listener_rows": active, "gnutls_serv_pids": alive_pids,
              "listener_closed": not active and not alive_pids}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["listener_closed"]:
        raise SystemExit(f"DTLS listener still active: {result}")
    print(f"PASS: no gnutls-serv process or UDP/{args.port} listener")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
