#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
SEEDS.mkdir(exist_ok=True)
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
CLOSE = (b'<?xml version="1.0" encoding="UTF-8"?>'
         b'<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="2">'
         b'<close-session/></rpc>' + END)
(SEEDS / "01-client-hello.netconf").write_bytes(HELLO)
(SEEDS / "02-hello-get.netconf").write_bytes(HELLO + GET)
(SEEDS / "03-hello-get-close.netconf").write_bytes(HELLO + GET + CLOSE)
print("Wrote NETCONF 1.0 hello, get, and close-session seeds")
