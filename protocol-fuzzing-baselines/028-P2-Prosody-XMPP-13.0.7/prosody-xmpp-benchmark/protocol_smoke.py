#!/usr/bin/env python3
import socket

OPEN = (b"<stream:stream to='example.test' xmlns='jabber:client' "
        b"xmlns:stream='http://etherx.jabber.org/streams' version='1.0'>")
with socket.create_connection(("127.0.0.1", 5222), timeout=5) as sock:
    sock.settimeout(8)
    sock.sendall(OPEN)
    chunks = []
    while sum(map(len, chunks)) < 65536:
        part = sock.recv(8192)
        if not part:
            break
        chunks.append(part)
        if b"</stream:features>" in b"".join(chunks):
            break
    response = b"".join(chunks)
    if b"<stream:stream" not in response or b"<stream:features" not in response:
        raise SystemExit("XMPP stream smoke failed: " + repr(response[:1000]))
    print("prosody_xmpp_stream=PASS")
    print("features_bytes=" + str(len(response)))
