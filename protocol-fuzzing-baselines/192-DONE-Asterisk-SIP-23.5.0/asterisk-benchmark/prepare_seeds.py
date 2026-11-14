#!/usr/bin/env python3
"""可重复生成 SIP/TCP 会话种子和逐文件 SHA-256 清单。"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re


SDP = (
    b"v=0\r\n"
    b"o=alice 1 1 IN IP4 127.0.0.1\r\n"
    b"s=Asterisk SIP fuzz seed\r\n"
    b"c=IN IP4 127.0.0.1\r\n"
    b"t=0 0\r\n"
    b"m=audio 4000 RTP/AVP 0\r\n"
    b"a=rtpmap:0 PCMU/8000\r\n"
)


def request(
    method: str,
    target: str,
    call_id: str,
    cseq: int,
    branch: str,
    from_tag: str,
    *,
    body: bytes = b"",
    headers: tuple[tuple[str, str], ...] = (),
) -> bytes:
    rows = [
        f"{method} {target} SIP/2.0",
        f"Via: SIP/2.0/TCP 127.0.0.1:5061;branch={branch}",
        "Max-Forwards: 70",
        f"From: <sip:alice@127.0.0.1>;tag={from_tag}",
        # 与 Request-URI 保持同一 SIP 域，确保 REGISTER 种子走真实注册路径。
        f"To: <{target}>",
        f"Call-ID: {call_id}",
        f"CSeq: {cseq} {method}",
        "Contact: <sip:alice@127.0.0.1:5061;transport=tcp>",
        "User-Agent: Asterisk-SIP-Fuzz-Benchmark",
    ]
    rows.extend(f"{name}: {value}" for name, value in headers)
    if body and not any(name.lower() == "content-type" for name, _ in headers):
        rows.append("Content-Type: application/sdp")
    rows.append(f"Content-Length: {len(body)}")
    return ("\r\n".join(rows) + "\r\n\r\n").encode("ascii") + body


def sessions() -> dict[str, tuple[bytes, int, str]]:
    options = request(
        "OPTIONS", "sip:100@127.0.0.1", "options@127.0.0.1", 1,
        "z9hG4bK-options", "options",
    )
    register = request(
        "REGISTER", "sip:alice@127.0.0.1", "register@127.0.0.1", 1,
        "z9hG4bK-register", "register",
        headers=(("Expires", "300"),),
    )
    unregister = request(
        "REGISTER", "sip:alice@127.0.0.1", "unregister@127.0.0.1", 1,
        "z9hG4bK-unregister", "unregister",
        headers=(("Expires", "0"),),
    )
    invite = request(
        "INVITE", "sip:100@127.0.0.1", "dialog@127.0.0.1", 2,
        "z9hG4bK-dialog", "dialog", body=SDP,
        headers=(("Allow", "INVITE, ACK, CANCEL, BYE, OPTIONS"),),
    )
    cancel = request(
        "CANCEL", "sip:100@127.0.0.1", "dialog@127.0.0.1", 2,
        "z9hG4bK-dialog", "dialog",
    )
    bye = request(
        "BYE", "sip:100@127.0.0.1", "bye@127.0.0.1", 3,
        "z9hG4bK-bye", "bye",
    )
    ack = request(
        "ACK", "sip:100@127.0.0.1", "ack@127.0.0.1", 2,
        "z9hG4bK-ack", "ack",
    )
    message_body = b"fuzz seed message\r\n"
    message = request(
        "MESSAGE", "sip:100@127.0.0.1", "message@127.0.0.1", 1,
        "z9hG4bK-message", "message", body=message_body,
        headers=(("Content-Type", "text/plain"),),
    )
    sdp_invite = request(
        "INVITE", "sip:100@127.0.0.1", "sdp@127.0.0.1", 1,
        "z9hG4bK-sdp", "sdp", body=SDP,
    )
    bad_length = (
        b"OPTIONS sip:alice@127.0.0.1 SIP/2.0\r\n"
        b"Via: SIP/2.0/TCP 127.0.0.1:5061;branch=z9hG4bK-truncated\r\n"
        b"From: <sip:alice@127.0.0.1>;tag=truncated\r\n"
        b"To: <sip:alice@127.0.0.1>\r\n"
        b"Call-ID: truncated@127.0.0.1\r\n"
        b"CSeq: 1 OPTIONS\r\n"
        b"Content-Length: 80\r\n\r\nshort"
    )
    return {
        "01-options": (options, 1, "OPTIONS 正常探测"),
        "02-register": (register, 1, "REGISTER 成功注册"),
        "03-unregister": (unregister, 1, "REGISTER 注销"),
        "04-register-options": (register + options, 2, "注册后查询能力"),
        "05-invite-cancel": (invite + cancel, 2, "INVITE 后 CANCEL 事务"),
        "06-register-invite-cancel": (
            register + invite + cancel, 3, "注册后呼叫并取消"),
        "07-sdp-invite": (sdp_invite, 1, "带 SDP 的 INVITE"),
        "08-ack": (ack, 1, "ACK 请求边界"),
        "09-bye": (bye, 1, "BYE 请求边界"),
        "10-message": (message, 1, "MESSAGE 正文解析"),
        "11-truncated-length": (bad_length, 1, "声明长度大于实际正文"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成固定的 SIP/TCP 会话语料")
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, (data, request_count, purpose) in sessions().items():
        filename = f"{name}.bin"
        (args.output / filename).write_bytes(data)
        manifest.append({
            "file": filename,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "request_count": request_count,
            "purpose": purpose,
            "methods": [
                match.decode("ascii")
                for match in re.findall(rb"(?m)^([A-Z]+) sip:", data)
            ],
        })
    (args.output / "seeds-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
