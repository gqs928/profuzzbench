#!/usr/bin/env python3
"""在全新 Ganesha 进程中独立回放 AFLNet 报告的崩溃和挂起候选。"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
import sys

from seed_replay import replay_one


def replayable_packets(path: pathlib.Path) -> bytes:
    """去掉 AFLNet 的本机端序回放长度前缀，还原 TCP 线缆数据。"""
    raw = path.read_bytes()
    offset = 0
    packets = []
    while offset < len(raw):
        if len(raw) - offset < 4:
            raise ValueError(f"AFLNet 回放文件长度前缀不完整：{path}")
        size = struct.unpack_from("=I", raw, offset)[0]
        offset += 4
        if size > len(raw) - offset:
            raise ValueError(f"AFLNet 回放文件包长度越界：{path}")
        packets.append(raw[offset : offset + size])
        offset += size
    return b"".join(packets)


def no_response(run: dict) -> bool:
    states = run.get("response_states", [])
    return not states or states[0].get("state") is None


def main() -> int:
    afl_out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/fuzz/aflnet")
    output = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "/results/anomaly-replay")
    repetitions = int(sys.argv[3] if len(sys.argv) > 3 else "10")
    if repetitions < 1:
        raise SystemExit("独立回放次数必须大于零")
    output.mkdir(parents=True, exist_ok=True)

    candidates = []
    for kind, directory in (
        ("crash", afl_out / "replayable-crashes"),
        ("hang", afl_out / "replayable-hangs"),
    ):
        if not directory.exists():
            continue
        for sample in sorted(directory.iterdir()):
            if not sample.is_file() or sample.name == "README.txt":
                continue
            candidates.append((kind, sample))

    reports = []
    for number, (kind, sample) in enumerate(candidates, start=1):
        wire = replayable_packets(sample)
        materialized = output / f"candidate-{number:03d}-{kind}.bin"
        materialized.write_bytes(wire)
        expected_signal_match = re.search(r",sig:(\d+),", sample.name)
        expected_signal = int(expected_signal_match.group(1)) if expected_signal_match else None
        runs = [
            replay_one(
                materialized,
                "afl",
                f"candidate-{number:03d}-{kind}-{attempt:02d}",
                output,
            )
            for attempt in range(1, repetitions + 1)
        ]
        signal_replays = sum(
            run.get("server_exit_before_cleanup") == -expected_signal
            for run in runs
        ) if expected_signal is not None else 0
        no_response_replays = sum(no_response(run) for run in runs)
        report = {
            "kind": kind,
            "sample": sample.name,
            "sample_sha256": hashlib.sha256(sample.read_bytes()).hexdigest(),
            "wire_sample": materialized.name,
            "wire_sha256": hashlib.sha256(wire).hexdigest(),
            "expected_signal": expected_signal,
            "independent_process_repetitions": repetitions,
            "matching_signal_replays": signal_replays,
            "no_response_replays": no_response_replays,
            "confirmed": signal_replays > 0 if kind == "crash" else no_response_replays > 0,
            "runs": runs,
        }
        reports.append(report)

    document = {
        "variant": "AFL-instrumented NFS-Ganesha",
        "independent_process_per_replay": True,
        "candidate_count": len(reports),
        "repetitions_per_candidate": repetitions,
        "candidates": reports,
    }
    (output / "ganesha-anomaly-replay.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    confirmed = sum(report["confirmed"] for report in reports)
    print(
        f"已对 {len(reports)} 个 Ganesha 异常候选各用新进程回放 {repetitions} 次；"
        f"可复现候选 {confirmed} 个，详情见 {output / 'ganesha-anomaly-replay.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
