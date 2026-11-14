# ZLMediaKit RTSP baseline

This package pins the ZLMediaKit main-branch snapshot `fb3265725f0880da1f52a3cc6e6eb04bbc327fa3` and all source submodules. The repository did not supply a release tag for this snapshot, so the commit is recorded as the implementation version in the table and build lock. AFLNet's RTSP adapter drives the AFL-instrumented `MediaServer` binary.

The container enables RTSP on TCP 8554, disables the other listener ports, and turns off telemetry and unrelated build features to keep the benchmark focused. `ENABLE_MP4` remains enabled because this snapshot's `ext-codec` archive references the bundled FLV/MOV metadata symbols even when media playback is outside the profile. It runs with Docker `--network none`; the smoke test validates OPTIONS `200 OK` and PLAY `454 Session Not Found` on one connection. No RTP media source is configured. A DESCRIBE request for a nonexistent stream waits for a publisher, so the baseline seeds avoid that nonresponsive case and cover RTSP control parsing without claiming media payload coverage.

Build from this directory with `docker build -t profuzzbench/zlmediakit-aflnet:fb326572 .`. Pre-create an empty host output directory and run a short acceptance pass with:

```sh
mkdir -p results/rtsp-smoke
docker run --rm --network none -v "$PWD/results:/work/results" \
  profuzzbench/zlmediakit-aflnet:fb326572 -lc '/work/run.sh /work/results/rtsp-smoke 30s'
bash validate.sh results/rtsp-smoke
```

The default campaign lasts 1800 seconds. AFLNet launches `target-wrapper.sh`, which immediately `exec`s the actual MediaServer binary so the forkserver stays attached to the service. The script profile skips AFLNet's file-type precheck only after the instrumented target's forkserver and the real RTSP response-state graph are independently verified. Results keep that response-state graph and the target bitmap visible as separate metrics; a zero bitmap is reported as unavailable target-code feedback.

## Formal run and hang triage

The 2026-11-06 formal campaign ran for 1,802 seconds and completed 569 executions. AFLNet recorded 14 response paths, 29.12% target bitmap coverage, 35.79% stability, zero crashes, and five hang candidates; the inferred state graph reached depth 2. All five candidates were replayed with AFLNet's sequence replayer against fresh server processes. Each process remained alive and passed a separate OPTIONS health check with `200 OK`; no reproducible service hang or crash was confirmed. The low stability and shallow state depth mean these figures should be treated as exploratory RTSP control-plane feedback, not a stable comparative coverage score. Replay logs and per-candidate health results are in `results/rtsp-30m-final/hang-triage/`.
