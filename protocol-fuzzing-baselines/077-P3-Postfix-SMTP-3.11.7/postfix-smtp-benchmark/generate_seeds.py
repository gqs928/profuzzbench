#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "seeds"
SEEDS.mkdir(exist_ok=True)

cases = {
    "ehlo-quit": b"EHLO fuzzer.invalid\r\nQUIT\r\n",
    "helo-noop-quit": b"HELO fuzzer.invalid\r\nNOOP\r\nQUIT\r\n",
    "mail-rcpt-data": (
        b"EHLO fuzzer.invalid\r\n"
        b"MAIL FROM:<sender@fuzz.invalid>\r\n"
        b"RCPT TO:<recipient@fuzz.invalid>\r\n"
        b"DATA\r\nSubject: baseline\r\n\r\nbody\r\n.\r\n"
        b"QUIT\r\n"
    ),
    "mail-rset": (
        b"EHLO fuzzer.invalid\r\nMAIL FROM:<sender@fuzz.invalid>\r\n"
        b"RSET\r\nNOOP\r\nQUIT\r\n"
    ),
    "vrfy-expn": b"EHLO fuzzer.invalid\r\nVRFY root\r\nEXPN postmaster\r\nQUIT\r\n",
    "pipelined-commands": (
        b"EHLO fuzzer.invalid\r\nNOOP\r\nNOOP\r\nRSET\r\n"
        b"MAIL FROM:<sender@fuzz.invalid>\r\nQUIT\r\n"
    ),
    "ehlo-extensions": (
        b"EHLO fuzzer.invalid\r\n"
        b"MAIL FROM:<sender@fuzz.invalid> SMTPUTF8 BODY=8BITMIME\r\n"
        b"RCPT TO:<recipient@fuzz.invalid>\r\nRSET\r\nQUIT\r\n"
    ),
    "malformed-commands": b"EHLO\r\nMAIL FROM:<>\r\nRCPT TO:<>\r\nBOGUS\r\nQUIT\r\n",
}
for name, data in cases.items():
    (SEEDS / name).write_bytes(data)
print("generated", len(cases), "SMTP seeds")
