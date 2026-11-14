#!/usr/bin/env python3
import argparse
import json
import socket
import struct
import time
from pathlib import Path


REQUEST = bytes([3, 0, 0, 19, 14, 0xE0, 0, 0, 0, 0, 0, 1, 0, 8, 0, 3, 0, 0, 0])


def read_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise RuntimeError(f"connection closed after {len(data)} of {size} bytes")
        data.extend(part)
    return bytes(data)


def transact(timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", 3390), timeout=2) as sock:
                sock.settimeout(3)
                sock.sendall(REQUEST)
                header = read_exact(sock, 4)
                if header[:2] != b"\x03\x00":
                    raise RuntimeError(f"invalid TPKT header: {header.hex()}")
                length = struct.unpack("!H", header[2:])[0]
                if length < 11 or length > 4096:
                    raise RuntimeError(f"invalid TPKT length: {length}")
                response = header + read_exact(sock, length - 4)
                if response[5] != 0xD0:
                    raise RuntimeError(f"expected X.224 Connection Confirm, got {response.hex()}")
                if len(response) < 19 or response[11] != 2:
                    raise RuntimeError(f"expected RDP_NEG_RSP, got {response.hex()}")
                selected = struct.unpack("!I", response[15:19])[0]
                if selected != 0:
                    raise RuntimeError(f"expected classic RDP protocol 0, selected {selected}")
                return {
                    "status": "pass",
                    "tpkt_length": length,
                    "x224_code": response[5],
                    "negotiation_response_type": response[11],
                    "selected_protocol": selected,
                    "scope": "X.224/RDP security negotiation; no MCS login or session setup",
                }
        except (OSError, RuntimeError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(last_error or "RDP smoke timeout")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = transact(args.timeout)
    except Exception as exc:
        result = {"status": "fail", "error": str(exc)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] != "pass":
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
