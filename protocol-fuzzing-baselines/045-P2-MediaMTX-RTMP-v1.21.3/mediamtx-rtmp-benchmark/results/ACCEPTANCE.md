# MediaMTX RTMP v1.21.3 benchmark acceptance

- Target: official MediaMTX v1.21.3 source archive, SHA-256 recorded in source-lock.json.
- Protocol: RTMP v3 over TCP. MediaMTX listens at 127.0.0.1:1935; AFLNet reaches a local handshake bridge at 127.0.0.1:1936.
- Method: AFLNet 0f51f9e response-state campaign, with the profile's RTMP chunk/AMF response parser and a corpus covering connect, createStream, releaseStream, and publish.
- Handshake handling: each testcase includes C0/C1 and a placeholder C2; the bridge obtains server S1 per connection and supplies the protocol-correct C2 echo.
- Formal fuzz active time: 1800 seconds (requested 1800).
- AFLNet states and Go-native coverage are preserved under results/rtmp-30m; preflight and fresh post-campaign smoke are separate.
- Image/container cleanup is recorded in results/cleanup.txt.
