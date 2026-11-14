# ZLMediaKit RTMP benchmark acceptance

- Target: ZLMediaKit master source snapshot at commit fb3265725f0880da1f52a3cc6e6eb04bbc327fa3; the GitHub Releases page had no published release; this commit was the current master head on 2026-11-11. Main and submodule digests/revisions are in source-lock.json and source/COMPONENTS.txt.
- Protocol: RTMP v3 over TCP. ZLMediaKit listens on 127.0.0.1:1935 and AFLNet reaches it through the local dynamic C2 handshake bridge at 127.0.0.1:1936.
- Method: AFLNet ran 1800 active seconds with the RTMP response-state parser; AFLNet helper bitmap and ZLMediaKit native GCC coverage are reported separately.
- AFLNet: 2732 executions, 3 response paths, stability 100.00%, 0 unique crashes, 0 unique hangs.
- Queue replay: 3/3 entries completed the dynamic RTMP handshake; replay and fresh post-smoke coverage are separate from formal campaign coverage.
- Container and target image cleanup are recorded in results/cleanup.txt.
