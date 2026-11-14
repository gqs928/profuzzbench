#!/usr/bin/env python3
"""Atheris target for Impacket's upstream SMB2/SMB3 wire structures."""

import struct
import sys

import atheris

with atheris.instrument_imports():
    from impacket import smb3structs as smb


_EXPECTED_REJECTIONS = (struct.error, IndexError, KeyError, ValueError, UnicodeError)
_COMMANDS = {
    0x0000: ("SMB2Negotiate", "SMB2Negotiate_Response"),
    0x0001: ("SMB2SessionSetup", "SMB2SessionSetup_Response"),
    0x0002: ("SMB2Logoff", "SMB2Logoff_Response"),
    0x0003: ("SMB2TreeConnect", "SMB2TreeConnect_Response"),
    0x0004: ("SMB2TreeDisconnect", "SMB2TreeDisconnect_Response"),
    0x0005: ("SMB2Create", "SMB2Create_Response"),
    0x0006: ("SMB2Close", "SMB2Close_Response"),
    0x0007: ("SMB2Flush", "SMB2Flush_Response"),
    0x0008: ("SMB2Read", "SMB2Read_Response"),
    0x0009: ("SMB2Write", "SMB2Write_Response"),
    0x000A: ("SMB2Lock", "SMB2Lock_Response"),
    0x000B: ("SMB2Ioctl", "SMB2Ioctl_Response"),
    0x000C: ("SMB2Cancel", "SMB2Cancel"),
    0x000D: ("SMB2Echo", "SMB2Echo_Response"),
    0x000E: ("SMB2QueryDirectory", "SMB2QueryDirectory_Response"),
    0x000F: ("SMB2ChangeNotify", "SMB2ChangeNotify_Response"),
    0x0010: ("SMB2QueryInfo", "SMB2QueryInfo_Response"),
    0x0011: ("SMB2SetInfo", "SMB2SetInfo_Response"),
    0x0012: ("SMB2OplockBreakNotification", "SMB2LeaseBreakNotification",
             "SMB2LeaseBreakAcknowledgement"),
}


def _parse(parser, data):
    if parser is None or not data:
        return None
    try:
        return parser(data)
    except _EXPECTED_REJECTIONS:
        return None
    except Exception as exc:
        # Impacket's Structure parser uses plain Exception for malformed
        # constant fields and unterminated wire strings. Keep those ordinary
        # parse rejections separate from unexpected exceptions found by fuzzing.
        message = exc.args[0] if exc.args else str(exc)
        if type(exc) is Exception and isinstance(message, str) and message.startswith(
            ("Unpacked data doesn't match constant value", "Field ")
        ):
            return None
        if type(exc) is Exception and isinstance(message, str) and "not NUL-" in message:
            return None
        raise


def _parse_contexts(parser, data, count=None):
    offset = 0
    remaining = count if count is not None else 16
    for _ in range(min(16, remaining)):
        if offset + 8 > len(data):
            break
        item = _parse(parser, data[offset:])
        if item is None:
            break
        header_length = 16 if "NameLength" in item.fields else 8
        length = header_length + item["DataLength"] + item.fields.get("NameLength", 0)
        next_offset = item["Next"] if "Next" in item.fields and item["Next"] else (length + 7) & ~7
        if next_offset <= 0 or offset + next_offset > len(data):
            break
        offset += next_offset


def _parse_body(command, flags, status, data):
    if not data:
        return
    if status:
        _parse(smb.SMB2Error, data)
        _parse(smb.SMB2ErrorSymbolicLink, data)

    candidates = _COMMANDS.get(command, ())
    if len(candidates) == 3:
        parsers = candidates
    elif candidates:
        name = candidates[1] if flags & smb.SMB2_FLAGS_SERVER_TO_REDIR else candidates[0]
        parsers = (name,)
    else:
        parsers = ()

    parsed = None
    for parser_name in parsers:
        parser = getattr(smb, parser_name, None)
        parsed = _parse(parser, data) or parsed

    # Exercise the upstream nested variable-length structures as well as the
    # outer command structures. Offsets in SMB2 command bodies are relative to
    # the beginning of the 64-byte SMB2 header.
    if command == 0x0000 and not (flags & smb.SMB2_FLAGS_SERVER_TO_REDIR):
        context_offset = int.from_bytes(data[28:32], "little") if len(data) >= 36 else 0
        context_count = int.from_bytes(data[32:34], "little") if len(data) >= 36 else 0
        relative = context_offset - smb.SMB2_PACKET_SIZE
        if context_offset and 0 <= relative < len(data):
            _parse_contexts(smb.SMB2NegotiateContext, data[relative:], context_count)
        _parse(smb.SMB2PreAuthIntegrityCapabilities, data)
        _parse(smb.SMB2EncryptionCapabilities, data)
        _parse(smb.SMB2CompressionCapabilities, data)

    if command == 0x0005 and parsed is not None:
        context_offset = parsed.fields.get("CreateContextsOffset", 0)
        context_length = parsed.fields.get("CreateContextsLength", 0)
        relative = context_offset - smb.SMB2_PACKET_SIZE
        if context_length and 0 <= relative < len(data):
            end = min(len(data), relative + context_length)
            _parse_contexts(smb.SMB2CreateContext, data[relative:end])



def _parse_packet(data):
    if data.startswith(b"\xfdSMB"):
        _parse(smb.SMB2_TRANSFORM_HEADER, data)
        return
    if data.startswith(b"\xfcSMB"):
        _parse(smb.SMB2_COMPRESSION_TRANSFORM_HEADER, data)
        _parse(smb.SMB2_COMPRESSION_PAYLOAD_HEADER, data[16:])
        _parse(smb.SMB2_COMPRESSION_PATTERN_PAYLOAD_V1, data[16:])
        return
    if not data.startswith(b"\xfeSMB"):
        return

    offset = 0
    for _ in range(16):
        if len(data) - offset < smb.SMB2_PACKET_SIZE:
            break
        packet_data = data[offset:]
        packet = _parse(smb.SMB2Packet, packet_data)
        # SMB3 uses a related but distinct request header layout. Parse it too
        # so the harness covers both upstream header structures.
        _parse(smb.SMB3Packet, packet_data)
        if packet is None:
            break
        command = int.from_bytes(packet_data[12:14], "little")
        flags = int.from_bytes(packet_data[16:20], "little")
        next_command = int.from_bytes(packet_data[20:24], "little")
        segment_length = next_command if next_command >= smb.SMB2_PACKET_SIZE and next_command <= len(packet_data) else len(packet_data)
        body = packet_data[smb.SMB2_PACKET_SIZE:segment_length]
        # In requests these four bytes are channel-sequence/reserved fields,
        # not an NTSTATUS value; only responses carry Status here.
        status = packet["Status"] if flags & smb.SMB2_FLAGS_SERVER_TO_REDIR else 0
        _parse_body(command, flags, status, body)
        if next_command < smb.SMB2_PACKET_SIZE or next_command > len(packet_data):
            break
        offset += next_command


def TestOneInput(data):
    # Accept either raw SMB2/3 PDUs or one RFC 1002 session-message frame.
    if len(data) >= 8 and data[:1] == b"\x00" and data[4:8] in (b"\xfeSMB", b"\xfdSMB", b"\xfcSMB"):
        frame_length = int.from_bytes(data[1:4], "big")
        if 0 < frame_length <= len(data) - 4:
            data = data[4:4 + frame_length]
    _parse_packet(data)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
