# MySQL Classic protocol state mapping

The profile fuzzes MySQL Classic `COM_QUERY` request packets. A loopback proxy performs a fresh server greeting/authentication exchange for each test connection, then forwards AFLNet request bytes and SQL responses without rewriting them. The adapter parses the 4-byte packet header (3-byte little-endian payload length and sequence number) and assigns response states: ordinary result packet, EOF, OK, SQL error, LOCAL INFILE, and other. Authentication messages are handled by the proxy and are tested separately by smoke validation, so server-side authentication is outside this fuzz campaign.

Because the proxy consumes the initial greeting/auth exchange, the parser prefixes AFLNet's canonical state 0 before the first SQL response state. This gives state-aware initialization the required initial-state entry. The campaign uses AFLNet network-only state feedback, not compiler instrumentation; its bitmap counter is not source-code coverage.
