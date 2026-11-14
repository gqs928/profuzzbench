# NGINX RTMP benchmark acceptance

- Target: NGINX 1.30.6 stable with upstream nginx-rtmp-module v1.2.2 (commit 23e1873aa62acb58b7881eed2a501f5bf35b82e9); exact source archives and hashes are in source-lock.json.
- Protocol: RTMP v3 over TCP. NGINX listens on 127.0.0.1:1935 and AFLNet reaches it through the C2 handshake bridge on 127.0.0.1:1936.
- Method: AFLNet 1800 active seconds (requested 1,800), RTMP response-state parser, queue replay through fresh RTMP sessions, and GCC/gcovr target coverage.
- AFLNet: 4996 executions, 3 response paths, stability 100.00%, 0 unique crashes, 0 unique hangs.
- Queue replay: 3/3 queue entries completed the dynamic RTMP handshake.
- Formal target coverage is captured before the separate queue replay under results/rtmp-30m/campaign. Queue replay and its independent coverage are under results/rtmp-30m/replay; the fresh post-smoke is under results/rtmp-30m/post-smoke.
- Container and image cleanup are recorded in results/cleanup.txt.

The AFLNet bitmap describes only the lifecycle helper; target coverage is reported separately from NGINX and the RTMP module through GCC native coverage.
