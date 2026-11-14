#!/usr/bin/env python3
from __future__ import annotations
"""Replay AFLNet queue entries against an isolated gcov build."""
from pathlib import Path
import os
import re
import socket
import subprocess
import sys
import time

WORKDIR = Path("/home/ubuntu/experiments")
GCOV_DIR = WORKDIR / "inspircd-gcov"
PORT = 6667


def summary() -> tuple[str, str]:
    result = subprocess.run(
        ["gcovr", "-r", str(GCOV_DIR), "-s"], cwd=GCOV_DIR,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True,
    ).stdout
    line = re.search(r"^lines:\s*([0-9.]+)%\s*\(([0-9]+) out of ([0-9]+)\)", result, re.M)
    branch = re.search(r"^branches:\s*([0-9.]+)%\s*\(([0-9]+) out of ([0-9]+)\)", result, re.M)
    if not line or not branch:
        raise RuntimeError(f"could not parse gcovr summary:\n{result}")
    return f"{line.group(1)},{line.group(2)}", f"{branch.group(1)},{branch.group(2)}"


def replay_one(target: Path, config: Path, payload: bytes, log_path: Path) -> None:
    clean_env = {**os.environ, "INSPIRCD_DATA_DIR": str(GCOV_DIR / "run" / "data")}
    subprocess.run(["bash", "/workspace/clean.sh"], env=clean_env, check=True)
    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            [str(target), "-F", "-L", "-P", "-c", str(config)],
            cwd=GCOV_DIR, stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "ASAN_OPTIONS": "abort_on_error=1:symbolize=0:detect_leaks=0"},
        )
        client = None
        try:
            deadline = time.monotonic() + 10
            while True:
                if proc.poll() is not None:
                    raise RuntimeError(f"gcov server exited {proc.returncode}; see {log_path}")
                try:
                    probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
                    probe.close()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"gcov server did not bind TCP/{PORT}; see {log_path}")
                    time.sleep(0.05)
            client = socket.create_connection(("127.0.0.1", PORT), timeout=3)
            client.sendall(payload)
            client.settimeout(0.15)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    if not client.recv(65536):
                        break
                except socket.timeout:
                    break
                except OSError:
                    break
        finally:
            if client is not None:
                client.close()
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: coverage_replay.py FUZZ_RESULT_DIR [SKIPCOUNT]", file=sys.stderr)
        return 2
    fuzz_dir = Path(sys.argv[1])
    skipcount = int(sys.argv[2]) if len(sys.argv) == 3 else 5
    if skipcount < 1:
        raise SystemExit("SKIPCOUNT must be positive")
    queue = fuzz_dir / "queue"
    target = GCOV_DIR / "run" / "bin" / "inspircd"
    config = GCOV_DIR / "run" / "conf" / "inspircd.conf"
    if not queue.is_dir() or not target.is_file():
        raise SystemExit("AFLNet queue or gcov target is missing")
    if GCOV_DIR.resolve() != Path("/home/ubuntu/experiments/inspircd-gcov").resolve():
        raise SystemExit(f"refusing to reset counters outside isolated gcov build: {GCOV_DIR}")

    cases = sorted(path for path in queue.glob("id:*") if path.is_file())
    if not cases:
        raise SystemExit(f"no queue cases in {queue}")
    for counter in GCOV_DIR.rglob("*.gcda"):
        counter.unlink()

    csv_path = fuzz_dir / "cov_over_time.csv"
    csv_path.write_text("Time,l_per,l_abs,b_per,b_abs\n", encoding="ascii")
    log_path = fuzz_dir / "coverage-server.log"
    last_sample = None
    for index, case in enumerate(cases, 1):
        replay_one(target, config, case.read_bytes(), log_path)
        last_sample = case
        if index % skipcount == 0 or index == len(cases):
            lines, branches = summary()
            stamp = int(time.time())
            with csv_path.open("a", encoding="ascii") as csv_file:
                csv_file.write(f"{stamp},{lines},{branches}\n")

    report_dir = fuzz_dir / "cov_html"
    report_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["gcovr", "-r", str(GCOV_DIR), "--html", "--html-details",
         "-o", str(report_dir / "index.html")],
        cwd=GCOV_DIR, check=True,
    )
    print(f"Replayed {len(cases)} queue cases. CSV: {csv_path}")
    print(f"HTML report: {report_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
