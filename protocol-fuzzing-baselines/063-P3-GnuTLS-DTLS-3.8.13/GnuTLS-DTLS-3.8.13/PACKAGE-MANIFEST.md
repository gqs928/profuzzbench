# Package contents

- `Dockerfile`, pinned image variables, Compose configuration, and reproducible build/run scripts.
- GnuTLS 3.8.13 official source archive, detached signature, upstream keyring, and the exported verification keyring used to validate both release signatures.
- GNU Nettle 3.10.2 source archive, detached signature, and upstream maintainer key. It is built into the image because Ubuntu 24.04 provides Nettle 3.9.1, below GnuTLS 3.8.13's minimum requirement.
- AFLNet ProFuzzBench snapshot and three checksum-pinned GnuTLS-compatible ClientHello seeds with distinct SNI values.
- Seed record validator and reproducible local ClientHello capture relay, direct DTLS handshake/echo smoke test, bounded campaign runner, raw/KL/IPSM queue replay validator, and listener/process shutdown verifier.
- Build logs, exact runtime version evidence, formal 1,800-second campaign output, 574-sample replay results, the eight-sample replay-window preflight, and acceptance report.
- Replay readiness matches the local endpoint column from `ss -lunH`; response collection waits for delayed DTLS datagrams and separately records malformed record-boundary samples that are rejected before target transmission.

The shared cross-protocol automation experience library is kept in the central deliverables directory rather than repeated in this protocol ZIP.
