#!/usr/bin/env python3
"""用全新集群逐种子回放协议流程，并重复验证同一种子是否稳定。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from coverage_replay import replay_one


BUSINESS_STATES = {
    "simple-read-write": {20, 22, 10},
    "transaction-recovery": {41, 12, 10},
    "extended-query": {21, 22, 23, 10},
    "copy-in": {20, 30, 22, 10},
    "ssl-negotiation": {54, 10},
    "protocol-3.2": {10},
    "login-rejected": {40},
    "database-rejected": {41},
}


def transcript(record: dict[str, object]) -> list[dict[str, object]]:
    normalized = []
    for response in record.get("responses", []):
        normalized.append({
            key: value for key, value in response.items()
            if key != "server_alive"
        })
    return normalized


def states(record: dict[str, object]) -> set[int]:
    found: set[int] = set()
    for response in record.get("responses", []):
        for item in response.get("response_states", []):
            kind = item.get("type")
            state_id = {
                "R": 1 if item.get("auth_code") == "0" else 2,
                "Z": {"I": 10, "T": 11, "E": 12}.get(
                    str(item.get("transaction", ""))),
                "C": 20, "I": 20, "T": 21, "D": 22,
                "1": 23, "2": 23, "3": 23, "n": 23, "s": 23,
                "G": 30, "H": 30, "W": 30, "d": 30, "c": 30, "f": 30,
                "S": 51, "K": 52, "v": 53,
                "N": 54 if item.get("hex") == "4e" else 50,
            }.get(str(kind))
            if kind == "E":
                state_id = 40 if str(item.get("sqlstate", "")).startswith("28") else 41
            if state_id is not None:
                found.add(state_id)
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：seed_replay.py 结果目录", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    seeds = Path("/home/ubuntu/experiments/seeds")
    postgres = Path("/home/ubuntu/experiments/postgres-reference/bin/postgres")
    initdb = Path("/home/ubuntu/experiments/postgres-reference/bin/initdb")
    pg_ctl = Path("/home/ubuntu/experiments/postgres-reference/bin/pg_ctl")
    pg_isready = Path("/home/ubuntu/experiments/postgres-reference/bin/pg_isready")
    root.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    for seed in sorted(seeds.iterdir()):
        if not seed.is_file():
            continue
        record = replay_one(seed, postgres, initdb, pg_ctl, pg_isready,
                            root, 55432, 0.15)
        record["kind"] = "seed"
        records.append(record)

    stable_seed = seeds / "simple-read-write"
    stable_runs = [
        replay_one(stable_seed, postgres, initdb, pg_ctl, pg_isready,
                   root, 55432, 0.15)
        for _ in range(10)
    ]
    stable_transcripts = [transcript(item) for item in stable_runs]
    stable_match = all(item == stable_transcripts[0]
                       for item in stable_transcripts[1:])
    flow_results = {}
    for name, required in BUSINESS_STATES.items():
        matching = next((item for item in records
                         if Path(str(item["sample"])).name == name), None)
        observed = states(matching) if matching else set()
        flow_results[name] = {
            "passed": matching is not None
            and bool(matching.get("independently_replayed"))
            and required.issubset(observed),
            "required_state_ids": sorted(required),
            "observed_state_ids": sorted(observed),
        }

    report = {
        "endpoint": "tcp://127.0.0.1:55432",
        "reset_policy": "每个种子和重复轮次使用新临时目录并运行 initdb",
        "seed_count": len(records),
        "seed_replays_succeeded": sum(
            bool(item.get("independently_replayed")) for item in records
        ),
        "business_flows": flow_results,
        "stable_seed": stable_seed.name,
        "stable_repetitions": len(stable_runs),
        "stable_transcripts_match": stable_match,
        "stable_transcripts": stable_transcripts,
        "seed_records": records,
        "stable_records": stable_runs,
    }
    (root / "seed-replay.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (root / "seed-transcripts.jsonl").open("w", encoding="utf-8") as out:
        for item in records:
            out.write(json.dumps({
                "seed": Path(str(item["sample"])).name,
                "sha256": item["sha256"],
                "responses": transcript(item),
                "server_exit": item.get("server_exit"),
            }, ensure_ascii=False) + "\n")
    print(json.dumps({
        "seeds": len(records),
        "replays_succeeded": report["seed_replays_succeeded"],
        "business_flows_passed": sum(
            bool(item["passed"]) for item in flow_results.values()
        ),
        "stable_repetitions": len(stable_runs),
        "stable_transcripts_match": stable_match,
    }, ensure_ascii=False))
    return 0 if (
        report["seed_replays_succeeded"] == len(records)
        and all(item["passed"] for item in flow_results.values())
        and stable_match
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
