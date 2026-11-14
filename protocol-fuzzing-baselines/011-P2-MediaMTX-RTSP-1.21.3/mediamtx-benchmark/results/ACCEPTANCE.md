# MediaMTX RTSP fuzz-baseline acceptance

## Scope and build identity

- Target: MediaMTX `v1.21.3`, RTSP over TCP on `127.0.0.1:8554`.
- Source archive SHA-256: `b6d0f252adb85be5d1a3897a22883af335b54218b6cc66c831e3dd1cc03c6f36`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, archive SHA-256 `251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d`.
- Runtime image ID: `sha256:299a2689762c87cb584011bc9db68bf6502cab07697923799bae7de12a088f7b`.
- The Go target is built with native Go coverage (`-cover -coverpkg=./...`). AFLNet's forkserver and bitmap come from a small AFL-instrumented C lifecycle helper, not from MediaMTX. AFL `bitmap_cvg` and AFL crash/hang counters therefore describe the helper/forkserver signal; target feedback is the RTSP response-state graph plus Go coverage.

## Formal campaign

The campaign ran for 1,800 seconds by AFLNet timestamps and 1,801 seconds by the external wall clock. The wrapper reached its configured timer (exit `124`), AFLNet exited cleanly (`0`), and the target handled SIGTERM and exited `0`; Go coverage counters were flushed. The post-campaign RTSP health and publisher/reader smoke passed.

| Metric | Result |
|---|---:|
| Executions | 967 |
| Total paths | 7 |
| New paths found | 0 |
| Variable paths | 0 |
| Helper stability | 100.00% |
| Helper bitmap coverage | 0.01% |
| AFLNet crashes / hang candidates | 0 / 1 |
| RTSP response states observed | 200, 400, 404, 454 |
| Go statement coverage, campaign-only | 9.3% |
| Go statement coverage, fresh post-smoke process | 11.4% |
| Go statement coverage, combined campaign + smoke | 11.6% |

The state graph records each of the observed response codes as an edge from the initial state. Go coverage scopes are kept separate so the post-smoke transaction is not attributed to fuzzing.

## Hang-candidate replay

AFLNet produced one replayable hang candidate, sequence SHA-256 `9e98f78d8e65f1ad379fc00d1f3f77e4a40c4fe6fbc30566059fdafd2bc6790b`. Its first 92-byte request is saved as `results/rtsp-30m/candidate-replay/first-request.rtsp` and has SHA-256 `ba4ebe1cc8051b89e245038f89b073e00dd4d6c37f37aeda38cc13eacc961f46`. It is a malformed `PLAY` request with an invalid session header and range value.

The first request was replayed against three fresh MediaMTX processes, each with a 15-second response deadline. All three connections received zero response bytes through the deadline, which exceeds the configured 10-second RTSP read timeout. In all three trials, an independent fresh `OPTIONS` health request received `RTSP/1.0 200 OK`; each server then handled SIGTERM, exited `0`, and flushed Go coverage counters. This supports a repeatable per-connection no-response candidate. The available evidence does not establish a process-wide hang, crash, confirmed defect, or security impact.

## Functional smoke and evidence limits

The post-campaign RTSP transaction passed `OPTIONS`, publisher `ANNOUNCE` / `SETUP` / `RECORD`, reader `DESCRIBE` / `SETUP` / `PLAY`, and `TEARDOWN` (all response codes `200`). AFL's low bitmap and zero crash count must not be presented as target-native coverage or a clean bill of health: the bitmap and process counters are helper-only, while Go coverage and response-state evidence are the target-side observations. The 60-second final preflight is retained separately and is not substituted for the formal run.
