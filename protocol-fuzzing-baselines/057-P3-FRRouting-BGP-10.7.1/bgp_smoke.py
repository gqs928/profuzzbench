#!/usr/bin/env python3
"""Negotiate one loopback BGP-4 peer and test a valid IPv4 UPDATE."""
from __future__ import annotations

import argparse
import json
import socket
import struct
import time
from pathlib import Path

from prepare_seeds import keepalive, open_message, update


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError(f"peer closed after {len(data)}/{size} bytes")
        data.extend(chunk)
    return bytes(data)


def receive_message(sock: socket.socket) -> tuple[int, bytes]:
    header = recv_exact(sock, 19)
    length = struct.unpack(">H", header[16:18])[0]
    if length < 19 or length > 65535:
        raise ValueError(f"invalid BGP message length: {length}")
    return header[18], recv_exact(sock, length - 19)


def run_once(host: str, port: int) -> dict[str, object]:
    messages: list[dict[str, int]] = []
    deadline = time.monotonic() + 8.0
    with socket.create_connection((host, port), timeout=3.0) as sock:
        sock.settimeout(3.0)
        # FRR sends its OPEN immediately after accepting TCP. Read it before
        # replying so the smoke follows the observed BGP FSM ordering instead
        # of racing the listener startup with the peer OPEN.
        saw_open = False
        saw_keepalive = False
        while time.monotonic() < deadline and not saw_open:
            kind, body = receive_message(sock)
            messages.append({"type": kind, "bytes": len(body)})
            if kind == 3:
                raise RuntimeError(f"BGP NOTIFICATION {body[:2].hex()}")
            if kind == 1:
                saw_open = True
        if not saw_open:
            raise TimeoutError("BGP OPEN response not received")
        sock.sendall(open_message())
        sock.sendall(keepalive())
        while time.monotonic() < deadline and not saw_keepalive:
            kind, body = receive_message(sock)
            messages.append({"type": kind, "bytes": len(body)})
            if kind == 3:
                raise RuntimeError(f"BGP NOTIFICATION {body[:2].hex()}")
            saw_keepalive = kind == 4
        if not saw_keepalive:
            raise TimeoutError("BGP KEEPALIVE response not received")
        sock.sendall(update())
        sock.sendall(keepalive())
        sock.settimeout(0.5)
        try:
            while True:
                kind, body = receive_message(sock)
                messages.append({"type": kind, "bytes": len(body)})
                if kind == 3:
                    raise RuntimeError(f"BGP NOTIFICATION {body[:2].hex()}")
        except socket.timeout:
            pass
        return {"established": True, "messages": messages,
                "update_bytes": len(update())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=179)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [run_once(args.host, args.port) for _ in range(args.passes)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"passes": records}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"PASS: {len(records)} BGP OPEN/KEEPALIVE/UPDATE flows; {args.output}")


if __name__ == "__main__":
    main()
