#!/usr/bin/env python3
"""Create deterministic IMAP4rev1 conversation seeds for AFLNet."""

from __future__ import annotations

import sys
from pathlib import Path


def command(tag: str, text: str) -> bytes:
    return f"{tag} {text}\r\n".encode("ascii")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prepare_seeds.py OUTPUT_DIR", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    message = (
        b"From: bench@example.invalid\r\n"
        b"To: fuzzuser@localhost\r\n"
        b"Subject: IMAP benchmark seed\r\n"
        b"\r\n"
        b"A small fixed message body.\r\n"
    )
    append = (
        command("A01", "LOGIN fuzzuser resp-benchmark-pass")
        + command("A02", "CREATE INBOX")
        + f"A03 APPEND INBOX {{{len(message)}+}}\r\n".encode("ascii")
        + message
        + b"\r\n"
        + command("A04", "SELECT INBOX")
        + command("A05", "STATUS INBOX (MESSAGES UNSEEN UIDNEXT UIDVALIDITY)")
        + command("A06", "FETCH 1 (UID FLAGS BODY.PEEK[HEADER])")
        + command("A07", "STORE 1 +FLAGS (\\Seen)")
        + command("A08", "UID SEARCH ALL")
        + command("A09", "EXPUNGE")
        + command("A10", "LOGOUT")
    )

    seeds = {
        "preauth-basic": b"".join(
            [command("A01", "CAPABILITY"), command("A02", "NOOP"),
             command("A03", "LOGIN fuzzuser wrong-password"),
             command("A04", "CAPABILITY"), command("A05", "LOGOUT")]
        ),
        "login-mailbox": b"".join(
            [command("B01", "CAPABILITY"),
             command("B02", "LOGIN fuzzuser resp-benchmark-pass"),
             command("B03", "CAPABILITY"), command("B04", 'LIST "" "*"'),
             command("B05", "CREATE INBOX"), command("B06", "SELECT INBOX"),
             command("B07", "STATUS INBOX (MESSAGES UNSEEN UIDNEXT UIDVALIDITY)"),
             command("B08", "SEARCH ALL"), command("B09", "LOGOUT")]
        ),
        "append-fetch": append,
        "auth-plain": b"".join(
            [command("C01", "CAPABILITY"),
             command("C02", "AUTHENTICATE PLAIN "
                     "AGZ1enp1c2VyAHJlc3AtYmVuY2htYXJrLXBhc3M="),
             command("C03", "LIST \"\" \"INBOX*\""), command("C04", "LOGOUT")]
        ),
        "namespace-lsub": b"".join(
            [command("D01", "LOGIN fuzzuser resp-benchmark-pass"),
             command("D02", "NAMESPACE"), command("D03", "LIST \"\" \"%\""),
             command("D04", "LSUB \"\" \"*\""), command("D05", "LOGOUT")]
        ),
        "quoted-arguments": b"".join(
            [command("E01", "LOGIN fuzzuser resp-benchmark-pass"),
             command("E02", "CREATE INBOX"),
             command("E03", 'CREATE "INBOX.quoted space"'),
             command("E04", 'LIST "" "INBOX.quoted*"'),
             command("E05", 'DELETE "INBOX.quoted space"'),
             command("E06", "LOGOUT")]
        ),
        "truncated-command": b"A01 LOGIN fuzzuser {31+}\r\nshort",
        "bad-literal-count": b"A01 APPEND INBOX {x+}\r\nbody\r\n",
        "partial-command": b"A01 FETCH 1 (BODY.PEEK[HEADER",
    }
    for name, data in seeds.items():
        (out / name).write_bytes(data)
    print(f"Generated {len(seeds)} IMAP conversation seeds in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
