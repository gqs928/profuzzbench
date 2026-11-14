#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import socket


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4433)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", args.port))
        closed, reason = True, "UDP port rebound successfully after target cleanup"
    except OSError as exc:
        closed, reason = False, str(exc)
    finally:
        sock.close()
    report = {"port": args.port, "transport": "udp", "listener_closed": closed, "check": reason}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not closed:
        raise SystemExit(f"LSQUIC http_server still owns UDP/{args.port}: {reason}")
    print(f"PASS: UDP/{args.port} listener closed")


if __name__ == "__main__":
    main()
