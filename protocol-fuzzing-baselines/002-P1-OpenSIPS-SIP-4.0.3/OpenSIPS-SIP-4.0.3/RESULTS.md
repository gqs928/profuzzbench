# OpenSIPS 4.0.3 SIP/UDP baseline results

## Scope and build identity

- Target: the real OpenSIPS SIP server over UDP on loopback port 5060, with SIP status-code feedback from AFLNet.
- Source: tag 4.0.3, commit ca1549c1350a455aa73a420fbecaba53d7d451dd.
- AFLNet: commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.
- Base image: Ubuntu 24.04, digest sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852.
- Benchmark image: opensips-sip-aflnet:4.0.3, ID sha256:bbb2e50c9147d697a5fa1a4fd9724a1d4d84939d9e3cdcf105a9b63982af640e.
- Build and real-service smoke passed. A valid SIP OPTIONS request received a 200 response (330 bytes). See results/build/service-smoke.json.
- The profile loads proto_udp and sl and routes requests through the real SIP parser and request route. This baseline covers SIP/UDP only; SIP/TCP, TLS, database-backed registration, and proxy routing are out of scope.

## Formal run

AFLNet ran for exactly 1,800 seconds. The wrapper's timeout returned 124 after its expected SIGINT; run.json confirms last_update minus start_time equals 1,800 seconds.

| Measure | Result |
|---|---:|
| Executions | 820 |
| Paths total | 31 |
| Paths found | 25 |
| Variable paths | 28 |
| Stability | 92.93% |
| Bitmap coverage | 7.17% |
| Unique crashes | 0 |
| AFLNet hang candidates | 50 |
| Cycles completed | 0 |

Initial calibration took about 1.31 seconds per seed. AFLNet skipped two of six seeds because they timed out during dry run, leaving four accepted seeds. The campaign ended before completing the first queue cycle, and execution throughput averaged 0.61 per second. These limits are part of the baseline and should accompany comparisons across versions or implementations.

## Hang-candidate replay

Each of the 50 hang candidates was tested three times against a fresh OpenSIPS process, followed by a valid SIP OPTIONS health probe. All 150 target processes remained alive and all 150 health probes passed. The 147 candidate datagrams that fit the IPv4 UDP payload limit received no SIP response within the five-second replay window. One 76,590-byte candidate exceeds the 65,507-byte IPv4 UDP payload limit and could not be sent as a single datagram; all three attempts are recorded as unreplayable for that transport, without truncating the candidate.

No persistent service hang or crash was confirmed. The 47 candidates that were deliverable over UDP were silent-input candidates, not confirmed defects; the oversized candidate cannot be claimed as a reproduced target behavior. Per-attempt records and server logs are under results/sip-30m/triage-final/.

## Reproduction

Build the pinned image with ./build.sh, then run the formal campaign:

    docker run --rm --network none --user "$(id -u):$(id -g)" \
      -v "$PWD/results:/work/results" \
      opensips-sip-aflnet:4.0.3 /work/run.sh /work/results/sip-30m 1800

Replay the resulting candidates with three fresh-process repetitions:

    docker run --rm --network none --user "$(id -u):$(id -g)" \
      -v "$PWD:/work" opensips-sip-aflnet:4.0.3 -lc \
      'python3 /work/triage_hangs.py /work/results/sip-30m/aflnet-out/replayable-hangs /work/results/sip-30m/triage 3'

Raw campaign output is under results/sip-30m/. Build inputs, version locks, and service smoke evidence are under results/build/ and source-checksums.sha256.
