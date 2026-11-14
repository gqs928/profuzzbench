# tgt iSCSI 1.0.98 baseline results

The corrected formal run used four binary protocol transcripts and ran for 1,797 seconds against the pinned tgt 1.0.98 AFL build. The initial attempt was discarded because its corpus accidentally contained a JSON seed manifest; the corrected input directory contains only the four `.bin` protocol seeds, and the final AFLNet startup log confirms all four inputs.

| Measure | Result |
|---|---:|
| AFLNet executions | 1,345 |
| Queue paths | 75 |
| Variable paths | 75 |
| Stability | 90.93% |
| AFL bitmap coverage | 2.74% |
| Crashes / hangs | 0 / 0 |
| Response-state graph | 8 nodes, 8 edges |

The formal run and parsed state graph are in `results/iscsi-30m/fuzz-30m/`. `fuzzer_stats` is the source for AFLNet counts, `run-parameters.txt` records the requested and observed durations, and `SHA256SUMS` verifies the complete run directory. The protocol smoke exchange and seed-generation manifest are in `results/iscsi-30m/protocol-smoke/`; the manifest is evidence only and was not an AFL input.

The campaign covers plaintext iSCSI Login negotiation and a SCSI INQUIRY path on TCP/3260. A 90.93% AFL bitmap stability value indicates variable paths and should be preserved as an exploratory-result caveat; it does not change the response-state graph or imply a defect. No crash or hang was observed.
