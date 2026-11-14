# Prosody 13.0.7 XMPP baseline results

Run date: 2026-11-09 UTC. Target: official [Prosody 13.0.7 source release](https://prosody.im/doc/release/13.0.7), SHA-256 `f671df3c7535c7269afc89579ea26fc13d1006b40ef5df4ccb71a560197f151b`. The detached signature verifies against the retained Prosody key; that signing key is expired as of the verification date, so the package records both the signature result and this key-status caveat.

## Profile and method

- Transport: XMPP client-to-server over loopback TCP/5222, virtual host `example.test`.
- Target config: Prosody 13.0.7 compiled against Lua 5.4; S2S disabled; anonymous authentication; local self-signed TLS certificate; one long-lived Lua service and a fresh TCP connection per testcase.
- Fuzzer: AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, dumb mode, XMPP stream/stanza request boundaries and XML response-tag feedback.
- Formal duration: 1,802 active seconds after initial seed dry-run.
- Container limit: 1.2 GiB memory, 1 CPU; loopback target traffic only.

## Formal campaign

| Metric | Result |
|---|---:|
| AFLNet executions | 364 |
| Queue files | 9 |
| New response-state paths | 2 |
| Queue cycles completed | 0 |
| Stability | 100.00% |
| AFL bitmap coverage | 0.00% |
| Unique crashes / hangs | 0 / 0 |

The first queue cycle did not complete. The bitmap is zero because this is a black-box Lua service and the profile uses response-state feedback rather than Lua source instrumentation; it must not be interpreted as source coverage. Treat this as an exploratory protocol-state baseline with incomplete queue traversal.

## Post-run checks

- XMPP stream smoke passed before and after the formal campaign; the final stream-features response was 490 bytes.
- Queue replay connected and received a response for all 9/9 files; 0 timeouts, resets, or errors.
- Logs and complete campaign evidence are in `protocol-smoke-final/` and `xmpp-30m/`.

## Reproduction

From the package root:

```sh
docker build -t profuzzbench-prosody:13.0.7 .
mkdir -p results/xmpp-30m
docker run --rm --network none --memory=1200m --cpus=1 \
  -v "$PWD/results/xmpp-30m:/results/xmpp-30m" \
  profuzzbench-prosody:13.0.7 \
  bash /opt/benchmark/fuzz.sh /results/xmpp-30m 1800
```
