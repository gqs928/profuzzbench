# IMAP benchmark full acceptance

Overall: **PASS**

| # | Criterion | Result |
|---:|---|---|
| 1 | Pinned target rebuilds from source | PASS |
| 2 | Normal protocol behavior preserved | PASS |
| 3 | Business-state seeds replayed step by step | PASS |
| 4 | AFLNet response-state graph mapped to real responses | PASS |
| 5 | Instrumented gcov replay and core-function report | PASS |
| 6 | Reset and repeated replay consistency | PASS |
| 7 | Controlled fault recorded; normal runs have no hangs | PASS |
| 8 | Independent run artifacts and coverage series retained | PASS |

- Protocol smoke: 20 sessions; all checks passed=True
- No-cache image ID: sha256:01ba131e1dcf6ea0048f6338f92d980dcad4a30cd5c53e3ffbbce0d8f81b9da0; cached refresh reused identical image=True.
- Seed replay: 27 sessions; normalized response-state sequences stable=True
- Business-state flows successful: append-fetch, login-mailbox, auth-plain, namespace-lsub, quoted-arguments.
- Response-state graph: 11 nodes and 18 edges; 11 nodes mapped to semantic IMAP response classes.
- gcov server: /home/ubuntu/experiments/cyrus-gcov; fresh gcda files: 139.
- Fixed corpus coverage: 12970/76797 lines (16.9%), 6131/52479 branches (11.7%); range across three resets: 0.0026 line and 0.0057 branch percentage points (limit 0.1), varying source rows=4.
- AFLNet variable_paths by independent run: 2, 2, 2; saved variable inputs replayed=6, normalized response states stable=True. See variable-path-audit.csv.
- Controlled-fault AFLNet unique_crashes=1; saved crash inputs=1.

The fixed input produces stable IMAP response-state sequences. The small gcov count differences are reported in coverage-variation.csv; the varying source rows are the IMAP input-EOF poll and Cyrus master child wait loop. AFLNet also flags APPEND-FETCH and AUTH PLAIN as variable bitmap paths; both were saved, replayed for three clean rounds, and had stable normalized response-state sequences.

The controlled crash target is a separate test fixture and is not linked into Cyrus. Normal Cyrus fuzz runs remain the protocol-preservation and hang checks.
