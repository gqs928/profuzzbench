#!/usr/bin/env python3
"""Generate deterministic, line-framed POP3 command-sequence seeds."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def make_seeds(username: str, password: str) -> dict[str, bytes]:
    def transcript(*commands: str) -> bytes:
        return "".join(f"{command}\r\n" for command in commands).encode("ascii")

    return {
        "capability.pop3": transcript("CAPA", "NOOP", "QUIT"),
        "auth-failure.pop3": transcript(
            f"USER {username}", "PASS wrong-benchmark-password", "QUIT"
        ),
        "mailbox-read.pop3": transcript(
            f"USER {username}",
            f"PASS {password}",
            "STAT",
            "LIST",
            "UIDL",
            "RETR 1",
            "NOOP",
            "QUIT",
        ),
        "delete-reset.pop3": transcript(
            f"USER {username}",
            f"PASS {password}",
            "DELE 1",
            "RSET",
            "STAT",
            "QUIT",
        ),
        "unknown-command.pop3": transcript("X-INVALID", "CAPA", "QUIT"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic POP3 seeds")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--username", default="fuzzuser")
    parser.add_argument("--password", required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for name, data in sorted(make_seeds(args.username, args.password).items()):
        path = args.output_dir / name
        path.write_bytes(data)
        manifest.append(
            {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        )
    if args.manifest:
        args.manifest.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Generated {len(manifest)} deterministic POP3 seeds in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
