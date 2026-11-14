#!/usr/bin/env python3
"""Small dependency-free ZooKeeper Jute client for seeds, checks, and smoke."""
from __future__ import annotations

import json
import socket
import struct
import sys

MAX_PACKET = 16 * 1024 * 1024


def i32(value: int) -> bytes:
    return struct.pack(">i", value)


def i64(value: int) -> bytes:
    return struct.pack(">q", value)


def jute_string(value: str) -> bytes:
    data = value.encode("utf-8")
    return i32(len(data)) + data


def jute_buffer(value: bytes) -> bytes:
    return i32(len(value)) + value


def packet(body: bytes) -> bytes:
    if len(body) > MAX_PACKET:
        raise ValueError(f"packet too large: {len(body)}")
    return struct.pack(">I", len(body)) + body


def connect_request(timeout_ms: int = 10000) -> bytes:
    body = (i32(0) + i64(0) + i32(timeout_ms) + i64(0) +
            jute_buffer(bytes(16)) + b"\x00")
    return packet(body)


def request(xid: int, opcode: int, payload: bytes = b"") -> bytes:
    return packet(i32(xid) + i32(opcode) + payload)


def read_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = sock.recv(size - len(chunks))
        if not part:
            raise ConnectionError(f"peer closed with {size-len(chunks)} bytes outstanding")
        chunks.extend(part)
    return bytes(chunks)


def read_packet(sock: socket.socket) -> bytes:
    size = struct.unpack(">I", read_exact(sock, 4))[0]
    if size > MAX_PACKET:
        raise ValueError(f"server packet too large: {size}")
    return read_exact(sock, size)


def connect(host: str, port: int, timeout: float = 10.0) -> tuple[socket.socket, dict[str, int]]:
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(10.0)
    sock.sendall(connect_request())
    body = read_packet(sock)
    if len(body) < 21:
        sock.close()
        raise ValueError(f"short ConnectResponse: {len(body)} bytes")
    version, session_timeout = struct.unpack_from(">ii", body)
    session_id = struct.unpack_from(">q", body, 8)[0]
    passwd_size = struct.unpack_from(">i", body, 16)[0]
    if passwd_size < 0 or 20 + passwd_size + 1 > len(body):
        sock.close()
        raise ValueError("malformed ConnectResponse password field")
    return sock, {"protocol_version": version, "session_timeout_ms": session_timeout,
                  "session_id": session_id, "read_only": body[20 + passwd_size] != 0}


def reply(sock: socket.socket, xid: int, opcode: int, payload: bytes = b"") -> dict[str, int]:
    sock.sendall(request(xid, opcode, payload))
    body = read_packet(sock)
    if len(body) < 16:
        raise ValueError(f"short ReplyHeader: {len(body)} bytes")
    response_xid, zxid, error = struct.unpack_from(">iqi", body)
    if response_xid != xid:
        raise AssertionError(f"xid mismatch: expected {xid}, got {response_xid}")
    return {"xid": response_xid, "zxid": zxid, "error": error,
            "payload_bytes": len(body) - 16, "opcode": opcode}


def path_request(path: str, watch: bool = False) -> bytes:
    return jute_string(path) + (b"\x01" if watch else b"\x00")


def create_request(path: str, data: bytes) -> bytes:
    # ACL vector: one world:anyone entry with all standard permissions.
    acl = i32(31) + jute_string("world") + jute_string("anyone")
    return (jute_string(path) + jute_buffer(data) + i32(1) + acl + i32(0))


def set_data_request(path: str, data: bytes, version: int = -1) -> bytes:
    return jute_string(path) + jute_buffer(data) + i32(version)


def delete_request(path: str, version: int = -1) -> bytes:
    return jute_string(path) + i32(version)


def smoke_flow(host: str, port: int, iteration: int) -> dict[str, object]:
    sock, session = connect(host, port)
    results: list[dict[str, int]] = []
    path = f"/aflnet-baseline-{iteration}-{session['session_id']:x}"
    try:
        results.append(reply(sock, 1, 3, path_request("/")))       # exists
        results.append(reply(sock, 2, 4, path_request("/")))       # getData
        results.append(reply(sock, 3, 8, path_request("/")))       # getChildren
        results.append(reply(sock, 4, 1, create_request(path, b"seed")))
        results.append(reply(sock, 5, 4, path_request(path)))      # getData
        results.append(reply(sock, 6, 5, set_data_request(path, b"updated")))
        results.append(reply(sock, 7, 9, jute_string(path)))        # sync
        results.append(reply(sock, 8, 2, delete_request(path)))
        results.append(reply(sock, -2, 11))                        # ping
    finally:
        sock.close()
    failures = [item for item in results if item["error"] != 0]
    return {"iteration": iteration, "session": session, "replies": results,
            "success": not failures, "errors": failures}


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] != "check":
        print("usage: zookeeper_client.py check HOST PORT", file=sys.stderr)
        return 2
    host, port = sys.argv[2], int(sys.argv[3])
    sock, session = connect(host, port)
    sock.close()
    print(json.dumps({"connect_ok": True, "host": host, "port": port,
                      "session": session}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
