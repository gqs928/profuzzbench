# Kea 3.2.1 DHCPv4/UDP baseline results

## Scope and build identity

- Target: the real Kea DHCPv4 server, UDP relay path on loopback port 6767. DHCPv6 and raw Ethernet/IP broadcast handling are outside this profile.
- Source: tag `Kea-3.2.1`, commit `1737462bc79276e3269304ea8cd3d1c03400e30d`; source archive SHA-256 is in `source-checksums.sha256`.
- AFLNet: commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`. The adapter treats each UDP datagram as one request and extracts BOOTP direction plus DHCP option 53 into non-overlapping state IDs.
- Build: the `kea-dhcp4` dependency closure completed all 404 Ninja steps in 377 seconds. Kea was compiled with AFL GCC/G++ assembler instrumentation and `-O1 -g -fno-omit-frame-pointer`; ASan was not enabled. This result reports AFL edge-map feedback only.
- The binary logs `3.2.1-git` because the source archive lacks Git metadata. The locked upstream tag and commit identify the tested release as Kea 3.2.1.
- Image used for the formal run: `kea-dhcp4-aflnet:3.2.1-relay`, ID `sha256:8c9e8a2b8576e0387654e31572383aa1b063650fb181dc11c087e9470873d2cc`. Build IDs and package versions are preserved under `results/build/`.

Kea's default raw-socket mode refuses to bind to loopback. Its UDP socket mode accepts relay traffic, so the isolated harness sets `giaddr` to `127.0.0.1` and binds AFLNet's client socket to port 67 with `-l 67`; Kea listens on port 6767 and returns unicast replies to the relay port. The AFLNet patch narrowly permits source port 67. The container runs with `--network none`, as the workspace user, and only `CAP_NET_BIND_SERVICE` for the fixed relay port.

## Service and reset validation

Ten fresh Kea processes each completed the same relay-path transcript:

`DHCPDISCOVER → DHCPOFFER → DHCPREQUEST → DHCPACK`

All 10 returned the same address, `127.0.0.100`, and stayed alive through the exchange. Kea uses a non-persistent in-memory lease database, and AFLNet forks a new target process for each test case. Multi-threading is disabled in the test profile. See `results/build/service-smoke.json` and the per-process logs in `results/build/smoke/`.

The 60-second adapter calibration recorded 41 executions and an AFLNet response-state edge for DHCPOFFER (`0x20002`). The formal run also recorded DHCPACK (`0x20005`) in `ipsm.dot`. The calibration is retained separately and is not included in the formal duration.

## Formal run

The isolated AFLNet campaign ran for exactly 1,800 seconds. The wrapper received timeout exit code 124 after its scheduled SIGINT; `run.json` verifies `last_update - start_time = 1,800` seconds.

| Measure | Result |
|---|---:|
| Executions | 699 |
| Paths total | 27 |
| Paths found | 19 |
| Variable paths | 10 |
| Stability | 99.95% |
| Bitmap coverage | 31.34% |
| Unique crashes | 0 |
| AFLNet hang candidates | 25 |
| Executions per second | 0.49 |
| Maximum depth | 2 |
| Queue cycles completed | 0 |
| Peak RSS | 29 MB |

AFLNet dry-run calibration skipped 5 of the 8 seeds on timeout (`decline`, `inform`, `malformed-option`, `release`, and `short-bootp`). It warned that instrumentation output varied for `discover`, `request`, and `truncated`; the overall measured stability was 99.95%. The 30-minute campaign ended before completing its first queue cycle. Preserve the dry-run skips and cycle state when comparing runs; the total execution count alone does not describe campaign progress.

## Hang-candidate replay

Each of the 25 candidates was sent unchanged to a fresh Kea process 3 times. All 75 candidate datagrams were within the IPv4 UDP payload limit and were sent. None received a DHCP response within the 5-second candidate window, but every Kea process remained alive; every subsequent valid DHCPDISCOVER received a DHCPOFFER. All 75 attempts are classified as `target_survived_and_health_probe_passed`, not confirmed hangs. No crash or persistent service hang is claimed. The exact candidates, per-attempt logs, and JSON records are under `results/dhcp4-30m/triage/`.

## Reproduction

Build the image from the locked source archives and full adapter patch:

```sh
./build.sh
```

Run the 30-minute profile in an isolated container:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --cap-add NET_BIND_SERVICE \
  -v "$PWD/results:/work/results" \
  kea-dhcp4-aflnet:3.2.1 /work/run.sh /work/results/dhcp4-30m 1800
```

The `fuzzer_stats`, `run.json`, AFLNet log, state graph, queue, calibration and replay evidence are included with this report. The shared framework experience library is maintained separately and is intentionally not included in this protocol package.
