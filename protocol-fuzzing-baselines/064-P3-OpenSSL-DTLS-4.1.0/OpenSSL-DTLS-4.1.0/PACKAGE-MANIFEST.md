# Package contents

- Pinned OpenSSL 4.1.0 source archive, official SHA-256 checksum, detached signature, and official signing keyring.
- AFLNet ProFuzzBench snapshot and three DTLS 1.2 ClientHello seeds, each checksum-pinned.
- Instrumented OpenSSL build recipe, bounded campaign runner, OpenSSL-native seed capture helper, seed validator, DTLS handshake/reverse-echo smoke test, raw/KL replay validator, and listener/process shutdown verifier.
- Evidence-gated `package.py` validator that checks the bounded 1,800-second deadline (allowing the final AFLNet stats timestamp to land at 1,801 seconds), pre/post smoke, full replay classification, package CRC, and SHA-256.
- One-client DTLS echo harness linked against the AFL-instrumented OpenSSL libraries.
- Build logs, exact runtime version evidence, formal 30-minute campaign output, full replay results, and acceptance report.

The completed campaign ran for 1,800 seconds by supervisor deadline and reports its final stats separately. The full 636-sample queue replay distinguishes invalid DTLS record framing, clean one-client target exits, responses, and target readiness.

The shared cross-protocol automation experience library is kept in the central deliverables directory rather than repeated in each protocol ZIP.
