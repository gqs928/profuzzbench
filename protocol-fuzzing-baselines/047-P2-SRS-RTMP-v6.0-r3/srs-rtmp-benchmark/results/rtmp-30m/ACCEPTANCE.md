# SRS RTMP benchmark acceptance

- Target: official SRS v6.0-r3 source release, signed release commit 9f6d88164c8608d80ac41264998e80b8076d5e43; source digests are in source-lock.json.
- Protocol: RTMP v3 over TCP. SRS listens on 127.0.0.1:1935 and AFLNet reaches it through the local dynamic C2 handshake bridge at 127.0.0.1:1936.
- Method: AFLNet ran 1801 active seconds with the RTMP response-state parser; AFLNet helper bitmap and SRS native GCC coverage are reported separately.
- AFLNet: 4161 executions, 3 response paths, stability 100.00%, 0 unique crashes, 0 unique hangs.
- Queue replay: 3/3 entries completed the dynamic RTMP handshake; replay and fresh post-smoke coverage are separate from formal campaign coverage.
- Container and target image cleanup are recorded in results/cleanup.txt.
