#!/usr/bin/env python3
"""Small, deterministic iSCSI initiator for smoke checks and seed capture."""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
from pathlib import Path


TARGET = b"iqn.2026-11.invalid:codex-tgt"
INITIATOR = b"iqn.2026-11.invalid:codex-initiator"
ISID = bytes.fromhex("800000000001")


def pdu_length(header: bytes) -> int:
    data_len = int.from_bytes(header[5:8], "big")
    ahs_len = header[4] * 4
    pad = (-data_len) & 3
    return 48 + ahs_len + data_len + pad


def recv_exact(sock: socket.socket, count: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < count:
        part = sock.recv(count - len(chunks))
        if not part:
            raise ConnectionError(f"target closed after {len(chunks)}/{count} bytes")
        chunks.extend(part)
    return bytes(chunks)


def recv_pdu(sock: socket.socket) -> bytes:
    header = recv_exact(sock, 48)
    return header + recv_exact(sock, pdu_length(header) - 48)


def login_pdu(*, stage: int, next_stage: int, tsih: int, itt: int,
              cmdsn: int, expstatsn: int, keys: bytes) -> bytes:
    header = bytearray(48)
    header[0] = 0x43  # immediate Login Request
    header[1] = 0x80 | (stage << 2) | next_stage  # Transit to next stage
    header[4] = 0
    header[5:8] = len(keys).to_bytes(3, "big")
    header[8:14] = ISID
    header[14:16] = tsih.to_bytes(2, "big")
    header[16:20] = itt.to_bytes(4, "big")
    header[20:22] = (0).to_bytes(2, "big")
    header[24:28] = cmdsn.to_bytes(4, "big")
    header[28:32] = expstatsn.to_bytes(4, "big")
    pad = b"\x00" * ((-len(keys)) & 3)
    return bytes(header) + keys + pad


def inquiry_pdu(*, itt: int, cmdsn: int, expstatsn: int) -> bytes:
    header = bytearray(48)
    header[0] = 0x01  # SCSI Command
    header[1] = 0xC0  # Final + Read
    header[16:20] = itt.to_bytes(4, "big")
    header[20:24] = (36).to_bytes(4, "big")
    header[24:28] = cmdsn.to_bytes(4, "big")
    header[28:32] = expstatsn.to_bytes(4, "big")
    header[32] = 0x12  # INQUIRY
    header[36] = 36
    return bytes(header)


def collect_login(sock: socket.socket, req: bytes) -> tuple[bytes, int, int, int]:
    sock.sendall(req)
    response = recv_pdu(sock)
    opcode = response[0] & 0x3F
    if opcode != 0x23:
        raise RuntimeError(f"expected Login Response (0x23), got opcode=0x{opcode:02x}: {response.hex()}")
    status_class, status_detail = response[36], response[37]
    if status_class != 0:
        raise RuntimeError(
            f"iSCSI login rejected: class={status_class} detail={status_detail} pdu={response.hex()}"
        )
    tsih = int.from_bytes(response[14:16], "big")
    expstatsn = (int.from_bytes(response[24:28], "big") + 1) & 0xFFFFFFFF
    next_cmdsn = int.from_bytes(response[28:32], "big")
    return response, tsih, expstatsn, next_cmdsn


def run_smoke(host: str, port: int, save_dir: Path | None) -> dict[str, object]:
    deadline = time.monotonic() + 8
    while True:
        try:
            sock = socket.create_connection((host, port), timeout=1)
            break
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)
    sock.settimeout(5)
    requests: list[bytes] = []
    responses: list[bytes] = []
    try:
        security_keys = (
            b"InitiatorName=" + INITIATOR + b"\x00"
            b"SessionType=Normal\x00"
            b"TargetName=" + TARGET + b"\x00"
            b"AuthMethod=None\x00"
        )
        first = login_pdu(stage=0, next_stage=1, tsih=0, itt=1,
                          cmdsn=1, expstatsn=0, keys=security_keys)
        requests.append(first)
        r1, tsih, expstatsn, cmdsn = collect_login(sock, first)
        responses.append(r1)

        operational_keys = (
            b"HeaderDigest=None\x00DataDigest=None\x00"
            b"MaxConnections=1\x00InitialR2T=Yes\x00ImmediateData=Yes\x00"
            b"MaxRecvDataSegmentLength=8192\x00FirstBurstLength=65536\x00"
            b"MaxBurstLength=262144\x00MaxOutstandingR2T=1\x00"
            b"ErrorRecoveryLevel=0\x00"
        )
        second = login_pdu(stage=1, next_stage=3, tsih=tsih, itt=1,
                           cmdsn=cmdsn, expstatsn=expstatsn,
                           keys=operational_keys)
        requests.append(second)
        r2, tsih, expstatsn, cmdsn = collect_login(sock, second)
        responses.append(r2)

        inquiry = inquiry_pdu(itt=2, cmdsn=cmdsn,
                              expstatsn=expstatsn)
        requests.append(inquiry)
        sock.sendall(inquiry)
        response_pdus: list[bytes] = []
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            pdu = recv_pdu(sock)
            response_pdus.append(pdu)
            op = pdu[0] & 0x3F
            if op in (0x21, 0x25):
                # A target may put SCSI status in a Data-In or a separate response.
                if pdu[3] != 0:
                    raise RuntimeError(f"SCSI Inquiry returned status {pdu[3]}: {pdu.hex()}")
                if op == 0x21 or (pdu[1] & 0x01):
                    break
        if not response_pdus:
            raise TimeoutError("no response to SCSI Inquiry")
        if not any((p[0] & 0x3F) in (0x21, 0x25) for p in response_pdus):
            raise RuntimeError("Inquiry did not produce Data-In or SCSI Response")
        responses.extend(response_pdus)

        raw_seed = b"".join(requests)
        if save_dir is not None:
            save_dir.mkdir(parents=True, exist_ok=True)
            (save_dir / "login-inquiry.bin").write_bytes(raw_seed)
            (save_dir / "login-only.bin").write_bytes(first + second)
            (save_dir / "security-login.bin").write_bytes(first)
            malformed = bytearray(first)
            malformed[5:8] = (0xFFFFFF).to_bytes(3, "big")
            (save_dir / "oversized-login.bin").write_bytes(malformed)
            manifest = []
            for path in sorted(save_dir.glob("*.bin")):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                manifest.append({"file": path.name, "bytes": path.stat().st_size,
                                 "sha256": digest})
            (save_dir / "seeds-manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        return {
            "target_iqn": TARGET.decode(),
            "initiator_iqn": INITIATOR.decode(),
            "port": port,
            "tsih": tsih,
            "request_pdus": len(requests),
            "response_pdus": [p[0] & 0x3F for p in responses],
            "status_classes": [p[36] for p in responses if (p[0] & 0x3F) == 0x23],
            "scsi_statuses": [p[3] for p in response_pdus if (p[0] & 0x3F) in (0x21, 0x25)],
            "seed_bytes": len(raw_seed),
        }
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3260)
    parser.add_argument("--save-seeds", type=Path)
    args = parser.parse_args()
    result = run_smoke(args.host, args.port, args.save_seeds)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
