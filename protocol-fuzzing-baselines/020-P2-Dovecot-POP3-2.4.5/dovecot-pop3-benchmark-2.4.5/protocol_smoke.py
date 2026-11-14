#!/usr/bin/env python3
"""Exercise a real POP3 authorization and mail transaction over TCP."""

from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path


def read_line(reader) -> bytes:
    line = reader.readline(65537)
    if not line:
        raise ConnectionError("POP3 server closed the connection")
    if len(line) > 65536:
        raise ValueError("POP3 response line exceeded 64 KiB")
    return line


def send(sock: socket.socket, command: str) -> None:
    sock.sendall(command.encode("ascii") + b"\r\n")


def response(sock: socket.socket, reader, *, multiline: bool = False) -> list[bytes]:
    first = read_line(reader)
    lines = [first]
    if first.startswith(b"-ERR"):
        return lines
    if not first.startswith(b"+OK"):
        raise RuntimeError(f"unexpected POP3 status line: {first!r}")
    if multiline:
        while True:
            line = read_line(reader)
            lines.append(line)
            if line in (b".\r\n", b".\n"):
                break
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1110)
    parser.add_argument("--username", default="fuzzuser")
    parser.add_argument("--password", required=True)
    parser.add_argument("--save-seeds", type=Path)
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

    states: list[str] = []
    try:
        sock.settimeout(5)
        reader = sock.makefile("rb")
        greeting = read_line(reader)
        if not greeting.startswith(b"+OK"):
            raise RuntimeError(f"invalid POP3 greeting: {greeting!r}")
        states.append("greeting:+OK")

        send(sock, "CAPA")
        capa = response(sock, reader, multiline=True)
        states.append("CAPA:" + ("+OK" if capa[0].startswith(b"+OK") else "-ERR"))

        send(sock, f"USER {args.username}")
        user = response(sock, reader)
        if not user[0].startswith(b"+OK"):
            raise RuntimeError(f"USER failed: {user[0]!r}")
        states.append("USER:+OK")

        send(sock, "PASS wrong-benchmark-password")
        bad_password = response(sock, reader)
        if not bad_password[0].startswith(b"-ERR"):
            raise RuntimeError(f"invalid password was not rejected: {bad_password[0]!r}")
        states.append("PASS-invalid:-ERR")

        send(sock, f"USER {args.username}")
        if not response(sock, reader)[0].startswith(b"+OK"):
            raise RuntimeError("USER was not accepted after a failed password")
        send(sock, f"PASS {args.password}")
        if not response(sock, reader)[0].startswith(b"+OK"):
            raise RuntimeError("valid POP3 credentials were rejected")
        states.append("PASS-valid:+OK")

        for command, multi in [
            ("STAT", False),
            ("LIST", True),
            ("UIDL", True),
            ("RETR 1", True),
            ("NOOP", False),
            ("DELE 1", False),
            ("RSET", False),
            ("STAT", False),
            ("QUIT", False),
        ]:
            send(sock, command)
            lines = response(sock, reader, multiline=multi)
            if not lines[0].startswith(b"+OK"):
                raise RuntimeError(f"{command} failed: {lines[0]!r}")
            states.append(command.split()[0] + ":+OK")

        if args.save_seeds:
            args.save_seeds.mkdir(parents=True, exist_ok=True)
            (args.save_seeds / "smoke-summary.json").write_text(
                json.dumps(
                    {"host": args.host, "port": args.port, "states": states},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(
                {"protocol": "POP3", "host": args.host, "port": args.port,
                 "states": states},
                indent=2,
            )
        )
    finally:
        try:
            reader.close()
        except (UnboundLocalError, OSError):
            pass
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
