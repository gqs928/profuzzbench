#!/usr/bin/env python3
"""把固定邮件写入隔离 Maildir，供协议回放逐轮复位。"""

from __future__ import annotations

import shutil
from pathlib import Path

STATE_ROOT = Path("/tmp/dovecot-benchmark-state")
MAIL_ROOT = STATE_ROOT / "mail"


def main() -> int:
    if STATE_ROOT != Path("/tmp/dovecot-benchmark-state"):
        raise RuntimeError("拒绝操作固定测试状态目录之外的路径")

    shutil.rmtree(MAIL_ROOT, ignore_errors=True)
    maildir = MAIL_ROOT / "home" / "fuzzuser" / "Maildir"
    for name in ("cur", "new", "tmp"):
        (maildir / name).mkdir(parents=True, exist_ok=True)

    message = (
        b"From: bench@example.invalid\r\n"
        b"To: fuzzuser@localhost\r\n"
        b"Subject: fixed baseline message\r\n"
        b"Message-ID: <baseline@benchmark.invalid>\r\n"
        b"Date: Thu, 01 Jan 1970 00:00:00 +0000\r\n"
        b"\r\n"
        b"Deterministic mailbox content for repeatable IMAP replay.\r\n"
    )
    (maildir / "new" / "1700000000.1_bench.localhost:2,").write_bytes(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
