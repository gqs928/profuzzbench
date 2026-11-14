#!/usr/bin/env python3
"""NFSv3/ONC RPC over TCP 的最小可回放客户端与 XDR 编码器。"""

from __future__ import annotations

import hashlib
import socket
import struct
from typing import Iterable


NFS_PROGRAM = 100003
MOUNT_PROGRAM = 100005
RPC_VERSION = 2
NFS_VERSION = 3
MOUNT_VERSION = 3
NFS_PORT = int(__import__("os").environ.get("NFS_PORT", "12049"))
MOUNT_PORT = int(__import__("os").environ.get("MOUNT_PORT", "12050"))
NFS_PSEUDO = __import__("os").environ.get("NFS_PSEUDO", "/nfs-fuzz")
MAX_RECORD = 16 * 1024 * 1024


def u32(value: int) -> bytes:
    return struct.pack(">I", value & 0xFFFFFFFF)


def u64(value: int) -> bytes:
    return struct.pack(">Q", value & 0xFFFFFFFFFFFFFFFF)


def xdr_opaque(value: bytes) -> bytes:
    padding = (-len(value)) % 4
    return u32(len(value)) + value + bytes(padding)


def xdr_string(value: str | bytes) -> bytes:
    encoded = value.encode("utf-8") if isinstance(value, str) else value
    return xdr_opaque(encoded)


def record(payload: bytes) -> bytes:
    if len(payload) > 0x7FFFFFFF:
        raise ValueError("RPC record 超过 record marker 可表示的长度")
    return u32(0x80000000 | len(payload)) + payload


def auth_sys(uid: int = 1000, gid: int = 1000) -> bytes:
    body = u32(1) + xdr_string("fuzzbench") + u32(uid) + u32(gid) + u32(0)
    return u32(1) + xdr_opaque(body)


def rpc_call(program: int, version: int, procedure: int, arguments: bytes, xid: int) -> bytes:
    payload = b"".join(
        (
            u32(xid),
            u32(0),
            u32(RPC_VERSION),
            u32(program),
            u32(version),
            u32(procedure),
            auth_sys(),
            u32(0),
            u32(0),
            arguments,
        )
    )
    return record(payload)


def read_exact(sock: socket.socket, count: int) -> bytes:
    result = bytearray()
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise ConnectionError(f"RPC 回复在 {count} 字节前关闭")
        result.extend(chunk)
    return bytes(result)


def receive_record(sock: socket.socket) -> tuple[bytes, bytes]:
    """读取并拼接一个 RPC record，返回完整线缆数据和 record 内容。"""
    wire = bytearray()
    payload = bytearray()
    while True:
        marker_bytes = read_exact(sock, 4)
        wire.extend(marker_bytes)
        marker = struct.unpack(">I", marker_bytes)[0]
        fragment_len = marker & 0x7FFFFFFF
        if fragment_len > MAX_RECORD or len(payload) + fragment_len > MAX_RECORD:
            raise ValueError("RPC record 超过回放上限")
        fragment = read_exact(sock, fragment_len)
        wire.extend(fragment)
        payload.extend(fragment)
        if marker & 0x80000000:
            return bytes(wire), bytes(payload)


def split_records(data: bytes) -> list[bytes]:
    """按 record marker 切出完整 RPC record，保留每个 record 的线缆字节。"""
    records = []
    cursor = 0
    while cursor < len(data):
        start = cursor
        complete = False
        while not complete:
            if len(data) - cursor < 4:
                return records + [data[start:]]
            marker = struct.unpack_from(">I", data, cursor)[0]
            fragment_len = marker & 0x7FFFFFFF
            cursor += 4
            if fragment_len > MAX_RECORD or fragment_len > len(data) - cursor:
                return records + [data[start:]]
            cursor += fragment_len
            complete = bool(marker & 0x80000000)
        records.append(data[start:cursor])
    return records


def parse_rpc_reply(payload: bytes, expected_xid: int | None = None) -> bytes:
    if len(payload) < 12:
        raise ValueError("RPC 回复头不完整")
    xid, message_type, reply_status = struct.unpack_from(">III", payload)
    if expected_xid is not None and xid != expected_xid:
        raise ValueError(f"RPC XID 不匹配：期望 {expected_xid:#x}，收到 {xid:#x}")
    if message_type != 1:
        raise ValueError(f"RPC 消息类型不是 REPLY：{message_type}")
    if reply_status == 1:
        reject_status = struct.unpack_from(">I", payload, 12)[0]
        raise ValueError(f"RPC_MSG_DENIED：reject_stat={reject_status}")
    if reply_status != 0 or len(payload) < 24:
        raise ValueError(f"RPC 回复头无效：reply_stat={reply_status}")
    verifier_len = struct.unpack_from(">I", payload, 16)[0]
    padded_len = (verifier_len + 3) & ~3
    accept_offset = 20 + padded_len
    if accept_offset + 4 > len(payload):
        raise ValueError("RPC verifier 长度越过回复边界")
    accept_status = struct.unpack_from(">I", payload, accept_offset)[0]
    if accept_status != 0:
        raise ValueError(f"RPC_MSG_ACCEPTED：accept_stat={accept_status}")
    return payload[accept_offset + 4 :]


def nfs_status(reply_body: bytes) -> int:
    if len(reply_body) < 4:
        raise ValueError("NFSv3 回复缺少 status 字段")
    return struct.unpack_from(">I", reply_body)[0]


def opaque_at(data: bytes, offset: int, maximum: int = 65536) -> tuple[bytes, int]:
    if offset + 4 > len(data):
        raise ValueError("XDR opaque 长度字段不完整")
    length = struct.unpack_from(">I", data, offset)[0]
    if length > maximum:
        raise ValueError(f"XDR opaque 长度超过上限：{length}")
    start = offset + 4
    end = start + length
    padded_end = end + ((-length) % 4)
    if padded_end > len(data):
        raise ValueError("XDR opaque 数据越过回复边界")
    return data[start:end], padded_end


def mount_filehandle(reply_body: bytes) -> bytes:
    if len(reply_body) < 4:
        raise ValueError("MOUNT 回复不完整")
    status = struct.unpack_from(">I", reply_body)[0]
    if status != 0:
        raise ValueError(f"MOUNT MNT 失败：status={status}")
    handle, _ = opaque_at(reply_body, 4, 64)
    if not handle:
        raise ValueError("MOUNT MNT 返回空文件句柄")
    return handle


def getattr_args(filehandle: bytes) -> bytes:
    return xdr_opaque(filehandle)


def access_args(filehandle: bytes, access: int = 0x3F) -> bytes:
    return xdr_opaque(filehandle) + u32(access)


def lookup_args(directory: bytes, name: str | bytes) -> bytes:
    return xdr_opaque(directory) + xdr_string(name)


def setattr3() -> bytes:
    """创建种子只设置 create mode；其余属性均使用协议的 DONT_CHANGE。"""
    return u32(0) + u32(0) + u32(0) + u32(0) + u32(0) + u32(0)


def create_args(directory: bytes, name: str | bytes, guarded: bool = False) -> bytes:
    create_mode = 1 if guarded else 0
    return xdr_opaque(directory) + xdr_string(name) + u32(create_mode) + setattr3()


def write_args(filehandle: bytes, data: bytes, offset: int = 0) -> bytes:
    return (
        xdr_opaque(filehandle)
        + u64(offset)
        + u32(len(data))
        + u32(2)
        + xdr_opaque(data)
    )


def read_args(filehandle: bytes, offset: int = 0, count: int = 4096) -> bytes:
    return xdr_opaque(filehandle) + u64(offset) + u32(count)


def readdir_args(directory: bytes, count: int = 4096) -> bytes:
    return xdr_opaque(directory) + u64(0) + bytes(8) + u32(count)


def remove_args(directory: bytes, name: str | bytes) -> bytes:
    return lookup_args(directory, name)


def rename_args(
    from_directory: bytes,
    from_name: str | bytes,
    to_directory: bytes,
    to_name: str | bytes,
) -> bytes:
    return lookup_args(from_directory, from_name) + lookup_args(to_directory, to_name)


def parse_optional_handle_after_status(reply_body: bytes, offset: int = 4) -> bytes:
    if nfs_status(reply_body) != 0:
        raise ValueError(f"NFSv3 操作失败：status={nfs_status(reply_body)}")
    if offset + 4 > len(reply_body):
        raise ValueError("NFSv3 post_op_fh3 标记不完整")
    present = struct.unpack_from(">I", reply_body, offset)[0]
    if present != 1:
        raise ValueError("成功响应中没有返回文件句柄")
    handle, _ = opaque_at(reply_body, offset + 4, 64)
    if not handle:
        raise ValueError("NFSv3 返回空文件句柄")
    return handle


def lookup_filehandle(reply_body: bytes) -> bytes:
    """从 NFSv3 LOOKUP 成功响应中取出必需的 object filehandle。"""
    if nfs_status(reply_body) != 0:
        raise ValueError(f"NFSv3 LOOKUP 失败：status={nfs_status(reply_body)}")
    handle, _ = opaque_at(reply_body, 4, 64)
    if not handle:
        raise ValueError("NFSv3 LOOKUP 返回空文件句柄")
    return handle


def parse_read_data(reply_body: bytes) -> bytes:
    if nfs_status(reply_body) != 0:
        raise ValueError(f"NFS READ 失败：status={nfs_status(reply_body)}")
    cursor = 4
    if cursor + 4 > len(reply_body):
        raise ValueError("READ post_op_attr 标记不完整")
    attributes_present = struct.unpack_from(">I", reply_body, cursor)[0]
    cursor += 4
    if attributes_present:
        cursor += 84
    if cursor + 8 > len(reply_body):
        raise ValueError("READ count/eof 字段不完整")
    count = struct.unpack_from(">I", reply_body, cursor)[0]
    cursor += 8
    data, _ = opaque_at(reply_body, cursor, MAX_RECORD)
    if len(data) != count:
        raise ValueError(f"READ count 不匹配：count={count} bytes={len(data)}")
    return data


class RpcClient:
    def __init__(self, port: int, timeout: float = 3.0):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.next_xid = 0x4E465300
        self.responses: list[bytes] = []

    def call(self, program: int, version: int, procedure: int, arguments: bytes) -> bytes:
        self.next_xid = (self.next_xid + 1) & 0xFFFFFFFF
        xid = self.next_xid
        self.sock.sendall(rpc_call(program, version, procedure, arguments, xid))
        wire, payload = receive_record(self.sock)
        self.responses.append(wire)
        return parse_rpc_reply(payload, xid)

    def close(self) -> None:
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def get_root_handle(host: str = "127.0.0.1", port: int = MOUNT_PORT, pseudo: str = NFS_PSEUDO) -> bytes:
    with RpcClient(port) as client:
        body = client.call(MOUNT_PROGRAM, MOUNT_VERSION, 1, xdr_string(pseudo))
    return mount_filehandle(body)


def session_digest(responses: Iterable[bytes]) -> str:
    return hashlib.sha256(b"".join(responses)).hexdigest()
