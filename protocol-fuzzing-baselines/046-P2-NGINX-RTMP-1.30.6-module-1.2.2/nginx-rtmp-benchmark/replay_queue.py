#!/usr/bin/env python3
"""Replay AFLNet's length-prefixed message queue through the RTMP bridge."""
from __future__ import annotations
import argparse
import json
import socket
import struct
import time
from pathlib import Path

HANDSHAKE_REPLY = 3073
C2_SIZE = 1536


def read_exact(sock: socket.socket, size: int) -> bytes:
    out = bytearray()
    while len(out) < size:
        part = sock.recv(size - len(out))
        if not part:
            raise EOFError(f"connection ended after {len(out)}/{size} bytes")
        out.extend(part)
    return bytes(out)


def parse_messages(path: Path) -> list[bytes]:
    data = path.read_bytes()
    messages = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError("trailing bytes before next message length")
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if size == 0 or size > 16 * 1024 * 1024 or offset + size > len(data):
            raise ValueError(f"invalid message size {size}")
        messages.append(data[offset:offset + size])
        offset += size
    if not messages:
        raise ValueError("empty replay")
    return messages


def drain_available(sock: socket.socket, timeout: float = 0.08) -> tuple[int, bool, bool]:
    end = time.monotonic() + timeout
    received = 0
    closed = reset = False
    while time.monotonic() < end:
        sock.settimeout(max(0.001, end - time.monotonic()))
        try:
            data = sock.recv(65536)
        except socket.timeout:
            break
        except ConnectionResetError:
            reset = True
            break
        if not data:
            closed = True
            break
        received += len(data)
    return received, closed, reset


def replay(path: Path, host: str, port: int, timeout: float) -> dict[str, object]:
    result: dict[str, object] = {
        "file": path.name, "messages": 0, "connected": False,
        "handshake_ok": False, "bytes_sent": 0, "response_bytes": 0,
        "responses_after_handshake": 0, "responses_after_messages": 0,
        "connect_errors": 0, "send_errors": 0,
        "resets_after_response": 0, "peer_closes": 0, "timeouts": 0,
        "error": None,
    }
    try:
        messages = parse_messages(path)
        result["messages"] = len(messages)
        if len(messages[0]) != 1537:
            raise ValueError(f"first RTMP region is {len(messages[0])} bytes, expected C0/C1=1537")
        with socket.create_connection((host, port), timeout=timeout) as sock:
            result["connected"] = True
            sock.settimeout(timeout)
            sock.sendall(messages[0])
            result["bytes_sent"] = int(result["bytes_sent"]) + len(messages[0])
            handshake = read_exact(sock, HANDSHAKE_REPLY)
            if handshake[0] != 3:
                raise ValueError(f"unexpected RTMP handshake version {handshake[0]}")
            result["response_bytes"] = int(result["response_bytes"]) + len(handshake)
            result["handshake_ok"] = True
            if len(messages) > 1:
                c2 = handshake[1:1 + C2_SIZE]
                sock.sendall(c2)
                result["bytes_sent"] = int(result["bytes_sent"]) + len(c2)
                received, closed, reset = drain_available(sock)
                result["response_bytes"] = int(result["response_bytes"]) + received
                if received:
                    result["responses_after_handshake"] = int(result["responses_after_handshake"]) + 1
                if closed:
                    result["peer_closes"] = int(result["peer_closes"]) + 1
                if reset:
                    result["resets_after_response"] = int(result["resets_after_response"]) + int(received > 0)
                    result["send_errors"] = int(result["send_errors"]) + int(received == 0)
            for message in messages[2:]:
                try:
                    sock.sendall(message)
                    result["bytes_sent"] = int(result["bytes_sent"]) + len(message)
                except OSError:
                    result["send_errors"] = int(result["send_errors"]) + 1
                    break
                received, closed, reset = drain_available(sock)
                result["response_bytes"] = int(result["response_bytes"]) + received
                if received:
                    result["responses_after_messages"] = int(result["responses_after_messages"]) + 1
                if closed:
                    result["peer_closes"] = int(result["peer_closes"]) + 1
                    break
                if reset:
                    result["resets_after_response"] = int(result["resets_after_response"]) + int(received > 0)
                    result["send_errors"] = int(result["send_errors"]) + int(received == 0)
                    break
                if not received:
                    result["timeouts"] = int(result["timeouts"]) + 1
    except (OSError, EOFError, ValueError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if not result["connected"]:
            result["connect_errors"] = 1
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1936)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(p for p in args.queue.iterdir() if p.is_file() and not p.name.startswith("."))
    rows = [replay(path, args.host, args.port, args.timeout) for path in paths]
    totals: dict[str, int] = {key: 0 for key in (
        "messages", "bytes_sent", "response_bytes", "responses_after_handshake",
        "responses_after_messages", "connect_errors", "send_errors",
        "resets_after_response", "peer_closes", "timeouts")}
    for row in rows:
        for key in totals:
            totals[key] += int(row[key])
    report = {
        "endpoint": f"{args.host}:{args.port}", "queue_files": len(paths),
        "connected": sum(bool(row["connected"]) for row in rows),
        "handshake_ok": sum(bool(row["handshake_ok"]) for row in rows),
        "totals": totals, "items": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("queue_files", "connected", "handshake_ok", "totals")}, indent=2))


if __name__ == "__main__":
    main()
