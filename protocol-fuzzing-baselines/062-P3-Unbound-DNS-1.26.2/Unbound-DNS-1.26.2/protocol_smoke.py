#!/usr/bin/env python3
"""Exercise local static-zone A/AAAA/MX and NXDOMAIN over DNS/TCP."""
from __future__ import annotations

import argparse
import json
import socket
import struct
from pathlib import Path

from prepare_seeds import query
from unbound_probe import receive


def once(host: str, port: int, name: str, qtype: int, ident: int) -> dict[str, int | str]:
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(5)
        sock.sendall(query(name, qtype, ident))
        body = receive(sock)
    rid, flags, qd, an, ns, ar = struct.unpack_from("!HHHHHH", body)
    if rid != ident or not flags & 0x8000:
        raise RuntimeError(f"invalid response: {name} type={qtype} id={rid:#x} flags={flags:#x}")
    return {"qname": name, "qtype": qtype, "id": rid, "flags": flags,
            "aa": (flags >> 10) & 1, "rcode": flags & 15, "questions": qd,
            "answers": an, "authority": ns, "additional": ar}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5300)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for i in range(args.passes):
        rows.extend([
            once(args.host, args.port, "www.fuzz.test", 1, 0x7100 + i),
            once(args.host, args.port, "www.fuzz.test", 28, 0x7200 + i),
            once(args.host, args.port, "mail.fuzz.test", 15, 0x7300 + i),
            once(args.host, args.port, "missing.fuzz.test", 1, 0x7400 + i),
        ])
    for row in rows:
        missing = row["qname"] == "missing.fuzz.test"
        expected_rcode = 3 if missing else 0
        if row["rcode"] != expected_rcode or (not missing and row["answers"] < 1):
            raise SystemExit(f"unexpected response for {row['qname']} type={row['qtype']}: {row}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"target": "Unbound 1.26.2", "queries": rows}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"PASS: {len(rows)} Unbound DNS/TCP static-zone queries; {args.output}")


if __name__ == "__main__":
    main()
