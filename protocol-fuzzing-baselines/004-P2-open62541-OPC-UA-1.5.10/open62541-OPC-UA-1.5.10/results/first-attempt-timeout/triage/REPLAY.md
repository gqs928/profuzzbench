# First-run timeout candidate replay

- Candidate: `candidate.bin`, SHA-256 `9ad592538ab7091f30084aec55c2fcf34b6f223dfa914a4547d23feb22ebd055`
- First in-process run: libFuzzer stopped after 698 seconds with exit code 70 on its 5-second unit timeout. The run had 531 executed units and 1,074 MiB peak RSS; see the adjacent `../run.json` and `../libfuzzer.log`.
- The candidate is byte-identical to multiple upstream `MSGF` `GetEndpointsRequest` corpus files, including `seeds/upstream-corpus/accesscontrol_00003_msg_GetEndpointsRequest.bin`.
- Fresh-process replay: 11/11 runs exited 0. Each completed in 2.242–2.265 seconds, below the configured 5-second timeout. Per-run logs and exit codes are in `attempt-01.log` through `attempt-11.log` and `replay-summary.tsv`.
- Classification: the timeout did not reproduce in fresh processes, so it is retained as an unconfirmed timeout candidate, not a confirmed hang or crash. The final campaign uses one-worker libFuzzer fork mode so a slow iteration is isolated and does not terminate the 30-minute campaign.
