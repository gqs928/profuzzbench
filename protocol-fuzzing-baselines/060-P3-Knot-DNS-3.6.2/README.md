# Knot DNS 3.6.2 — DNS/TCP baseline

This profile targets the current stable Knot DNS 3.6.2 release published on 2026-10-21. The upstream release source archive is locked by its published SHA-256 and verified against the CZ.NIC release signing key. It runs one isolated authoritative `fuzz.test` zone on port 5300. Knot's `server.listen` binds the standard DNS transports; the benchmark driver sends and scores DNS/TCP only. TLS, QUIC, recursion, zone transfer, dynamic update, and DNSSEC signing are outside the campaign.

AFLNet's built-in `DNS` parser models the UDP DNS message without the DNS-over-TCP two-byte length prefix, so it is not used for this profile. `DNS_TCP` is registered as a separate protocol adapter: request segmentation follows each declared TCP frame length, and response states derive from QR, opcode, AA, TC, and RCODE. Truncated or malformed frames remain available to the target and receive an explicit malformed-state marker. The parser unit checks multiple framed messages and truncation. The build applies a generic fix for AFLNet's unterminated `-N` endpoint copy and rejects the image unless 64 repeated valid endpoint parses pass.

Each testcase restarts the Knot daemon and recreates its runtime state while the served zone remains immutable. Readiness uses a framed DNS query and validates a successful authoritative answer; a TCP connect alone is insufficient. AFLNet's helper bitmap is reported separately and is not claimed as Knot source coverage.

Upstream: [Knot DNS releases](https://www.knot-dns.cz/download/), [Knot DNS 3.6.2 configuration reference](https://www.knot-dns.cz/docs/3.6/html/reference.html), [RFC 7766](https://www.rfc-editor.org/rfc/rfc7766).

After the formal campaign and queue replay, run the post-campaign smoke and verify the listener is closed:

```sh
./post-smoke.sh /results/dns-tcp-smoke-post-20261112
```

Framework adaptation lessons are maintained in the shared central experience library, not this protocol ZIP.
