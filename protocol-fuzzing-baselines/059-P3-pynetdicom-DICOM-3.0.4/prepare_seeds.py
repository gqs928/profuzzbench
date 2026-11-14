#!/usr/bin/env python3
"""Build compact DICOM UL sessions for the Verification and Storage SCPs."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
APP_CONTEXT = "1.2.840.10008.3.1.1.1"
IMPLICIT_LE = "1.2.840.10008.1.2"
EXPLICIT_LE = "1.2.840.10008.1.2.1"
VERIFICATION = "1.2.840.10008.1.1"
SECONDARY_CAPTURE = "1.2.840.10008.5.1.4.1.1.7"
IMPLEMENTATION_UID = "1.2.826.0.1.3680043.10.543.1"


def uid(value: str) -> bytes:
    out = value.encode("ascii")
    return out + (b"\0" if len(out) & 1 else b"")


def text(value: str) -> bytes:
    out = value.encode("ascii")
    return out + (b" " if len(out) & 1 else b"")


def item(kind: int, payload: bytes) -> bytes:
    return bytes((kind, 0)) + struct.pack(">H", len(payload)) + payload


def pdu(kind: int, body: bytes) -> bytes:
    return bytes((kind, 0)) + struct.pack(">I", len(body)) + body


def presentation_context(context_id: int, abstract_syntax: str,
                         transfer_syntaxes: tuple[str, ...]) -> bytes:
    fields = bytes((context_id, 0, 0, 0))
    fields += item(0x30, uid(abstract_syntax))
    for transfer_syntax in transfer_syntaxes:
        fields += item(0x40, uid(transfer_syntax))
    return item(0x20, fields)


def associate_request(called: str = "STORESCP") -> bytes:
    called_ae = called.encode("ascii")[:16].ljust(16, b" ")
    calling_ae = b"PROFUZZ".ljust(16, b" ")
    fixed = struct.pack(">HH", 1, 0) + called_ae + calling_ae + bytes(32)
    variable = item(0x10, uid(APP_CONTEXT))
    variable += presentation_context(1, VERIFICATION, (IMPLICIT_LE,))
    variable += presentation_context(3, SECONDARY_CAPTURE,
                                     (IMPLICIT_LE, EXPLICIT_LE))
    user = item(0x51, struct.pack(">I", 16384))
    user += item(0x52, uid(IMPLEMENTATION_UID))
    user += item(0x55, b"PROFZ5801")
    variable += item(0x50, user)
    return pdu(0x01, fixed + variable)


def command_element(group: int, element: int, value: bytes) -> bytes:
    return struct.pack("<HHI", group, element, len(value)) + value


def command_set(fields: bytes) -> bytes:
    return command_element(0x0000, 0x0000, struct.pack("<I", len(fields))) + fields


def command_pdata(context_id: int, command: bytes) -> bytes:
    pdv = bytes((context_id, 0x03)) + command
    return pdu(0x04, struct.pack(">I", len(pdv)) + pdv)


def dataset_pdata(context_id: int, dataset: bytes) -> bytes:
    pdv = bytes((context_id, 0x02)) + dataset
    return pdu(0x04, struct.pack(">I", len(pdv)) + pdv)


def make_echo() -> bytes:
    fields = command_element(0x0000, 0x0002, uid(VERIFICATION))
    fields += command_element(0x0000, 0x0100, struct.pack("<H", 0x0030))
    fields += command_element(0x0000, 0x0110, struct.pack("<H", 1))
    fields += command_element(0x0000, 0x0800, struct.pack("<H", 0x0101))
    return command_set(fields)


def make_store() -> bytes:
    fields = command_element(0x0000, 0x0002, uid(SECONDARY_CAPTURE))
    fields += command_element(0x0000, 0x0100, struct.pack("<H", 0x0001))
    fields += command_element(0x0000, 0x0110, struct.pack("<H", 2))
    fields += command_element(0x0000, 0x0700, struct.pack("<H", 0))
    fields += command_element(0x0000, 0x0800, struct.pack("<H", 0x0000))
    fields += command_element(0x0000, 0x1000,
                              uid("1.2.826.0.1.3680043.10.543.1.1"))
    return command_set(fields)


def make_dataset() -> bytes:
    fields = bytearray()
    fields += command_element(0x0008, 0x0016, uid(SECONDARY_CAPTURE))
    fields += command_element(0x0008, 0x0018,
                              uid("1.2.826.0.1.3680043.10.543.1.1"))
    fields += command_element(0x0008, 0x0060, text("OT"))
    fields += command_element(0x0010, 0x0010, text("FUZZ^BASELINE"))
    fields += command_element(0x0010, 0x0020, text("BENCH-001"))
    fields += command_element(0x0020, 0x000D,
                              uid("1.2.826.0.1.3680043.10.543.2.1"))
    fields += command_element(0x0020, 0x000E,
                              uid("1.2.826.0.1.3680043.10.543.2.2"))
    fields += command_element(0x0028, 0x0002, struct.pack("<H", 1))
    fields += command_element(0x0028, 0x0004, text("MONOCHROME2"))
    fields += command_element(0x0028, 0x0010, struct.pack("<H", 1))
    fields += command_element(0x0028, 0x0011, struct.pack("<H", 1))
    fields += command_element(0x0028, 0x0100, struct.pack("<H", 8))
    fields += command_element(0x0028, 0x0101, struct.pack("<H", 8))
    fields += command_element(0x0028, 0x0102, struct.pack("<H", 7))
    fields += command_element(0x0028, 0x0103, struct.pack("<H", 0))
    fields += command_element(0x7FE0, 0x0010, bytes((0x5A, 0)))
    return bytes(fields)


def build_sessions() -> dict[str, tuple[str, bytes]]:
    assoc = associate_request()
    release = pdu(0x05, bytes(4))
    echo = assoc + command_pdata(1, make_echo()) + release
    store = (assoc + command_pdata(3, make_store()) +
             dataset_pdata(3, make_dataset()) + release)
    return {
        "association-only.bin": ("valid association request", assoc),
        "valid-c-echo.bin": ("association, C-ECHO, release", echo),
        "valid-c-store.bin": ("association, one-pixel Secondary Capture C-STORE, release", store),
        "truncated-pdu.bin": ("truncated DICOM UL PDU header", b"\x01\x00\x00\x00\x00"),
        "invalid-pdu-length.bin": ("oversized DICOM UL PDU length", b"\x04\x00\xff\xff\xff\xff"),
    }


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, (description, data) in build_sessions().items():
        (SEEDS / name).write_bytes(data)
        manifest.append({"file": name, "description": description,
                         "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
    (ROOT / "seeds-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} DICOM UL sessions to {SEEDS}")


if __name__ == "__main__":
    main()
