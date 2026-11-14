#!/usr/bin/env python3
"""用真实 IMAP 客户端步骤验证参考版和插桩版服务端。"""

from __future__ import annotations

import argparse
import csv
import json
import socket
import sys
import time
from pathlib import Path

from imap_tools import (
    ImapError,
    append_response,
    command_response,
    connect_imap,
    response_states,
    start_server,
    stop_server,
    tagged_status,
    wait_until_ready,
)

USER = "fuzzuser"
PASSWORD = "dovecot-benchmark-pass"


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ImapError(description)


def run_one(variant: str, round_number: int, log_dir: Path) -> dict[str, object]:
    started = time.monotonic()
    process = start_server(variant, log_dir / f"{variant}-{round_number:02d}.log")
    all_states: list[int] = []
    commands = 0
    try:
        wait_until_ready(process)

        sock, reader, greeting = connect_imap()
        try:
            require(greeting.startswith(b"* OK"), f"欢迎行异常：{greeting!r}")
            all_states.extend(response_states([greeting]))
            response, lines = command_response(sock, reader, "N001", "CAPABILITY")
            require(tagged_status(lines, "N001") == "OK", "CAPABILITY 未成功")
            require(any(b"CAPABILITY" in line.upper() for line in lines), "缺少能力响应")
            all_states.extend(response_states(lines))
            commands += 1

            response, lines = command_response(
                sock, reader, "N002", "LOGIN fuzzuser incorrect-password"
            )
            require(tagged_status(lines, "N002") == "NO", "错误密码没有得到 NO")
            all_states.extend(response_states(lines))
            commands += 1
        finally:
            reader.close()
            sock.close()

        sock, reader, greeting = connect_imap()
        try:
            require(greeting.startswith(b"* OK"), "成功登录会话未收到正常欢迎行")
            all_states.extend(response_states([greeting]))
            steps: list[tuple[str, str]] = [
                ("P001", "CAPABILITY"),
                ("P002", f"LOGIN {USER} {PASSWORD}"),
                ("P003", 'LIST "" "*"'),
                ("P004", 'LSUB "" "*"'),
                ("P005", "SELECT INBOX"),
                ("P006", "STATUS INBOX (MESSAGES UNSEEN UIDNEXT UIDVALIDITY)"),
                ("P007", "SEARCH ALL"),
                ("P008", "FETCH 1 (UID FLAGS BODY.PEEK[HEADER])"),
            ]
            for tag, command in steps:
                _, lines = command_response(sock, reader, tag, command)
                status = tagged_status(lines, tag)
                require(status == "OK", f"{command} 返回 {status}")
                all_states.extend(response_states(lines))
                commands += 1

            message = (
                b"From: append@example.invalid\r\n"
                b"To: fuzzuser@localhost\r\n"
                b"Subject: smoke append\r\n\r\n"
                b"Stable APPEND payload.\r\n"
            )
            _, lines = append_response(sock, reader, "P009", message)
            require(tagged_status(lines, "P009") == "OK", "APPEND 未成功")
            all_states.extend(response_states(lines))
            commands += 1

            for tag, command in [
                ("P010", "SEARCH ALL"),
                ("P011", "FETCH 2 (UID FLAGS BODY.PEEK[HEADER])"),
                ("P012", "STORE 2 +FLAGS (\\Seen \\Deleted)"),
                ("P013", "EXPUNGE"),
                ("P014", "STATUS INBOX (MESSAGES UNSEEN)"),
                ("P015", "NOOP"),
                ("P016", "LOGOUT"),
            ]:
                _, lines = command_response(sock, reader, tag, command)
                status = tagged_status(lines, tag)
                require(status == "OK", f"{command} 返回 {status}")
                all_states.extend(response_states(lines))
                commands += 1
        finally:
            reader.close()
            sock.close()

        return {
            "variant": variant,
            "round": round_number,
            "status": "PASS",
            "commands": commands,
            "response_states": json.dumps(all_states),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "error": "",
        }
    except (OSError, ImapError, socket.timeout) as exc:
        return {
            "variant": variant,
            "round": round_number,
            "status": "FAIL",
            "commands": commands,
            "response_states": json.dumps(all_states),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "error": str(exc),
        }
    finally:
        stop_server(process)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dovecot IMAP 真客户端流程冒烟验证")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("repetitions", type=int, nargs="?", default=10)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for variant in ("reference", "afl"):
        for round_number in range(1, args.repetitions + 1):
            row = run_one(variant, round_number, args.output_dir)
            records.append(row)
            print(
                f"{variant} 第 {round_number}/{args.repetitions} 轮："
                f"{row['status']}，命令数={row['commands']}，耗时={row['elapsed_seconds']} 秒"
            )
            if row["status"] != "PASS":
                print(f"失败原因：{row['error']}", file=sys.stderr)

    fieldnames = [
        "variant",
        "round",
        "status",
        "commands",
        "response_states",
        "elapsed_seconds",
        "error",
    ]
    with (args.output_dir / "protocol-smoke.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    (args.output_dir / "protocol-smoke.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if records and all(row["status"] == "PASS" for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
