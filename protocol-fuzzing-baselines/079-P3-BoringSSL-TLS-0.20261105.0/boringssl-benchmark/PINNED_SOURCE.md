# BoringSSL source pin

- Repository: `https://github.com/google/boringssl.git`
- Release tag: `0.20261105.0`
- Annotated tag object: `5e7f7792f2223216967aa9abc6be8e5b1727e41d`
- Peeled source commit: `3dc4b63808921e914a3fb1fa61869abc3938781b`
- Commit date: `2026-11-05`
- Local verification: `git describe --tags --exact-match` returned the release tag and `git rev-parse HEAD` matched the peeled commit.
- Official release index: `https://github.com/google/boringssl/releases`

The benchmark will build the upstream `server` fuzzer and use the matching
`fuzz/server_corpus`. This is BoringSSL's in-process TLS server handshake
fuzzer, not a network listener or throughput test. Upstream documents that
`-DFUZZ=1` enables libFuzzer coverage and AddressSanitizer and recommends
`max_len=4096` for this target in `FUZZING.md`.
