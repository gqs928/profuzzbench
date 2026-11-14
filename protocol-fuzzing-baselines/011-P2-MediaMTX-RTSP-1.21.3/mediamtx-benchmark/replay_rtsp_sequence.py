#!/usr/bin/env python3
"""Replay one AFLNet RTSP request sequence against a fresh MediaMTX service."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import time
from pathlib import Path


def messages_from_aflnet(path: Path) -> list[bytes]:
    data = path.read_bytes()
    messages: list[bytes] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError(f"truncated length prefix at byte {offset}")
        length = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        if length > len(data) - offset:
            raise ValueError(f"message at byte {offset} declares {length} bytes, only {len(data) - offset} remain")
        messages.append(data[offset:offset + length])
        offset += length
    if not messages:
        raise ValueError("empty AFLNet sequence")
    return messages


def receive_response(sock: socket.socket) -> tuple[str, int, int]:
    data = bytearray()
    while b"\r\n\r\n" not in data:
        try:
            chunk = sock.recv(65536)
        except socket.timeout as error:
            raise TimeoutError(f"timed out waiting for RTSP headers; received {len(data)} bytes: {bytes(data)!r}") from error
        if not chunk:
            raise ConnectionError("peer closed before RTSP headers")
        data.extend(chunk)
    boundary = data.index(b"\r\n\r\n") + 4
    header = bytes(data[:boundary]).decode("iso-8859-1", "replace")
    status_line = header.split("\r\n", 1)[0]
    match = re.search(r"\s([1-5][0-9]{2})(?:\s|$)", status_line)
    if not match:
        raise ValueError(f"unrecognized RTSP status line: {status_line!r}")
    content_length = 0
    for line in header.split("\r\n")[1:]:
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break
    while len(data) < boundary + content_length:
        try:
            chunk = sock.recv(65536)
        except socket.timeout as error:
            raise TimeoutError(f"timed out waiting for RTSP body; received {len(data) - boundary} of {content_length} bytes") from error
        if not chunk:
            raise ConnectionError("peer closed during RTSP response body")
        data.extend(chunk)
    return status_line, int(match.group(1)), len(data) - boundary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sequence", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8554)
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--delay-ms", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    messages = messages_from_aflnet(args.sequence)
    results: list[dict] = []
    connection_status = "open"
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        for index, message in enumerate(messages, start=1):
            method = message.split(None, 1)[0].decode("ascii", "replace") if message else ""
            started = time.monotonic()
            try:
                sock.sendall(message)
                status_line, status_code, body_bytes = receive_response(sock)
                results.append({"index": index, "method": method, "request_bytes": len(message),
                                "response": status_line, "status_code": status_code,
                                "response_body_bytes": body_bytes,
                                "elapsed_seconds": round(time.monotonic() - started, 3)})
            except (OSError, ValueError, ConnectionError) as error:
                connection_status = "no_response_or_connection_error"
                results.append({"index": index, "method": method, "request_bytes": len(message),
                                "error": f"{type(error).__name__}: {error}",
                                "elapsed_seconds": round(time.monotonic() - started, 3)})
                break
            if args.delay_ms:
                time.sleep(args.delay_ms / 1000)

    report = {"sequence": str(args.sequence), "sha256": hashlib.sha256(args.sequence.read_bytes()).hexdigest(),
              "destination": f"{args.host}:{args.port}", "connection_status": connection_status,
              "messages_in_sequence": len(messages), "replayed_messages": results,
              "classification": "replay evidence only; a timeout is not by itself a confirmed defect"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
