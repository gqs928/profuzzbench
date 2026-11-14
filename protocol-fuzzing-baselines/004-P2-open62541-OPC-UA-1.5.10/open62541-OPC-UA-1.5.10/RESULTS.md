# open62541 1.5.10 OPC UA/TCP baseline results

## Target and build identity

- Upstream release: open62541 `v1.5.10`, commit `93c3bdfc9ea4718b503c6cbf57876237addd0f2c`; source archive SHA-256 is recorded in `source-checksums.sha256`.
- Target: upstream OSS-Fuzz `tests/fuzz/fuzz_tcp_message.cc`, built as a libFuzzer target with Clang 18.1.3, AddressSanitizer and UndefinedBehaviorSanitizer. The image is `sha256:1d7b71026f38a7777d937e6b00e7e374b89add340fe6a0d6e62a0993847f09c5`; image and package identities are under `results/build/`.
- Base image: Ubuntu 24.04, `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852`.
- The patch resets an atomic server-loop flag for every in-process iteration, disables mDNS for the isolated TCP profile, disables only UBSan's function-pointer type check on the library callback tables, and preserves ASan plus the remaining UBSan checks. Patch SHA-256 and exact-application checks are recorded.
- Smoke: 10 consecutive valid HEL invocations completed in 11.320 seconds; no sanitizer diagnostics were emitted.

## Scope

Each input starts a fresh server, opens one loopback TCP connection to port 4840, sends one arbitrary byte stream, stops and joins the server thread, and destroys the server. The target does not read the server response or maintain a client session across inputs. The formal profile covers standalone OPC UA TCP message handling, not a multi-message SecureChannel/session exchange, UDP discovery, mDNS, or other open62541 fuzz targets. The upstream generated corpus contains message fragments cut from many larger client/server exchanges; those exchanges are not replayed as sessions by this target. A known local callback scenario such as the one discussed in [upstream issue #8131](https://github.com/open62541/open62541/issues/8131) is outside this target's configured path.

The complete set of 1,324 upstream generated corpus files is preserved in `seeds/upstream-corpus/`. Because this target processes one standalone message per iteration and server initialization is comparatively expensive, the formal run uses one deterministic representative for each of the 35 upstream message/service-request categories plus one valid HEL seed (36 files total). `seeds/FORMAL_CORPUS_SELECTION.tsv` records each chosen source file and hash. Fork-mode corpus minimization retained three coverage-interesting inputs by the end of the run.

## Formal run

The final run used one libFuzzer fork-mode worker, `-timeout=5`, `-rss_limit_mb=2048`, a 3 GiB container limit, one CPU, and no network access. `-max_total_time=1800` was set; the outer wrapper recorded 1,810 seconds and the libFuzzer parent recorded 1,809 seconds. Exit code was 0.

| Measure | Result |
|---|---:|
| Executions | 1,803 |
| Average throughput | about 1.00 exec/s |
| Final libFuzzer coverage features (`cov`) | 76 |
| Final feature count (`ft`) | 54 |
| Final minimized fuzz corpus | 3 inputs |
| Fork jobs | 55 |
| Timeout / OOM / crash candidates | 0 / 0 / 0 |
| Timeout artifacts from the final campaign | 0 |

`cov` and `ft` are libFuzzer feedback counters, not source line or branch coverage. The fork-mode parent does not emit a peak-RSS statistic; periodic container samples remained below 600 MiB, and the worker reported no OOM. No separate gcov/LLVM source-coverage replay was performed.

## Timeout candidate from the preliminary in-process run

An earlier non-fork run over the full upstream corpus stopped after 698 seconds with exit code 70 on one 5-second libFuzzer timeout (531 executed units, peak RSS 1,074 MiB). The 97-byte artifact is byte-identical to upstream `MSGF GetEndpointsRequest` seeds. It completed in 2.242–2.265 seconds in 11 separate fresh-process replays (11/11 exit code 0), so it is retained as an unconfirmed timeout candidate rather than a confirmed hang. Exact input, hashes, logs and per-attempt statuses are in `results/first-attempt-timeout/triage/`.

Two further runs were setup diagnostics and are not part of the formal result: a fork-mode full-corpus merge was stopped after 377 seconds with no fuzz units completed, and a preliminary representative-corpus fork run was stopped after 400 seconds when review found that the upstream `volatile` stop flag was a cross-thread data race. Those logs are retained under `results/premerge-full-corpus-interrupted/` and `results/fork-partial-volatile/`; the final image uses the atomic flag and the final 1,800-second campaign.

## Reproduction

```sh
./build.sh
./run.sh smoke
./run.sh formal
```

`results/opcua-30m/run.json` records the final requested/observed duration and exit code. `results/opcua-30m/libfuzzer.log` is the raw campaign output, and `results/opcua-30m/corpus/` contains the formal seed set plus any interesting inputs. The full upstream seed set and deterministic reduced-profile map are retained separately. The shared framework experience library is maintained outside this protocol package.
