#!/usr/bin/env python3
"""从 AFLNet 越过初始校准后计时，并保存可核对的运行参数。"""

from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import sys
import time


def stats(path: pathlib.Path) -> dict[str, str]:
    values = {}
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
    return values


def main() -> int:
    seconds = int(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    command = ["/home/ubuntu/aflnet/afl-fuzz", *sys.argv[3:]]
    output.mkdir(parents=True, exist_ok=True)
    log_path = output.parent / "aflnet.log"
    stats_path = output / "fuzzer_stats"
    record_path = output.parent / "run-parameters.json"
    record_path.unlink(missing_ok=True)
    input_index = sys.argv[3:].index("-i") + 4
    input_dir = pathlib.Path(sys.argv[input_index])
    initial_seed_count = sum(1 for _ in input_dir.glob("*.bin"))
    if initial_seed_count == 0:
        raise RuntimeError(f"AFLNet 初始语料为空：{input_dir}")
    run_record = {
        "duration_seconds": seconds,
        "command": command,
        "initial_seed_count": initial_seed_count,
        "AFLNET_commit": os.environ.get("AFLNET_REF"),
        "protocol": "NFS",
        "network_target": "tcp://127.0.0.1/12049",
        "state_aware": True,
        "region_mutation": True,
        "server_cleanup_hook": "/workspace/clean.sh",
        "server_process_restarted_per_testcase": True,
    }
    launch_epoch = int(time.time())
    with log_path.open("wb") as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        started = None
        next_status = time.monotonic()
        startup_deadline = time.monotonic() + 600
        try:
            while started is None:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"AFLNet 在进入模糊阶段前退出，代码={process.returncode}；日志见 {log_path}"
                    )
                current_stats = stats(stats_path)
                # 用当前进程的队列推进记录识别正式变异，避免依赖延迟刷新的终端日志。
                fuzzing_started = (
                    int(current_stats.get("start_time", "0")) >= launch_epoch - 5
                    and int(current_stats.get("execs_done", "0")) >= initial_seed_count
                    and int(current_stats.get("paths_total", "0")) >= initial_seed_count
                    and (
                        int(current_stats.get("cur_path", "0")) > 0
                        or int(current_stats.get("cycles_done", "0")) > 0
                        or int(current_stats.get("paths_total", "0")) > initial_seed_count
                    )
                )
                if fuzzing_started:
                    started = time.monotonic()
                    run_record["fuzz_started_utc"] = time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    )
                    run_record["fuzz_timer_trigger"] = "当前进程 fuzzer_stats 队列推进"
                    run_record["fuzzer_stats_at_start"] = current_stats
                    record_path.write_text(
                        json.dumps(run_record, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    print("AFLNet 已越过初始校准，开始计满模糊时长", flush=True)
                    break
                if time.monotonic() > startup_deadline:
                    raise RuntimeError(f"AFLNet 初始校准超过 600 秒；日志见 {log_path}")
                time.sleep(0.2)

            while process.poll() is None and time.monotonic() - started < seconds:
                current = time.monotonic()
                if current >= next_status:
                    current_stats = stats(stats_path)
                    print(
                        "运行中："
                        f"execs={current_stats.get('execs_done', '?')}，"
                        f"队列={current_stats.get('paths_total', '?')}，"
                        f"崩溃={current_stats.get('unique_crashes', '?')}",
                        flush=True,
                    )
                    next_status = current + 60
                time.sleep(min(1.0, max(0.05, seconds - (current - started))))

            if process.poll() is None:
                run_record["fuzz_finished_utc"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                )
                run_record["fuzz_elapsed_seconds"] = round(time.monotonic() - started, 3)
                run_record["fuzzer_stats_at_end"] = stats(stats_path)
                record_path.write_text(
                    json.dumps(run_record, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                    raise RuntimeError("AFLNet 收到 SIGINT 后 30 秒内没有退出")
            else:
                raise RuntimeError(f"AFLNet 在计时结束前退出，代码={process.returncode}")
        except BaseException:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGINT)
                    process.wait(timeout=10)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            raise

    run_record["fuzzer_exit_code"] = process.returncode
    run_record["fuzzer_stats_final"] = stats(stats_path)
    record_path.write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if process.returncode not in (0, -signal.SIGINT, 130):
        raise RuntimeError(f"AFLNet 退出代码异常：{process.returncode}")
    if run_record.get("fuzz_elapsed_seconds", 0) < seconds:
        raise RuntimeError("AFLNet 实际模糊阶段没有达到要求时长")
    print(
        f"AFLNet 实际模糊阶段 {run_record['fuzz_elapsed_seconds']:.1f} 秒，"
        f"退出代码 {process.returncode}；日志见 {log_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
