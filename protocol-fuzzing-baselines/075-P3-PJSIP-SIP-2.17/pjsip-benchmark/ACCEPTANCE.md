# Acceptance record

Status: complete.

- Implementation: PJSIP/pjproject 2.17, tag commit `5a457451fa2712ba18e12b01738e8ff3af2b26fd`.
- Target: upstream `tests/fuzz/fuzz-sip.c` using `LLVMFuzzerTestOneInput`.
- Scope: SIP message parsing and the target's selected header/body, transaction, authentication, and dialog paths; in-process only, no listening SIP service.
- Fuzz engine: LLVM libFuzzer with AddressSanitizer, one worker; source seed corpus is the upstream `fuzz-sip_seed_corpus.zip`.
- Preflight: 60 seconds; 661,112 executions, 6,816 new units, 1,436 covered edges, 5,002 features, 456 MB peak RSS, exit code 0, no sanitizer/crash markers. The first attempt completed its fuzz run but the reporting wrapper failed because Python 3 was missing; Python 3 was added and the complete preflight was repeated successfully.
- Formal: `pjsip-fuzz-30m-20261113`, requested 1,800 seconds; libFuzzer completed 1,865 seconds (1,872-second outer wall-clock span), 7,840,988 executions, 24,710 new units, 1,519 covered edges, 6,843 features, 532 MB peak RSS, exit code 0, no sanitizer/crash markers.
- Final-image smoke: 10 seconds; 115,149 executions, 2,436 new units, 1,385 covered edges, 4,234 features, 418 MB peak RSS, exit code 0, no sanitizer/crash markers.

Report libFuzzer native time, execution, edge/feature, and corpus-growth metrics. AFLNet stability/bitmap, service readiness/listener, and network replay evidence do not apply. Final acceptance requires a successful 30-minute run without sanitizer/crash markers, saved logs/metrics/corpus, standalone ZIP CRC/SHA-256 validation, and exact image cleanup after confirming no container references. Framework guidance belongs only in the central aggregated experience library.
