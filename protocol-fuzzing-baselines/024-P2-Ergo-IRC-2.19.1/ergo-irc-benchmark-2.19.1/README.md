# Ergo IRC benchmark baseline

This package adapts upstream **Ergo 2.19.1** to the IRC benchmark profile in this repository. It contains the source archives, pinned toolchain and fuzzer inputs, a loopback-only configuration, build/validation/run scripts, and generated evidence. Reusable cross-protocol framework lessons live in the shared protocol-baseline experience library, not in this protocol package.

## Scope and instrumentation

- Target: Ergo v2.19.1, plaintext IRC over IPv4 loopback TCP/6667. TLS, WebSocket, IPv6, external database services, and public listeners are disabled or outside this profile.
- Source: upstream release archive; SHA-256 and exact URL are recorded in source-lock.json.
- Build variants: reference and AFLNet variants are the same static Go build from the pinned source; the coverage variant uses Go coverage instrumentation across all packages.
- Fuzzer: AFLNet's IRC response-state adapter in uninstrumented (`-n`) mode. QEMU 2.10.0 builds with the included modern-Linux patch, but Go 1.27.3 fails to reserve its page-summary memory under QEMU, so binary feedback is disabled. The included AFLNet dumb-mode patches avoid a zombie-child wait deadlock and admit queue inputs when they discover new IRC response-state sequences. Queue replay separately collects application Go coverage through GOCOVERDIR; `bitmap_cvg` therefore remains zero and is not reported as application coverage.
- Runtime: the container has no external network; the sole configured listener binds to 127.0.0.1:6667. The target wrapper removes and recreates its working directory before every sample, resetting Ergo's persistent `ircd.db` and lock file; AFLNet keeps a separate work directory.

## Rebuild and verify

From this directory, run ./build.sh and then ./validate.sh.

Validation compares IRC numeric reply paths for five sessions across reference/AFL/Go-coverage builds, runs a 180-second AFLNet state-feedback smoke, checks that a new response-state path is queued and the state graph is nontrivial, replays every queued sample against the Go-coverage build, and writes checksums under results/validation/.

For a formal run, create a new host output directory and mount the package's `results/` directory at `/results`. The campaign writes to `results/irc-30m/campaign`; its coverage replay report and Go coverage data are kept alongside it. Then run:

~~~sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" \
  profuzzbench/ergo-irc:2.19.1 \
  bash /opt/benchmark/run.sh /results/irc-30m/campaign 30m
~~~

After the campaign exits, replay the queue in the same image, mounting the same results directory:

~~~sh
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD/results:/results" profuzzbench/ergo-irc:2.19.1 \
  python3 /opt/benchmark/coverage_replay.py \
    /results/irc-30m/campaign/queue /results/irc-30m/coverage
~~~

A run counts as formally complete only when its process exits, fuzzer_stats spans the full 30-minute window, the queue and state graph are present, and coverage replay has no failed samples. A smoke result alone is not completion evidence.

## Source archive manifest

See source-lock.json for Ergo 2.19.1, Go 1.27.3, AFLNet commit 0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732, the IRC adapter hashes, and the QEMU source digest. The source directory holds the exact archives used during the build; results contains validation/formal evidence when generated.

After formal validation and packaging, remove the local image with ./clean.sh. It removes only this package's tagged image.
