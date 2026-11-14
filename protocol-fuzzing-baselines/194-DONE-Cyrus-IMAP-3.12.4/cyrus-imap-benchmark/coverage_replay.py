#!/usr/bin/env python3
"""Replay each AFLNet queue input on a freshly reset gcov Cyrus server."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


PORT = int(os.environ.get("IMAP_PORT", "1143"))
MAX_INPUT_BYTES = 1_048_576


def queue_files(root: Path) -> list[Path]:
    queues = [root] if root.name == "queue" and root.is_dir() else sorted(
        path for path in root.rglob("queue") if path.is_dir()
    ) if root.is_dir() else []
    files = sorted(
        {item for queue in queues for item in queue.iterdir()
         if item.is_file() and item.name.startswith("id:")},
        key=lambda item: item.name,
    )
    if not files:
        raise RuntimeError(f"no AFLNet queue inputs below {root}")
    return files


def cleanup() -> None:
    subprocess.run(["/workspace/reset-state.sh"], check=True)


def stop_master(proc: subprocess.Popen[bytes]) -> int:
    if proc.poll() is None:
        try:
            # Ask Cyrus master to stop first; killing its entire process group
            # at once can terminate imapd before its gcov counters are flushed.
            os.kill(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            result = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                result = proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                result = proc.wait(timeout=5)
    else:
        result = proc.returncode or 0
    cleanup()
    return result


def wait_for_server(proc: subprocess.Popen[bytes], log_path: Path) -> socket.socket:
    deadline = time.monotonic() + 12
    last_error = ""
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"master exited ({proc.returncode}); log={log_path}")
        try:
            sock = socket.create_connection(("127.0.0.1", PORT), timeout=0.4)
            sock.settimeout(0.5)
            sock.recv(4096)
            return sock
        except OSError as exc:
            last_error = str(exc)
            time.sleep(0.04)
    raise RuntimeError(f"server did not listen on {PORT}: {last_error}; log={log_path}")


def replay_one(prefix: Path, data: bytes, log_path: Path) -> dict[str, object]:
    cleanup()
    env = os.environ.copy()
    # start-server.sh reads CYRUS_PREFIX. Setting only CYRUS_GCOV_PREFIX
    # here selects the AFL build by default and produces no gcov data.
    env["CYRUS_PREFIX"] = str(prefix)
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            ["/workspace/start-server.sh"], stdout=log, stderr=subprocess.STDOUT,
            env=env, start_new_session=True,
        )
        sock: socket.socket | None = None
        status = "replayed"
        error = ""
        response_bytes = 0
        try:
            sock = wait_for_server(proc, log_path)
            sock.sendall(data)
            quiet_deadline = time.monotonic() + 0.75
            while time.monotonic() < quiet_deadline:
                try:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    response_bytes += len(chunk)
                    quiet_deadline = time.monotonic() + 0.25
                except socket.timeout:
                    continue
                except OSError as exc:
                    status = "connection_error"
                    error = str(exc)
                    break
            if proc.poll() is not None and proc.returncode not in (0,):
                status = "master_exited"
                error = f"master exited after input with {proc.returncode}"
        except (OSError, TimeoutError, RuntimeError) as exc:
            status = "replay_error"
            error = str(exc)
        finally:
            if sock is not None:
                sock.close()
            returncode = stop_master(proc)
            log.flush()
    if status == "replay_error" and "did not listen" in error:
        raise RuntimeError(f"{error}; see {log_path}")
    return {
        "status": status,
        "master_returncode_after_shutdown": returncode,
        "input_bytes": len(data),
        "response_bytes": response_bytes,
        "error": error,
        "log": str(log_path),
    }


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: coverage_replay.py FUZZ_OUTPUT_DIR OUTPUT_DIR QUEUE_LIMIT", file=sys.stderr)
        return 2
    fuzz_dir, output_dir = Path(sys.argv[1]), Path(sys.argv[2])
    limit = int(sys.argv[3])
    prefix = Path(os.environ.get("CYRUS_GCOV_PREFIX", "/home/ubuntu/experiments/cyrus-gcov"))
    if not (prefix / "libexec" / "master").exists():
        raise RuntimeError(f"gcov Cyrus master missing under {prefix}")
    if prefix.name != "cyrus-gcov":
        raise RuntimeError(f"coverage replay must use the gcov-instrumented build, got {prefix}")
    if limit < 0:
        raise RuntimeError("QUEUE_LIMIT must be zero (all inputs) or positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise RuntimeError(f"coverage replay directory is not empty: {output_dir}")
    inputs = queue_files(fuzz_dir)
    if limit:
        inputs = inputs[:limit]

    results: list[dict[str, object]] = []
    for index, path in enumerate(inputs):
        data = path.read_bytes()
        if len(data) > MAX_INPUT_BYTES:
            results.append({"input": path.name, "status": "skipped_oversize", "input_bytes": len(data)})
            continue
        result = replay_one(prefix, data, output_dir / f"master-{index:05d}.log")
        result["input"] = path.name
        results.append(result)
    report = {
        "queue_directory": str(fuzz_dir),
        "server_build": str(prefix),
        "instrumentation": "GCC gcov (--coverage)",
        "queue_inputs_found": len(queue_files(fuzz_dir)),
        "inputs_replayed_or_skipped": len(results),
        "queue_limit": limit,
        "master_exits_after_input": sum(item["status"] == "master_exited" for item in results),
        "replay_errors": sum(item["status"] in {"replay_error", "connection_error"} for item in results),
        "results": results,
    }
    (output_dir / "replay.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Replayed {len(results)} queue inputs on reset gcov Cyrus servers; evidence={output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
