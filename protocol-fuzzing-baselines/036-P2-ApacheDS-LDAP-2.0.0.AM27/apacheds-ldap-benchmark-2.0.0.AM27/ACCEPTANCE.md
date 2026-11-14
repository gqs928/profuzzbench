# ApacheDS LDAP benchmark acceptance

## Version and artifact identity

The upstream Apache Directory download page lists ApacheDS 2.0.0.AM27 as its latest published release. The official archive `apacheds-2.0.0.AM27.tar.gz` passed its SHA-512 check. The server JAR inside the official archive reports `2.0.0.AM28-SNAPSHOT`; the upstream page explains that the archive was built after the version was bumped and is still the AM27 release. This identity distinction is recorded in `source-lock.json` and `target-version.txt`.

## Validation

- AFLNet and the LDAP adapter built successfully from the locked AFLNet commit and patches.
- Preflight: 26 seconds, 104 executions, 8 paths (6 newly found), 100% stability, 0 crashes and 0 hangs.
- Preflight queue replay: 8/8 inputs connected, 18 LDAP response frames, 0 no-response inputs, 4 bounded waits for an additional frame, 0 resets and 0 errors.
- LDAP smoke passed before and after the formal campaign and queue replay. It verified a successful anonymous BindResponse and RootDSE SearchResultDone.
- Formal campaign: 1,801 active seconds; AFLNet exited with status 0; 3,772 executions; 111 paths (109 newly found); 100% stability; 0 variable paths; 0 crashes; 0 hangs; cycles_done=0.
- Full queue replay: 111/111 queue inputs connected and each received at least one LDAP response; 154 response frames total; 0 no-response inputs, 0 resets and 0 errors. The replay reader reports 86 bounded 1.2-second waits for additional frames.
- The server container remained running and was not OOM-killed after replay. Its exact runtime service JAR metadata was checked against the upstream AM27 packaging notice.

AFLNet bitmap coverage is 0.00% because the target uses a separate readiness ELF to drive a persistent LDAP service, not an instrumented ApacheDS JVM. The reported AFLNet state/path stability should not be interpreted as source-code coverage.

## Resource cleanup

After verifying the independent ZIP and checksum, the benchmark container and image are removed with `stop-server-and-remove-image.sh`. The shared experience library is maintained outside this protocol package.
