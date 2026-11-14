#!/usr/bin/env python3
"""Exercise direct h2c against Apache and check its HTTP/2 response."""
from __future__ import annotations

import argparse
import json
import pathlib
import socket
import time

from h2.config import H2Configuration
from h2.connection import H2Connection
from h2.events import DataReceived, ResponseReceived, StreamEnded


def request(host: str, port: int, timeout: float) -> dict[str, object]:
    config = H2Configuration(client_side=True, header_encoding="utf-8")
    conn = H2Connection(config=config)
    stream_id = conn.get_next_available_stream_id()
    response_headers: dict[str, str] = {}
    body = bytearray()
    ended = False

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        conn.initiate_connection()
        sock.sendall(conn.data_to_send())
        conn.send_headers(stream_id, [
            (":method", "GET"), (":scheme", "http"),
            (":authority", "localhost"), (":path", "/"),
        ], end_stream=True)
        sock.sendall(conn.data_to_send())
        deadline = time.monotonic() + timeout
        while not ended and time.monotonic() < deadline:
            data = sock.recv(65536)
            if not data:
                break
            for event in conn.receive_data(data):
                if isinstance(event, ResponseReceived):
                    response_headers = dict(event.headers)
                elif isinstance(event, DataReceived):
                    body.extend(event.data)
                    conn.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
                elif isinstance(event, StreamEnded) and event.stream_id == stream_id:
                    ended = True
            pending = conn.data_to_send()
            if pending:
                sock.sendall(pending)

    status = response_headers.get(":status")
    marker = b"fuzzbench-http2-ready"
    if not ended or status != "200" or marker not in body:
        raise RuntimeError(f"bad HTTP/2 response: ended={ended}, status={status}, body={bytes(body)!r}")
    return {"status": status, "stream_ended": ended, "body_bytes": len(body), "marker_seen": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=20240)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    checks = [request(args.host, args.port, args.timeout) for _ in range(args.passes)]
    result = {"target": "Apache HTTP Server 2.4.71 mod_http2", "protocol": "HTTP/2 h2c over TCP",
              "passes": args.passes, "all_responses_valid": True, "checks": checks}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {args.passes} h2c handshakes; HTTP/2 200 responses with body marker")


if __name__ == "__main__":
    main()
