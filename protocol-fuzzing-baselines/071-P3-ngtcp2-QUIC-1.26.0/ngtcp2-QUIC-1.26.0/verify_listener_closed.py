#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib


def port_bound(port: int) -> bool:
    port_hex = f"{port:04X}"
    for table in (pathlib.Path("/proc/net/udp"), pathlib.Path("/proc/net/udp6")):
        try:
            lines = table.read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) > 1 and fields[1].rsplit(":", 1)[-1].upper() == port_hex:
                return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4433)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    closed = not port_bound(args.port)
    reason = "no IPv4 or IPv6 UDP socket remains in /proc/net/udp[6]" if closed else "UDP socket remains in /proc/net/udp[6]"
    report = {"port": args.port, "transport": "udp", "listener_closed": closed, "check": reason}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not closed:
        raise SystemExit(f"ngtcp2 osslserver still owns UDP/{args.port}: {reason}")
    print(f"PASS: UDP/{args.port} listener closed")


if __name__ == "__main__":
    main()
