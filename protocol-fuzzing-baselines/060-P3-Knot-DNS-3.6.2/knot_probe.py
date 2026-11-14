#!/usr/bin/env python3
"""Protocol-level Knot DNS/TCP readiness probe for the authoritative zone."""
from __future__ import annotations

import argparse
import socket
import struct
import time

from prepare_seeds import query


def receive(sock: socket.socket) -> bytes:
    prefix = sock.recv(2)
    while len(prefix) < 2:
        data = sock.recv(2 - len(prefix))
        if not data:
            raise EOFError("peer closed before DNS/TCP length prefix")
        prefix += data
    length = struct.unpack("!H", prefix)[0]
    if length < 12:
        raise ValueError(f"invalid DNS message length {length}")
    body = bytearray()
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise EOFError(f"peer closed after {len(body)} of {length} DNS bytes")
        body.extend(chunk)
    return bytes(body)


def probe(host: str, port: int, timeout: float) -> dict[str, int]:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(query("www.fuzz.test", 1, 0xBEEF))
        response = receive(sock)
    ident, flags, qd, an, ns, ar = struct.unpack_from("!HHHHHH", response)
    if ident != 0xBEEF or not flags & 0x8000 or not flags & 0x0400:
        raise RuntimeError(f"not an authoritative DNS response: id={ident:#x}, flags={flags:#06x}")
    if flags & 0x000F or an < 1:
        raise RuntimeError(f"health query failed: RCODE={flags & 0xF}, answers={an}")
    return {"id": ident, "flags": flags, "questions": qd, "answers": an,
            "authority": ns, "additional": ar}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5300)
    parser.add_argument("--deadline", type=float, default=20.0)
    args = parser.parse_args()
    end = time.monotonic() + args.deadline
    last: Exception | None = None
    while time.monotonic() < end:
        try:
            response = probe(args.host, args.port, 2.0)
            print(f"PASS: authoritative DNS/TCP readiness {response}")
            return
        except (OSError, EOFError, ValueError, RuntimeError) as exc:
            last = exc
            time.sleep(0.1)
    raise SystemExit(f"DNS/TCP readiness failed: {last}")


if __name__ == "__main__":
    main()
