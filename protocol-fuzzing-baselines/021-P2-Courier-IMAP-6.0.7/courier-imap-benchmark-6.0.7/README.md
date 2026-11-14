# Courier POP3/IMAP baseline

This package contains two independent protocol profiles built from the official Courier-IMAP 6.0.7 release. The same Courier-IMAP source distribution contains both POP3 and IMAP servers, so the profiles intentionally share one reproducible image while producing separate POP3 and IMAP delivery packages.

The build also pins Courier-authlib 0.73.2, Courier Unicode 2.6.0, AFLNet commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732, the Ubuntu base-image digest, and an Ubuntu package snapshot. source-checksums.sha256 records every source archive checksum. The image compiles reference, AFL-instrumented, and gcov-instrumented builds from the same Courier-IMAP archive.

## Build and validate

From this directory:

~~~sh
./build.sh
./validate.sh profuzzbench/courier-aflnet:6.0.7 "$PWD/results/validation" 60s
~~~

`build.sh` first builds the shared Courier 6.0.7 base image, then applies the IMAP state-parser adapter as a small overlay. Both profiles use the final `profuzzbench/courier-aflnet:6.0.7` image. Validation runs authenticated POP3 and IMAP smoke sessions, then short AFLNet runs for both state parsers. The profiles use isolated container networking and do not publish host ports.

## POP3 profile

~~~sh
docker run --rm --network none --user root \
  -v "$PWD:/workspace:ro" -v "$PWD/results/pop3-30m:/results" \
  profuzzbench/courier-aflnet:6.0.7 \
  bash /opt/benchmark/run.sh pop3 /results/fuzz-30m 30m
~~~

## IMAP profile

~~~sh
docker run --rm --network none --user root \
  -v "$PWD:/workspace:ro" -v "$PWD/results/imap-30m:/results" \
  profuzzbench/courier-aflnet:6.0.7 \
  bash /opt/benchmark/run.sh imap /results/fuzz-30m 30m
~~~

The POP3 adapter frames one LF-terminated command per mutable AFLNet request and maps positive status, negative status, and positive multiline termination to stable response states. The IMAP profile uses the existing IMAP state parser and deterministic IMAP command seeds. Both profiles reset the one-message Maildir before each testcase.

AFLNet launches a small instrumented ELF supervisor because Courier's TCP listener forks and execs the login and protocol servers. The supervisor closes the inherited forkserver descriptors in the listener child to prevent a nested forkserver; the AFL shared-memory map remains available to instrumented Courier workers. It forwards termination signals to the listener process group so testcase servers are reaped cleanly.

After both profiles finish and their evidence is copied into their individual delivery archives, remove the shared image:

~~~sh
docker image rm -f profuzzbench/courier-aflnet:6.0.7
docker image rm -f profuzzbench/courier-aflnet:6.0.7-base
docker builder prune -af
~~~

The smoke evidence verifies protocol behavior and authentication. The fuzz results report execution and AFLNet protocol-state feedback; bitmap coverage is reported as measured and is not inferred from response states.

## Upstream releases

- [Courier download and release notes](https://www.courier-mta.org/download.html)
- [Courier-IMAP installation and requirements](https://www.courier-mta.org/install.html)
- [Courier-authlib user database setup](https://www.courier-mta.org/authlib/README_authlib.html)
- [POP3 specification, RFC 1939](https://www.rfc-editor.org/rfc/rfc1939)
- [IMAP4rev1 specification, RFC 3501](https://www.rfc-editor.org/rfc/rfc3501)
