#!/usr/bin/env python3
"""Generate deterministic, complete NATS client streams for AFLNet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
CONNECT = (b'CONNECT {"verbose":true,"pedantic":true,"protocol":1,"headers":true,'
           b'"lang":"nats-benchmark","version":"1.0.0"}\r\n')
HEADER = b"NATS/1.0\r\nX-Test: seed\r\n\r\n"


def pub(subject: str, payload: bytes, reply: str | None = None) -> bytes:
    args = f"PUB {subject} ".encode()
    if reply:
        args += reply.encode() + b" "
    return args + str(len(payload)).encode() + b"\r\n" + payload + b"\r\n"


def hpub(subject: str, body: bytes, reply: str | None = None) -> bytes:
    args = f"HPUB {subject} ".encode()
    if reply:
        args += reply.encode() + b" "
    return (args + str(len(HEADER)).encode() + b" " +
            str(len(HEADER) + len(body)).encode() + b"\r\n" + HEADER + body + b"\r\n")


def main() -> None:
    SEEDS.mkdir(exist_ok=True)
    cases = {
        "connect-ping.bin": CONNECT + b"PING\r\n",
        "connect-sub-pub-echo.bin": CONNECT + b"SUB bench.seed 1\r\n" +
                                    pub("bench.seed", b"hello"),
        "connect-hpub-echo.bin": CONNECT + b"SUB bench.header 1\r\n" +
                                 hpub("bench.header", b"payload"),
        "connect-reply-pub.bin": CONNECT + b"SUB bench.req 1\r\n" +
                                 pub("bench.req", b"request", "bench.reply") +
                                 b"PING\r\n",
        "connect-unsub.bin": CONNECT + b"SUB bench.unsub 2\r\nUNSUB 2\r\nPING\r\n",
        "connect-wildcard.bin": CONNECT + b"SUB bench.wildcard.* 3\r\n" +
                                pub("bench.wildcard.one", b"one") +
                                pub("bench.wildcard.two", b"two") + b"PING\r\n",
        "connect-invalid-subject.bin": CONNECT + b"SUB bench.bad. 4\r\n",
        "connect-truncated-pub.bin": CONNECT + b"PUB bench.truncated 10\r\nshort",
    }
    rows = []
    for name, data in cases.items():
        (SEEDS / name).write_bytes(data)
        rows.append({"name": name, "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(),
                     "contains_connect": data.startswith(b"CONNECT "),
                     "contains_crlf": data.endswith(b"\r\n")})
    (ROOT / "seeds-manifest.json").write_text(json.dumps({
        "target": "NATS Server 2.15.3",
        "protocol": "NATS client protocol v1 over plaintext TCP/4222",
        "framing": "CRLF control lines; PUB/HPUB payload byte counts plus trailing CRLF",
        "server_first": "Each connection receives INFO before the client CONNECT stream",
        "cases": rows,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"prepared {len(cases)} NATS streams")


if __name__ == "__main__":
    main()
