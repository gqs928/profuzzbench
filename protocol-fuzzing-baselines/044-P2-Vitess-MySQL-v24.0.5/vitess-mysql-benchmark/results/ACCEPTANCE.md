# Vitess MySQL Classic v24.0.5 benchmark acceptance

- Target: official Vitess v24.0.5 vttestserver image, pinned by digest in source-lock.json; runtime reported v24.0.5.
- Protocol path: AFLNet MySQL Classic COM_QUERY through a loopback authentication proxy to vtgate.
- Formal campaign: 1,801 active seconds; AFLNet exit 0; 7,415 executions; 362 paths (354 newly found); stability 100%; 0 variable paths, 0 crashes, 0 hangs; cycles_done=0.
- Feedback: MySQL response-state feedback only. AFL bitmap 0% is not Vitess source coverage.
- Queue replay: 362/362 connected; 0 connect/send errors; all 79 reset-on-read cases had already returned response bytes. The remaining samples ended by peer close or idle timeout. Full packet and error-marker counts are in queue-replay.json.
- Fresh post-run SELECT 1 smoke passed with five MySQL response packets. Container restart count was 0.
- No saved hang candidates required replay triage. The exact Vitess container and image were removed after validation; cleanup evidence is in cleanup.txt.
- Generated replayable-queue and replayable-new-ipsm-paths copies are omitted from the ZIP to avoid duplicating the retained 362-file queue corpus.

See run-status.txt, fuzzer_stats, run-parameters.txt, queue-replay.json, post-run-smoke.json, vttestserver-container.log, and container-final-state.txt for raw evidence. Reusable lessons are maintained centrally in the framework experience library, outside this profile package.
