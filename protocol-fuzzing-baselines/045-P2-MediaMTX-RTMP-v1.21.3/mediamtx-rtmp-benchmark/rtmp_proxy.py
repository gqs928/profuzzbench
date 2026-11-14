#!/usr/bin/env python3
"""Local RTMP handshake bridge: generates the dynamic C2 echo then relays bytes."""
from __future__ import annotations
import argparse
import json
import select
import socket
import threading
import time
from pathlib import Path

C1_SIZE = 1537
C2_SIZE = 1536
S0S1S2_SIZE = 3073


class Counters:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.values = {
            "accepted": 0,
            "handshake_ok": 0,
            "handshake_rejected_or_incomplete": 0,
            "c0c1_bytes_received": 0,
            "c2_bytes_received": 0,
            "bytes_to_target": 0,
            "bytes_to_fuzzer": 0,
        }

    def add(self, key: str, amount: int = 1) -> None:
        with self.lock:
            self.values[key] += amount

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock:
            path.write_text(json.dumps(self.values, indent=2) + "\n")


def recv_exact(sock: socket.socket, size: int, timeout: float) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < size and time.monotonic() < deadline:
        sock.settimeout(max(0.01, deadline - time.monotonic()))
        try:
            chunk = sock.recv(size - len(data))
        except socket.timeout:
            break
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def relay(client: socket.socket, target: socket.socket, counters: Counters) -> None:
    endpoints = [client, target]
    while True:
        readable, _, _ = select.select(endpoints, [], [], 0.25)
        if not readable:
            continue
        for source in readable:
            destination = target if source is client else client
            try:
                data = source.recv(65536)
            except OSError:
                return
            if not data:
                return
            try:
                destination.sendall(data)
            except OSError:
                return
            counters.add("bytes_to_target" if destination is target else "bytes_to_fuzzer", len(data))


def serve(client: socket.socket, address, target_host: str, target_port: int,
          counters: Counters, output: Path) -> None:
    upstream = None
    try:
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        upstream = socket.create_connection((target_host, target_port), timeout=2)
        upstream.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # AFLNet polls for unsolicited server data before it sends the first
        # request. Its default poll interval is 1s, so a shorter timeout here
        # closes every accepted connection before C0/C1 arrives.
        c0c1 = recv_exact(client, C1_SIZE, 3.0)
        counters.add("c0c1_bytes_received", len(c0c1))
        if len(c0c1) != C1_SIZE:
            counters.add("handshake_rejected_or_incomplete")
            return
        upstream.sendall(c0c1)
        counters.add("bytes_to_target", len(c0c1))
        server_handshake = recv_exact(upstream, S0S1S2_SIZE, 0.5)
        if len(server_handshake) != S0S1S2_SIZE or server_handshake[0] != 3:
            counters.add("handshake_rejected_or_incomplete")
            if server_handshake:
                client.sendall(server_handshake)
                counters.add("bytes_to_fuzzer", len(server_handshake))
            return
        client.sendall(server_handshake)
        counters.add("bytes_to_fuzzer", len(server_handshake))
        # AFLNet's receive path can wait up to its 500ms socket timeout after
        # consuming S0/S1/S2 before sending the corresponding C2.
        c2 = recv_exact(client, C2_SIZE, 3.0)
        counters.add("c2_bytes_received", len(c2))
        if len(c2) != C2_SIZE:
            counters.add("handshake_rejected_or_incomplete")
            return
        # A valid C2 is the exact S1 bytes received on this connection.
        upstream.sendall(server_handshake[1:1 + C2_SIZE])
        counters.add("bytes_to_target", C2_SIZE)
        counters.add("handshake_ok")
        relay(client, upstream, counters)
    except (OSError, TimeoutError):
        counters.add("handshake_rejected_or_incomplete")
    finally:
        for stream in (client, upstream):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        counters.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=1936)
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target-port", type=int, default=1935)
    parser.add_argument("--stats", type=Path, default=Path("/tmp/rtmp-proxy-stats.json"))
    args = parser.parse_args()
    counters = Counters()
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((args.listen_host, args.listen_port))
    listener.listen(256)
    listener.settimeout(0.25)
    try:
        while True:
            try:
                client, address = listener.accept()
            except socket.timeout:
                continue
            counters.add("accepted")
            threading.Thread(
                target=serve,
                args=(client, address, args.target_host, args.target_port, counters, args.stats),
                daemon=True,
            ).start()
    finally:
        listener.close()
        counters.save(args.stats)


if __name__ == "__main__":
    main()
