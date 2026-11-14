# BIND 9.20.30 DNS/UDP baseline results

## Scope and build identity

- Target: BIND 9.20.30 authoritative DNS over UDP, loopback port 5353, AFLNet DNS state feedback.
- Source: tag `v9.20.30`, commit `769c3fb93a0a06b2f1f44b5156c4f7e52f57ef78`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- Image: `bind9-dns-aflnet:9.20.30`, ID `sha256:13883a05db5377ab08d5be2e3bcccb2aace2491305ae6dc5983f8e5939f02231`.
- Build and real-service smoke: passed. The service answered DNS/UDP and DNS/TCP queries for the configured authoritative zone. See `results/build/service-smoke.json` and `results/build/named.log`.
- Campaign boundary: DNS/UDP only. DNS/TCP was smoke-tested but not fuzzed. DoH/HTTP2 and DNSSEC signing paths were not part of this profile.

## Formal run

The isolated AFLNet campaign ran for 1,800 seconds. The external timeout returned 124 as expected after sending SIGINT; `run.json` confirms `last_update - start_time = 1,800` seconds.

| Measure | Result |
|---|---:|
| Executions | 1,211 |
| Paths total | 34 |
| Paths found | 21 |
| Variable paths | 32 |
| Stability | 89.86% |
| Bitmap coverage | 24.52% |
| Unique crashes | 0 |
| AFLNet hang candidates | 6 |

The campaign stopped during AFLNet's first queue cycle. Instrumented executions averaged about 0.72 per second. AFLNet also skipped two slow seed inputs during dry-run calibration; these facts are retained in `results/dns-30m/aflnet.log` and the raw statistics.

## Hang-candidate replay

Each of the 6 AFLNet hang candidates was sent to a fresh instrumented `named` process 3 times. Three candidates returned a 12-byte DNS header in every replay; the other three were silent until the replay timeout. In all 18 attempts, `named` remained alive and answered a subsequent valid DNS health query. They are not confirmed persistent service hangs. Per-attempt process logs and `results/dns-30m/hang-replay/triage-summary.json` preserve the evidence.

No crash or hang vulnerability is claimed from this run. AFLNet's silence-based hang signal should be cross-checked against server process liveness and an independent valid request for UDP services.

## Reproduction

```sh
./build.sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/work/results" \
  bind9-dns-aflnet:9.20.30 /work/run.sh /work/results/dns-30m 1800
```

The original campaign output is under `results/dns-30m/`; build inputs and the service smoke are under `results/build/`.
