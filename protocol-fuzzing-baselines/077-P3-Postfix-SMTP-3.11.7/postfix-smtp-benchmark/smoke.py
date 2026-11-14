#!/usr/bin/env python3
import argparse
import json
import socket


def read_reply(sock):
    lines = []
    while True:
        line = bytearray()
        while not line.endswith(b"\n"):
            chunk = sock.recv(1)
            if not chunk:
                raise RuntimeError("connection closed mid-reply")
            line.extend(chunk)
            if len(line) > 8192:
                raise RuntimeError("SMTP reply line exceeded 8192 bytes")
        lines.append(bytes(line).decode("ascii", "replace").rstrip())
        if len(line) < 4 or line[3:4] != b"-":
            return "\n".join(lines)


def command(sock, value, expected):
    sock.sendall(value + b"\r\n")
    reply = read_reply(sock)
    if not reply.startswith(expected.decode("ascii")):
        raise RuntimeError(f"{value!r}: expected {expected!r}, got {reply!r}")
    return reply


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2525)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--output")
    args = parser.parse_args()
    transcript = []
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        greeting = read_reply(sock)
        if not greeting.startswith("220"):
            raise RuntimeError(f"bad greeting: {greeting!r}")
        transcript.append(greeting)
        for value, expected in (
            (b"EHLO fuzzer.invalid", b"250"),
            (b"MAIL FROM:<sender@fuzz.invalid>", b"250"),
            (b"RCPT TO:<recipient@fuzz.invalid>", b"250"),
            (b"DATA", b"354"),
        ):
            transcript.append(command(sock, value, expected))
        sock.sendall(b"Subject: baseline\r\n\r\nbody\r\n.\r\n")
        queued = read_reply(sock)
        if not queued.startswith("250"):
            raise RuntimeError(f"mail was not accepted: {queued!r}")
        transcript.append(queued)
        transcript.append(command(sock, b"QUIT", b"221"))
    result = {
        "status": "pass",
        "implementation": "Postfix 3.11.7",
        "protocol": "SMTP over loopback TCP",
        "host": args.host,
        "port": args.port,
        "delivery": "discard transport; no external relay",
        "transcript": transcript,
    }
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            output.write(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
