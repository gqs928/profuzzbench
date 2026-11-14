# GStreamer gst-rtsp-server 1.28.8 RTSP/TCP baseline

This independent package builds the upstream stable `gst-rtsp-server` 1.28.8 source release as the AFLNet target. The RTSP server library and the upstream `test-launch` sample are compiled with AFLNet's GCC instrumentation wrapper. The application serves a small live raw-video stream through RTSP over TCP interleaving, so the target handles real OPTIONS, DESCRIBE, SETUP, PLAY, and TEARDOWN requests.

The target release is fixed to the official source tarball and SHA-256 recorded under `source/`. Ubuntu 26.04 provides the GStreamer core and plugins-base runtime/development libraries at 1.28.2; `gst-rtsp-server` 1.28.8 declares a minimum dependency of 1.28.0. Both target and dependency versions are recorded separately in build evidence. The upstream `test-launch` sample receives one small, hash-locked harness patch to exit its GLib main loop on SIGINT/SIGTERM; this gives AFLNet a clean per-testcase server reset without changing the RTSP library.

## Build and preflight

```sh
./build.sh
```

`build.sh` creates `gstreamer-rtsp-aflnet:1.28.8`, records the image ID and compiler/dependency versions, and runs a 60-second protocol/feedback preflight. The formal campaign is run separately:

```sh
docker run -d --name gst-rtsp-30m --network none \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/work/results" \
  gstreamer-rtsp-aflnet:1.28.8 \
  -lc '/work/run.sh /work/results/rtsp-30m 1800s'
docker wait gst-rtsp-30m
```

The fuzzer uses AFLNet's built-in RTSP request and response-code parser. Each RTSP request is delimited by CRLF-CRLF. It maintains the target process lifecycle and records AFL edge feedback separately from the RTSP response-state graph. In the final short preflight, the instrumented target reported `bitmap_cvg=0.00%` and `stability=0.00%`, despite instrumentation symbols being present; therefore this result does not establish usable target edge coverage. The formal report preserves the raw bitmap and states whether it is usable. RTSP/TCP is the measured scope; UDP transport, TLS, authentication and alternate media pipelines are outside this profile.

## Acceptance evidence

`results/preflight-live/` contains the final short run and protocol smoke; earlier failed attempts remain in `results/preflight/` for diagnosis. `results/rtsp-30m/` contains the formal 1,800-second campaign, raw AFLNet output, RTSP response graph, statistics, and post-run smoke. The smoke negotiates a TCP-interleaved stream and checks OPTIONS, SDP generation, SETUP, PLAY and TEARDOWN. The response-state graph and AFL bitmap are separate measurements; a nonempty graph does not turn a zero bitmap into target code coverage. `package.sh` creates the standalone ZIP without copying a protocol-specific experience entry; framework-oriented lessons are consolidated in the shared `deliverables/12-protocol-baselines-2026-11-03-framework/基准化经验库.md`.

## Reproduction

The build inputs are the official `gst-rtsp-server` 1.28.8 source archive, AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`, an Ubuntu 26.04 image pinned by digest, and the exact installed package list in `results/build/build-lock.txt`. Run `sha256sum -c source/SHA256SUMS` from `source/` before building and `sha256sum -c results/SHA256SUMS` from `results/` after the campaign.

## Upstream references

- GStreamer module and stable release status: https://gstreamer.freedesktop.org/modules/gst-rtsp-server.html
- Official source tarballs and publisher checksums: https://gstreamer.freedesktop.org/src/gst-rtsp/
