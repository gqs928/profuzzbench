# SRS RTMP benchmark profile

This profile targets the official SRS v6.0-r3 release, commit `9f6d88164c8608d80ac41264998e80b8076d5e43`. The release page identifies its build version as v6.0.195 and marks the signed release as the latest stable v6 release. Newer v7 alpha and v8 development tags are excluded. The downloaded release archive matches the MD5 published on the release page; its SHA-256 is locked locally in `source-lock.json`.

The scope is RTMP v3 over TCP. Optional RTC, SRT, HLS, HTTP API/server/callback, DVR, ingest and stream-caster features are disabled. The SRS FFmpeg stub class must remain compiled in this release because the RTMP encoder translation unit references it even when transcoding is not exercised; the profile configures no transcode engines and tests only the RTMP listener. SRS listens on TCP 1935; AFLNet connects through a local RTMP handshake bridge on 1936. The bridge supplies C2 by echoing the server's S1 for each connection. AFLNet response-state feedback and SRS GCC/gcovr native coverage are reported as separate metrics.

Build the pinned target, run the parser and server preflight, then start the 30-minute campaign sequentially:

```sh
bash build.sh
docker run -d --name srs-rtmp-30m --network none \
  --user "$(id -u):$(id -g)" -v "$PWD/results:/work/results" \
  srs-rtmp-aflnet:v6.0-r3 \
  -lc '/work/run.sh /work/results/rtmp-30m 1800'
docker wait srs-rtmp-30m
docker logs srs-rtmp-30m > results/rtmp-30m/container.log 2>&1
bash validate.sh results/rtmp-30m
bash stop-server-and-remove-image.sh
bash package.sh
```

The official build guide uses `./configure` followed by `make`; this profile adds native coverage flags and `-fprofile-abs-path` so gcovr resolves sources from isolated run directories, and disables out-of-scope services. `source/SHA256SUMS`, `source-lock.json`, and the build log preserve source and build identity. Each run keeps preflight, formal fuzz, queue replay, and fresh post-smoke evidence in distinct directories. Do not reuse a nonempty result directory.

Upstream references: [SRS v6.0-r3 release](https://github.com/ossrs/srs/releases/tag/v6.0-r3), [SRS 6.0 source build guide](https://www.ossrs.net/lts/en-us/docs/v6/doc/getting-started-build), and [SRS RTMP configuration guide](https://xiaowei.ossrs.net/lts/en-us/docs/v6/doc/rtmp).
