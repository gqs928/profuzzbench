#!/usr/bin/env python3
"""Smoke-test YugabyteDB YCQL Native Protocol v4 through one persistent node."""
from __future__ import annotations

import hashlib
import json
import os
import signal
import socket
import struct
import subprocess
import sys
from pathlib import Path

HOST = os.environ.get("YCQL_HOST") or socket.gethostbyname(socket.gethostname())
PORT = int(os.environ.get("YCQL_PORT", "9042"))
STARTER = os.environ.get("YUGABYTE_STARTER", "/opt/benchmark/start-yugabyte.sh")
RESETTER = os.environ.get("YUGABYTE_RESETTER", "/opt/benchmark/reset-yugabyte.sh")
STOPPER = os.environ.get("YUGABYTE_STOPPER", "/opt/benchmark/stop-yugabyte.sh")
VERSION = 0x04


def cql_string(value: str) -> bytes:
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def frame(opcode: int, body: bytes = b"", stream: int = 0) -> bytes:
    return struct.pack(">BBhBI", VERSION, 0, stream, opcode, len(body)) + body


def startup() -> bytes:
    body = struct.pack(">H", 1) + cql_string("CQL_VERSION") + cql_string("3.0.0")
    return frame(0x01, body, 1)


def query(text: str, stream: int) -> bytes:
    encoded = text.encode("utf-8")
    body = struct.pack(">I", len(encoded)) + encoded + struct.pack(">HB", 1, 0)
    return frame(0x07, body, stream)


def read_exact(sock: socket.socket, count: int) -> bytes:
    parts = bytearray()
    while len(parts) < count:
        data = sock.recv(count - len(parts))
        if not data:
            raise ConnectionError(f"peer closed with {count - len(parts)} bytes outstanding")
        parts.extend(data)
    return bytes(parts)


def read_frame(sock: socket.socket) -> bytes:
    header = read_exact(sock, 9)
    version, _flags, _stream, _opcode = struct.unpack_from(">BBhB", header)
    size = struct.unpack_from(">I", header, 5)[0]
    if version not in (0x84, 0x85) or size > 16 * 1024 * 1024:
        raise ValueError(f"invalid Cassandra response header {header.hex()}")
    return header + read_exact(sock, size)


def error_code(response: bytes) -> int | None:
    if response[4] != 0x00 or len(response) < 13:
        return None
    return struct.unpack_from(">I", response, 9)[0]


def error_message(response: bytes) -> str | None:
    if error_code(response) is None or len(response) < 15:
        return None
    size = struct.unpack_from(">H", response, 13)[0]
    if size > len(response) - 15:
        return "<truncated error message>"
    return response[15:15 + size].decode("utf-8", errors="replace")


def run_flow(name: str, queries: list[str], iteration: int) -> dict[str, object]:
    replies: list[dict[str, object]] = []
    expected = [0x06, 0x02] + ([0x08] * len(queries))
    requests = [frame(0x05, b"", 0), startup()]
    requests.extend(query(text, stream) for stream, text in enumerate(queries, start=2))
    with socket.create_connection((HOST, PORT), timeout=10) as sock:
        sock.settimeout(20)
        for request, expected_opcode in zip(requests, expected, strict=True):
            stream_id = struct.unpack_from(">h", request, 2)[0]
            opcode = request[4]
            sock.sendall(request)
            response = read_frame(sock)
            response_stream = struct.unpack_from(">h", response, 2)[0]
            response_opcode = response[4]
            if response_stream != stream_id:
                raise AssertionError(f"{name}: stream {response_stream} != {stream_id}")
            if response_opcode != expected_opcode:
                raise AssertionError(
                    f"{name}: request {opcode:#x} expected response {expected_opcode:#x}, "
                    f"got {response_opcode:#x}, error={error_code(response)} "
                    f"message={error_message(response)!r}")
            replies.append({"request_opcode": opcode, "request_stream": stream_id,
                            "response_opcode": response_opcode,
                            "response_stream": response_stream,
                            "response_bytes": len(response),
                            "response_sha256": hashlib.sha256(response).hexdigest()})
    return {"flow": name, "iteration": iteration, "responses": replies,
            "all_streams_matched": True}


def listener_closed() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.2):
            return False
    except OSError:
        return True


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: yugabyte_smoke.py OUTDIR [repetitions]", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    repetitions = int(sys.argv[2]) if len(sys.argv) == 3 else 1
    if not 1 <= repetitions <= 5:
        raise ValueError("repetitions must be in [1, 5]")
    if outdir.exists() and any(outdir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("YUGABYTE_LOG_FILE", str(outdir / "yugabyte-node.log"))
    os.environ.setdefault("YUGABYTE_LIFECYCLE_LOG", str(outdir / "yugabyte-lifecycle.tsv"))
    os.environ.setdefault("YCQL_HOST", HOST)
    os.environ.setdefault("YCQL_PORT", str(PORT))

    flows = [
        ("release-version", ["SELECT release_version FROM system.local"]),
        ("cluster-name", ["SELECT cluster_name FROM system.local"]),
        ("create-keyspace", ["CREATE KEYSPACE IF NOT EXISTS afl_fuzz WITH replication = "
                              "{'class':'SimpleStrategy','replication_factor':'1'}"]),
        ("multi-query", ["SELECT release_version FROM system.local",
                         "SELECT cluster_name FROM system.local"]),
    ]
    rows: list[dict[str, object]] = []
    started = False
    stop_ok = False
    try:
        subprocess.run([STARTER], check=True, timeout=330)
        started = True
        for iteration in range(1, repetitions + 1):
            for name, queries in flows:
                subprocess.run([RESETTER], check=True, timeout=30)
                rows.append(run_flow(name, queries, iteration))
    finally:
        if started:
            subprocess.run([STOPPER], check=False, timeout=80)
            stop_ok = listener_closed()

    result = {"target": "YugabyteDB 2026.1.3.0 build 100",
              "protocol": "YCQL Native Protocol v4",
              "reset": "one isolated node; drop all non-system keyspaces before each flow",
              "repetitions": repetitions,
              "flows_per_repetition": len(flows),
              "successful_responses": sum(len(row["responses"]) for row in rows),
              "all_flows_passed": len(rows) == len(flows) * repetitions,
              "listener_closed_after_stop": stop_ok,
              "flows": rows}
    (outdir / "protocol-smoke.json").write_text(json.dumps(result, indent=2) + "\n",
                                                 encoding="utf-8")
    if not result["all_flows_passed"] or not stop_ok:
        raise RuntimeError(f"smoke failed: {json.dumps(result, sort_keys=True)}")
    print(f"PASS: {repetitions} repetitions over {len(flows)} YugabyteDB flows; "
          f"{result['successful_responses']} Native Protocol responses; listener closed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, AssertionError, ConnectionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
