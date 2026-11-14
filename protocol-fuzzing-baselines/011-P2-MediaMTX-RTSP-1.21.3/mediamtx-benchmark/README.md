# MediaMTX RTSP/TCP benchmark v1.21.3

This independent profile builds the official MediaMTX `v1.21.3` source archive with Go 1.27 native coverage instrumentation and runs AFLNet's RTSP response-state mode against one local server. It covers RTSP over TCP on `127.0.0.1:8554`; the server profile disables RTMP, HLS, WebRTC, SRT, APIs, and playback and uses anonymous publish/read permissions only inside the isolated container.

The Go target is not AFL-instrumented. AFLNet uses a small AFL-instrumented C lifecycle helper with a forkserver so each testcase can be ended cleanly. The AFL bitmap and process-crash counter describe that helper; timeout candidates are AFLNet run-loop outcomes and require independent protocol replay before they can be attributed to MediaMTX. AFLNet supplies the RTSP response-state graph. Actual MediaMTX Go coverage is collected separately with `-coverpkg=./...` and `GOCOVERDIR`, then merged and summarized with `go tool covdata` and `go tool cover`.

Build and run the validation profile:

```sh
./build.sh
```

Run the formal 30-minute campaign from this directory:

```sh
docker run -d --name mediamtx-rtsp-30m --network none \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/work/results" \
  mediamtx-rtsp-aflnet:v1.21.3 \
  -lc '/work/run.sh /work/results/rtsp-30m 1800s'
docker wait mediamtx-rtsp-30m
./package.sh
```

MediaMTX remains a separately managed service throughout the campaign. AFLNet sends RTSP requests to that persistent service and uses the forkserver helper only for per-input lifecycle tracking. The Go service is stopped after the campaign and flushes native coverage counters. The response-state graph is the AFLNet target feedback signal; the helper bitmap and process-crash counter are not MediaMTX coverage or defect counts. AFLNet timeout candidates require independent protocol replay before they can be attributed to MediaMTX. Coverage counters are collected from the campaign service and a separate fresh post-smoke service, then merged; the post-smoke portion proves normal RTSP traffic reaches Go-instrumented code but must not be counted as fuzz-induced coverage. Campaign, build, smoke, response-state, coverage, and source-hash evidence is preserved under `results/`; the shared framework experience library is maintained outside this protocol ZIP.

If AFLNet reports a timeout candidate, `replay_candidate.sh` starts a fresh MediaMTX process for each of three replays, and `replay_rtsp_sequence.py` decodes and sends the length-prefixed RTSP messages. It records response timeouts and post-replay server health separately from campaign counters; a timeout is a candidate until independently reproduced and classified.

`summarize_coverage.sh` can emit separate Go summaries for the campaign service and the fresh post-smoke service; neither should be inferred from the merged percentage alone.
