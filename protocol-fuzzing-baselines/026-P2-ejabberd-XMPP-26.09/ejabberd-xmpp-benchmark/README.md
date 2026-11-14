# ejabberd 26.09 XMPP benchmark

This directory builds ejabberd 26.09, the latest release pinned in `source-lock.json`, with a loopback-only XMPP profile. The tested scope covers stream open/features, optional STARTTLS, and selected pre-authentication IQ, presence, message, and SASL exchanges; it does not claim a successful authenticated account session. The smoke test compares stream features and STARTTLS negotiation across reference, AFLNet-run, and replay variants. STARTTLS is enabled explicitly with `starttls: true`; setting `starttls_required: false` only makes it optional. The client sends the XMPP stream opener first, then parses server features; after STARTTLS, it opens a new XML stream inside TLS. AFLNet uses XMPP response-state feedback in dumb mode; the included patches queue inputs when a new response-state sequence appears and reap the direct-exec network target. The `cover` runtime copy is used for queue replay only; no BEAM source-coverage collector is enabled or claimed.

## Build and validate

```sh
docker build --progress=plain -t profuzzbench/ejabberd-xmpp:26.09 .
bash ./validate.sh "$PWD/results/validation" 120s
```

The smoke test exercises stream open, STARTTLS, and post-TLS stream features. The short run checks that AFLNet discovers and queues a new response-state sequence and produces a nontrivial state graph, then replays every queued sample against the `cover` runtime copy. The replay report records connection/reset behavior; it does not report code coverage.

The launcher gives each sample a fresh working directory, `HOME`, Mnesia spool, log directory, and PID path, and binds EPMD to loopback. This prevents state from an earlier XMPP sample from changing later responses. The Debian runtime dependencies use the date-pinned Trixie snapshot in `source-lock.json`; apt Release signature verification remains enabled.

## Formal campaign

The completed 1,800-second run and queue replay are documented in [`results/RESULTS.md`](results/RESULTS.md). It finished with 3,000 executions, 38 queue files (31 state-labelled), a 18-node/34-edge IPSM graph, 100% stability, and no crashes. Five AFLNet hang candidates were each replayed three times; none caused repeated service unavailability. No BEAM source coverage is collected.


```sh
mkdir -p results/xmpp-30m
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results/xmpp-30m:/results" profuzzbench/ejabberd-xmpp:26.09 \
  bash /opt/benchmark/fuzz.sh /results/campaign 30m
```

Keep `fuzzer_stats`, `ipsm.dot`, queue replay output, build versions, and `SHA256SUMS` in the delivery. The AFLNet dumb-mode patch handles direct-child reaping when network mode stops the target process.

See `source-lock.json` for the source archive, OTP runtime image, AFLNet commit, and XMPP adapter digests. Shared framework guidance is maintained in the central experience library, not in this protocol package.
