#!/usr/bin/env python3
"""对照参考版与 AFL/ASan 版的真实 SIP/TCP 业务流程并重复复位。"""

from __future__ import annotations

import hashlib
import json
import pathlib
import socket
import subprocess
import sys
import time

from sip_tools import (
    SIPReader,
    port_is_closed,
    response_code,
    smoke_flow,
    start_server,
    stop_server,
    wait_listener,
    wait_server_ready,
)


def read_final(reader: SIPReader, timeout: float = 5.0) -> list[int]:
    statuses = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = reader.read_one(deadline - time.monotonic())
        if message is None:
            break
        code = response_code(message)
        if code is not None:
            statuses.append(code)
            if code >= 200:
                return statuses
    raise TimeoutError(f"没有收到 SIP 最终响应；已收到：{statuses}")


def run_one(variant: str, index: int, output: pathlib.Path) -> dict:
    run_id = "same-input"
    log_path = output / "server-logs" / f"{run_id}.log"
    result = {
        "variant": variant,
        "iteration": index,
        "pid": None,
        "startup_seconds": None,
        "options": [],
        "register": [],
        "invite": [],
        "cancel": [],
        "server_exit_code": None,
        "port_released": False,
        "exception": None,
    }
    process = None
    log_file = None
    connection = None
    try:
        process, log_file = start_server(variant, log_path)
        result["pid"] = process.pid
        startup_started = time.monotonic()
        wait_listener(process)
        wait_server_ready(variant)
        result["startup_seconds"] = round(time.monotonic() - startup_started, 4)
        connection = socket.create_connection(("127.0.0.1", 5060), timeout=3)
        reader = SIPReader(connection)
        flow = smoke_flow(run_id)
        result["request_sha256"] = {
            name: hashlib.sha256(data).hexdigest() for name, data in flow.items()
        }

        connection.sendall(flow["options"])
        result["options"] = read_final(reader)
        connection.sendall(flow["register"])
        result["register"] = read_final(reader)
        connection.sendall(flow["invite"])
        invite_deadline = time.monotonic() + 4.0
        while time.monotonic() < invite_deadline:
            message = reader.read_one(invite_deadline - time.monotonic())
            if message is None:
                break
            code = response_code(message)
            if code is not None:
                result["invite"].append(code)
                if 100 <= code < 200:
                    break
                if code >= 200:
                    break
        connection.sendall(flow["cancel"])
        cancel_deadline = time.monotonic() + 5.0
        while time.monotonic() < cancel_deadline:
            try:
                message = reader.read_one(cancel_deadline - time.monotonic())
            except socket.timeout:
                continue
            if message is None:
                break
            code = response_code(message)
            if code is not None:
                result["cancel"].append(code)
                if 200 in result["cancel"] and 487 in result["cancel"]:
                    break
    except Exception as error:  # 每轮保存错误，报告据此给出明确失败原因。
        result["exception"] = f"{type(error).__name__}: {error}"
    finally:
        if connection is not None:
            connection.close()
        if process is not None:
            result["server_exit_code"] = stop_server(process)
        if log_file is not None:
            log_file.close()
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not port_is_closed():
            time.sleep(0.05)
        result["port_released"] = port_is_closed()
        subprocess.run(["/workspace/clean.sh"], check=False)

    final_codes = result["options"] + result["register"] + result["cancel"]
    result["passed"] = (
        result["exception"] is None
        and 200 in result["options"]
        and 200 in result["register"]
        and any(100 <= code < 200 for code in result["invite"])
        and 200 in result["cancel"]
        and 487 in result["cancel"]
        and result["port_released"]
        and result["server_exit_code"] in (0, -15, -9)
    )
    result["final_response_codes"] = final_codes
    return result


def main() -> int:
    output = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/protocol-smoke")
    repetitions = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    output.mkdir(parents=True, exist_ok=True)
    sessions = []
    for variant in ("reference", "afl"):
        for index in range(1, repetitions + 1):
            row = run_one(variant, index, output)
            sessions.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)

    transcripts = {
        variant: [
            {
                key: row[key]
                for key in ("options", "register", "invite", "cancel")
            }
            for row in sessions
            if row["variant"] == variant
        ]
        for variant in ("reference", "afl")
    }
    all_same = all(
        len({json.dumps(row, sort_keys=True) for row in rows}) == 1
        for rows in transcripts.values()
    )
    cross_match = transcripts["reference"] == transcripts["afl"]
    request_sets = [row.get("request_sha256") for row in sessions]
    same_input = len({json.dumps(row, sort_keys=True) for row in request_sets}) == 1
    canonical = json.dumps(transcripts["reference"][0] if transcripts["reference"] else {},
                           sort_keys=True, separators=(",", ":"))
    transcript_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    report = {
        "repetitions_per_variant": repetitions,
        "sessions": sessions,
        "all_sessions_passed": all(row["passed"] for row in sessions),
        "same_transcript_within_each_variant": all_same,
        "same_exact_requests_across_all_runs": same_input,
        "reference_and_afl_transcripts_match": cross_match,
        "transcript_sha256": transcript_hash,
        "expected_business_flow": {
            "options_final": 200,
            "register_final": 200,
            "invite_provisional": "1xx",
            "cancel_final": [200, 487],
        },
    }
    (output / "protocol-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "sessions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sessions),
        encoding="utf-8",
    )
    summary = {
        "repetitions_per_variant": repetitions,
        "transcript_sha256": transcript_hash,
        "all_sessions_passed": report["all_sessions_passed"],
        "same_transcript_within_each_variant": all_same,
        "same_exact_requests_across_all_runs": same_input,
        "reference_and_afl_transcripts_match": cross_match,
    }
    (output / "reset-check.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (
        len(sessions) == repetitions * 2
        and report["all_sessions_passed"]
        and all_same
        and same_input
        and cross_match
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
