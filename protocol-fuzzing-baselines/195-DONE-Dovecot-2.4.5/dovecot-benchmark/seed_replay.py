#!/usr/bin/env python3
"""把同一 IMAP 会话从干净邮箱重复回放并比较响应状态序列。"""

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
    ImapReader,
    normalize_states,
    replay_data,
    start_server,
    stop_server,
    wait_until_ready,
)


def replay_once(variant: str, seed: Path, round_number: int, output: Path) -> dict[str, object]:
    started = time.monotonic()
    process = start_server(variant, output / f"{variant}-{seed.stem}-{round_number:02d}.log")
    result: dict[str, object] = {
        "variant": variant,
        "seed": seed.name,
        "round": round_number,
        "status": "FAIL",
        "commands": 0,
        "timeouts": 0,
        "response_bytes": 0,
        "response_states": "",
        "errors": "",
        "server_exit": "",
        "elapsed_seconds": 0,
    }
    try:
        wait_until_ready(process)
        sock = socket.create_connection(("127.0.0.1", 1143), timeout=12.0)
        sock.settimeout(12.0)
        reader = ImapReader(sock)
        try:
            summary = replay_data(sock, reader, seed.read_bytes())
            result.update(summary)
            result["response_states"] = normalize_states(summary)
            result["errors"] = "; ".join(summary["errors"])
            result["status"] = "PASS" if summary["timeouts"] == 0 and not summary["errors"] else "PARTIAL"
        finally:
            reader.close()
            sock.close()
    except (OSError, ImapError, socket.timeout) as exc:
        result["errors"] = str(exc)
    finally:
        result["server_exit"] = stop_server(process)
        result["elapsed_seconds"] = round(time.monotonic() - started, 4)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="重复回放同一种子并核对状态稳定性")
    parser.add_argument("seed", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--repeat", type=int, default=10)
    parser.add_argument("--variant", choices=("reference", "afl", "gcov"), default="afl")
    args = parser.parse_args()
    if not args.seed.is_file() or args.repeat < 1:
        parser.error("种子文件必须存在，重复次数必须大于零")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = [
        replay_once(args.variant, args.seed, round_number, args.output_dir)
        for round_number in range(1, args.repeat + 1)
    ]
    signatures = {str(row["response_states"]) for row in records}
    stable = len(signatures) == 1 and all(row["status"] == "PASS" for row in records)
    result = {
        "seed": args.seed.name,
        "variant": args.variant,
        "repetitions": args.repeat,
        "stable": stable,
        "signature_count": len(signatures),
        "records": records,
    }
    (args.output_dir / "seed-replay.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    fields = list(records[0]) if records else []
    with (args.output_dir / "seed-replay.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(
        f"种子 {args.seed.name}：{args.repeat} 次回放，"
        f"状态签名数={len(signatures)}，稳定={str(stable).lower()}"
    )
    return 0 if stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
