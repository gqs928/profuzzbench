# BoringSSL TLS server fuzz benchmark

Source is pinned to upstream release `0.20261105.0` at commit
`3dc4b63808921e914a3fb1fa61869abc3938781b`. The selected target is the
upstream `server` libFuzzer harness with its paired `fuzz/server_corpus`.
The test exercises TLS server handshake parsing in process; it does not run a
TCP listener. The official `FUZZING.md` documents the fuzzer build mode and a
4096-byte maximum input for this target.

The upstream `FUZZ=1` mode is explicitly unsafe for production and relaxes
cryptographic checks so the TLS state machine can progress beyond crypto
invariants. Results therefore describe parser/state-machine behavior in the
upstream fuzzing mode, not a production TLS server or complete cryptographic
validation.

This delivery includes the pinned source and build recipe, preflight and
30-minute run logs, final libFuzzer counters, corpus, and sanitizer artifacts
if any. The formal run lasted 1,805 seconds in libFuzzer and 1,807 seconds
outer wall time: 4,110,930 executions, 9,859 coverage counters, 34,011
features, 2,277 exec/s, and 484 MB peak RSS. The process exited 0 with no
AddressSanitizer findings or artifact files. `ACCEPTANCE.md` contains the
complete evidence. This is upstream fuzzing mode, which relaxes crypto checks;
it does not measure a production TLS server.
