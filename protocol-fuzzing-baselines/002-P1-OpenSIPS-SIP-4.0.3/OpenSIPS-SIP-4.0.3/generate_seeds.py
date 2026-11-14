#!/usr/bin/env python3
"""Generate deterministic SIP/UDP request seeds for OpenSIPS."""

from pathlib import Path
import sys


def request(method: str, *, body: bytes = b"") -> bytes:
    uri = b"sip:service@example.test"
    lines = [
        method.encode() + b" " + uri + b" SIP/2.0",
        b"Via: SIP/2.0/UDP 127.0.0.1:5062;branch=z9hG4bKbench-" + method.encode() + b";rport",
        b"Max-Forwards: 70",
        b"From: <sip:fuzzer@example.test>;tag=bench",
        b"To: <sip:service@example.test>",
        b"Call-ID: " + method.lower().encode() + b"@benchmark.example",
        b"CSeq: 1 " + method.encode(),
    ]
    if method == "INVITE":
        lines.extend([b"Contact: <sip:fuzzer@127.0.0.1>", b"Content-Type: application/sdp"])
    lines.extend([b"Content-Length: " + str(len(body)).encode(), b""])
    return b"\r\n".join(lines) + b"\r\n" + body


def main(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    corpus = {
        "options.sip": request("OPTIONS"),
        "register.sip": request("REGISTER"),
        "invite.sip": request("INVITE", body=(
            b"v=0\r\no=fuzzer 1 1 IN IP4 127.0.0.1\r\ns=bench\r\n"
            b"c=IN IP4 127.0.0.1\r\nt=0 0\r\nm=audio 4000 RTP/AVP 0\r\n"
        )),
        "bye.sip": request("BYE"),
        "malformed.sip": b"OPTIONS sip:bad SIP/2.0\r\nVia: SIP/2.0/UDP\r\n\r\n",
        "truncated.sip": b"INVITE sip:service@example.test SIP/2.0\r\nContent-Length: 200\r\n",
    }
    for name, payload in corpus.items():
        (destination / name).write_bytes(payload)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_seeds.py DESTINATION")
    main(Path(sys.argv[1]))
