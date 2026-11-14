#!/usr/bin/env python3
"""确定性地产生 Kafka 原生二进制协议会话语料。"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


TOPIC = "fuzz-topic"
CLIENT_ID = b"kafka-fuzz-bench"


def i8(value: int) -> bytes:
    return struct.pack(">b", value)


def i16(value: int) -> bytes:
    return struct.pack(">h", value)


def u16(value: int) -> bytes:
    return struct.pack(">H", value)


def i32(value: int) -> bytes:
    return struct.pack(">i", value)


def u32(value: int) -> bytes:
    return struct.pack(">I", value)


def i64(value: int) -> bytes:
    return struct.pack(">q", value)


def kafka_string(value: str | bytes) -> bytes:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return i16(len(raw)) + raw


def frame(api_key: int, api_version: int, correlation_id: int, body: bytes,
          *, client_id: bytes = CLIENT_ID) -> bytes:
    header = u16(api_key) + u16(api_version) + u32(correlation_id) + kafka_string(client_id)
    request = header + body
    return u32(len(request)) + request


def api_versions(correlation_id: int = 1) -> bytes:
    return frame(18, 0, correlation_id, b"")


def metadata(correlation_id: int = 2, topic: str = TOPIC) -> bytes:
    return frame(3, 1, correlation_id, i32(1) + kafka_string(topic))


def _crc32c(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def _varint(value: int) -> bytes:
    # Kafka 使用 ZigZag 编码的有符号变长整数。
    encoded = (value << 1) ^ (value >> 31)
    out = bytearray()
    while encoded & ~0x7F:
        out.append((encoded & 0x7F) | 0x80)
        encoded >>= 7
    out.append(encoded)
    return bytes(out)


def _record_batch(value: bytes) -> bytes:
    record_tail = b"\x00" + _varint(0) + _varint(0) + _varint(-1) \
        + _varint(len(value)) + value + _varint(0)
    record = _varint(len(record_tail)) + record_tail
    post_crc = (i16(0) + i32(0) + i64(0) + i64(0) + i64(-1)
                + i16(-1) + i32(-1) + i32(1) + record)
    crc = _crc32c(post_crc)
    remainder = i32(-1) + b"\x02" + u32(crc) + post_crc
    batch_length = len(remainder)
    return i64(0) + i32(batch_length) + remainder


def produce(correlation_id: int = 3, value: bytes = b"benchmark-record") -> bytes:
    records = _record_batch(value)
    body = (i16(1) + i32(5000) + i32(1) + kafka_string(TOPIC)
            + i32(1) + i32(0) + i32(len(records)) + records)
    # Produce v3 在 acks 和 timeout 前包含可空的 transactional_id。
    body = i16(-1) + body
    return frame(0, 3, correlation_id, body)


def fetch(correlation_id: int = 4) -> bytes:
    # Kafka 4.2 已不接受 Fetch v0；v4 在主题数组前增加大小上限和隔离级别。
    body = (i32(-1) + i32(100) + i32(0) + i32(1_048_576) + i8(0)
            + i32(1) + kafka_string(TOPIC)
            + i32(1) + i32(0) + i64(0) + i32(1_048_576))
    return frame(1, 4, correlation_id, body)


def list_offsets(correlation_id: int = 5) -> bytes:
    body = (i32(-1) + i32(1) + kafka_string(TOPIC) + i32(1) + i32(0)
            + i16(1) + i64(-1))
    return frame(2, 1, correlation_id, body)


def find_coordinator(correlation_id: int = 6) -> bytes:
    # FindCoordinator v0 使用 group id 定位协调器。
    return frame(10, 0, correlation_id, kafka_string("fuzz-group"))


def invalid_api_version() -> bytes:
    return frame(18, 32767, 7, b"")


def invalid_api_key() -> bytes:
    return frame(32767, 0, 8, b"")


def make_seeds() -> dict[str, bytes]:
    versions = api_versions()
    meta = metadata()
    write = produce()
    read = fetch()
    offsets = list_offsets()
    coordinator = find_coordinator()
    truncated = u32(128) + u16(18) + u16(0) + u32(9) + kafka_string(CLIENT_ID)
    return {
        "api-versions.bin": versions,
        "metadata.bin": meta,
        "versions-metadata.bin": versions + meta,
        "metadata-produce.bin": meta + write,
        "produce-fetch.bin": write + read,
        "stateful-roundtrip.bin": versions + meta + write + read,
        "offsets-coordinator.bin": offsets + coordinator,
        "unsupported-version.bin": invalid_api_version(),
        "unknown-api-key.bin": invalid_api_key(),
        "truncated-frame.bin": truncated,
    }


def read_api_keys(data: bytes) -> list[int | str]:
    result: list[int | str] = []
    cursor = 0
    while cursor + 4 <= len(data):
        length = struct.unpack_from(">I", data, cursor)[0]
        end = cursor + 4 + length
        if length < 8 or end > len(data):
            result.append("畸形或截断尾帧")
            break
        result.append(struct.unpack_from(">H", data, cursor + 4)[0])
        cursor = end
    return result


def main() -> int:
    if len(sys.argv) != 3:
        print("用法：prepare_seeds.py 输出目录 manifest.json", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError(f"种子输出目录必须为空：{output}")
    entries = []
    for name, data in sorted(make_seeds().items()):
        path = output / name
        path.write_bytes(data)
        entries.append({
            "name": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "api_keys": read_api_keys(data),
        })
    manifest = {
        "protocol": "Apache Kafka TCP request frames",
        "topic": TOPIC,
        "request_frame_length": "4-byte big-endian length prefix, excluding prefix",
        "correlation_id_states": {
            "1": "ApiVersions response",
            "2": "Metadata response",
            "3": "Produce response",
            "4": "Fetch response",
            "5": "ListOffsets response",
            "6": "FindCoordinator response",
        },
        "seeds": entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
