# Impacket SMB2/3 baseline

This profile benchmarks the latest published stable Impacket release, 0.13.1, using the upstream SMB2/SMB3 packet and command structure parsers. The in-process Atheris target covers bare and RFC 1002-framed SMB2/3 PDUs, compound headers, command structures, selected negotiate/create contexts, and SMB3 transform headers. It does not run a listening server or claim SMB1, authentication, or end-to-end network coverage.

The implementation archive and Atheris/six wheels are checked against their locked SHA-256 values during the image build. The container has no runtime network access and runs one fuzz worker with a two-CPU quota and 4 GiB memory limit. Atheris/libFuzzer coverage and execution counters are the reportable metrics; AFLNet stability/bitmap and service-readiness/replay fields do not apply to this parser target.

The 60-second preflight and formal campaign passed. The formal engine ran for 1,801 seconds and completed 555,056 executions, adding 304 inputs, with 184 Python coverage edges, 1,071 features, 50 MB peak RSS, exit code 0, and no failure markers. See `ACCEPTANCE.md` and `results/` for the full evidence. Optional libFuzzer sanitizer-callback symbol warnings remain in the raw log; this profile does not claim ASan instrumentation.

Run `./build.sh`, `./preflight-benchmark.sh 60`, then `./run-benchmark.sh 1800 impacket-smb-30m-20261113`. Each run writes its log, metrics, timing, corpus, and crash artifacts below `results/`. After validating the standalone delivery package, remove only this profile's exact image ID as recorded in `build-logs/image-id-size.txt`.

Framework-specific automation guidance is aggregated in the central `deliverables/12-protocol-baselines-2026-11-03-framework/基准化经验库.md`; this project package intentionally contains no standalone experience entry.
