#!/usr/bin/env python3
"""Exercise an authenticated IMAP mailbox session over loopback."""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path


class IMAP:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.reader = sock.makefile("rb")

    def line(self) -> bytes:
        data = self.reader.readline(65537)
        if not data:
            raise ConnectionError("IMAP server closed the connection")
        if len(data) > 65536:
            raise ValueError("IMAP line exceeded 64 KiB")
        return data

    def command(self, tag: str, text: str) -> bytes:
        self.sock.sendall(f"{tag} {text}\r\n".encode("ascii"))
        response = bytearray()
        prefix = tag.encode("ascii") + b" "
        while True:
            line = self.line()
            response.extend(line)
            if line.startswith(prefix):
                return bytes(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1143)
    parser.add_argument("--username", default="fuzzuser")
    parser.add_argument("--password", required=True)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    deadline = time.monotonic() + 10
    while True:
        try:
            sock = socket.create_connection((args.host, args.port), timeout=1)
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)
    sock.settimeout(5)
    client = IMAP(sock)
    checks: dict[str, bool] = {}
    try:
        greeting = client.line()
        if not greeting.startswith((b"* OK", b"* PREAUTH")):
            raise RuntimeError(f"invalid greeting: {greeting!r}")
        capability = client.command("A01", "CAPABILITY")
        checks["capability"] = b"CAPABILITY" in capability.upper() and b"A01 OK" in capability
        bad_login = client.command("A02", "LOGIN fuzzuser wrong-benchmark-password")
        checks["invalid_login_rejected"] = b"A02 NO" in bad_login
        login = client.command("A03", f"LOGIN {args.username} {args.password}")
        checks["login"] = b"A03 OK" in login
        if not checks["login"]:
            raise RuntimeError(f"valid IMAP LOGIN failed: {login!r}")
        select = client.command("A04", "SELECT INBOX")
        checks["select"] = b"A04 OK" in select
        fetch = client.command("A05", "FETCH 1 (UID FLAGS BODY.PEEK[HEADER])")
        checks["fetch"] = b"A05 OK" in fetch and b"FETCH" in fetch.upper()
        search = client.command("A06", "UID SEARCH ALL")
        checks["search"] = b"A06 OK" in search
        store = client.command("A07", "STORE 1 +FLAGS (\\Seen)")
        checks["store"] = b"A07 OK" in store
        logout = client.command("A08", "LOGOUT")
        checks["logout"] = b"A08 OK" in logout
        failed = [name for name, okay in checks.items() if not okay]
        if failed:
            raise RuntimeError(f"IMAP checks failed: {failed}")
        evidence = {"protocol": "IMAP4rev1", "host": args.host, "port": args.port, "checks": checks}
        if args.save:
            args.save.parent.mkdir(parents=True, exist_ok=True)
            args.save.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        client.reader.close()
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
