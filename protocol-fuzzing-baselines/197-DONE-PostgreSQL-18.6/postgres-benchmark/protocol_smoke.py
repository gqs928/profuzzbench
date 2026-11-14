#!/usr/bin/env python3
"""用原始协议客户端与 psql 验证 PostgreSQL 正常和异常会话。"""

from __future__ import annotations

import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HOST = "127.0.0.1"
PORT = int(os.environ.get("POSTGRES_SMOKE_PORT", "55432"))
REPETITIONS = int(os.environ.get("POSTGRES_SMOKE_REPETITIONS", "10"))
TIMEOUT = 3.0


class SmokeFailure(RuntimeError):
    pass


def packet(body: bytes) -> bytes:
    return struct.pack("!I", len(body) + 4) + body


def startup(user: str = "postgres", database: str = "postgres",
            version: int = 196608) -> bytes:
    parameters = (
        b"user\0" + user.encode() + b"\0"
        + b"database\0" + database.encode() + b"\0"
        + b"client_encoding\0UTF8\0\0"
    )
    return packet(struct.pack("!I", version) + parameters)


def message(tag: bytes, body: bytes = b"") -> bytes:
    return tag + packet(body)


def query(sql: str) -> bytes:
    return message(b"Q", sql.encode() + b"\0")


def receive_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise EOFError("服务端在一帧结束前关闭连接")
        data.extend(part)
    return bytes(data)


def receive_frame(sock: socket.socket) -> bytes:
    tag = receive_exact(sock, 1)
    length_bytes = receive_exact(sock, 4)
    length = struct.unpack("!I", length_bytes)[0]
    if length < 4 or length > 64 * 1024 * 1024:
        raise SmokeFailure(f"服务端返回非法消息长度：{length}")
    return tag + length_bytes + receive_exact(sock, length - 4)


def fields(body: bytes) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    offset = 0
    while offset < len(body) and body[offset] != 0:
        key = body[offset:offset + 1].decode("ascii", "replace")
        offset += 1
        end = body.find(b"\0", offset)
        if end < 0:
            break
        result[key] = body[offset:end]
        offset = end + 1
    return result


def summary(frame: bytes) -> dict[str, str]:
    tag = frame[:1]
    body = frame[5:]
    if tag == b"K":
        return {"type": "K", "value": "<运行期密钥已归一化>"}
    if tag == b"R" and len(body) >= 4:
        return {"type": "R", "auth_code": str(struct.unpack("!I", body[:4])[0])}
    if tag == b"Z" and body:
        return {"type": "Z", "transaction": body[:1].decode("ascii", "replace")}
    if tag == b"C":
        return {"type": "C", "command": body.rstrip(b"\0").decode("ascii", "replace")}
    if tag == b"E":
        error = fields(body)
        return {
            "type": "E",
            "severity": error.get("S", b"").decode("utf-8", "replace"),
            "sqlstate": error.get("C", b"").decode("ascii", "replace"),
            "message": error.get("M", b"").decode("utf-8", "replace"),
        }
    return {"type": tag.decode("ascii", "replace"), "hex": frame.hex()}


def receive_until(sock: socket.socket, terminal_tags: set[bytes]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    while True:
        try:
            frame = receive_frame(sock)
        except (EOFError, socket.timeout):
            return result
        result.append(summary(frame))
        if frame[:1] in terminal_tags:
            return result


def receive_until_ready(sock: socket.socket) -> list[dict[str, str]]:
    return receive_until(sock, {b"Z"})


def open_session(user: str = "postgres", database: str = "postgres",
                 version: int = 196608, ssl: bool = False) -> tuple[socket.socket, list[dict[str, str]]]:
    deadline = time.monotonic() + 10
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        try:
            sock.connect((HOST, PORT))
            break
        except OSError as exc:
            last_error = exc
            sock.close()
            time.sleep(0.05)
    else:
        raise SmokeFailure(f"PostgreSQL 未监听 {HOST}:{PORT}：{last_error}")

    if ssl:
        sock.sendall(struct.pack("!II", 8, 80877103))
        response = receive_exact(sock, 1)
        if response != b"N":
            sock.close()
            raise SmokeFailure(f"隔离环境预期明文拒绝 SSLRequest，得到 {response!r}")
    sock.sendall(startup(user, database, version))
    frames = receive_until_ready(sock)
    return sock, frames


def exchange(sock: socket.socket, data: bytes) -> list[dict[str, str]]:
    sock.sendall(data)
    return receive_until_ready(sock)


def run_scenarios(postgres: Path, initdb: Path, pg_ctl: Path,
                  build: str, repetition: int, output: Path) -> dict[str, object]:
    tag = f"{build}-run-{repetition:02d}"
    log_path = output / f"{tag}.server.log"
    transcript: dict[str, object] = {"build": build, "repetition": repetition}
    with tempfile.TemporaryDirectory(prefix="postgres-smoke-") as tempdir:
        data_dir = Path(tempdir) / "data"
        init = subprocess.run(
            [str(initdb), "-D", str(data_dir), "--no-sync",
             "--auth-local=trust", "--auth-host=trust", "--username=postgres",
             "--encoding=UTF8", "--locale=C"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=30,
        )
        if init.returncode:
            raise SmokeFailure(f"{tag}: initdb 失败：{init.stdout[-2000:]}")
        with (data_dir / "postgresql.conf").open("a", encoding="utf-8") as conf:
            conf.write(
                f"\nlisten_addresses = '{HOST}'\nport = {PORT}\n"
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
        with log_path.open("w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [str(postgres), "-D", str(data_dir)],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
            try:
                sock, login_frames = open_session()
                if not any(f.get("type") == "Z" for f in login_frames):
                    raise SmokeFailure(f"{tag}: 正常用户登录未进入 ReadyForQuery：{login_frames}")
                transcript["startup_3_0"] = login_frames
                transcript["simple_query"] = exchange(sock, query("SELECT 42;"))
                write_read: list[dict[str, str]] = []
                for sql in (
                    "CREATE TEMP TABLE smoke_rows(id integer, value text);",
                    "INSERT INTO smoke_rows VALUES (7, 'seven');",
                    "SELECT id, value FROM smoke_rows;",
                ):
                    write_read.extend(exchange(sock, query(sql)))
                if not any(frame.get("type") == "D" for frame in write_read):
                    raise SmokeFailure(f"{tag}: 表写入后没有读取到 DataRow：{write_read}")
                transcript["temporary_write_read"] = write_read
                transcript["transaction_recovery"] = (
                    exchange(sock, query("BEGIN;"))
                    + exchange(sock, query("SELECT 1 / 0;"))
                    + exchange(sock, query("ROLLBACK;"))
                    + exchange(sock, query("SELECT 42;"))
                )
                extended = b"".join([
                    message(b"P", b"\0SELECT $1::integer + $2::integer\0\0\0"),
                    message(b"B", b"\0\0\0\0\0\2\0\0\0\2" + b"19"
                            + b"\0\0\0\2" + b"23" + b"\0\0"),
                    message(b"D", b"P\0"),
                    message(b"E", b"\0\0\0\0\0"),
                    message(b"S"),
                ])
                transcript["extended_query"] = exchange(sock, extended)

                transcript["copy_table_create"] = exchange(
                    sock, query("CREATE TEMP TABLE smoke_copy(id integer, value text);")
                )
                sock.sendall(query("COPY smoke_copy FROM STDIN;"))
                transcript["copy_in_response"] = receive_until(sock, {b"G"})
                if not any(f.get("type") == "G" for f in transcript["copy_in_response"]):
                    raise SmokeFailure(f"{tag}: COPY 未进入 CopyInResponse")
                sock.sendall(message(b"d", b"8\teight\n") + message(b"c"))
                transcript["copy_in_completion"] = receive_until_ready(sock)
                transcript["copy_readback"] = exchange(
                    sock, query("SELECT id, value FROM smoke_copy;")
                )
                sock.sendall(message(b"X"))
                sock.close()

                bad_user, bad_user_frames = open_session(user="missing_fuzz_role")
                transcript["login_rejected"] = bad_user_frames
                bad_user.close()
                bad_database, bad_database_frames = open_session(
                    database="missing_fuzz_database"
                )
                transcript["database_rejected"] = bad_database_frames
                bad_database.close()

                version32, version32_frames = open_session(version=196610)
                transcript["startup_3_2"] = version32_frames
                if not any(f.get("type") == "Z" for f in version32_frames):
                    raise SmokeFailure(f"{tag}: 3.2 协议启动失败：{version32_frames}")
                transcript["query_3_2"] = exchange(version32, query("SELECT 32;"))
                version32.sendall(message(b"X"))
                version32.close()

                ssl_sock, ssl_frames = open_session(ssl=True)
                transcript["ssl_request_then_query"] = ssl_frames
                transcript["ssl_followup_query"] = exchange(
                    ssl_sock, query("SELECT 18;")
                )
                ssl_sock.sendall(message(b"X"))
                ssl_sock.close()

                env = dict(os.environ)
                env.update({
                    "PGHOST": HOST,
                    "PGPORT": str(PORT),
                    "PGUSER": "postgres",
                    "PGDATABASE": "postgres",
                    "PGCONNECT_TIMEOUT": "5",
                })
                psql = subprocess.run(
                    ["psql", "--no-psqlrc", "--quiet", "--tuples-only",
                     "--no-align", "--command", "SELECT 42;"],
                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=10,
                )
                if psql.returncode or psql.stdout.strip() != "42":
                    raise SmokeFailure(
                        f"{tag}: psql 正常客户端验证失败：{psql.stdout} {psql.stderr}"
                    )
                transcript["psql_client"] = {
                    "exit": psql.returncode, "stdout": psql.stdout.strip()
                }
            finally:
                try:
                    subprocess.run(
                        [str(pg_ctl), "-D", str(data_dir), "stop", "--mode=immediate",
                         "--wait", "--timeout=3"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, timeout=5,
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
                transcript["server_exit"] = server.returncode
    return transcript


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：protocol_smoke.py 结果目录", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    reference = Path(os.environ.get(
        "POSTGRES_REFERENCE_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/postgres",
    ))
    afl = Path(os.environ.get(
        "POSTGRES_AFL_BIN",
        "/home/ubuntu/experiments/postgres-afl/bin/postgres",
    ))
    initdb = Path(os.environ.get(
        "POSTGRES_INITDB_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/initdb",
    ))
    pg_ctl = Path(os.environ.get(
        "POSTGRES_PG_CTL_BIN",
        "/home/ubuntu/experiments/postgres-reference/bin/pg_ctl",
    ))
    for binary in (reference, afl, initdb, pg_ctl):
        if not binary.is_file():
            print(f"缺少验收程序：{binary}", file=sys.stderr)
            return 2

    records: list[dict[str, object]] = []
    try:
        for repetition in range(1, REPETITIONS + 1):
            records.append(run_scenarios(reference, initdb, pg_ctl,
                                         "reference", repetition, output))
            records.append(run_scenarios(afl, initdb, pg_ctl,
                                         "afl-instrumented", repetition, output))
    except (OSError, SmokeFailure, subprocess.SubprocessError) as exc:
        (output / "protocol-smoke-error.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        raise

    comparisons = []
    for repetition in range(REPETITIONS):
        original = records[repetition * 2]
        instrumented = records[repetition * 2 + 1]
        left = {key: value for key, value in original.items()
                if key not in {"build", "repetition", "server_exit"}}
        right = {key: value for key, value in instrumented.items()
                 if key not in {"build", "repetition", "server_exit"}}
        comparisons.append({
            "repetition": repetition + 1,
            "same_protocol_transcript": left == right,
            "reference_server_exit": original.get("server_exit"),
            "afl_server_exit": instrumented.get("server_exit"),
        })
    report = {
        "postgresql_version": "18.6",
        "protocols": ["3.0", "3.2"],
        "endpoint": f"tcp://{HOST}:{PORT}",
        "repetitions_per_build": REPETITIONS,
        "scenarios": [
            "Startup、认证拒绝、数据库拒绝、SSLRequest",
            "简单查询、临时表写入读取、事务错误回滚后继续",
            "扩展查询 Parse/Bind/Describe/Execute/Sync、COPY 输入",
            "psql 正常客户端",
        ],
        "records": records,
        "comparisons": comparisons,
        "all_transcripts_match": all(item["same_protocol_transcript"]
                                     for item in comparisons),
    }
    (output / "protocol-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "repetitions": REPETITIONS,
        "transcripts_match": report["all_transcripts_match"],
        "evidence": str(output / "protocol-smoke.json"),
    }, ensure_ascii=False))
    return 0 if report["all_transcripts_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
