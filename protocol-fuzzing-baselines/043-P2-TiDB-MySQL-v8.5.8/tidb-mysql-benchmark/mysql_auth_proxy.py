#!/usr/bin/env python3
"""Loopback-only proxy: authenticate to a MySQL-family server, then expose SQL wire traffic to AFLNet."""
from __future__ import annotations
import argparse
import hashlib
import os
import select
import socket
import subprocess
import tempfile
import threading
from pathlib import Path

MAX_PACKET = 0xFFFFFF
CLIENT_LONG_PASSWORD = 0x00000001
CLIENT_LONG_FLAG = 0x00000004
CLIENT_CONNECT_WITH_DB = 0x00000008
CLIENT_PROTOCOL_41 = 0x00000200
CLIENT_TRANSACTIONS = 0x00002000
CLIENT_SECURE_CONNECTION = 0x00008000
CLIENT_PLUGIN_AUTH = 0x00080000

class ProtocolError(Exception):
    pass

def recv_exact(sock: socket.socket, count: int) -> bytes:
    out = bytearray()
    while len(out) < count:
        part = sock.recv(count - len(out))
        if not part:
            raise ConnectionError("peer closed during MySQL packet")
        out.extend(part)
    return bytes(out)

def recv_packet(sock: socket.socket) -> tuple[int, bytes]:
    header = recv_exact(sock, 4)
    length = header[0] | (header[1] << 8) | (header[2] << 16)
    if length > MAX_PACKET:
        raise ProtocolError(f"oversized MySQL packet: {length}")
    return header[3], recv_exact(sock, length)

def packet(sequence: int, payload: bytes) -> bytes:
    n = len(payload)
    if n > MAX_PACKET:
        raise ProtocolError(f"outgoing packet too large: {n}")
    return bytes((n & 255, (n >> 8) & 255, (n >> 16) & 255, sequence & 255)) + payload

def nul_field(data: bytes, start: int) -> tuple[bytes, int]:
    end = data.find(b"\0", start)
    if end < 0:
        raise ProtocolError("unterminated handshake field")
    return data[start:end], end + 1

def parse_greeting(payload: bytes) -> tuple[int, bytes, str]:
    if not payload or payload[0] != 10:
        raise ProtocolError("unsupported MySQL greeting protocol")
    _, pos = nul_field(payload, 1)
    pos += 4
    salt1 = payload[pos:pos + 8]
    pos += 8
    if pos >= len(payload):
        raise ProtocolError("truncated MySQL greeting")
    pos += 1
    low = int.from_bytes(payload[pos:pos + 2], "little")
    pos += 2
    caps = low
    salt2 = b""
    plugin = "mysql_native_password"
    if pos + 1 < len(payload):
        pos += 1  # character set
        pos += 2  # status flags
        caps |= int.from_bytes(payload[pos:pos + 2], "little") << 16
        pos += 2
        auth_len = payload[pos] if pos < len(payload) else 0
        pos += 1 + 10
        if caps & CLIENT_SECURE_CONNECTION and pos < len(payload):
            take = min(max(13, auth_len - 8), len(payload) - pos)
            salt2 = payload[pos:pos + take].rstrip(b"\0")
            pos += take
        if caps & CLIENT_PLUGIN_AUTH and pos < len(payload):
            raw, _ = nul_field(payload, pos)
            if raw:
                plugin = raw.decode("ascii", "replace")
    salt = (salt1 + salt2).rstrip(b"\0")
    if len(salt) < 8:
        raise ProtocolError("greeting lacks a usable authentication salt")
    return caps, salt, plugin

def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

def auth_token(plugin: str, password: str, salt: bytes) -> bytes:
    raw = password.encode("utf-8")
    if plugin == "mysql_native_password":
        if not raw:
            return b""
        one = hashlib.sha1(raw).digest()
        two = hashlib.sha1(one).digest()
        three = hashlib.sha1(salt + two).digest()
        return xor_bytes(one, three)
    if plugin == "caching_sha2_password":
        if not raw:
            return b""
        one = hashlib.sha256(raw).digest()
        two = hashlib.sha256(one).digest()
        three = hashlib.sha256(two + salt).digest()
        return xor_bytes(one, three)
    if plugin == "sha256_password":
        # Ask the server for its RSA key; handle the key response after the first reply.
        return b"\x01"
    if plugin == "mysql_clear_password":
        if not salt or not password:
            return raw + b"\0"
        return raw + b"\0"
    raise ProtocolError(f"unsupported MySQL authentication plugin {plugin!r}")

def auth_switch(payload: bytes) -> tuple[str, bytes]:
    raw = payload[1:]
    plugin_b, pos = nul_field(raw, 0)
    name = plugin_b.decode("ascii", "replace")
    return name, raw[pos:].rstrip(b"\0")

def rsa_encrypt(password: str, salt: bytes, pem: bytes) -> bytes:
    secret = password.encode("utf-8") + b"\0"
    masked = xor_bytes(secret, (salt * ((len(secret) + len(salt) - 1) // len(salt)))[:len(secret)])
    with tempfile.TemporaryDirectory(prefix="mysql-auth-") as tmp:
        key = Path(tmp) / "server-public.pem"
        plain = Path(tmp) / "password.bin"
        cipher = Path(tmp) / "password.enc"
        key.write_bytes(pem)
        plain.write_bytes(masked)
        cmd = ["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(key),
               "-in", str(plain), "-out", str(cipher), "-pkeyopt", "rsa_padding_mode:oaep",
               "-pkeyopt", "rsa_oaep_md:sha1", "-pkeyopt", "rsa_mgf1_md:sha1"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return cipher.read_bytes()

def complete_auth(up: socket.socket, first_seq: int, payload: bytes,
                  plugin: str, salt: bytes, password: str) -> None:
    seq = first_seq
    current_plugin = plugin
    current_salt = salt
    while True:
        if payload[:1] == b"\x00":
            return
        if payload[:1] == b"\xff":
            code = int.from_bytes(payload[1:3], "little") if len(payload) >= 3 else -1
            raise ProtocolError(f"backend authentication error {code}")
        if payload[:1] == b"\xfe" and len(payload) > 1:
            current_plugin, current_salt = auth_switch(payload)
            token = auth_token(current_plugin, password, current_salt)
            up.sendall(packet((seq + 1) & 255, token))
            seq, payload = recv_packet(up)
            continue
        if payload[:1] == b"\x01" and len(payload) >= 2:
            status = payload[1]
            if current_plugin == "sha256_password" and len(payload) > 8:
                encrypted = rsa_encrypt(password, current_salt, payload[1:])
                up.sendall(packet((seq + 1) & 255, encrypted))
                seq, payload = recv_packet(up)
                continue
            if status == 3:  # caching_sha2 fast-auth accepted; final OK follows
                seq, payload = recv_packet(up)
                continue
            if status == 4:
                up.sendall(packet((seq + 1) & 255, b"\x02"))
                key_seq, key_payload = recv_packet(up)
                if key_payload[:1] != b"\x01":
                    raise ProtocolError("backend did not return the requested RSA public key")
                pem = key_payload[1:]
                encrypted = rsa_encrypt(password, current_salt, pem)
                up.sendall(packet((key_seq + 1) & 255, encrypted))
                seq, payload = recv_packet(up)
                continue
        raise ProtocolError(f"unexpected backend auth packet 0x{payload[:1].hex()} (sequence {seq})")

def backend_login(args) -> socket.socket:
    up = socket.create_connection((args.backend_host, args.backend_port), timeout=5)
    up.settimeout(10)
    seq, greeting = recv_packet(up)
    caps, salt, plugin = parse_greeting(greeting)
    offered = (CLIENT_LONG_PASSWORD | CLIENT_LONG_FLAG | CLIENT_PROTOCOL_41 |
               CLIENT_TRANSACTIONS | CLIENT_SECURE_CONNECTION)
    if caps & CLIENT_PLUGIN_AUTH:
        offered |= CLIENT_PLUGIN_AUTH
    offered &= caps
    token = auth_token(plugin, args.password, salt)
    response = bytearray()
    response += offered.to_bytes(4, "little")
    response += (16 * 1024 * 1024).to_bytes(4, "little")
    response += bytes([45]) + bytes(23)
    response += args.user.encode("utf-8") + b"\0"
    if offered & CLIENT_SECURE_CONNECTION:
        response += bytes([len(token)]) + token
    else:
        response += token + b"\0"
    if offered & CLIENT_PLUGIN_AUTH:
        response += plugin.encode("ascii") + b"\0"
    up.sendall(packet((seq + 1) & 255, bytes(response)))
    auth_seq, auth_payload = recv_packet(up)
    complete_auth(up, auth_seq, auth_payload, plugin, salt, args.password)
    up.settimeout(None)
    return up

def error_packet() -> bytes:
    payload = b"\xff" + (1045).to_bytes(2, "little") + b"#28000Benchmark proxy upstream login failed"
    return packet(0, payload)

def handle(client: socket.socket, args) -> None:
    client.settimeout(10)
    up = None
    try:
        up = backend_login(args)
        client.settimeout(None)
        sockets = [client, up]
        while sockets:
            ready, _, _ = select.select(sockets, [], [], 30)
            if not ready:
                continue
            for src in ready:
                data = src.recv(65536)
                if not data:
                    try:
                        (up if src is client else client).shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                    sockets.remove(src)
                    continue
                dest = up if src is client else client
                dest.sendall(data)
    except (OSError, ProtocolError, subprocess.SubprocessError) as exc:
        try:
            client.sendall(error_packet())
        except OSError:
            pass
        print(f"upstream session failed: {exc}", flush=True)
    finally:
        if up:
            up.close()
        client.close()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--listen-host", default="127.0.0.1")
    ap.add_argument("--listen-port", type=int, required=True)
    ap.add_argument("--backend-host", default="127.0.0.1")
    ap.add_argument("--backend-port", type=int, required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", default="")
    args = ap.parse_args()
    if args.listen_host not in ("127.0.0.1", "localhost"):
        raise SystemExit("benchmark proxy must bind only to loopback")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.listen_host, args.listen_port))
    srv.listen(64)
    print(f"listening=127.0.0.1:{args.listen_port} backend={args.backend_host}:{args.backend_port} user={args.user}", flush=True)
    while True:
        client, _ = srv.accept()
        threading.Thread(target=handle, args=(client, args), daemon=True).start()

if __name__ == "__main__":
    main()
