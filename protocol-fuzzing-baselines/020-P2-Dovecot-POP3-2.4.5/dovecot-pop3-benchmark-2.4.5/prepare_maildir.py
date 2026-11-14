#!/usr/bin/env python3
"""Recreate the fixed POP3 Maildir for one benchmark testcase."""

from pathlib import Path
import shutil

STATE_ROOT = Path("/tmp/dovecot-pop3-benchmark-state")
MAIL_ROOT = STATE_ROOT / "mail"


def main() -> int:
    shutil.rmtree(MAIL_ROOT, ignore_errors=True)
    maildir = MAIL_ROOT / "home" / "fuzzuser" / "Maildir"
    for name in ("cur", "new", "tmp"):
        (maildir / name).mkdir(parents=True, exist_ok=True)
    message = (
        b"From: bench@example.invalid\r\n"
        b"To: fuzzuser@localhost\r\n"
        b"Subject: fixed POP3 baseline message\r\n"
        b"Message-ID: <pop3-baseline@benchmark.invalid>\r\n"
        b"Date: Thu, 01 Jan 1970 00:00:00 +0000\r\n\r\n"
        b"Deterministic Maildir content for POP3 command replay.\r\n"
    )
    (maildir / "new" / "1700000000.1_bench.localhost:2,").write_bytes(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
