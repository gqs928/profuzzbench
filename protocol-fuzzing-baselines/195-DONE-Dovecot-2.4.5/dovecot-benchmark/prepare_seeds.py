#!/usr/bin/env python3
"""生成固定、可回放的 IMAP 业务会话种子。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

USERNAME = "fuzzuser"
PASSWORD = "dovecot-benchmark-pass"


def command(tag: str, text: str) -> bytes:
    return f"{tag} {text}\r\n".encode("ascii")


def make_seeds() -> dict[str, bytes]:
    message = (
        b"From: bench@example.invalid\r\n"
        b"To: fuzzuser@localhost\r\n"
        b"Subject: fixed baseline message\r\n"
        b"Message-ID: <baseline@benchmark.invalid>\r\n"
        b"\r\n"
        b"Deterministic mailbox content for repeatable IMAP replay.\r\n"
    )
    append_message = (
        b"From: sender@example.invalid\r\n"
        b"To: fuzzuser@localhost\r\n"
        b"Subject: appended message\r\n"
        b"Message-ID: <append@benchmark.invalid>\r\n"
        b"\r\n"
        b"APPEND literal bytes include a body line.\r\n"
    )
    plain = base64.b64encode(
        b"\0" + USERNAME.encode("ascii") + b"\0" + PASSWORD.encode("ascii")
    ).decode("ascii")

    return {
        "preauth-failed-login.imap": b"".join(
            [
                command("A001", "CAPABILITY"),
                command("A002", "NOOP"),
                command("A003", "LOGIN fuzzuser wrong-password"),
                command("A004", "CAPABILITY"),
                command("A005", "LOGOUT"),
            ]
        ),
        "login-mailbox.imap": b"".join(
            [
                command("B001", "CAPABILITY"),
                command("B002", f"LOGIN {USERNAME} {PASSWORD}"),
                command("B003", 'LIST "" "*"'),
                command("B004", 'LSUB "" "*"'),
                command("B005", "SELECT INBOX"),
                command("B006", "STATUS INBOX (MESSAGES UNSEEN UIDNEXT UIDVALIDITY)"),
                command("B007", "SEARCH ALL"),
                command("B008", "FETCH 1 (UID FLAGS BODY.PEEK[HEADER])"),
                command("B009", "STORE 1 +FLAGS (\\Seen)"),
                command("B010", "NOOP"),
                command("B011", "LOGOUT"),
            ]
        ),
        "append-fetch.imap": b"".join(
            [
                command("C001", f"LOGIN {USERNAME} {PASSWORD}"),
                command("C002", "SELECT INBOX"),
                f"C003 APPEND INBOX {{{len(append_message)}+}}\r\n".encode("ascii"),
                append_message,
                b"\r\n",
                command("C004", "SEARCH ALL"),
                command("C005", "FETCH 2 (UID FLAGS BODY.PEEK[HEADER])"),
                command("C006", "LOGOUT"),
            ]
        ),
        "auth-plain.imap": b"".join(
            [
                command("D001", "CAPABILITY"),
                command("D002", f"AUTHENTICATE PLAIN {plain}"),
                command("D003", "SELECT INBOX"),
                command("D004", "LOGOUT"),
            ]
        ),
        "quoted-mailbox.imap": b"".join(
            [
                command("E001", f"LOGIN {USERNAME} {PASSWORD}"),
                command("E002", 'CREATE "Archive 2026"'),
                command("E003", 'LIST "" "Archive*"'),
                command("E004", 'DELETE "Archive 2026"'),
                command("E005", "LOGOUT"),
            ]
        ),
        "namespace-id.imap": b"".join(
            [
                command("F001", f"LOGIN {USERNAME} {PASSWORD}"),
                command("F002", "ID NIL"),
                command("F003", "NAMESPACE"),
                command("F004", "LOGOUT"),
            ]
        ),
        "invalid-command.imap": b"".join(
            [
                command("G001", f"LOGIN {USERNAME} {PASSWORD}"),
                command("G002", "FETCH 1 (NOT-A-REAL-ITEM)"),
                command("G003", "SEARCH THIS-IS-NOT-A-KEY"),
                command("G004", "LOGOUT"),
            ]
        ),
        "literal-boundary.imap": (
            command("H001", f"LOGIN {USERNAME} {PASSWORD}")
            + f"H002 APPEND INBOX {{{len(message)}+}}\r\n".encode("ascii")
            + message
            + b"\r\n"
            + command("H003", "SELECT INBOX")
            + command("H004", "LOGOUT")
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成固定 IMAP 会话种子")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for name, data in sorted(make_seeds().items()):
        path = args.output_dir / name
        path.write_bytes(data)
        manifest.append(
            {
                "name": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    if args.manifest:
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"已生成 {len(manifest)} 个固定 IMAP 会话种子：{args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
