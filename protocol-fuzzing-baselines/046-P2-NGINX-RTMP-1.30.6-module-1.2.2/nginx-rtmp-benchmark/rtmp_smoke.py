#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import socket
import time
from pathlib import Path
from rtmp_protocol import connect_command, rtmp_message


def recv_exact(sock: socket.socket, size: int, deadline: float) -> bytes:
    chunks = bytearray()
    while len(chunks) < size and time.monotonic() < deadline:
        try:
            part = sock.recv(size - len(chunks))
        except socket.timeout:
            continue
        if not part:
            break
        chunks.extend(part)
    return bytes(chunks)


def run(host: str, port: int, timeout: float) -> dict:
    c1 = b"\x00\x00\x00\x01\x00\x00\x00\x00" + bytes((i * 29 + 11) & 0xff for i in range(1528))
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(0.15)
        sock.sendall(b"\x03" + c1)
        handshake = recv_exact(sock, 3073, time.monotonic() + timeout)
        if len(handshake) != 3073 or handshake[0] != 3:
            raise RuntimeError(f"invalid RTMP server handshake ({len(handshake)} bytes)")
        # The local handshake bridge substitutes the exact S1 echo for this C2.
        sock.sendall(b"\x00" * 1536)
        sock.sendall(rtmp_message(connect_command(host, 1935)))
        response = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and b"_result" not in response:
            try:
                part = sock.recv(8192)
            except socket.timeout:
                continue
            if not part:
                break
            response.extend(part)
        if b"_result" not in response:
            sample = bytes(response[:96]).hex()
            raise RuntimeError(f"RTMP connect did not receive _result; received={len(response)} bytes sample={sample}")
        if b"_error" in response and response.find(b"_error") < response.find(b"_result"):
            raise RuntimeError("RTMP server returned _error before connect _result")
    return {
        "protocol": "RTMP v3",
        "endpoint": f"{host}:{port}",
        "handshake_bytes": len(handshake),
        "handshake_version": handshake[0],
        "connect_response_bytes": len(response),
        "has_connect_result": True,
        "connect_round_trip_seconds": round(timeout - max(0, deadline - time.monotonic()), 4),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1936)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.host, args.port, args.timeout)
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
