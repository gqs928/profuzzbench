#!/usr/bin/env python3
"""Wait until the MQTT listener completes a real CONNECT/CONNACK exchange."""

from __future__ import annotations

import argparse
import os
import socket
import time

from mqtt_packets import connect


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError("broker closed the readiness connection")
        data.extend(chunk)
    return bytes(data)


def recv_packet(sock: socket.socket) -> bytes:
    header = bytearray(recv_exact(sock, 1))
    length = bytearray()
    for _ in range(4):
        digit = recv_exact(sock, 1)
        length.extend(digit)
        if digit[0] < 0x80:
            break
    else:
        raise ValueError("broker returned an invalid Remaining Length")

    remaining = 0
    multiplier = 1
    for digit in length:
        remaining += (digit & 0x7F) * multiplier
        multiplier *= 128
    return bytes(header + length) + recv_exact(sock, remaining)


def wait_for_mqtt(host: str = "127.0.0.1", port: int = 1883,
                  timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    client_id = f"emqx-readiness-{os.getpid()}"

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5) as sock:
                sock.settimeout(0.5)
                sock.sendall(connect(4, client_id))
                connack = recv_packet(sock)
                if (connack[0] >> 4) != 2 or len(connack) < 4 or connack[3] != 0:
                    raise ValueError(f"unexpected CONNACK: {connack.hex()}")
                sock.sendall(b"\xe0\x00")
                return
        except (OSError, EOFError, ValueError) as exc:
            last_error = exc
            time.sleep(0.25)

    raise TimeoutError(f"MQTT CONNECT/CONNACK readiness timed out: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    wait_for_mqtt(args.host, args.port, args.timeout)
    print(f"PASS: MQTT CONNECT/CONNACK readiness at {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
