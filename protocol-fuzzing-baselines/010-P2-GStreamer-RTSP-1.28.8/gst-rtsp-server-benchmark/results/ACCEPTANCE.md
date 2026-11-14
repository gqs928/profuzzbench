# GStreamer gst-rtsp-server RTSP/TCP fuzz-baseline acceptance

## Scope and build identity

- Target: upstream `gst-rtsp-server` `1.28.8`, RTSP over TCP on `127.0.0.1:8554`; the sample serves a 16×16, 1 fps live raw-video pipeline.
- Source archive SHA-256: `59181ed21a5bc0533fb4f77cb7bc6005d89365e834b0c1294afb9ab5f7d96fe0`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, archive SHA-256 `251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d`.
- Runtime image ID: `sha256:6214ceff8b244d52728a111809f6845669bc5df3da630c85c072b776bc0bb8df`.
- The upstream `test-launch` sample receives a hash-locked GLib signal-handler patch so SIGINT/SIGTERM can end its main loop for AFLNet resets. The patch changes only the sample harness, not the RTSP server library. GStreamer runtime dependencies are 1.28.2 and are separately locked.
- AFL instrumentation symbols were present in the target library (`24` symbols). Unlike the MediaMTX/VerneMQ sidecar profiles, AFLNet launches this instrumented executable and library directly; the formal AFL bitmap is target-process feedback.

## Formal campaign

The AFLNet timestamps span exactly 1,800 seconds; external wall-clock evidence spans 1,801 seconds. The configured timer expired normally (wrapper exit `124`) and AFLNet exited `0`. No crash or hang was recorded.

| Metric | Result |
|---|---:|
| Executions | 899 |
| Executions per second | 0.66 |
| Total paths / new paths | 31 / 25 |
| Variable paths | 31 |
| AFL stability | 73.05% |
| Target AFL bitmap coverage | 3.14% |
| Completed queue cycles | 0 |
| Peak RSS | 42 MiB |
| Unique crashes / hangs | 0 / 0 |
| RTSP response states | 200, 400, 404, 461 |
| Response-state graph edges | 10 |

The final graph is `results/rtsp-30m/aflnet-out/ipsm.dot`. The 3.14% bitmap demonstrates non-zero target edge feedback, but all 31 paths were marked variable, stability remained 73.05%, and the queue did not complete a cycle. This is a completed exploratory baseline, not a stable coverage-comparison result.

## Preflight, smoke, and interpretation

The final 60-second preflight (`aflnet-60s-final6`) produced 22 executions, 6 paths, one variable path, `stability=0.00%`, and `bitmap_cvg=0.00%`. The formal campaign later produced a non-zero target bitmap. Keep both observations: a short preflight was enough to verify response-state operation and service startup, but its zero bitmap did not predict the longer run's bitmap. A non-zero formal bitmap also does not compensate for the low stability; reports and automation should retain both signals and apply the profile's stability threshold.

After the campaign, RTSP `OPTIONS`, `DESCRIBE`, `SETUP`, `PLAY`, and `TEARDOWN` all returned `200`. The measured profile is RTSP/TCP only; it makes no claim about UDP transport, TLS, authentication, other media pipelines, or source line/branch coverage. Earlier preflight attempts remain in `results/preflight/` for diagnosis; `results/preflight-live/` contains the final preflight.
