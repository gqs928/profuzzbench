#!/usr/bin/env python3
"""Replay one Memcached ASCII seed in fresh servers and compare state/coverage."""
from __future__ import annotations

import argparse
import csv
import hashlib
import pathlib
import re
import select
import socket
import subprocess
import time


STATE_NAMES = {
    b"VERSION": "VERSION", b"STAT": "STAT", b"VALUE": "VALUE",
    b"END": "END", b"STORED": "STORED", b"NOT_STORED": "NOT_STORED",
    b"EXISTS": "EXISTS", b"NOT_FOUND": "NOT_FOUND", b"DELETED": "DELETED",
    b"TOUCHED": "TOUCHED", b"OK": "OK", b"ERROR": "ERROR",
    b"CLIENT_ERROR": "CLIENT_ERROR", b"SERVER_ERROR": "SERVER_ERROR",
}


def response_states(data: bytes) -> list[str]:
    states = []
    cursor = 0
    while cursor < len(data):
        end = data.find(b"\r\n", cursor)
        if end < 0:
            break
        line = data[cursor:end]
        fields = line.split()
        token = fields[0] if fields else b""
        states.append(STATE_NAMES.get(token, "UNKNOWN"))
        cursor = end + 2
        if token == b"VALUE" and len(fields) >= 4:
            try:
                body_size = int(fields[3])
            except ValueError:
                continue
            body_end = cursor + body_size
            if body_end + 2 <= len(data) and data[body_end:body_end + 2] == b"\r\n":
                cursor = body_end + 2
    return states


def gcda_signature(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    files = sorted(root.rglob("*.gcda"))
    if not files:
        raise RuntimeError(f"no .gcda files created under {root}")
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def coverage_summary(root: pathlib.Path) -> tuple[str, str]:
    result = subprocess.run(
        ["gcovr", "-r", str(root), "-s"], cwd=root,
        check=True, capture_output=True, text=True,
    )
    line = re.search(r"^lines:\s*([0-9.]+)%", result.stdout, re.MULTILINE)
    branch = re.search(r"^branches:\s*([0-9.]+)%", result.stdout, re.MULTILINE)
    if line is None or branch is None:
        raise RuntimeError(f"could not parse gcovr summary:\n{result.stdout}")
    return line.group(1), branch.group(1)


def recv_response(sock: socket.socket) -> bytes:
    chunks = []
    got_data = False
    idle_since = None
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        ready, _, _ = select.select([sock], [], [], 0.1)
        if ready:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            got_data = True
            idle_since = time.monotonic()
        elif got_data and idle_since is not None and time.monotonic() - idle_since >= 0.25:
            break
    return b"".join(chunks)


def run_once(server: pathlib.Path, seed: bytes, port: int, out: pathlib.Path,
             iteration: int) -> tuple[bytes, str, str, str]:
    root = server.parent
    # This is an isolated build directory in the disposable acceptance
    # container, not the mounted result directory or the user's host tree.
    for path in root.rglob("*.gcda"):
        path.unlink()

    log_path = out / f"run-{iteration:02d}.server.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            [str(server), "-B", "ascii", "-p", str(port), "-U", "0", "-t", "1"],
            cwd=root, stdout=log, stderr=log,
        )
        try:
            deadline = time.monotonic() + 5
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"server exited early with {process.returncode}; see {log_path}")
                try:
                    probe = socket.create_connection(("127.0.0.1", port), timeout=0.2)
                    probe.close()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"server did not listen on {port}; see {log_path}")
                    time.sleep(0.05)

            with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
                client.settimeout(1)
                client.sendall(seed)
                response = recv_response(client)
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                raise RuntimeError(f"server failed to stop cleanly; see {log_path}")

    states = response_states(response)
    expected = ["STORED", "VALUE", "END", "DELETED", "END"]
    if states != expected:
        raise RuntimeError(f"unexpected protocol state sequence in run {iteration}: {states}; response={response!r}")
    line_cov, branch_cov = coverage_summary(root)
    return response, ",".join(states), f"{line_cov}/{branch_cov}", gcda_signature(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, type=pathlib.Path)
    parser.add_argument("--seed", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--port", type=int, default=11212)
    args = parser.parse_args()

    server = args.server.resolve()
    seed_path = args.seed.resolve()
    out = args.out.resolve()
    if not server.is_file() or not seed_path.is_file():
        raise FileNotFoundError("gcov server or seed file does not exist")
    if not (1 <= args.runs <= 100):
        raise ValueError("runs must be between 1 and 100")
    out.mkdir(parents=True, exist_ok=True)
    seed = seed_path.read_bytes()
    rows = []
    signatures = []
    for iteration in range(1, args.runs + 1):
        response, states, coverage, gcda_hash = run_once(
            server, seed, args.port, out, iteration,
        )
        response_path = out / f"run-{iteration:02d}.response"
        response_path.write_bytes(response)
        response_hash = hashlib.sha256(response).hexdigest()
        signatures.append((states, coverage, gcda_hash, response_hash))
        rows.append((iteration, states, coverage, response_hash, gcda_hash))
        print(f"run-{iteration:02d}: states={states}; line/branch={coverage}; gcda_sha256={gcda_hash}")

    csv_path = out / "repeatability.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["run", "states", "line_branch_percent", "response_sha256", "gcda_sha256"])
        writer.writerows(rows)
    # Coverage counters can differ slightly because process startup and worker
    # scheduling are included in gcov data. The acceptance criterion is semantic
    # repeatability: exact protocol states and response bytes, plus a tightly
    # bounded spread in aggregate line/branch coverage. Keep raw gcda hashes in
    # the CSV as diagnostics, but do not make their byte identity a pass gate.
    protocol_signatures = {(states, response_hash)
                           for states, _coverage, _gcda_hash, response_hash in signatures}
    if len(protocol_signatures) != 1:
        raise SystemExit(f"FAIL: repeated seed changed protocol states or response bytes; details: {csv_path}")

    coverage_values = [tuple(float(value) for value in coverage.split("/"))
                       for _states, coverage, _gcda_hash, _response_hash in signatures]
    line_spread = max(value[0] for value in coverage_values) - min(value[0] for value in coverage_values)
    branch_spread = max(value[1] for value in coverage_values) - min(value[1] for value in coverage_values)
    coverage_tolerance = 0.5  # percentage points, across all independent runs
    if line_spread > coverage_tolerance or branch_spread > coverage_tolerance:
        raise SystemExit(
            "FAIL: repeated seed coverage spread exceeds "
            f"{coverage_tolerance:.1f} percentage points "
            f"(lines={line_spread:.1f}, branches={branch_spread:.1f}); details: {csv_path}"
        )

    print(
        f"PASS: identical protocol states and response bytes in {args.runs} fresh-server replays; "
        f"coverage spread lines/branches={line_spread:.1f}/{branch_spread:.1f} pp "
        f"(limit {coverage_tolerance:.1f} pp). Raw gcda hashes are retained for diagnosis."
    )
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
