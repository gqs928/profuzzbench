#!/usr/bin/env python3
"""Replay the same IRC business seed on ten fresh gcov server processes."""
from __future__ import annotations
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

WORKDIR = Path("/home/ubuntu/experiments")
GCOV_DIR = WORKDIR / "inspircd-gcov"
PORT = 6667


def replay(payload: bytes, run_dir: Path, number: int) -> tuple[bytes, list[int]]:
    target = GCOV_DIR / "run" / "bin" / "inspircd"
    config = GCOV_DIR / "run" / "conf" / "inspircd.conf"
    clean_env = {**os.environ, "INSPIRCD_DATA_DIR": str(GCOV_DIR / "run" / "data")}
    subprocess.run(["bash", "/workspace/clean.sh"], env=clean_env, check=True)
    log_file = (run_dir / f"run-{number:02d}.server.log").open("wb")
    process = subprocess.Popen(
        [str(target), "-F", "-L", "-P", "-c", str(config)],
        cwd=GCOV_DIR, stdout=log_file, stderr=subprocess.STDOUT,
        env={**os.environ, "ASAN_OPTIONS": "abort_on_error=1:symbolize=0:detect_leaks=0"},
    )
    client = None
    transcript = bytearray()
    try:
        deadline = time.monotonic() + 10
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"gcov target exited {process.returncode}; see run-{number:02d}.server.log")
            try:
                probe = socket.create_connection(("127.0.0.1", PORT), timeout=0.2)
                probe.close()
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"gcov target did not bind TCP/{PORT}")
                time.sleep(0.05)
        client = socket.create_connection(("127.0.0.1", PORT), timeout=3)
        client.settimeout(5)
        pending = bytearray()

        def wait_for(marker: bytes, command: str) -> None:
            deadline = time.monotonic() + 8
            while marker not in pending:
                if b" 451 " in pending:
                    raise RuntimeError(
                        f"server rejected {command!r} before registration; received 451"
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError(
                        f"timeout waiting for {marker!r} after {command!r}"
                    )
                client.settimeout(remaining)
                block = client.recv(65536)
                if not block:
                    raise RuntimeError(
                        f"server closed while waiting for {marker!r} after {command!r}"
                    )
                pending.extend(block)
                transcript.extend(block)
            end = pending.index(marker) + len(marker)
            del pending[:end]

        # Replay the same seed commands in order, but wait for protocol barriers.
        # In particular, do not send channel operations until numeric 001 confirms
        # that NICK/USER registration has completed on this fresh server process.
        commands = [line.decode("ascii") for line in payload.splitlines() if line]
        if len(commands) < 2 or not commands[0].upper().startswith("NICK ") \
                or not commands[1].upper().startswith("USER "):
            raise RuntimeError("channel-session seed must start with NICK then USER")

        markers = {
            "JOIN": b" 366 ",
            "TOPIC": b" TOPIC #bench :reproducible topic",
            "NAMES": b" 366 ",
            "WHO": b" 315 ",
            "PART": b" PART #bench",
            "PING": b" PONG ",
            "VERSION": b" 351 ",
        }
        try:
            for command in commands:
                client.sendall(command.encode("ascii") + b"\r\n")
                verb = command.split(None, 1)[0].upper()
                if verb == "USER":
                    wait_for(b" 001 ", command)
                elif verb in markers:
                    wait_for(markers[verb], command)
                elif verb == "QUIT":
                    break
        except (OSError, RuntimeError) as exc:
            (run_dir / "response.bin").write_bytes(transcript)
            codes_so_far = [int(code) for code in re.findall(rb" (?P<code>[0-9]{3}) ", transcript)]
            raise RuntimeError(
                f"run {number}: {exc}; response saved; numeric replies so far: {codes_so_far}"
            ) from exc

        data = bytes(transcript)
        (run_dir / "response.bin").write_bytes(data)
        codes = [int(code) for code in re.findall(rb" (?P<code>[0-9]{3}) ", data)]
        if 1 not in codes or 366 not in codes or 315 not in codes:
            raise RuntimeError(f"run {number}: missing expected IRC registration/channel replies: {codes}")
        return data, codes
    finally:
        if client is not None:
            client.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_file.close()


def gcov_summary() -> tuple[float, float]:
    output = subprocess.run(
        ["gcovr", "-r", str(GCOV_DIR), "-s"], cwd=GCOV_DIR,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True,
    ).stdout
    lines = re.search(r"^lines:\s*([0-9.]+)%", output, re.M)
    branches = re.search(r"^branches:\s*([0-9.]+)%", output, re.M)
    if not lines or not branches:
        raise RuntimeError(f"unable to parse gcovr summary:\n{output}")
    return float(lines.group(1)), float(branches.group(1))


def combined_gcda_hash() -> str:
    digest = hashlib.sha256()
    counters = sorted(GCOV_DIR.rglob("*.gcda"))
    for counter in counters:
        digest.update(counter.relative_to(GCOV_DIR).as_posix().encode())
        digest.update(counter.read_bytes())
    return digest.hexdigest()


def stable_response(data: bytes) -> bytes:
    # Numeric 003 reports server creation time, which can be generated at each
    # process start; preserve its code and normalize only that volatile text.
    normalized = []
    for line in data.splitlines():
        if re.search(rb"\s003\s", line):
            line = re.sub(rb"(\s003\s+\S+\s+:).*$", rb"\1<volatile-server-created>", line)
        normalized.append(line)
    return b"\r\n".join(normalized) + (b"\r\n" if normalized else b"")


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: repeatability.py OUTPUT_DIR [RUNS]", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    runs = int(sys.argv[2]) if len(sys.argv) == 3 else 10
    if runs < 2:
        raise SystemExit("RUNS must be at least 2")
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_path = WORKDIR / "in-irc" / "channel-session"
    seed = seed_path.read_bytes()
    (out_dir / "seed-channel-session.bin").write_bytes(seed)
    (out_dir / "replay-command.txt").write_text(
        "python3 /workspace/repeatability.py /results/repeatability 10\n"
        "Per run: inspircd-gcov/run/bin/inspircd -F -L -P -c "
        "/home/ubuntu/experiments/inspircd-gcov/run/conf/inspircd.conf\n",
        encoding="utf-8",
    )
    records = []
    for number in range(1, runs + 1):
        for counter in GCOV_DIR.rglob("*.gcda"):
            counter.unlink()
        run_dir = out_dir / f"run-{number:02d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        response, codes = replay(seed, run_dir, number)
        (run_dir / "response.bin").write_bytes(response)
        (run_dir / "replay-command.txt").write_text(
            f"fresh server + TCP/6667; send seed-channel-session.bin ({len(seed)} bytes)\n",
            encoding="utf-8",
        )
        raw_hash = hashlib.sha256(response).hexdigest()
        normalized_hash = hashlib.sha256(stable_response(response)).hexdigest()
        line_pct, branch_pct = gcov_summary()
        record = {
            "run": number,
            "states": ",".join(map(str, codes)),
            "response_sha256": normalized_hash,
            "raw_response_sha256": raw_hash,
            "line_coverage": line_pct,
            "branch_coverage": branch_pct,
            "gcda_sha256": combined_gcda_hash(),
        }
        records.append(record)
        print(f"run-{number:02d}: states={record['states']}; line/branch="
              f"{line_pct:.1f}/{branch_pct:.1f}; normalized_response_sha256={normalized_hash}")

    csv_path = out_dir / "repeatability.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    lines = [row["line_coverage"] for row in records]
    branches = [row["branch_coverage"] for row in records]
    line_spread = max(lines) - min(lines)
    branch_spread = max(branches) - min(branches)
    responses_stable = len({row["response_sha256"] for row in records}) == 1
    states_stable = len({row["states"] for row in records}) == 1
    report = {
        "runs": runs,
        "states_stable": states_stable,
        "normalized_response_stable": responses_stable,
        "line_coverage_spread_pp": line_spread,
        "branch_coverage_spread_pp": branch_spread,
        "coverage_limit_pp": 0.5,
        "volatile_response_field_normalized": "numeric 003 creation-time text only",
        "csv": str(csv_path),
    }
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not states_stable or not responses_stable or line_spread > 0.5 or branch_spread > 0.5:
        print(f"FAIL: repeatability thresholds not met: {report}", file=sys.stderr)
        return 1
    print("PASS: identical IRC states/normalized response bytes in fresh-server replays; "
          f"coverage spread lines/branches={line_spread:.1f}/{branch_spread:.1f} pp (limit 0.5 pp).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
