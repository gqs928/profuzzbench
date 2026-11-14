#!/usr/bin/env python3
"""生成固定的 PostgreSQL Startup、简单查询、扩展查询与边界语料。"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


def packet(payload: bytes) -> bytes:
    return struct.pack("!I", len(payload) + 4) + payload


def startup(user: bytes = b"postgres", database: bytes = b"postgres",
            version: int = 196608) -> bytes:
    fields = (
        b"user\0" + user + b"\0"
        + b"database\0" + database + b"\0"
        + b"client_encoding\0UTF8\0\0"
    )
    return packet(struct.pack("!I", version) + fields)


def message(kind: bytes, body: bytes = b"") -> bytes:
    if len(kind) != 1:
        raise ValueError("消息类型必须为一个字节")
    return kind + packet(body)


def query(sql: str) -> bytes:
    return message(b"Q", sql.encode("utf-8") + b"\0")


def terminate() -> bytes:
    return message(b"X")


def parse_statement(sql: str) -> bytes:
    return message(b"P", b"\0" + sql.encode("utf-8") + b"\0" + b"\0\0")


def bind_two_text_values(first: bytes, second: bytes) -> bytes:
    body = (
        b"\0\0"
        + b"\0\0"
        + struct.pack("!H", 2)
        + struct.pack("!I", len(first)) + first
        + struct.pack("!I", len(second)) + second
        + b"\0\0"
    )
    return message(b"B", body)


def describe_statement() -> bytes:
    return message(b"D", b"S\0")


def execute_portal() -> bytes:
    return message(b"E", b"\0\0\0\0\0")


def startup_packet(data: bytes, offset: int) -> int | None:
    if len(data) - offset < 8 or data[offset] != 0:
        return None
    length = struct.unpack_from("!I", data, offset)[0]
    if length >= 8 and length <= len(data) - offset:
        return length
    return None


def message_length(data: bytes, offset: int) -> int | None:
    if len(data) - offset < 5:
        return None
    length = struct.unpack_from("!I", data, offset + 1)[0]
    if 4 <= length <= len(data) - offset - 1:
        return length + 1
    return None


def request_count(data: bytes) -> int:
    count = 0
    offset = 0
    while offset < len(data):
        length = startup_packet(data, offset)
        if length is None:
            length = message_length(data, offset)
        if length is None:
            count += 1
            break
        count += 1
        offset += length
    return count


def seeds() -> dict[str, tuple[str, bytes]]:
    basic = startup() + b"".join([
        query("SELECT 1;"),
        query("CREATE TEMP TABLE bench_rows(id integer, value text);"),
        query("INSERT INTO bench_rows VALUES (7, 'seven');"),
        query("SELECT id, value FROM bench_rows;"),
        terminate(),
    ])
    transaction = startup() + b"".join([
        query("BEGIN;"),
        query("SELECT 1 / 0;"),
        query("ROLLBACK;"),
        query("SELECT 42;"),
        terminate(),
    ])
    extended = startup() + b"".join([
        parse_statement("SELECT $1::integer + $2::integer"),
        bind_two_text_values(b"19", b"23"),
        describe_statement(),
        execute_portal(),
        message(b"S"),
        terminate(),
    ])
    copy_in = startup() + b"".join([
        query("CREATE TEMP TABLE copy_rows(id integer, value text);"),
        query("COPY copy_rows FROM STDIN;"),
        message(b"d", b"8\teight\n"),
        message(b"c"),
        query("SELECT id, value FROM copy_rows;"),
        terminate(),
    ])
    ssl = (
        struct.pack("!II", 8, 80877103)
        + startup()
        + query("SELECT 18;")
        + terminate()
    )
    version_32 = startup(version=196610) + query("SELECT 32;") + terminate()
    return {
        "simple-read-write": (
            "登录后执行建表、写入、读取与断开连接。",
            basic,
        ),
        "transaction-recovery": (
            "事务中触发 SQL 错误，回滚后继续执行查询。",
            transaction,
        ),
        "extended-query": (
            "按 Parse、Bind、Describe、Execute、Sync 顺序执行参数化查询。",
            extended,
        ),
        "copy-in": (
            "进入 COPY 输入状态，发送数据与结束标记，再读取表内容。",
            copy_in,
        ),
        "ssl-negotiation": (
            "发送 SSLRequest，接受明文拒绝后完成正常启动与查询。",
            ssl,
        ),
        "protocol-3.2": (
            "使用 PostgreSQL 18 支持的 3.2 协议版本完成查询。",
            version_32,
        ),
        "login-rejected": (
            "使用不存在的角色启动连接，观察服务端拒绝响应。",
            startup(user=b"missing_fuzz_role"),
        ),
        "database-rejected": (
            "使用不存在的数据库启动连接，观察服务端拒绝响应。",
            startup(database=b"missing_fuzz_database"),
        ),
        "protocol-version-rejected": (
            "请求未定义的 4.0 协议版本，观察启动阶段错误。",
            startup(version=262144),
        ),
        "empty-query": (
            "提交空 Query 并检查 EmptyQueryResponse 与就绪状态。",
            startup() + query("") + terminate(),
        ),
        "multi-statement": (
            "在一个简单查询消息中顺序执行多条 SQL 语句。",
            startup() + query("SELECT 1; SELECT 2;") + query("SELECT 3;")
            + terminate(),
        ),
        "truncated-startup": (
            "保留不完整 StartupMessage 尾部，供长度边界回放。",
            b"\0\0\0\x20\0\x03\0\0user\0postgres",
        ),
        "invalid-message-length": (
            "启动后发送小于协议最小值的消息长度。",
            startup() + b"Q\0\0\0\2",
        ),
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("用法：prepare_seeds.py 种子目录 清单文件", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format_version": 1,
        "protocol": "PostgreSQL Frontend/Backend Protocol 3.0 and 3.2",
        "source_version": "PostgreSQL 18.6",
        "seeds": [],
    }
    for name, (description, data) in sorted(seeds().items()):
        path = output / name
        path.write_bytes(data)
        manifest["seeds"].append({
            "name": name,
            "file": name,
            "bytes": len(data),
            "requests": request_count(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "说明": description,
        })
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已生成 {len(manifest['seeds'])} 条 PostgreSQL 种子：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
