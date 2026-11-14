# Formal results — ejabberd 26.09 (XMPP/TCP)

## Result

The detached AFLNet campaign ran for 1,800 seconds. `fuzzer_stats.start_time` is `1794202273` and `last_update` is `1794204073` (an exact 1,800-second interval); the benchmark container exited with status 0. The container ran from `2026-11-09T05:31:13.277390371Z` through `2026-11-09T06:01:13.960280001Z`.

| Metric | Formal result |
|---|---:|
| Target / runtime | ejabberd 26.09 / Erlang OTP 29.0.6 |
| AFLNet | 2.56b, commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732` |
| Executions | 3,000 |
| Queue files | 38 total; 31 have `+state` labels |
| `paths_total` / `paths_found` | 38 / 31 |
| `variable_paths` / `cycles_done` | 0 / 2 |
| Stability / AFL bitmap | 100.00% / 0.00% |
| Unique crashes / AFLNet hang candidates | 0 / 5 |
| IPSM graph | 18 nodes / 34 edges |

`+state` file count, `paths_total`, `paths_found`, cycles, and graph size are recorded independently because they describe different AFLNet state. The bitmap is zero because this profile uses XMPP response-state feedback in dumb mode; it is not source-code coverage.

## Queue replay and hang triage

All 38 formal queue samples connected to an isolated replay service and all 38 payloads were sent. There were 0 replay errors. Ten malformed/closing inputs caused the peer to reset while the replay tool was reading; these are recorded as target-side connection behavior, not replay infrastructure errors.

Each of the five AFLNet hang candidates was replayed three times against a fresh ejabberd instance. All 15 attempts left the target alive, and an independent follow-up XMPP stream/features probe succeeded on all 15. No candidate met the repeated service-unavailable criterion, so none is classified as a confirmed service hang. One candidate caused a peer reset during all three replays while the service remained healthy.

The separate 120-second validation run completed 420 executions with 100% stability, 0 crashes, and 0 hangs; its 12 queued samples connected and were sent with 0 replay errors. The reference/AFL/replay smoke checks also verified plaintext stream features, optional STARTTLS `<proceed>`, TLS handshake, and post-TLS stream features.

## Scope and limits

The profile covers loopback XMPP client-to-server stream opening and features, optional STARTTLS, and selected pre-authentication IQ, presence, message, and SASL attempts. It does not claim a successful authenticated account session. Each testcase gets a fresh working directory, `HOME`, Mnesia spool, log directory, and PID path.

No BEAM application source-line or branch coverage collector was enabled. The report uses AFLNet XMPP response-state feedback and the IPSM graph only. Queue replay measures connection/send/reset behavior; it does not measure code coverage.

## Resource cleanup

After the delivery ZIP and checksums were verified, the exact campaign container `ejabberd-xmpp-30m-20261109` and image `profuzzbench/ejabberd-xmpp:26.09` (ID `sha256:b09f2fabd11cd2e5180fda6494f9a812c08446c012f0631477af2d460702b331`, reported image size 1,293,006,040 bytes) were removed. A read-only Docker inspection confirmed both exact objects were absent.

## Evidence files

- `campaign/fuzzer_stats`, `campaign/ipsm.dot`, `campaign/queue/`, and `campaign/replayable-hangs/` — raw formal campaign evidence.
- `coverage-replay/replay.json` and `coverage-replay/coverage.txt` — per-sample replay outcomes and explicit coverage limitation.
- `hang-triage/candidate-*/report.json` — three fresh replays and health checks per hang candidate.
- `ipsm.plain`, `container-state.json`, `image-info.json`, and `campaign.log` — parsed graph and runtime metadata.
- `../validation-final/` — short validation and protocol/TLS smoke evidence.

Upstream release: [ejabberd 26.09](https://github.com/processone/ejabberd/releases/tag/26.09). The 26.09 listen-options documentation specifies `starttls: true` as making STARTTLS available; `starttls_required` controls whether encryption is mandatory.
