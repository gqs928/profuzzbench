# OpenLDAP LDAP benchmark acceptance

## Version and source identity

The target is OpenLDAP 2.7.2, the upstream current Feature Release verified on 2026-11-10. OpenLDAP 2.6.16 is the separately maintained LTS line. The 2.7.2 source signature passed verification with the OpenLDAP Project key, fingerprint `3CE269B5398BC8B785645E987F67D5FD1CE1CBCE`; the source archive SHA-256 is locked in `source-lock.json`.

## Validation

- The BER-aware AFLNet target and LDAP parser tests built successfully from the locked AFLNet source and local adapter.
- Pre-run LDAP smoke passed: anonymous BindResponse success and RootDSE SearchResultDone success.
- Formal campaign: 1,801 active seconds; wrapper exit status 0; 4,131 executions; 127 queue paths (125 newly found); 0 variable paths; 100% stability; 0 crashes; 0 hangs; `cycles_done=0`.
- Full queue replay: 127/127 inputs connected; 153 complete LDAP response frames; 80 inputs received no response; 37 bounded waits for additional frames; 0 resets and 0 replay errors.
- The post-replay smoke again passed anonymous Bind and RootDSE Search. The server remained usable after queue replay, so the 80 silent individual inputs are not evidence of a service hang. LDAP Unbind has no response by protocol design and is excluded from live seeds.
- AFLNet bitmap coverage is 0.00% because this is a black-box state-feedback profile using a separate ELF readiness target and a persistent slapd service; it does not report OpenLDAP source coverage.

## Resource cleanup

The dedicated container and image are removed after package and SHA-256 verification. The earlier 1,210-second interrupted attempt is retained separately in the working profile as `results/ldap-20m-interrupted-20261110`; the delivered `results/ldap-30m` contains only the completed formal run.

Per-protocol lessons are recorded in the shared experience library and are not duplicated in this package.
