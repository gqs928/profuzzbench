# 389 Directory Server LDAP benchmark acceptance

## Release and runtime

- Upstream stable release checked on 2026-11-09: 389 Directory Server 3.3.1, per the [official 3.3.1 release page](https://www.port389.org/docs/389ds/releases/release-3-3-1.html).
- Runtime: `389-ds-base-3.3.1-3.fc45.x86_64` from Fedora 45 stable, verified with both `rpm -q 389-ds-base` and `ns-slapd -v`. The pinned Fedora base digest is in `source-lock.json`.
- The upstream `quay.io/389ds/dirsrv:latest` image was inspected and returned 2.4.6, so it was rejected for this 3.3.1 baseline. The exact Fedora 45 package release is listed on the [official Fedora package page](https://packages.fedoraproject.org/pkgs/389-ds-base/389-ds-base/fedora-45.html).
- The official 3.3.1 source archive SHA-512 was rechecked before packaging.

## Protocol validation

- Smoke before and after the campaign: anonymous LDAP BindResponse result code 0 and RootDSE SearchResultDone result code 0.
- 26-second preflight: exit 0, 26 active seconds, 67 execs, 6 paths (4 new), 100% stability, 0 crash, 0 hang.
- Formal campaign: exit 0, 1,801 active seconds, 3,568 execs, 164 paths (162 new), 0 variable paths, 100% stability, 0.00% bitmap coverage, 0 unique crashes, 0 unique hangs, `cycles_done=0`.
- The zero bitmap is expected for this black-box response-state profile and is not a claim about 389 DS source-code coverage.
- Queue replay: 164/164 connections succeeded, 794 complete LDAP response frames, 3 requests with no response frame, 50 waits for an additional frame timed out, 0 resets, 0 other errors. See `results/ldap-30m/replay-summary.json`.
- Container remained running and was not OOM-killed after replay; post-run smoke passed.

## Harness notes

- The LDAP response reader treats the first two BER bytes as the sequence tag and first length octet; it reads additional length octets only for BER long-form lengths. Smoke tests exercise a real RootDSE response.
- AFLNet rejects shell scripts as target executables even in dumb mode. A statically linked ELF readiness probe is used as the AFLNet process target while the separately supervised LDAP daemon remains persistent.
- `results/ldap-30m/fuzzer_stats`, `run-status.txt`, `fuzzer-summary.txt`, and replay summary retain the run evidence. Per-protocol framework experience is kept in the central experience library, not this package.

## Cleanup

After the independent ZIP and its checksum passed verification, the exact container `389ds-ldap-331` and image `profuzzbench-389ds-ldap:3.3.1` were removed. The unused 389 Quay image, Fedora 45 base image, and build cache were also removed; only the Ubuntu base image needed by the remaining profiles was retained.
