#!/usr/bin/env python3
"""逐样本隔离回放 AFLNet 语料并保留 gcov 运行证据。"""

from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path

from protocol_smoke import HOST, summary


def split_requests(data: bytes) -> list[bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        remaining = len(data) - offset
        if remaining >= 8 and data[offset] == 0:
            length = struct.unpack_from("!I", data, offset)[0]
            if 8 <= length <= remaining:
                frames.append(data[offset:offset + length])
                offset += length
                continue
        if remaining >= 5:
            length = struct.unpack_from("!I", data, offset + 1)[0]
            if 4 <= length < remaining:
                frame_size = length + 1
                frames.append(data[offset:offset + frame_size])
                offset += frame_size
                continue
        frames.append(data[offset:])
        break
    return frames


def split_responses(data: bytes) -> tuple[list[dict[str, str]], int]:
    frames: list[dict[str, str]] = []
    offset = 0
    while offset < len(data):
        if data[offset:offset + 1] == b"N" and (
                offset + 1 == len(data) or data[offset + 1] != 0):
            frames.append(summary(data[offset:offset + 1]))
            offset += 1
            continue
        if len(data) - offset < 5:
            break
        length = struct.unpack_from("!I", data, offset + 1)[0]
        if length < 4 or length > len(data) - offset - 1:
            break
        frame_size = length + 1
        frames.append(summary(data[offset:offset + frame_size]))
        offset += frame_size
    return frames, len(data) - offset


def response_quiet(sock: socket.socket, quiet_seconds: float) -> bytes:
    result = bytearray()
    last_data = time.monotonic()
    while time.monotonic() - last_data < quiet_seconds:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        result.extend(chunk)
        last_data = time.monotonic()
    return bytes(result)


def reset_cluster(initdb: Path, data_dir: Path, port: int) -> None:
    result = subprocess.run(
        [str(initdb), "-D", str(data_dir), "--no-sync",
         "--auth-local=trust", "--auth-host=trust", "--username=postgres",
         "--encoding=UTF8", "--locale=C"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(f"initdb 失败：{result.stdout[-2000:]}")
    with (data_dir / "postgresql.conf").open("a", encoding="utf-8") as config:
        config.write(
            f"\nlisten_addresses = '{HOST}'\nport = {port}\n"
            "unix_socket_directories = ''\nmax_connections = 20\n"
            "shared_buffers = '16MB'\nfsync = off\n"
            "full_page_writes = off\nsynchronous_commit = off\n"
            "log_min_messages = warning\n"
        )
    (data_dir / "pg_hba.conf").write_text(
        "local all all trust\n"
        f"host all all {HOST}/32 trust\n"
        "host all all ::1/128 reject\n",
        encoding="utf-8",
    )


def connect_when_ready(server: subprocess.Popen[bytes], port: int,
                       pg_isready: Path) -> socket.socket:
    deadline = time.monotonic() + 10
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"服务端启动时退出，返回码 {server.returncode}")
        probe = subprocess.run(
            [str(pg_isready), "-h", HOST, "-p", str(port), "-U", "postgres"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False, timeout=2,
        )
        if probe.returncode != 0:
            time.sleep(0.05)
            continue
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            sock.connect((HOST, port))
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
            time.sleep(0.05)
    raise RuntimeError(f"服务端在等待时间内未监听端口 {port}：{last_error}")


def replay_one(path: Path, postgres: Path, initdb: Path, pg_ctl: Path,
               pg_isready: Path, output: Path, port: int,
               quiet_seconds: float) -> dict[str, object]:
    data = path.read_bytes()
    record: dict[str, object] = {
        "sample": str(path),
        "sha256": __import__("hashlib").sha256(data).hexdigest(),
        "bytes": len(data),
        "request_count": 0,
        "responses": [],
        "server_exit": None,
        "independently_replayed": False,
    }
    with tempfile.TemporaryDirectory(prefix="postgres-gcov-") as tempdir:
        data_dir = Path(tempdir) / "data"
        reset_cluster(initdb, data_dir, port)
        log_id = __import__("hashlib").sha256(data).hexdigest()[:16]
        log_path = output / "server-logs" / f"{path.name}-{log_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("wb") as log:
            server = subprocess.Popen(
                [str(postgres), "-D", str(data_dir)],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
            sock: socket.socket | None = None
            try:
                sock = connect_when_ready(server, port, pg_isready)
                responses: list[dict[str, object]] = []
                requests = split_requests(data)
                record["request_count"] = len(requests)
                for index, request in enumerate(requests):
                    try:
                        sock.sendall(request)
                    except OSError as exc:
                        responses.append({
                            "request": index,
                            "send_error": str(exc),
                            "server_alive": server.poll() is None,
                        })
                        break
                    raw = response_quiet(sock, quiet_seconds)
                    states, trailing = split_responses(raw)
                    responses.append({
                        "request": index,
                        "request_bytes": len(request),
                        "response_states": states,
                        "unparsed_response_bytes": trailing,
                        "server_alive": server.poll() is None,
                    })
                    if server.poll() is not None:
                        break
                record["responses"] = responses
                record["independently_replayed"] = True
                record["server_exit"] = server.poll()
            except (OSError, RuntimeError, socket.timeout) as exc:
                record["replay_error"] = f"{type(exc).__name__}: {exc}"
                record["server_exit"] = server.poll()
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
                try:
                    subprocess.run(
                        [str(pg_ctl), "-D", str(data_dir), "stop",
                        "--mode=fast", "--wait", "--timeout=10"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, timeout=12,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.terminate()
                    try:
                        server.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait(timeout=2)
                record["server_exit"] = server.returncode
    return record


def collect_samples(queue: Path, crashes: list[Path]) -> list[Path]:
    samples: list[Path] = []
    for directory in [queue, *crashes]:
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if not path.is_file() or path.name.startswith(".") or path.name == "README.txt":
                continue
            samples.append(path)
    unique: dict[str, Path] = {}
    for path in samples:
        digest = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        unique.setdefault(digest, path)
    return [unique[digest] for digest in sorted(unique)]


def main() -> int:
    parser = argparse.ArgumentParser(description="逐条重放 PostgreSQL 队列与异常样本")
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument(
        "--crashes", type=Path, action="append", default=[],
        help="附加逐个回放的崩溃或挂起样本目录，可重复指定",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--postgres", default=os.environ.get(
        "POSTGRES_GCOV_BIN",
        "/home/ubuntu/experiments/postgres-gcov/bin/postgres",
    ), type=Path)
    parser.add_argument("--initdb", default=os.environ.get(
        "POSTGRES_INITDB_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/initdb",
    ), type=Path)
    parser.add_argument("--pg-ctl", default=os.environ.get(
        "POSTGRES_PG_CTL_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/pg_ctl",
    ), type=Path)
    parser.add_argument("--pg-isready", default=os.environ.get(
        "POSTGRES_PG_ISREADY_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/pg_isready",
    ), type=Path)
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--quiet-seconds", type=float, default=0.12)
    args = parser.parse_args()

    if not args.queue.is_dir():
        parser.error(f"队列目录不存在：{args.queue}")
    for executable in (args.postgres, args.initdb, args.pg_ctl, args.pg_isready):
        if not executable.is_file():
            parser.error(f"缺少程序：{executable}")
    args.output.mkdir(parents=True, exist_ok=True)
    samples = collect_samples(args.queue, args.crashes)
    if not samples:
        parser.error("没有找到可回放的队列或异常样本")
    parameters = {
        "queue": str(args.queue),
        "crashes": [str(path) for path in args.crashes],
        "sample_count": len(samples),
        "postgres": str(args.postgres),
        "initdb": str(args.initdb),
        "pg_isready": str(args.pg_isready),
        "port": args.port,
        "per_request_quiet_seconds": args.quiet_seconds,
        "each_sample_uses_fresh_cluster": True,
    }
    (args.output / "replay-parameters.json").write_text(
        json.dumps(parameters, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    records = []
    with (args.output / "queue-replay.jsonl").open("w", encoding="utf-8") as stream:
        for path in samples:
            record = replay_one(path, args.postgres, args.initdb, args.pg_ctl,
                                args.pg_isready, args.output, args.port,
                                args.quiet_seconds)
            records.append(record)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = {
        "samples_total": len(records),
        "samples_replayed": sum(bool(item["independently_replayed"]) for item in records),
        "server_abnormal_exits": sum(
            item.get("server_exit") not in (None, 0) for item in records
        ),
        "samples_with_replay_error": sum("replay_error" in item for item in records),
        "records": records,
    }
    (args.output / "replay-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: summary[key] for key in (
        "samples_total", "samples_replayed", "server_abnormal_exits",
        "samples_with_replay_error",
    )}, ensure_ascii=False))
    return 0 if summary["samples_replayed"] == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
