#!/usr/bin/env python3
"""Build a small deterministic SMB2/3 seed corpus from Impacket structures."""

from pathlib import Path
from impacket import smb3structs as smb


OUT = Path(__file__).with_name("seeds")


def packet(command, body, response=False):
    header = smb.SMB2Packet()
    header["Command"] = command
    header["MessageID"] = 1
    header["CreditRequestResponse"] = 32
    if response:
        header["Flags"] = smb.SMB2_FLAGS_SERVER_TO_REDIR
    header["Data"] = body.getData()
    return header.getData()


def add(name, data):
    (OUT / name).write_bytes(data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for child in OUT.iterdir():
        if child.is_file():
            child.unlink()

    negotiate = smb.SMB2Negotiate()
    negotiate["DialectCount"] = 5
    negotiate["SecurityMode"] = smb.SMB2_NEGOTIATE_SIGNING_ENABLED
    negotiate["ClientGuid"] = bytes(range(16))
    negotiate["ClientStartTime"] = b"\x00" * 8
    negotiate["Dialects"] = [smb.SMB2_DIALECT_002, smb.SMB2_DIALECT_21,
                             smb.SMB2_DIALECT_30, smb.SMB2_DIALECT_302,
                             smb.SMB2_DIALECT_311]
    add("smb2-negotiate-request", packet(smb.SMB2_NEGOTIATE, negotiate))

    smb3_header = smb.SMB3Packet()
    smb3_header["Command"] = smb.SMB2_NEGOTIATE
    smb3_header["MessageID"] = 1
    smb3_header["CreditRequestResponse"] = 32
    smb3_header["Data"] = negotiate.getData()
    add("smb3-negotiate-request", smb3_header.getData())

    negotiate_response = smb.SMB2Negotiate_Response()
    negotiate_response["SecurityMode"] = smb.SMB2_NEGOTIATE_SIGNING_ENABLED
    negotiate_response["DialectRevision"] = smb.SMB2_DIALECT_311
    negotiate_response["ServerGuid"] = bytes(range(16, 32))
    negotiate_response["Capabilities"] = smb.SMB2_GLOBAL_CAP_LARGE_MTU | smb.SMB2_GLOBAL_CAP_ENCRYPTION
    negotiate_response["MaxTransactSize"] = 65536
    negotiate_response["MaxReadSize"] = 65536
    negotiate_response["MaxWriteSize"] = 65536
    negotiate_response["AlignPad"] = b""
    negotiate_response["Buffer"] = b""
    negotiate_response["Padding"] = b""
    negotiate_response["NegotiateContextList"] = b""
    add("smb2-negotiate-response", packet(smb.SMB2_NEGOTIATE, negotiate_response, True))

    session_setup = smb.SMB2SessionSetup()
    session_setup["SecurityMode"] = smb.SMB2_NEGOTIATE_SIGNING_ENABLED
    session_setup["Buffer"] = b"NTLMSSP\x00\x01\x00\x00\x00"
    session_setup["SecurityBufferLength"] = len(session_setup["Buffer"])
    add("smb2-session-setup-request", packet(smb.SMB2_SESSION_SETUP, session_setup))

    tree_connect = smb.SMB2TreeConnect()
    tree_connect["Buffer"] = "\\\\SERVER\\SHARE".encode("utf-16le")
    tree_connect["PathLength"] = len(tree_connect["Buffer"])
    add("smb2-tree-connect-request", packet(smb.SMB2_TREE_CONNECT, tree_connect))

    create = smb.SMB2Create()
    create["DesiredAccess"] = 0x00120089
    create["ShareAccess"] = 7
    create["CreateDisposition"] = 1
    create["CreateOptions"] = 0x40
    create["Buffer"] = "\\fuzz.bin".encode("utf-16le")
    create["NameLength"] = len(create["Buffer"])
    add("smb2-create-request", packet(smb.SMB2_CREATE, create))

    write = smb.SMB2Write()
    write["Length"] = 12
    write["Buffer"] = b"seed-payload"
    write["FileID"] = smb.SMB2_FILEID()
    add("smb2-write-request", packet(smb.SMB2_WRITE, write))

    read = smb.SMB2Read()
    read["Length"] = 4096
    read["MinimumCount"] = 1
    read["FileID"] = smb.SMB2_FILEID()
    add("smb2-read-request", packet(smb.SMB2_READ, read))

    echo_response = smb.SMB2Echo()
    add("smb2-echo-response", packet(smb.SMB2_ECHO, echo_response, True))

    compressed = smb.SMB2_COMPRESSION_TRANSFORM_HEADER()
    compressed["ProtocolID"] = int.from_bytes(b"\xfcSMB", "little")
    compressed["OriginalCompressedSegmentSize"] = 128
    compressed["CompressionAlgorithm"] = 4
    compressed["Flags"] = 0
    compressed["Offset_Length"] = 0
    add("smb3-compression-header", compressed.getData() + b"\x41\x00\x00\x00\x20\x00\x00\x00A")

    encrypted = smb.SMB2_TRANSFORM_HEADER()
    encrypted["Signature"] = b"\x11" * 16
    encrypted["Nonce"] = b"\x22" * 16
    encrypted["OriginalMessageSize"] = 64
    encrypted["EncryptionAlgorithm"] = smb.SMB2_ENCRYPTION_AES128_GCM
    encrypted["SessionID"] = 1
    add("smb3-encryption-header", encrypted.getData() + b"\x00" * 64)

    first = smb.SMB2Packet()
    first["Command"] = smb.SMB2_ECHO
    first["MessageID"] = 2
    first["NextCommand"] = 72
    first["Data"] = smb.SMB2Echo().getData() + b"\x00" * 4
    second = smb.SMB2Packet()
    second["Command"] = smb.SMB2_LOGOFF
    second["MessageID"] = 3
    second["Data"] = smb.SMB2Logoff().getData()
    add("smb2-compound-echo-logoff", first.getData() + second.getData())

    # Keep both transport forms because Impacket's callers may hand the parser
    # either a bare PDU or its RFC 1002 session-message payload.
    for child in list(OUT.iterdir()):
        if child.is_file() and child.name.startswith(("smb2-", "smb3-")):
            payload = child.read_bytes()
            frame = b"\x00" + len(payload).to_bytes(3, "big") + payload
            add(child.name + "-netbios", frame)


if __name__ == "__main__":
    main()
