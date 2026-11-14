#!/usr/bin/env python3
"""Verify that the post-run OpenSSL DTLS echo target has stopped."""
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
              if len(line.split()) >= 5 and line.split()[3].endswith(f":{args.port}")]
    alive = {}
    for name in ("dtls_echo_server", "openssl"):
        proc = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True, check=False)
        alive[name] = proc.stdout.split()
    result = {"port": args.port, "udp_listener_rows": active, "target_process_pids": alive,
              "listener_closed": not active and not any(alive.values())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["listener_closed"]:
        raise SystemExit(f"DTLS listener still active: {result}")
    print(f"PASS: no OpenSSL DTLS target process or UDP/{args.port} listener")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
