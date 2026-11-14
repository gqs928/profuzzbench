#!/usr/bin/env python3
"""Generate STOMP 1.2 exchanges for ActiveMQ Classic."""
from pathlib import Path
OUT = Path(__file__).with_name("seeds")
NUL = b"\x00"

def frame(command: str, headers: dict[str, str] | None = None, body: bytes = b"") -> bytes:
    headers = headers or {}
    lines = [command, *(f"{k}:{v}" for k, v in headers.items())]
    return ("\n".join(lines) + "\n\n").encode() + body + NUL

connect = frame("STOMP", {"accept-version": "1.2", "host": "localhost",
                           "login": "admin", "passcode": "admin"})
sub = frame("SUBSCRIBE", {"id": "sub-0", "destination": "/queue/afl", "ack": "auto"})
send = frame("SEND", {"destination": "/queue/afl", "content-type": "text/plain"}, b"seed")
disconnect = frame("DISCONNECT", {"receipt": "disc-0"})

def main() -> None:
    OUT.mkdir(exist_ok=True)
    samples = {
        "01-connect-send-subscribe.stomp": connect + send + sub + disconnect,
        "02-connect-subscribe-send.stomp": connect + sub + send + disconnect,
        "03-connect-version-1.0.stomp": frame("CONNECT", {"accept-version": "1.0", "host": "localhost", "login": "admin", "passcode": "admin"}) + disconnect,
        "04-malformed-header.stomp": frame("STOMP", {"accept-version": "1.2", "host": "localhost", "login": "admin", "passcode": "admin", "x-invalid": "a:b"}) + b"BROKEN\nno-colon\n\x00",
        "05-truncated-frame.stomp": b"STOMP\naccept-version:1.2\nhost:localhost\n\n",
        "06-heartbeat.stomp": connect + b"\n\n" + disconnect,
    }
    for name, data in samples.items():
        (OUT / name).write_bytes(data)

if __name__ == "__main__":
    main()
