# Unbound 1.26.2 — DNS/TCP baseline

This target is the upstream Unbound 1.26.2 source release published by NLnet Labs on 2026-10-21. The archive is pinned by SHA-256 and verified with the official NLnet Labs releases G2 signing key. Runtime version is asserted from the built binary.

The profile sends DNS over TCP using RFC 7766 two-byte big-endian message lengths to a local immutable `fuzz.test` static zone on port 5300. This avoids external recursion, upstream DNS, cache state, and Internet dependencies. Although Unbound also listens on UDP, only TCP traffic is sent and scored. DNSSEC validation, DoT, DoH, and DoQ are outside this profile.

AFLNet's `DNS_TCP` request adapter segments length-prefixed queries and the response parser maps QR/opcode/AA/TC/RCODE to response states. The target is not built with AFL instrumentation; the AFL helper bitmap is not Unbound source coverage. Each testcase restarts the target and waits for a real DNS/TCP query before replay, preserving process isolation and making restart cost part of the measured throughput.

Build the image with `./build.sh`. Run a short preflight before the formal 30-minute campaign. Validate the campaign queue with `replay_queue.py`, then run post-campaign DNS/TCP smoke and listener-closure checks. Protocol-specific automation-framework experience is recorded in the central delivery directory's `基准化经验库.md`, not in this protocol ZIP.

Upstream: [Unbound release/download page](https://nlnetlabs.nl/projects/unbound/download/), [official source signing keys](https://igor.nlnetlabs.nl/signing-keys/), [RFC 7766](https://www.rfc-editor.org/rfc/rfc7766).
