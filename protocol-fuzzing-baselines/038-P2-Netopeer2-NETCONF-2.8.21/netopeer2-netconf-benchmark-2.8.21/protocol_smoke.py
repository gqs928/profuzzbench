#!/usr/bin/env python3
"""Smoke-test NETCONF 1.0 hello and a read-only <get/> over the SSH proxy."""
import os
import socket
import xml.etree.ElementTree as ET

HOST = os.environ.get("NETCONF_HOST", "127.0.0.1")
PORT = int(os.environ.get("NETCONF_PORT", "1830"))
END = b"]]>]]>"
NETCONF_NS = "urn:ietf:params:xml:ns:netconf:base:1.0"
MONITORING_NS = "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"
HELLO = (b'<?xml version="1.0" encoding="UTF-8"?>'
         b'<hello xmlns="' + NETCONF_NS.encode() + b'">'
         b'<capabilities><capability>urn:ietf:params:netconf:base:1.0</capability>'
         b'</capabilities></hello>' + END)
GET = (b'<?xml version="1.0" encoding="UTF-8"?>'
       b'<rpc xmlns="' + NETCONF_NS.encode() + b'" message-id="1">'
       b'<get><filter type="subtree"><netconf-state xmlns="' + MONITORING_NS.encode() +
       b'"/></filter></get></rpc>' + END)


def safe_summary(message):
    try:
        body = message[:-len(END)] if message.endswith(END) else message
        root = ET.fromstring(body)
        return f"root={root.tag.rsplit('}', 1)[-1]!r} message_id={root.attrib.get('message-id')!r} bytes={len(message)}"
    except ET.ParseError:
        return f"unparseable NETCONF message, bytes={len(message)}"


def read_message(sock, buf):
    while END not in buf:
        part = sock.recv(65536)
        if not part:
            raise RuntimeError("NETCONF stream closed before the end-of-message marker")
        buf.extend(part)
        if len(buf) > 4 * 1024 * 1024:
            raise RuntimeError("NETCONF message exceeds 4 MiB")
    frame, _, rest = buf.partition(END)
    buf[:] = rest
    return bytes(frame + END)


def main():
    with socket.create_connection((HOST, PORT), timeout=10) as sock:
        sock.settimeout(15)
        buf = bytearray()
        server_hello = read_message(sock, buf)
        if b"<hello" not in server_hello or NETCONF_NS.encode() not in server_hello:
            raise RuntimeError(f"expected NETCONF 1.0 server hello; {safe_summary(server_hello)}")
        sock.sendall(HELLO)
        sock.sendall(GET)
        reply = read_message(sock, buf)
        root = ET.fromstring(reply[:-len(END)])
        if root.tag != f"{{{NETCONF_NS}}}rpc-reply" or root.attrib.get("message-id") != "1":
            raise RuntimeError(f"expected rpc-reply for message-id 1; {safe_summary(reply)}")
        rpc_error = root.find(f"{{{NETCONF_NS}}}rpc-error")
        if rpc_error is not None:
            error_tag = rpc_error.findtext(f"{{{NETCONF_NS}}}error-tag", "unknown")
            raise RuntimeError(f"NETCONF <get/> returned rpc-error, error-tag={error_tag!r}")
        if root.find(f"{{{NETCONF_NS}}}data") is None:
            raise RuntimeError("NETCONF <get/> reply has no <data> element")
    print("netconf_1_0_ssh_subsystem=PASS")
    print("netconf_get_rpc_reply=PASS")


if __name__ == "__main__":
    main()
