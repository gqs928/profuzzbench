# ApacheDS LDAP benchmark

The upstream Apache Directory site currently publishes ApacheDS 2.0.0.AM27 as its latest release. Its package page warns that the binary archives may contain `AM28-SNAPSHOT` in their internal directory/version strings because the build happened after the source version was bumped; the published artifact is still the AM27 release. We preserve that evidence and the official SHA-512 lock here.

The official binary tarball is placed in a minimal Java 21 runtime image. Its default LDAP transport listens on container TCP 10389 and is published only to loopback as 127.0.0.1:1389. The default ApacheDS instance allows anonymous access and provides the RootDSE. The corpus uses anonymous Bind followed by a base-object RootDSE Search; the smoke script requires successful BindResponse and SearchResultDone.

Run `generate_seeds.py`, `build-aflnet.sh`, build `profuzzbench-apacheds-ldap:2.0.0.AM27`, start with `start-server.sh`, run `protocol_smoke.py`, then `fuzz.sh [output-directory] [active-seconds]` (default 1,800 seconds). `server.sh` is only a readiness check. `stop-server-and-remove-image.sh` removes only this task's container and image after the package has been verified.

The LDAP adapter splits BER LDAPMessage frames and extracts operation/result states. The fuzzer invokes a static ELF readiness probe while ApacheDS remains a managed persistent service; this avoids passing a shell script to AFLNet's executable check. The truncated BER fixture is excluded from the live corpus. Per-protocol experience is maintained in the shared experience library, not copied into this package.
