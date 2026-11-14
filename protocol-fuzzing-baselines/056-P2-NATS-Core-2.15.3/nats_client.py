#!/usr/bin/env python3
"""Small NATS core-protocol client used by seed generation and validation."""
from __future__ import annotations

import json
import socket
import sys
import time
from dataclasses import dataclass, field


@dataclass
class Client:
    sock: socket.socket
    pending: bytearray = field(default_factory=bytearray)

    def read_exact(self, size: int) -> bytes:
        while len(self.pending) < size:
            part = self.sock.recv(max(4096, size - len(self.pending)))
            if not part:
                raise ConnectionError(f"server closed with {size-len(self.pending)} bytes outstanding")
            self.pending.extend(part)
        output = bytes(self.pending[:size])
        del self.pending[:size]
        return output

    def read_line(self) -> bytes:
        while True:
            idx = self.pending.find(b"\r\n")
            if idx >= 0:
                line = bytes(self.pending[:idx])
                del self.pending[:idx + 2]
                return line
            part = self.sock.recv(4096)
            if not part:
                raise ConnectionError("server closed before CRLF line")
            self.pending.extend(part)

    def event(self) -> dict[str, object]:
        line = self.read_line()
        fields = line.split()
        if not fields:
            return {"kind": "empty"}
        opcode = fields[0].upper()
        if opcode == b"MSG":
            size = int(fields[-1])
            payload = self.read_exact(size + 2)
            if not payload.endswith(b"\r\n"):
                raise ValueError("MSG payload terminator missing")
            return {"kind": "MSG", "subject": fields[1].decode("ascii", "replace"),
                    "payload": payload[:-2]}
        if opcode == b"HMSG":
            total = int(fields[-1])
            headers = int(fields[-2])
            payload = self.read_exact(total + 2)
            if headers > total or not payload.endswith(b"\r\n"):
                raise ValueError("malformed HMSG payload framing")
            return {"kind": "HMSG", "subject": fields[1].decode("ascii", "replace"),
                    "headers": payload[:headers], "payload": payload[headers:-2]}
        if opcode == b"INFO":
            return {"kind": "INFO", "info": json.loads(line[5:].decode("utf-8"))}
        if opcode in (b"+OK", b"-ERR"):
            return {"kind": opcode.decode("ascii"), "line": line.decode("utf-8", "replace")}
        return {"kind": opcode.decode("ascii", "replace"),
                "line": line.decode("utf-8", "replace")}

    def next_event(self, timeout: float = 3.0) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while True:
            try:
                return self.event()
            except socket.timeout:
                if time.monotonic() >= deadline:
                    raise TimeoutError("timed out waiting for NATS event")
                self.sock.settimeout(max(0.05, deadline - time.monotonic()))

    def expect(self, kinds: set[str], timeout: float = 3.0) -> list[dict[str, object]]:
        deadline = time.monotonic() + timeout
        events: list[dict[str, object]] = []
        seen: set[str] = set()
        while not kinds.issubset(seen):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"missing NATS events {sorted(kinds-seen)}; got {events}")
            self.sock.settimeout(remaining)
            event = self.next_event(remaining)
            events.append(event)
            kind = str(event["kind"])
            if kind == "PING":
                self.sock.sendall(b"PONG\r\n")
            elif kind == "-ERR":
                raise RuntimeError(str(event["line"]))
            else:
                seen.add(kind)
        return events

    def connect_protocol(self) -> list[dict[str, object]]:
        info = self.expect({"INFO"}, 5.0)
        self.sock.sendall(
            b'CONNECT {"verbose":true,"pedantic":true,"protocol":1,"headers":true,'
            b'"lang":"nats-benchmark","version":"1.0.0"}\r\n')
        ok = self.expect({"+OK"})
        return info + ok


def connect(host: str, port: int, timeout: float = 3.0) -> Client:
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    return Client(sock)


def smoke_flow(host: str, port: int, iteration: int) -> dict[str, object]:
    client = connect(host, port)
    events: list[dict[str, object]] = []
    subject = f"bench.smoke.{iteration}"
    payload = f"hello-{iteration}".encode()
    header = b"NATS/1.0\r\nX-Benchmark: smoke\r\n\r\n"
    hpayload = b"hmsg-" + str(iteration).encode()
    try:
        events.extend(client.connect_protocol())
        client.sock.sendall(f"SUB {subject} 1\r\n".encode())
        events.extend(client.expect({"+OK"}))
        client.sock.sendall(f"PUB {subject} {len(payload)}\r\n".encode() + payload + b"\r\n")
        pub_events = client.expect({"+OK", "MSG"})
        events.extend(pub_events)
        msg = next(event for event in pub_events if event["kind"] == "MSG")
        if msg["payload"] != payload or msg["subject"] != subject:
            raise AssertionError(f"PUB echo mismatch: {msg}")
        total = len(header) + len(hpayload)
        client.sock.sendall(f"HPUB {subject} {len(header)} {total}\r\n".encode() +
                            header + hpayload + b"\r\n")
        hpub_events = client.expect({"+OK", "HMSG"})
        events.extend(hpub_events)
        hmsg = next(event for event in hpub_events if event["kind"] == "HMSG")
        if hmsg["headers"] != header or hmsg["payload"] != hpayload:
            raise AssertionError(f"HPUB echo mismatch: {hmsg}")
        client.sock.sendall(b"PING\r\n")
        events.extend(client.expect({"PONG"}))
        client.sock.sendall(b"UNSUB 1\r\n")
        events.extend(client.expect({"+OK"}))
        return {"iteration": iteration, "success": True, "subject": subject,
                "events": [str(event["kind"]) for event in events],
                "event_count": len(events), "pub_bytes": len(payload),
                "hpub_header_bytes": len(header), "hpub_payload_bytes": len(hpayload)}
    finally:
        client.sock.close()


def main() -> int:
    if len(sys.argv) not in (4, 5) or sys.argv[1] not in ("check", "smoke"):
        print("usage: nats_client.py check|smoke HOST PORT [ITERATION]", file=sys.stderr)
        return 2
    mode, host, port_text = sys.argv[1:4]
    port = int(port_text)
    if mode == "check":
        c = connect(host, port)
        events = c.connect_protocol()
        c.sock.sendall(b"PING\r\n")
        events.extend(c.expect({"PONG"}))
        c.sock.close()
        print(json.dumps({"connect_ok": True, "events": [e["kind"] for e in events]},
                         sort_keys=True))
        return 0
    result = smoke_flow(host, port, int(sys.argv[4]) if len(sys.argv) == 5 else 1)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError, AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
