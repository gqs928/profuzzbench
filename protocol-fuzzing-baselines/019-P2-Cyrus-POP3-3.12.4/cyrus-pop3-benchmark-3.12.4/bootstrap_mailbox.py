#!/usr/bin/env python3
"""Create one deterministic Cyrus INBOX message for POP3 fuzzing."""

import socket
import sys
import time
from typing import Optional

HOST, PORT = "127.0.0.1", 1143
MESSAGE = (
    b"From: benchmark@example.invalid\r\n"
    b"To: fuzzuser@localhost\r\n"
    b"Subject: fixed POP3 corpus message\r\n\r\n"
    b"This message is restored before each POP3 testcase.\r\n"
)


def line(sock: socket.socket) -> bytes:
    data = bytearray()
    while not data.endswith(b"\r\n"):
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError(f"server closed mid-line: {bytes(data)!r}")
        data.extend(chunk)
    return bytes(data)


def tagged(sock: socket.socket, tag: str) -> bytes:
    result = bytearray()
    prefix = tag.encode("ascii") + b" "
    while True:
        response_line = line(sock)
        result.extend(response_line)
        if response_line.startswith(prefix):
            return bytes(result)


def command(sock: socket.socket, tag: str, value: str) -> bytes:
    sock.sendall(f"{tag} {value}\r\n".encode("ascii"))
    response = tagged(sock, tag)
    if not response.splitlines()[-1].upper().startswith(f"{tag} OK".encode("ascii")):
        raise RuntimeError(f"IMAP command {value!r} failed: {response!r}")
    return response


def main() -> int:
    deadline = time.monotonic() + 15
    last_error: Optional[OSError] = None
    sock = None
    while time.monotonic() < deadline:
        try:
            # The master can accept a TCP connection before imapd finishes sending
            # its greeting while the bootstrap server initializes its databases.
            sock = socket.create_connection((HOST, PORT), timeout=10)
            break
        except OSError as exc:
            last_error = exc
            time.sleep(0.1)
    if sock is None:
        raise RuntimeError(f"IMAP bootstrap service unavailable: {last_error}")
    with sock:
        greeting = line(sock)
        if b"* OK" not in greeting.upper() and b"* PREAUTH" not in greeting.upper():
            raise RuntimeError(f"unexpected IMAP greeting: {greeting!r}")
        command(sock, "A01", "LOGIN fuzzuser resp-benchmark-pass")
        # A fresh state is used at image creation; CREATE fails if the image is rebuilt
        # on top of an existing work layer, so it is guarded and SELECT confirms it.
        sock.sendall(b"A02 CREATE INBOX\r\n")
        create_result = tagged(sock, "A02")
        create_upper = create_result.upper()
        if (b"A02 OK" not in create_upper and b"ALREADYEXISTS" not in create_upper
                and b"ALREADY EXISTS" not in create_upper):
            raise RuntimeError(f"CREATE INBOX failed: {create_result!r}")
        sock.sendall(f"A03 APPEND INBOX {{{len(MESSAGE)}}}\r\n".encode("ascii"))
        continuation = line(sock)
        if not continuation.startswith(b"+"):
            raise RuntimeError(f"APPEND continuation missing: {continuation!r}")
        sock.sendall(MESSAGE + b"\r\n")
        append_result = tagged(sock, "A03")
        if b"A03 OK" not in append_result.upper():
            raise RuntimeError(f"APPEND failed: {append_result!r}")
        command(sock, "A04", "LOGOUT")
    print("Provisioned fuzzuser INBOX with one deterministic message")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"mailbox bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
