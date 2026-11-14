#!/usr/bin/env python3
"""Idempotently enable an explicit loopback STOMP transport in activemq.xml."""
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
active = re.search(r"""(?m)^\s*<transportConnector\b[^>]*\bname=["']stomp["']""", text)
if active:
    print("stomp_connector=present")
elif "</transportConnectors>" in text:
    text = text.replace(
        "</transportConnectors>",
        '            <transportConnector name="stomp" uri="stomp://127.0.0.1:61613"/>\n        </transportConnectors>',
        1,
    )
    path.write_text(text)
    print("stomp_connector=added")
else:
    raise SystemExit("transportConnectors block not found")
