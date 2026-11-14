# xrdp 0.10.6.1 RDP baseline

This package builds xrdp commit `80c52879fead585d6347df5b3c587718adf8f5a5`, including the pinned `libpainter`, `librfxcodec`, and `ulalaca` submodule contents. The included AFLNet adapter handles RDP TPKT request boundaries and extracts X.224/RDP negotiation states. Unit tests cover valid and malformed frame lengths plus negotiation-state decoding.

The local configuration disables per-connection forking, selects classic RDP security, binds TCP port 3390 inside a `--network none` container, and supplies a pinned client negotiation seed. Smoke tests require an X.224 Connection Confirm and an RDP_NEG_RSP selecting protocol 0. A direct AFLNet launch of xrdp did not produce response states, so the accepted harness manages xrdp as a separate service and uses a small AFL-instrumented lifecycle helper for AFLNet's forkserver. The AFL bitmap and crash counters therefore describe only the helper; the target signal is the xrdp response-state graph. No xrdp source line coverage is claimed. This baseline exercises the RDP security negotiation stage; it does not claim MCS login or desktop-session coverage.

Build from this directory with `docker build -t profuzzbench/xrdp-aflnet:0.10.6.1 .`. Pre-create an empty output directory and run a short acceptance pass with:

```sh
mkdir -p results/rdp-smoke
docker run --rm --network none -v "$PWD/results:/work/results" \
  profuzzbench/xrdp-aflnet:0.10.6.1 -lc '/work/run.sh /work/results/rdp-smoke 30s'
bash validate.sh results/rdp-smoke
```

The default campaign lasts 1800 seconds. The result package records the AFLNet state graph, helper-only AFL metrics, target build lock, and pre/post RDP negotiation checks separately.

## Accepted formal run

The 2026-11-06 campaign completed 1,802 seconds with 703 executions, one response path, 100% helper stability, 0.01% helper bitmap, and no helper crashes or hangs. The RDP response graph contains the transition `0 → 536870912`, corresponding to the X.224 Connection Confirm; the pre/post checks selected protocol 0. These results cover initial RDP security negotiation only. The helper bitmap is not xrdp code coverage, and this run did not reach MCS login or desktop-session states.
