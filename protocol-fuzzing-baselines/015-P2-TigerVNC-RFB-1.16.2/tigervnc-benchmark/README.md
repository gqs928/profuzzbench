# TigerVNC 1.16.2 RFB baseline

This package builds TigerVNC's `x0vncserver` from commit `b555312d70d7ff017f866649a7e7167af4eb8fca` and runs AFLNet's RFB adapter against the actual AFL-instrumented server. The test server shares only a private 640×480 Xvfb display, binds RFB port 5901 to localhost, and offers the None security type inside a network-isolated container.

The RFB adapter patch and its parser tests are included under `source/` and `tests/`. The parser test covers RFB 3.8 negotiation and client-message boundaries, ServerInit state extraction, oversized client text lengths, RDP TPKT boundaries, and X.224 RDP negotiation states. The RDP checks share the adapter patch used by the xrdp package.

Build from this directory with `docker build -t profuzzbench/tigervnc-aflnet:1.16.2 .`. Pre-create an empty host output directory and run a short acceptance pass with:

```sh
mkdir -p results/rfb-smoke
docker run --rm --network none -v "$PWD/results:/work/results" \
  profuzzbench/tigervnc-aflnet:1.16.2 -lc '/work/run.sh /work/results/rfb-smoke 30s'
bash validate.sh results/rfb-smoke
```

The default run duration is 1800 seconds. The AFL timeout is 30 seconds because the instrumented server can take longer than AFL's default timeout to complete a full RFB exchange. Results retain the response-state graph and raw AFL bitmap separately; a zero bitmap is reported as no observed code feedback, not as coverage. The smoke test completes an RFB 3.8 None-security handshake, checks ServerInit, and sends a FramebufferUpdateRequest.

## Formal run

The 2026-11-06 campaign completed 1,800 seconds with 429 executions, 14 response paths, 5.04% target bitmap coverage, 67.97% stability, zero crashes, and zero hangs. The 640x480 Xvfb framebuffer and RFB 3.8 pre/post smoke checks passed. The relatively low stability means this is an exploratory profile; retain the target bitmap and response-state graph as separate signals and avoid treating the path count as a stable ranking metric.
