# Kea 3.2.1 DHCPv4/UDP fuzz benchmark

This package builds ISC Kea DHCPv4 3.2.1 and AFLNet from checksum-locked source archives. A small AFLNet adapter treats each UDP datagram as one DHCP message and extracts response states from BOOTP direction and DHCP option 53. The tested target is Kea's real DHCPv4 server on isolated container loopback port 6767.

## Build and smoke test

```sh
./build.sh
```

The smoke test starts a fresh Kea process ten times, sends a relayed DHCPDISCOVER followed by DHCPREQUEST, and checks for the stable DHCPOFFER/DHCPACK transcript. Kea's UDP socket mode is used because raw DHCP sockets cannot bind to loopback in this container. The harness therefore supplies a loopback relay address in `giaddr`, and the test client binds to standard relay port 67 to receive Kea's unicast replies. Run the container as the workspace user with `CAP_NET_BIND_SERVICE`; the target itself does not need raw sockets or network administration privileges.

## Run

The formal campaign is 30 minutes. Keep the container network isolated and grant only the capability needed to bind the relay port:

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  --cap-add NET_BIND_SERVICE \
  -v "$PWD/results:/work/results" \
  kea-dhcp4-aflnet:3.2.1 /work/run.sh /work/results/dhcp4-30m 1800
```

`run.sh` asks AFLNet to bind its UDP client to port 67 (`-l 67`) and send to Kea on port 6767. Kea replies to the relay address and port carried by each DHCP packet. A completed run requires matching requested duration in `run.json`, raw `fuzzer_stats`, the AFLNet queue, and the run log.

## Scope and limits

The profile covers DHCPv4 over UDP through Kea's relay-agent path. Seeds include DISCOVER, REQUEST, INFORM, RELEASE, DECLINE, truncated options, malformed options, and a short BOOTP header. Kea is built with AFL edge instrumentation and without ASan; the report distinguishes those signals. Multi-threading is disabled and the memfile lease database is non-persistent so fresh target processes begin from a clean lease state. The binary reports `3.2.1-git` because the checksum-locked release archive omits Git metadata; the source tag and commit identify the tested Kea release as 3.2.1.

The adapter does not fuzz the raw Ethernet/IP broadcast path or DHCPv6. A relay address is part of this isolated harness, so results describe Kea's DHCPv4 relay/UDP handling. The single-sample output and hang signal must be independently replayed with a fresh service process and a valid DHCP health query before being classified as a target failure.

## Locked inputs

- Kea release tag `Kea-3.2.1`, commit `1737462bc79276e3269304ea8cd3d1c03400e30d`.
- ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- Ubuntu 24.04 image digest `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- Source archive hashes are recorded in `source-checksums.sha256`; the AFLNet adapter patch is checked by `patch-checksums.sha256`. `SHA256SUMS.txt` covers the delivered package files.
