# Cyrus IMAP stateful fuzz benchmark

This package benchmarks the Cyrus IMAP server's plaintext IMAP command path with AFLNet. The target is the official stable Cyrus IMAP 3.12.4 source release. The source archive and AFLNet source archive are included and SHA-256 pinned. The image builds ordinary, AFL/ASan-instrumented, and gcov-instrumented Cyrus binaries from the same source and configuration.

The IMAP adapter splits client command streams at CRLF while honoring synchronizing and non-synchronizing literals. Literal message data is kept inside its APPEND command, including any embedded CRLF. Server feedback separates tagged OK/NO/BAD/BYE results, continuation prompts, and common untagged response types. Seed sessions cover pre-authentication commands, successful and failed LOGIN, SASL PLAIN, mailbox operations, APPEND, FETCH, SEARCH, namespace queries, and malformed or truncated inputs.

## Complete acceptance

Run all eight evidence gates with a clean, no-cache image rebuild, ten normal
sessions against each server build, three command-by-command seed replay rounds,
three independent AFLNet runs, three identical gcov replay rounds, and an
isolated controlled-fault probe:

```sh
./full-acceptance.sh cyrus-imap-fuzz "$PWD/results/imap-validation-complete" 60s
```

The complete report, semantic response-state map, stepwise transcripts,
function-level coverage evidence, run-summary CSV, repeated-coverage CSV, and
SHA-256 manifest are written below the selected result directory. The fault
probe runs a separate test server and never changes or links into Cyrus.

Coverage replay explicitly selects `/home/ubuntu/experiments/cyrus-gcov`, checks
that `.gcda` data was written, and records that build path. This guards against
accidentally measuring the AFL/ASan server while reporting gcov percentages.

## Basic build and validate

On Linux with Docker available, run:

```sh
chmod +x ./*.sh
./acceptance.sh cyrus-imap-fuzz "$PWD/results/imap-validation" 60s
```

The acceptance script verifies the parser adapter, builds the pinned image, runs ten fresh protocol sessions against both the reference and instrumented server by default, and starts a 60-second AFLNet trial. A small native launcher resets the previous session's temporary state, starts SASL, and execs Cyrus. The reset runs before the master starts; AFLNet's `-c` hook is intentionally a no-op because AFLNet calls that hook after launching the server and immediately before sending the request. The validation must produce a nonempty queue, an IPSM state graph with at least two states and one transition, server transcripts, build versions, and SHA-256 evidence. Set `IMAP_SMOKE_REPETITIONS` to change the repetition count.

## Longer run

After validation, run a 30-minute session:

```sh
mkdir -p results
docker run --rm --hostname localhost --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  cyrus-imap-fuzz bash /workspace/run.sh /results/imap-30m 30m
```

Replay the resulting queue on clean gcov server instances and create line and branch coverage reports:

```sh
docker run --rm --hostname localhost --network none \
  -v "$PWD:/workspace:ro" \
  -v "$PWD/results:/results" \
  cyrus-imap-fuzz bash /workspace/coverage-run.sh \
    /results/imap-30m /results/imap-coverage 0
```

The fuzzer and server share a container loopback interface. The container has no external network during protocol validation and fuzzing; port 1143 is not published on the host. Do not expose the test server outside the isolated container.

## Scope and limits

- IMAP4rev1 over plaintext TCP/1143, with a fixed local SASL test account.
- No TLS/STARTTLS, POP3, NNTP, Sieve, HTTP/JMAP, external directory backend, or throughput measurement.
- A short acceptance run checks reproducibility, protocol handling, target instrumentation, and state feedback. It is not a security audit and does not by itself establish that Cyrus has or has not a vulnerability.
- The gcov replay initializes a fresh Cyrus mailbox/database state for each queue input and records server return status and response byte count.

## Fixed source and protocol references

- Cyrus IMAP 3.12.4 release: [official release notes](https://www.cyrusimap.org/3.12/imap/download/release-notes/3.12/x/3.12.4.html) and [upstream repository](https://github.com/cyrusimap/cyrus-imapd).
- AFLNet source snapshot: ProFuzzBench AFLNet commit `0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732`.
- IMAP4rev1: [RFC 3501](https://www.rfc-editor.org/rfc/rfc3501); non-synchronizing literals: [RFC 7888](https://www.rfc-editor.org/rfc/rfc7888).
- The source archive hashes are in `source-checksums.sha256`; Docker also checks the archive hashes before extraction.
