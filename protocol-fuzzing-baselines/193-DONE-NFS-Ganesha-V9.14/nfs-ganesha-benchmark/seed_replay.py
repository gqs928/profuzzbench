#!/usr/bin/env python3
"""在独立服务进程中回放 RPC 种子，并记录可复查的状态序列。"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time

import nfs_rpc
from nfs_rpc import MOUNT_PORT, NFS_PORT


PREFIXES = {
    "reference": "GANESHA_REFERENCE",
    "afl": "GANESHA_AFL",
    "gcov": "GANESHA_GCOV",
}


def response_state(payload: bytes) -> int:
    """与 NFS 状态适配器使用相同的分层状态编码。"""
    if len(payload) < 12:
        return 0x40000
    if int.from_bytes(payload[4:8], "big") != 1:
        return 0x40000
    reply_status = int.from_bytes(payload[8:12], "big")
    if reply_status == 1:
        return 0x30000 | int.from_bytes(payload[12:16], "big")
    if reply_status != 0 or len(payload) < 24:
        return 0x40000
    verifier = int.from_bytes(payload[16:20], "big")
    offset = 20 + ((verifier + 3) & ~3)
    if offset + 8 > len(payload):
        return 0x40000
    accepted = int.from_bytes(payload[offset : offset + 4], "big")
    if accepted:
        return 0x20000 | accepted
    return 0x10000 | int.from_bytes(payload[offset + 4 : offset + 8], "big")


def target_env(variant: str, diagnostic_log: pathlib.Path) -> tuple[list[str], dict[str, str]]:
    prefix = PREFIXES[variant]
    install = pathlib.Path(os.environ[f"{prefix}_PREFIX"])
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(
        str(p)
        for p in (
            install / "lib",
            install / "lib64",
            install / "lib/ganesha",
            install / "lib/x86_64-linux-gnu",
            install / "lib/x86_64-linux-gnu/ganesha",
        )
    )
    return [
        str(install / "bin/ganesha.nfsd"),
        "-F",
        "-f",
        "/workspace/ganesha.conf",
        "-p",
        "/tmp/ganesha.pid",
        "-L",
        str(diagnostic_log),
        "-N",
        "NIV_CRIT",
    ], env


def stop(process: subprocess.Popen, log_file) -> int | None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    log_file.close()
    return process.returncode


def start(variant: str, label: str, output: pathlib.Path):
    log_path = output / f"server-{label}.log"
    diagnostic_log = output / f"ganesha-{label}.log"
    diagnostic_log.unlink(missing_ok=True)
    command, env = target_env(variant, diagnostic_log)
    log_file = log_path.open("wb")
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stop(process, log_file)
            raise RuntimeError(
                f"Ganesha 启动失败，日志见 {log_path} 与 {diagnostic_log}: "
                + log_path.read_text(errors="replace")[-5000:]
            )
        try:
            with socket.create_connection(("127.0.0.1", nfs_rpc.NFS_PORT), timeout=0.2):
                return process, log_file, log_path
        except OSError:
            time.sleep(0.1)
    stop(process, log_file)
    raise RuntimeError(f"Ganesha 启动超时，日志见 {log_path}")


def replay_one(seed: pathlib.Path, variant: str, label: str, output: pathlib.Path) -> dict:
    process, log_file, log_path = start(variant, label, output)
    states = []
    target_port = MOUNT_PORT if seed.name == "mount-root.bin" else NFS_PORT
    try:
        with socket.create_connection(("127.0.0.1", target_port), timeout=2) as sock:
            sock.settimeout(1.0)
            for index, wire in enumerate(nfs_rpc.split_records(seed.read_bytes()), start=1):
                sock.sendall(wire)
                try:
                    _, payload = nfs_rpc.receive_record(sock)
                    states.append({"request": index, "state": response_state(payload)})
                except (socket.timeout, ConnectionError, ValueError) as error:
                    states.append(
                        {
                            "request": index,
                            "state": None,
                            "transport": type(error).__name__,
                        }
                    )
                    break
        time.sleep(0.1)
        return_code = process.poll()
        log_size = log_path.stat().st_size if log_path.exists() else 0
        return {
            "seed": seed.name,
            "seed_sha256": hashlib.sha256(seed.read_bytes()).hexdigest(),
            "variant": variant,
            "target_port": target_port,
            "server_command": target_env(variant, output / f"ganesha-{label}.log")[0],
            "response_states": states,
            "server_exit_before_cleanup": return_code,
            "server_abnormal_exit": return_code is not None and return_code < 0,
            "server_log": str(log_path),
            "ganesha_diagnostic_log": str(output / f"ganesha-{label}.log"),
            "server_log_bytes": log_size,
        }
    finally:
        stop(process, log_file)


def main() -> int:
    seeds = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/seeds")
    output = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "/results/seed-replay")
    repeat = int(sys.argv[3] if len(sys.argv) > 3 else "10")
    variant = sys.argv[4] if len(sys.argv) > 4 else "reference"
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(seeds.glob("*.bin"))
    if not files:
        raise SystemExit(f"种子目录为空：{seeds}")

    # 所有种子至少回放一次，并对有先后关系的文件操作会话重复十次。
    causal = next((p for p in files if p.name == "create-lookup-readdir-remove.bin"), None)
    if causal is None or repeat < 10:
        raise SystemExit("缺少状态会话种子或重复次数小于 10")
    plan = [(seed, 1) for seed in files]
    plan += [(causal, attempt) for attempt in range(2, repeat + 1)]

    results = []
    for seed, attempt in plan:
        label = f"{seed.stem}-{attempt:02d}"
        results.append(replay_one(seed, variant, label, output))

    repeats = [item for item in results if item["seed"] == causal.name]
    stable = {
        json.dumps(item["response_states"], sort_keys=True) for item in repeats
    }
    if len(stable) != 1:
        raise RuntimeError("同一状态操作种子十次回放的协议状态序列不一致")

    report = {
        "variant": variant,
        "runs": len(results),
        "causal_seed_repetitions": len(repeats),
        "causal_seed_sha256": hashlib.sha256(causal.read_bytes()).hexdigest(),
        "causal_state_sequence_stable": True,
        "sessions": results,
    }
    (output / "seed-replay.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"通过：{len(files)} 个种子均已回放；同一状态操作种子重复 {len(repeats)} 次，"
        "RPC/NFS 状态序列一致"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
