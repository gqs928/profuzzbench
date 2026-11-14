#!/usr/bin/env python3
import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path


class RTSPClient:
    def __init__(self, host: str, port: int, timeout: float = 3.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.pending = b""
        self.cseq = 0

    def close(self) -> None:
        self.sock.close()

    def request(self, method: str, url: str, headers: list[str] | None = None):
        self.cseq += 1
        lines = [f"{method} {url} RTSP/1.0", f"CSeq: {self.cseq}", "User-Agent: gst-rtsp-baseline/1.0"]
        lines.extend(headers or [])
        self.sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("ascii"))
        return self.read_response()

    def read_response(self):
        while True:
            start = self.pending.find(b"RTSP/1.0 ")
            if start >= 0:
                if start:
                    self.pending = self.pending[start:]
                end = self.pending.find(b"\r\n\r\n")
                if end >= 0:
                    head = self.pending[:end + 4]
                    length = 0
                    for line in head.split(b"\r\n")[1:]:
                        if line.lower().startswith(b"content-length:"):
                            length = int(line.split(b":", 1)[1].strip())
                    total = end + 4 + length
                    if len(self.pending) >= total:
                        response = self.pending[:total]
                        self.pending = self.pending[total:]
                        status = re.match(rb"RTSP/1\.0\s+(\d{3})", response)
                        if not status:
                            raise RuntimeError(f"Malformed RTSP status line: {response[:80]!r}")
                        return int(status.group(1)), response
            self.pending += self.sock.recv(65536)


def retry_connect(host: str, port: int, timeout: float):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            return RTSPClient(host, port, timeout=2.0)
        except OSError as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"RTSP listener did not become ready: {last_error}")


def check(status: int, expected: int, label: str, response: bytes, evidence: dict) -> None:
    if status != expected:
        raise RuntimeError(f"{label}: expected {expected}, got {status}: {response[:240]!r}")
    evidence[label] = {"status": status, "response_bytes": len(response)}


def run(host: str, port: int, timeout: float) -> dict:
    base = f"rtsp://{host}:{port}/test"
    client = retry_connect(host, port, timeout)
    evidence: dict = {"target": "GStreamer gst-rtsp-server", "protocol": "RTSP/TCP"}
    try:
        status, response = client.request("OPTIONS", base)
        check(status, 200, "OPTIONS", response, evidence)
        if b"Public:" not in response:
            raise RuntimeError("OPTIONS response is missing the Public method list")

        status, response = client.request("DESCRIBE", base, ["Accept: application/sdp"])
        check(status, 200, "DESCRIBE", response, evidence)
        if b"Content-Type: application/sdp" not in response or b"a=control:stream=0" not in response:
            raise RuntimeError("DESCRIBE response does not contain the configured SDP track")

        track = base + "/stream=0"
        status, response = client.request("SETUP", track,
                                          ["Transport: RTP/AVP/TCP;unicast;interleaved=0-1"])
        check(status, 200, "SETUP", response, evidence)
        match = re.search(rb"(?im)^Session:\s*([^;\r\n]+)", response)
        if not match:
            raise RuntimeError("SETUP response is missing a Session identifier")
        session = match.group(1).decode("ascii")

        status, response = client.request("PLAY", base,
                                          [f"Session: {session}", "Range: npt=0.000-"])
        check(status, 200, "PLAY", response, evidence)
        status, response = client.request("TEARDOWN", base, [f"Session: {session}"])
        check(status, 200, "TEARDOWN", response, evidence)
    finally:
        client.close()
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8554)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        evidence = run(args.host, args.port, args.timeout)
        content = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
        print("PASS: OPTIONS, DESCRIBE, SETUP, PLAY and TEARDOWN (RTSP/TCP)")
        print(content, end="")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
