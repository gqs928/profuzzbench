# UnrealIRCd 6.2.7.1 IRC benchmark

This package benchmarks the latest stable UnrealIRCd release, 6.2.7.1, from the official source archive. It builds reference, ASan/AFLNet-instrumented, and gcov variants from that same archive. The IRC adapter splits client input at CRLF boundaries and maps server numeric replies to AFLNet states.

The benchmark configuration is derived from UnrealIRCd's upstream example, with plaintext IRC on `127.0.0.1:6667` and TLS IRC on `127.0.0.1:6697`. AFLNet fuzzes the plaintext listener; the differential smoke also completes a TLS handshake and checks IRC registration across the reference, AFL, and gcov variants. TLS uses the pinned, self-signed local test certificate in `certs/`. Server-link listeners, external DNSBL checks, and client hostname resolution are disabled so the loopback profile is deterministic without external services.

## Build and validate

```sh
chmod +x ./*.sh
./build.sh
./validate.sh profuzzbench/unrealircd-irc:6.2.7.1 "$PWD/results/validation" 60s
```

The protocol smoke acts as an IRC client: it answers server `PING` challenges, completes IRCv3 `CAP` negotiation, and sends registered-user commands only after numeric `001`. It compares parsed numeric reply paths across the three builds; response byte counts are retained as diagnostics because dynamic reply text can vary. The AFLNet smoke requires nonzero executions and a nontrivial IRC state graph. Replay the queue against the gcov target with:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" profuzzbench/unrealircd-irc:6.2.7.1 \
  python3 /opt/benchmark/coverage_replay.py \
    /results/validation/fuzz-smoke/queue /results/validation/coverage-smoke
```

The formal campaign defaults to 30 minutes:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" profuzzbench/unrealircd-irc:6.2.7.1 \
  bash /opt/benchmark/run.sh /results/irc-30m 30m
```

The completed result and its caveats are summarized in `results/RESULTS.md`. Keep the generated `fuzzer_stats`, IPSM, gcov report, queue replay and `SHA256SUMS` with each delivery. A short smoke does not replace the formal run.

## Pinned sources

- [UnrealIRCd release history](https://www.unrealircd.org/docs/History_of_UnrealIRCd_releases) and [official release notes](https://github.com/unrealircd/unrealircd/blob/unreal60_dev/doc/RELEASE-NOTES.md).
- [UnrealIRCd 6.2.7.1 source archive](https://github.com/unrealircd/unrealircd/releases) — SHA256 in `source-lock.json`.
- [AFLNet pinned source](https://github.com/aflnet/aflnet/tree/0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732).
- [IRC client protocol, RFC 2812](https://www.rfc-editor.org/rfc/rfc2812).
