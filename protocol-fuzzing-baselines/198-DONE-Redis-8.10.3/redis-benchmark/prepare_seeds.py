#!/usr/bin/env python3
"""Create deterministic RESP2/RESP3 request streams for AFLNet."""

from __future__ import annotations

import sys
from pathlib import Path


def command(*args: bytes) -> bytes:
    return b"*" + str(len(args)).encode() + b"\r\n" + b"".join(
        b"$" + str(len(arg)).encode() + b"\r\n" + arg + b"\r\n"
        for arg in args
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prepare_seeds.py OUTPUT_DIR", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    auth = command(b"AUTH", b"default", b"resp-benchmark-pass")
    auth_transition = b"".join([
        command(b"PING"),
        command(b"AUTH", b"default", b"incorrect"),
        auth,
        command(b"PING"),
    ])
    seeds = {
        "resp2-basic": b"".join(
            [auth_transition, command(b"SET", b"bench:key", b"value"),
             command(b"GET", b"bench:key"), command(b"INCR", b"bench:counter"),
             command(b"HSET", b"bench:hash", b"field", b"value"),
             command(b"HGETALL", b"bench:hash")]
        ),
        "resp2-tx": b"".join(
            [auth, command(b"MULTI"), command(b"SET", b"tx:key", b"value"),
             command(b"INCR", b"tx:counter"), command(b"EXEC")]
        ),
        "resp3-basic": b"".join(
            [auth_transition, command(b"HELLO", b"3"), command(b"SET", b"bench:key", b"value"),
             command(b"GET", b"bench:key"),
             command(b"HSET", b"bench:hash", b"field", b"value"),
             command(b"HGETALL", b"bench:hash")]
        ),
        "resp3-client": b"".join(
            [auth, command(b"HELLO", b"3"), command(b"CLIENT", b"ID"),
             command(b"CLIENT", b"INFO"), command(b"PING", b"payload")]
        ),
        "inline-ping": b"PING\r\n",
        "truncated-bulk": b"*2\r\n$4\r\nPING\r\n$5\r\nxy",
        "bad-count": b"*x\r\n$4\r\nPING\r\n",
    }
    for name, data in seeds.items():
        (out / name).write_bytes(data)
    print(f"Generated {len(seeds)} RESP2/RESP3 seed streams in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
