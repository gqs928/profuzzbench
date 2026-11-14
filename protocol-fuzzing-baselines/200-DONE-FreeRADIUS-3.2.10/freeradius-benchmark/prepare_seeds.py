#!/usr/bin/env python3
"""生成可重复的 RADIUS/TCP 认证和记账会话种子。"""

import hashlib
import hmac
import json
import pathlib
import sys


SECRET = b"testing123"
OUTPUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")


def attribute(kind: int, value: bytes) -> bytes:
    if len(value) > 253:
        raise ValueError("RADIUS 属性值超过协议上限")
    return bytes((kind, len(value) + 2)) + value


def packet(code: int, identifier: int, authenticator: bytes, attributes: bytes) -> bytes:
    length = 20 + len(attributes)
    if length > 4096:
        raise ValueError("RADIUS 测试报文超过基准上限")
    return bytes((code, identifier)) + length.to_bytes(2, "big") + authenticator + attributes


def pap_password(password: bytes, authenticator: bytes) -> bytes:
    padded = password + bytes((-len(password)) % 16)
    if not padded:
        padded = bytes(16)
    result = bytearray()
    previous = authenticator
    for offset in range(0, len(padded), 16):
        mask = hashlib.md5(SECRET + previous).digest()
        block = padded[offset : offset + 16]
        result.extend(left ^ right for left, right in zip(block, mask))
        previous = result[-16:]
    return bytes(result)


def with_message_authenticator(
    code: int, identifier: int, authenticator: bytes, attributes: bytes
) -> bytes:
    """按 RFC 2869 生成 Message-Authenticator，计算时把属性值置零。"""
    placeholder = attribute(80, bytes(16))
    unsigned = packet(code, identifier, authenticator, attributes + placeholder)
    digest = hmac.new(SECRET, unsigned, hashlib.md5).digest()
    return packet(code, identifier, authenticator, attributes + attribute(80, digest))


def access(identifier: int, password: bytes) -> bytes:
    authenticator = bytes((identifier + index) & 0xFF for index in range(16))
    attributes = b"".join(
        (
            attribute(1, b"alice"),
            attribute(2, pap_password(password, authenticator)),
            attribute(4, bytes((127, 0, 0, 1))),
            attribute(5, (7).to_bytes(4, "big")),
            attribute(6, (1).to_bytes(4, "big")),
        )
    )
    return with_message_authenticator(1, identifier, authenticator, attributes)


def accounting(identifier: int, status: int) -> bytes:
    attributes = b"".join(
        (
            attribute(1, b"alice"),
            attribute(4, bytes((127, 0, 0, 1))),
            attribute(5, (7).to_bytes(4, "big")),
            attribute(40, status.to_bytes(4, "big")),
            attribute(44, b"fuzzbench-session-0001"),
        )
    )
    request = packet(4, identifier, bytes(16), attributes)
    authenticator = hashlib.md5(request + SECRET).digest()
    return packet(4, identifier, authenticator, attributes)


def main() -> None:
    manifest_path = pathlib.Path(
        sys.argv[2] if len(sys.argv) > 2 else OUTPUT.parent / f"{OUTPUT.name}-manifest.json"
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for old_seed in OUTPUT.glob("*.bin"):
        old_seed.unlink()
    (OUTPUT / "manifest.json").unlink(missing_ok=True)
    seeds = {
        "access-accept.bin": access(1, b"wonderland"),
        "access-reject.bin": access(2, b"wrong-password"),
        "accounting-start.bin": accounting(3, 1),
        "accounting-stop.bin": accounting(4, 2),
        "login-accounting-sequence.bin": (
            access(5, b"wonderland") + accounting(6, 1) + accounting(7, 2)
        ),
        "reject-retry-sequence.bin": (
            access(8, b"wrong-password") + access(9, b"wonderland")
        ),
    }
    manifest = []
    for name, data in sorted(seeds.items()):
        path = OUTPUT / name
        path.write_bytes(data)
        manifest.append(
            {
                "file": name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "requests": len(list(iter_packets(data))),
            }
        )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def iter_packets(data: bytes):
    cursor = 0
    while cursor + 4 <= len(data):
        size = int.from_bytes(data[cursor + 2 : cursor + 4], "big")
        if size < 20 or cursor + size > len(data):
            return
        yield data[cursor : cursor + size]
        cursor += size


if __name__ == "__main__":
    main()
