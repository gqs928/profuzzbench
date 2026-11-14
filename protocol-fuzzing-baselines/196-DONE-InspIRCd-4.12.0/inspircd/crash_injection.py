#!/usr/bin/env python3
"""Test AFLNet crash recording and independent replay using test-only injection."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time


WORKDIR = Path(os.environ.get("WORKDIR", "/home/ubuntu/experiments"))
AFLNET = Path(os.environ.get("AFLNET", "/home/ubuntu/aflnet"))
TARGET_DIR = Path(os.environ.get("TARGET_DIR", str(WORKDIR / "inspircd-afl")))
TARGET = Path(os.environ.get("TARGET", str(TARGET_DIR / "run/bin/inspircd")))
CONFIG = Path(os.environ.get("CONFIG", str(TARGET_DIR / "run/conf/inspircd.conf")))
DICT = Path(os.environ.get("DICT", str(WORKDIR / "irc.dict")))
CLEAN_SCRIPT = Path(os.environ.get("CLEAN_SCRIPT", "/workspace/clean.sh"))
SHIM_SOURCE = Path(os.environ.get("SHIM_SOURCE", "/workspace/crash_injection_shim.c"))
PORT = int(os.environ.get("PORT", "6667"))
DATA_DIR = Path(os.environ.get("INSPIRCD_DATA_DIR", str(TARGET_DIR / "run/data")))
SEED = b"PING X\r\n"
TRIGGER = b"PING Y\r\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def crash_count(stats_file: Path) -> int:
    if not stats_file.is_file():
        return 0
    match = re.search(
        r"^unique_crashes\s*:\s*(\d+)\s*$",
        stats_file.read_text(errors="replace"),
        re.M,
    )
    return int(match.group(1)) if match else 0


def log_tail(path: Path, lines: int = 50) -> str:
    if not path.is_file():
        return "(log not created)"
    return "\n".join(path.read_text(errors="replace").splitlines()[-lines:])


def stop_process(process: subprocess.Popen[bytes] | None, wait_seconds: float = 8) -> int | None:
    if process is None:
        return None
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            return process.wait(timeout=wait_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
    return process.wait()


def prepare_environment(shim: Path) -> dict[str, str]:
    return {
        **os.environ,
        "ASAN_OPTIONS": "abort_on_error=1:symbolize=0:detect_leaks=0:detect_stack_use_after_return=1",
        "INSPIRCD_DATA_DIR": str(DATA_DIR),
        "LD_PRELOAD": str(shim),
        "AFL_NO_AFFINITY": "1",
    }


def check_prerequisites(out_dir: Path, timeout_seconds: int) -> None:
    require(timeout_seconds >= 30, "fuzz timeout must be at least 30 seconds")
    require((AFLNET / "afl-fuzz").is_file(), f"AFLNet binary missing: {AFLNET / 'afl-fuzz'}")
    require((AFLNET / "aflnet-replay").is_file(), f"AFLNet replay tool missing: {AFLNET / 'aflnet-replay'}")
    require(TARGET.is_file() and os.access(TARGET, os.X_OK), f"instrumented target missing/not executable: {TARGET}")
    require(CONFIG.is_file() and DICT.is_file() and CLEAN_SCRIPT.is_file(), "config, dictionary, or clean script missing")
    require(SHIM_SOURCE.is_file(), f"fault-injection shim missing: {SHIM_SOURCE}")
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
            raise RuntimeError(f"TCP/{PORT} is already occupied; refusing to fuzz the wrong service")
    except OSError:
        pass


def run_test(out_dir: Path, timeout_seconds: int) -> dict[str, object]:
    fuzzer_log = out_dir / "fuzzer.log"
    replay_log = out_dir / "replay.log"
    server_log = out_dir / "replay-server.log"
    stats_file = out_dir / "fuzzer_stats"
    fuzzer: subprocess.Popen[bytes] | None = None
    replay_server: subprocess.Popen[bytes] | None = None
    fuzzer_status: int | None = None
    replay_status: int | None = None
    server_status: int | None = None

    try:
        with tempfile.TemporaryDirectory(prefix="inspircd-crash-injection-") as temp_name:
            temp_dir = Path(temp_name)
            shim = temp_dir / "libirc-crash-injection.so"
            input_dir = temp_dir / "seed"
            input_dir.mkdir()
            (input_dir / "seed-one-bit-neighbor").write_bytes(SEED)

            compiled = subprocess.run(
                ["cc", "-shared", "-fPIC", "-O2", "-Wall", "-Wextra", str(SHIM_SOURCE), "-o", str(shim), "-ldl"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            require(compiled.returncode == 0, f"could not compile test shim:\n{compiled.stdout}")
            env = prepare_environment(shim)
            subprocess.run(["bash", str(CLEAN_SCRIPT)], env=env, check=True)

            # No -d: keep AFL's deterministic bit-flip stage enabled. The valid
            # PING seed produces a PONG state; flipping X -> Y reaches the shim.
            fuzz_command = [
                str(AFLNET / "afl-fuzz"), "-i", str(input_dir), "-x", str(DICT), "-o", str(out_dir),
                "-N", f"tcp://127.0.0.1/{PORT}", "-P", "IRC", "-E", "-q", "3", "-s", "3",
                "-R", "-K", "-D", "100000", "-W", "100", "-w", "100000", "-m", "none",
                "-t", "5000+", "-c", str(CLEAN_SCRIPT), str(TARGET), "-F", "-L", "-P", "-c", str(CONFIG),
            ]
            with fuzzer_log.open("wb") as log:
                fuzzer = subprocess.Popen(
                    fuzz_command, cwd=TARGET_DIR, env=env, stdout=log, stderr=subprocess.STDOUT
                )
                deadline = time.monotonic() + timeout_seconds
                while time.monotonic() < deadline:
                    if fuzzer.poll() is not None:
                        break
                    if crash_count(stats_file) > 0:
                        # Let AFLNet finish writing the sample and final stats.
                        time.sleep(1.0)
                        break
                    time.sleep(0.5)
                else:
                    stop_process(fuzzer)
                    fuzzer = None
                    raise RuntimeError(
                        f"no controlled crash found within {timeout_seconds}s; fuzzer log tail:\n"
                        f"{log_tail(fuzzer_log)}"
                    )
                fuzzer_status = stop_process(fuzzer)
                fuzzer = None

            require(crash_count(stats_file) > 0, f"AFLNet recorded no crash; log tail:\n{log_tail(fuzzer_log)}")
            crash_dir = out_dir / "replayable-crashes"
            candidates = sorted(path for path in crash_dir.glob("id:*") if path.is_file())
            # AFLNet stores each packet as a 32-bit length followed by payload.
            # Require the injected trigger in the recorded packet, not just any crash.
            sample = next((path for path in candidates if TRIGGER in path.read_bytes()), None)
            require(sample is not None, f"no recorded crash sample contains trigger {TRIGGER!r}; see {crash_dir}")

            subprocess.run(["bash", str(CLEAN_SCRIPT)], env=env, check=True)
            with server_log.open("wb") as log:
                replay_server = subprocess.Popen(
                    [str(TARGET), "-F", "-L", "-P", "-c", str(CONFIG)],
                    cwd=TARGET_DIR,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                ready_deadline = time.monotonic() + 15
                while time.monotonic() < ready_deadline:
                    if replay_server.poll() is not None:
                        raise RuntimeError(
                            f"fresh server exited before replay ({replay_server.returncode}); see {server_log}"
                        )
                    try:
                        with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError(f"fresh server did not bind TCP/{PORT}; see {server_log}")

                replay = subprocess.run(
                    [str(AFLNET / "aflnet-replay"), str(sample), "IRC", str(PORT), "100", "100000"],
                    cwd=TARGET_DIR,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=15,
                )
                replay_status = replay.returncode
                replay_log.write_text(replay.stdout, encoding="utf-8", errors="replace")
                try:
                    server_status = replay_server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_status = None
                replay_server = None

            server_text = server_log.read_text(errors="replace")
            require(
                server_status == -signal.SIGABRT,
                f"independent replay did not end the fresh server with SIGABRT (status={server_status}); "
                f"see {server_log}",
            )
            require(
                "CONTROLLED_IRC_CRASH_TRIGGERED" in server_text,
                f"test-shim trigger marker absent from {server_log}",
            )
            require(replay_status == 0, f"aflnet-replay exited {replay_status}; see {replay_log}")

            return {
                "test_only_fault_injection": True,
                "seed_hex": SEED.hex(" "),
                "controlled_trigger_hex": TRIGGER.hex(" "),
                "crash_sample": str(sample),
                "fuzzer_exit_status": fuzzer_status,
                "unique_crashes": crash_count(stats_file),
                "replay_exit_status": replay_status,
                "replay_server_returncode": server_status,
                "expected_signal": "SIGABRT",
                "trigger_marker_observed": True,
                "fuzzer_log": str(fuzzer_log),
                "replay_log": str(replay_log),
                "server_log": str(server_log),
            }
    finally:
        if fuzzer is not None:
            stop_process(fuzzer)
        if replay_server is not None and replay_server.poll() is None:
            replay_server.terminate()
            try:
                replay_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                replay_server.kill()
                replay_server.wait()


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: crash_injection.py OUTPUT_DIR [FUZZ_TIMEOUT_SECONDS]", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1]).resolve()
    timeout_seconds = int(sys.argv[2]) if len(sys.argv) == 3 else 180
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"FAIL: output directory must be empty: {out_dir}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "crash-injection.json"
    try:
        check_prerequisites(out_dir, timeout_seconds)
        report = run_test(out_dir, timeout_seconds)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("PASS: AFLNet recorded the controlled test abort and independent replay reproduced SIGABRT.")
        print(f"crash_sample={report['crash_sample']}")
        print(f"evidence={out_dir}")
        return 0
    except Exception as exc:
        report_path.write_text(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2) + "\n", encoding="utf-8")
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
