#!/usr/bin/env python3
"""Exercise MediaMTX RTSP/TCP with a publisher and reader transaction."""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
from pathlib import Path


class RTSPClient:
    def __init__(self, host: str, port: int, timeout: float):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.cseq = 0

    def request(self, method: str, uri: str, headers: dict[str, str] | None = None,
                body: bytes = b"") -> tuple[int, dict[str, str], bytes, str]:
        self.cseq += 1
        hdrs = {"CSeq": str(self.cseq), "User-Agent": "MediaMTX-baseline-smoke/1"}
        if headers:
            hdrs.update(headers)
        if body:
            hdrs["Content-Length"] = str(len(body))
        wire = f"{method} {uri} RTSP/1.0\r\n" + "".join(
            f"{key}: {value}\r\n" for key, value in hdrs.items()) + "\r\n"
        self.sock.sendall(wire.encode("ascii") + body)
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError(f"connection closed before {method} response")
            data.extend(chunk)
        head_end = data.index(b"\r\n\r\n") + 4
        head = bytes(data[:head_end]).decode("iso-8859-1")
        status_line, *header_lines = head.split("\r\n")
        status = int(status_line.split()[1])
        parsed: dict[str, str] = {}
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                parsed[key.strip().lower()] = value.strip()
        body_len = int(parsed.get("content-length", "0"))
        while len(data) < head_end + body_len:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError(f"connection closed during {method} response body")
            data.extend(chunk)
        return status, parsed, bytes(data[head_end:head_end + body_len]), status_line

    def close(self) -> None:
        self.sock.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8554)
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    base = f"rtsp://{args.host}:{args.port}/bench"
    flows: list[dict] = []
    deadline = time.monotonic() + args.timeout
    while True:
        try:
            publisher = RTSPClient(args.host, args.port, min(2, args.timeout))
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)

    reader = None
    sdp = ("v=0\r\n"
           "o=- 0 0 IN IP4 127.0.0.1\r\n"
           "s=MediaMTX baseline smoke\r\n"
           "c=IN IP4 0.0.0.0\r\n"
           "t=0 0\r\n"
           "m=video 0 RTP/AVP 96\r\n"
           "a=rtpmap:96 H264/90000\r\n"
           "a=control:trackID=0\r\n").encode()
    try:
        code, _, _, line = publisher.request("OPTIONS", base)
        if code != 200:
            raise RuntimeError(f"OPTIONS returned {line}")
        flows.append({"method": "OPTIONS", "status": code})

        code, _, _, line = publisher.request("ANNOUNCE", base,
            {"Content-Type": "application/sdp"}, sdp)
        if code != 200:
            raise RuntimeError(f"ANNOUNCE returned {line}")
        flows.append({"method": "ANNOUNCE", "status": code,
                      "sdp_sha256": hashlib.sha256(sdp).hexdigest()})

        code, headers, _, line = publisher.request("SETUP", base + "/trackID=0",
            {"Transport": "RTP/AVP/TCP;unicast;interleaved=0-1;mode=record"})
        if code != 200 or "session" not in headers:
            raise RuntimeError(f"publisher SETUP returned {line}")
        publisher_session = headers["session"].split(";", 1)[0]
        flows.append({"method": "SETUP publisher", "status": code,
                      "session_id_sha256": hashlib.sha256(publisher_session.encode()).hexdigest()})

        code, _, _, line = publisher.request("RECORD", base,
            {"Session": publisher_session, "Range": "npt=0.000-"})
        if code != 200:
            raise RuntimeError(f"RECORD returned {line}")
        flows.append({"method": "RECORD", "status": code})

        reader = RTSPClient(args.host, args.port, args.timeout)
        code, _, desc_sdp, line = reader.request("DESCRIBE", base,
            {"Accept": "application/sdp"})
        if code != 200 or not desc_sdp:
            raise RuntimeError(f"reader DESCRIBE returned {line}; body={len(desc_sdp)} bytes")
        flows.append({"method": "DESCRIBE reader", "status": code,
                      "sdp_bytes": len(desc_sdp),
                      "sdp_sha256": hashlib.sha256(desc_sdp).hexdigest()})

        code, headers, _, line = reader.request("SETUP", base + "/trackID=0",
            {"Transport": "RTP/AVP/TCP;unicast;interleaved=2-3"})
        if code != 200 or "session" not in headers:
            raise RuntimeError(f"reader SETUP returned {line}")
        reader_session = headers["session"].split(";", 1)[0]
        flows.append({"method": "SETUP reader", "status": code})

        code, _, _, line = reader.request("PLAY", base,
            {"Session": reader_session, "Range": "npt=0.000-"})
        if code != 200:
            raise RuntimeError(f"PLAY returned {line}")
        flows.append({"method": "PLAY", "status": code})

        code, _, _, line = reader.request("TEARDOWN", base,
            {"Session": reader_session})
        if code != 200:
            raise RuntimeError(f"TEARDOWN returned {line}")
        flows.append({"method": "TEARDOWN", "status": code})
    finally:
        if reader is not None:
            reader.close()
        publisher.close()

    result = {"target": "MediaMTX v1.21.3", "transport": "RTSP/TCP",
              "flows": flows, "status": "pass"}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
