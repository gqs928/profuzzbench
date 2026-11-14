# OpenSSL DTLS 1.2 AFLNet baseline

This package prepares the official OpenSSL 4.1.0 release, published 23 October 2026, as a local DTLS 1.2/UDP server target. The source is checksum-pinned and its detached signature is verified against the signing keyring published by the OpenSSL project. OpenSSL is built from source with AFLNet instrumentation, and AFLNet's built-in DTLS12 parser supplies response-state feedback. A small custom one-client UDP echo harness links against the instrumented OpenSSL libraries because `openssl s_server -rev` does not support DTLS.

The intended target is the instrumented `dtls_echo_server`, with a local self-signed certificate and a fixed UDP port. The harness binds one process to one client peer, performs a DTLS 1.2 server handshake through OpenSSL's datagram BIO, and reverses one application record. DTLS 1.0, DTLS 1.3, TLS/TCP, and external network services are excluded. Handshake, echo, and AFLNet state-feedback preflight must pass before the formal campaign starts.

The current seed corpus contains checksum-pinned GnuTLS 3.8.13 ClientHello datagrams. The package includes capture_seeds.py to generate target-native ClientHello datagrams from OpenSSL 4.1.0's own client when run inside the image. Only the verified final seed set is used for the formal run.

## Reproduce

    ./build.sh
    ./run-benchmark.sh /results/openssl-dtls-fuzz-30m 30m

To generate a new seed set and run with it:

    docker compose --env-file images.env -f compose.yaml run --rm --no-deps fuzz \
      python3 /opt/benchmark/capture_seeds.py --output /results/generated-seeds --passes 3
    SEED_DIR=/results/generated-seeds ./run-benchmark.sh /results/openssl-dtls-fuzz-30m 30m

The expected campaign resource bounds are 1,800 seconds, 2 CPU cores, 768 MiB memory, and a 10-second testcase timeout. The report includes the AFLNet queue, response-state graph, statistics, replay results, three-pass DTLS handshake/reverse-echo evidence, and listener shutdown check.

## Completed 2026-11-12 baseline

OpenSSL 4.1.0 completed the bounded DTLS 1.2 campaign with 18,804 executions, 314 paths, 104 variable paths, 95.27% stability, 25.46% AFLNet bitmap, 27 cycles, and zero crashes or hangs. The supervisor reached its 1,800-second deadline with one SIGINT; the final stats span 1,801 seconds because AFLNet wrote its last stats update immediately after the signal. Treat bitmap as instrumented harness/library feedback, not OpenSSL source coverage.

The full raw/KL/IPSM replay accounted for all 636 saved samples. It classified 218 structurally invalid streams before sending and brought 418 valid DTLS record sequences through target readiness. Replay parsed 404 response datagrams and 1,167 response states; 134 malformed/incomplete one-client sessions ended with the target's expected return code 0, and the remaining 284 targets stayed alive. No nonzero target exit or replay transport error occurred. Pre- and post-run smoke each completed three DTLS 1.2 handshakes and reverse echoes, and the UDP listener was closed after the run. See `ACCEPTANCE.md` and the included result directory for evidence.

The shared automation-framework experience library is maintained in the central deliverables directory, outside protocol ZIPs.
