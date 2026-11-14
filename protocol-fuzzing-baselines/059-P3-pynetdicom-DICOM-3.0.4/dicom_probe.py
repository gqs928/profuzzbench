#!/usr/bin/env python3
"""Wait for a DICOM Upper Layer association accept and cleanly release it."""
from __future__ import annotations

import argparse
import socket
import time

from prepare_seeds import associate_request, pdu
from protocol_smoke import recv_pdu


def probe(host: str, port: int, deadline: float) -> bool:
    end = time.monotonic() + deadline
    last_error: str | None = None
    while time.monotonic() < end:
        try:
            with socket.create_connection((host, port), timeout=0.5) as sock:
                sock.settimeout(1.0)
                sock.sendall(associate_request())
                kind, _ = recv_pdu(sock)
                if kind != 0x02:
                    last_error = f"association PDU type 0x{kind:02x}"
                    time.sleep(0.1)
                    continue
                sock.sendall(pdu(0x05, bytes(4)))
                release_kind, _ = recv_pdu(sock)
                if release_kind != 0x06:
                    last_error = f"release response PDU type 0x{release_kind:02x}"
                    continue
                return True
        except (OSError, EOFError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(0.1)
    print(f"DICOM readiness probe failed: {last_error}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11112)
    parser.add_argument("--deadline", type=float, default=20.0)
    args = parser.parse_args()
    if not probe(args.host, args.port, args.deadline):
        raise SystemExit(1)
    print("PASS: DICOM association accept and release")


if __name__ == "__main__":
    main()
