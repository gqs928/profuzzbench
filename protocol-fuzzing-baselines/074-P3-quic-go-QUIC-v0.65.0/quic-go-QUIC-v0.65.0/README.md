# quic-go QUIC header parser baseline

This profile benchmarks the upstream `FuzzHeaderParser` native Go fuzz target in quic-go v0.65.0 with the upstream Go testing fuzz engine. It covers QUIC v1/v2 packet header parsing in-process; it does not start a UDP service, complete a QUIC handshake, or send HTTP/3 requests.

The source and Go toolchain archives are pinned by SHA-256 in `source-lock.json`. Build and validate the image with `./build.sh`, run the isolated 60-second preflight with `./preflight-benchmark.sh`, then run the formal 30-minute campaign with `./run-benchmark.sh`. Each run uses its own Go cache so generated fuzz corpus does not leak between preflight and formal runs. See `ACCEPTANCE.md` for the evidence gates.

Results use Go native fuzz metrics. AFLNet stability, bitmap coverage, server readiness, listener, and packet replay fields do not apply to this in-process parser target and must not be synthesized. The aggregated automation experience library is maintained centrally and is not part of this per-protocol delivery.
