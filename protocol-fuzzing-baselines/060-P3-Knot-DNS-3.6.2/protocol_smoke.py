#!/usr/bin/env python3
"""Run positive and negative authoritative DNS/TCP queries."""
from __future__ import annotations

import argparse
import json
import socket
import struct
from pathlib import Path

from knot_probe import receive
from prepare_seeds import query


def once(host: str, port: int, name: str, qtype: int, ident: int) -> dict[str, int | str]:
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(5)
        sock.sendall(query(name, qtype, ident))
        body = receive(sock)
    rid, flags, qd, an, ns, ar = struct.unpack_from("!HHHHHH", body)
    if rid != ident or not flags & 0x8000 or not flags & 0x0400:
        raise RuntimeError(f"invalid authoritative response: {name} type={qtype} id={rid:#x} flags={flags:#x}")
    return {"qname": name, "qtype": qtype, "id": rid, "flags": flags,
            "rcode": flags & 15, "questions": qd, "answers": an,
            "authority": ns, "additional": ar}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5300)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for pass_index in range(args.passes):
        rows.extend([
            once(args.host, args.port, "www.fuzz.test", 1, 0x6100 + pass_index),
            once(args.host, args.port, "www.fuzz.test", 28, 0x6200 + pass_index),
            once(args.host, args.port, "missing.fuzz.test", 1, 0x6300 + pass_index),
        ])
    for row in rows:
        expected_rcode = 3 if row["qname"] == "missing.fuzz.test" else 0
        if row["rcode"] != expected_rcode:
            raise SystemExit(f"unexpected RCODE for {row['qname']} type={row['qtype']}: "
                             f"{row['rcode']} != {expected_rcode}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"queries": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(rows)} authoritative DNS/TCP queries; {args.output}")


if __name__ == "__main__":
    main()
