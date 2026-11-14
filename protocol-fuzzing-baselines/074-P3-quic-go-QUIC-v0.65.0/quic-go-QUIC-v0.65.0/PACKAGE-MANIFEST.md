# Package manifest

The standalone quic-go ZIP includes the pinned quic-go and Go archives, source/toolchain locks, native fuzz target invocation, preflight and formal logs, native fuzz metrics, saved fuzz cache corpus, any failure-triggering testdata corpus, acceptance record, and package/checksum evidence. It excludes transient Go build cache, Docker build cache, and the central aggregated experience library. The latter remains in the central deliverables directory so the per-protocol packages stay independently scoped.
