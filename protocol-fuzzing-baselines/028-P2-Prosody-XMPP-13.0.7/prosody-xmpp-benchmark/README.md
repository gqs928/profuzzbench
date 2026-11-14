# Prosody XMPP benchmark

This profile benchmarks the official Prosody 13.0.7 source release over loopback XMPP client-to-server TCP (port 5222). It uses the same XMPP stream/stanza request-boundary parser and response-tag state adapter as the ejabberd and Openfire profiles. Prosody runs as a single long-lived process, with one new TCP connection for each AFLNet testcase. The profile is black-box; AFLNet response states do not represent Lua source coverage.

The default formal campaign is 1,800 seconds after the first mutation testcase. Run `protocol_smoke.py` against a started container before fuzzing. The XMPP domain is `example.test`; S2S is disabled and the TLS certificate is a local test certificate. Build with `docker build -t profuzzbench-prosody:13.0.7 .`; for a formal run, mount an empty host results folder at `/results` and invoke `docker run --rm --network none --name prosody-campaign -v "$PWD/results/xmpp-30m:/results/xmpp-30m" profuzzbench-prosody:13.0.7 bash /opt/benchmark/fuzz.sh /results/xmpp-30m 1800`.

## Pinned sources

- Prosody 13.0.7 source: https://prosody.im/downloads/source/prosody-13.0.7.tar.gz; detached signature is retained under `source/`.
- AFLNet source commit: `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`; SHA-256 and build patches are retained in this package.
- Ubuntu 24.04 build base is pinned by digest in `Dockerfile`.
