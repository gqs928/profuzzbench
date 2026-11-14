# MySQL Classic protocol state mapping

The profile fuzzes MySQL Classic `COM_QUERY` request packets. A loopback proxy performs a fresh server greeting/authentication exchange for each test connection, then forwards AFLNet request bytes and SQL responses without rewriting them. The adapter parses the 4-byte packet header (3-byte little-endian payload length and sequence number) and assigns response states: ordinary result packet, EOF, OK, SQL error, LOCAL INFILE, and other. Authentication messages are handled by the proxy and are tested separately by smoke validation, so server-side authentication is outside this fuzz campaign.

Since the proxy consumes greeting and authentication, the adapter prepends synthetic state `0` to each non-empty SQL response sequence. This models AFLNet's initial state and creates an explicit edge to the first visible SQL response; without it, AFLNet's initial-state table is empty and seed initialization aborts.

| State ID | Response class |
|---:|---|
| 0 | Synthetic initial state before the proxy-forwarded SQL response |
| 21 | Result header, column definition, or row |
| 22 | EOF packet |
| 30 | OK packet (`0x00` marker with a payload of at least 7 bytes) |
| 40 | SQL error (`0xff`) |
| 41 | LOCAL INFILE request (`0xfb`) |
| 99 | Other response |

The `0x00` marker is ambiguous in a result stream: shorter packets can encode a row with an empty length-encoded field, so the adapter only calls it OK when the packet is at least 7 bytes. The campaign uses AFLNet network-only state feedback, not compiler instrumentation; its bitmap counter is not source-code coverage.
