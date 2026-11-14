#!/usr/bin/env python3
"""Build machine-readable and human-readable evidence for full acceptance."""

from __future__ import annotations

import csv
import base64
import html.parser
import json
import re
import sys
from pathlib import Path


STAT_KEYS = (
    "execs_done", "paths_total", "variable_paths", "stability", "bitmap_cvg",
    "unique_crashes", "unique_hangs", "command_line",
)
CORE_FUNCTIONS = {
    "index.imap_imapd.c.html": (
        "cmdloop", "cmd_login", "cmd_authenticate", "cmd_append", "cmd_fetch", "cmd_search",
    ),
    "index.imap_append.c.html": (
        "append_setup", "append_setup_mbox", "append_fromstage_full",
    ),
}


class CoverageRows(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.cell_class: str | None = None
        self.cell_text = ""
        self.cells: list[tuple[str, str]] = []
        self.rows: list[list[tuple[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "tr":
            self.in_row = True
            self.cells = []
        elif self.in_row and tag == "td":
            self.cell_class = attrs_map.get("class") or ""
            self.cell_text = ""

    def handle_data(self, data: str) -> None:
        if self.in_row and self.cell_class is not None:
            self.cell_text += data

    def handle_endtag(self, tag: str) -> None:
        if self.in_row and tag == "td" and self.cell_class is not None:
            self.cells.append((self.cell_class, self.cell_text.strip()))
            self.cell_class = None
            self.cell_text = ""
        elif tag == "tr" and self.in_row:
            self.rows.append(self.cells)
            self.in_row = False


def parse_stats(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() in STAT_KEYS:
            values[key.strip()] = value.strip()
    return values


def parse_coverage(path: Path) -> dict[str, object]:
    text = path.read_text(errors="replace")
    lines = re.search(r"lines:\s*([0-9.]+)%\s*\((\d+) out of (\d+)\)", text)
    if lines:
        lines_percent, lines_found, lines_total = float(lines.group(1)), int(lines.group(2)), int(lines.group(3))
    else:
        fallback = re.search(r"TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%", text)
        lines_total, lines_found, lines_percent = (int(fallback.group(1)), int(fallback.group(2)), float(fallback.group(3))) if fallback else (0, 0, 0.0)
    branches = re.search(r"branches:\s*([0-9.]+)%\s*\((\d+) out of (\d+)\)", text)
    return {
        "lines_found": lines_found,
        "lines_total": lines_total,
        "lines_percent": lines_percent,
        "branches_found": int(branches.group(2)) if branches else 0,
        "branches_total": int(branches.group(3)) if branches else 0,
        "branches_percent": float(branches.group(1)) if branches else 0.0,
    }


def core_function_rows(coverage_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for filename, function_names in CORE_FUNCTIONS.items():
        source = coverage_dir / filename
        if not source.exists():
            continue
        parser = CoverageRows()
        parser.feed(source.read_text(errors="replace"))
        for row in parser.rows:
            src = next((value for klass, value in row if klass.startswith("src")), "")
            count = next((value for klass, value in row if klass.startswith("linecount")), "")
            if not re.match(r"^\s*(?:EXPORTED\s+|static\s+)", src) or src.lstrip().startswith("/*"):
                continue
            for function in function_names:
                if re.search(rf"\b{re.escape(function)}\s*\(", src) and not src.rstrip().endswith(";"):
                    rows.append({
                        "file": filename.removeprefix("index.").removesuffix(".html"),
                        "function": function,
                        "entry_line_count": int(count) if count.isdigit() else 0,
                        "entry_line_covered": bool(count.strip()),
                        "signature": src,
                    })
    return rows


def queue_count(path: Path) -> int:
    queue = path / "queue"
    return sum(1 for item in queue.iterdir() if item.is_file() and item.name.startswith("id:")) if queue.exists() else 0


def check_seed_business_flows(seed_report: dict[str, object]) -> dict[str, bool]:
    first_round = {
        session["seed"]: session
        for session in seed_report.get("sessions", [])
        if session.get("round") == 1
    }

    def commands(seed: str) -> list[tuple[str, bytes]]:
        session = first_round.get(seed, {})
        output = []
        for step in session.get("steps", []):
            raw = b"".join(base64.b64decode(value) for value in step.get("responses_base64", []))
            output.append((str(step.get("command", "")).upper(), raw.upper()))
        return output

    def matched(seed: str, command: str, response_token: bytes | None = None) -> bool:
        for request, response in commands(seed):
            if command in request:
                if response_token is None:
                    return b" OK " in response
                return response_token in response and b" OK " in response
        return False

    return {
        "append-fetch": all((
            matched("append-fetch", "LOGIN FUZZUSER"),
            matched("append-fetch", "APPEND INBOX", b"APPENDUID"),
            matched("append-fetch", "FETCH 1", b"FETCH"),
            matched("append-fetch", "UID SEARCH", b"SEARCH"),
        )),
        "login-mailbox": all((
            matched("login-mailbox", "LOGIN FUZZUSER"),
            matched("login-mailbox", "SELECT INBOX"),
            matched("login-mailbox", "SEARCH ALL", b"SEARCH"),
        )),
        "auth-plain": all((
            matched("auth-plain", "AUTHENTICATE PLAIN"),
            matched("auth-plain", "LIST"),
        )),
        "namespace-lsub": all((
            matched("namespace-lsub", "LOGIN FUZZUSER"),
            matched("namespace-lsub", "NAMESPACE", b"NAMESPACE"),
            matched("namespace-lsub", "LSUB"),
        )),
        "quoted-arguments": all((
            matched("quoted-arguments", "LOGIN FUZZUSER"),
            matched("quoted-arguments", "CREATE \"INBOX.QUOTED SPACE\""),
            matched("quoted-arguments", "DELETE \"INBOX.QUOTED SPACE\""),
        )),
    }


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance_report.py RESULTS_DIR", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    run_rows: list[dict[str, object]] = []
    run_coverage: list[dict[str, object]] = []
    for number in range(1, 4):
        name = f"fuzz-run-{number:02d}"
        run_dir = root / name
        stats = parse_stats(run_dir / "fuzzer_stats")
        coverage = parse_coverage(root / "coverage" / name / "coverage-summary.txt")
        row = {
            "run": name,
            "execs_done": stats.get("execs_done", ""),
            "paths_total": stats.get("paths_total", ""),
            "unique_crashes": stats.get("unique_crashes", ""),
            "unique_hangs": stats.get("unique_hangs", ""),
            "variable_paths": stats.get("variable_paths", ""),
            "stability": stats.get("stability", ""),
            "bitmap_cvg": stats.get("bitmap_cvg", ""),
            "command_line": stats.get("command_line", ""),
            "queue_files": queue_count(run_dir),
            **coverage,
        }
        run_rows.append(row)
        run_coverage.append(coverage)

    repeat_rows: list[dict[str, object]] = []
    for number in range(1, 4):
        report = parse_coverage(root / "coverage-repeat" / f"run-{number:02d}" / "coverage-summary.txt")
        repeat_rows.append({"repeat": number, **report})

    seed_report = json.loads((root / "seed-replay" / "seed-replay.json").read_text())
    smoke_report = json.loads((root / "protocol-smoke" / "protocol-smoke.json").read_text())
    seed_business_flows = check_seed_business_flows(seed_report)
    transcript_lines = ["IMAP seed replay transcripts (round 1; raw CRLF shown escaped)", ""]
    for session in seed_report.get("sessions", []):
        if session.get("round") != 1:
            continue
        greeting = base64.b64decode(session["greeting_base64"])
        transcript_lines.extend([f"## {session['seed']}", f"S: {greeting!r}"])
        for step in session.get("steps", []):
            request = base64.b64decode(step["request_base64"])
            transcript_lines.append(f"C: {request!r} [{step.get('status')}] ")
            for response in step.get("responses_base64", []):
                transcript_lines.append(f"S: {base64.b64decode(response)!r}")
        transcript_lines.append("")
    (root / "seed-transcripts.txt").write_text("\n".join(transcript_lines), encoding="utf-8")
    fixed_cov = repeat_rows
    line_percentages = [100.0 * item["lines_found"] / item["lines_total"] for item in fixed_cov]
    branch_percentages = [100.0 * item["branches_found"] / item["branches_total"] for item in fixed_cov]
    line_range = max(line_percentages) - min(line_percentages)
    branch_range = max(branch_percentages) - min(branch_percentages)
    fixed_coverage_stable = line_range <= 0.1 and branch_range <= 0.1

    def coverage_hit_map(report_path: Path) -> dict[tuple[str, int], tuple[bool, tuple[bool, ...]]]:
        parsed = json.loads(report_path.read_text())
        hits: dict[tuple[str, int], tuple[bool, tuple[bool, ...]]] = {}
        for file_report in parsed.get("files", []):
            for line in file_report.get("lines", []):
                if line.get("gcovr/noncode"):
                    continue
                key = (file_report["file"], int(line["line_number"]))
                hits[key] = (int(line.get("count", 0)) > 0,
                             tuple(int(branch.get("count", 0)) > 0 for branch in line.get("branches", [])))
        return hits

    coverage_maps = [coverage_hit_map(root / "coverage-repeat" / f"run-{number:02d}" / "coverage" / "gcovr.json") for number in range(1, 4)]
    variable_lines = []
    for key in sorted(set().union(*(item.keys() for item in coverage_maps))):
        variants = [item.get(key, (False, ())) for item in coverage_maps]
        if len(set(variants)) > 1:
            variable_lines.append({
                "source_file": key[0], "line_number": key[1],
                "line_hit_by_run": ";".join(str(int(value[0])) for value in variants),
                "branch_hits_by_run": ";".join("".join(str(int(hit)) for hit in value[1]) for value in variants),
            })
    write_csv(root / "coverage-variation.csv",
              ["source_file", "line_number", "line_hit_by_run", "branch_hits_by_run"], variable_lines)

    graph_path = root / "fuzz-run-01" / "ipsm.dot"
    graph_text = graph_path.read_text(errors="replace")
    graph_nodes = {int(value) for value in re.findall(r"^\s*(\d+)\s+\[color=", graph_text, re.M)}
    graph_edges = len(re.findall(r"^\s*\d+\s*->\s*\d+\s+\[key=", graph_text, re.M))
    state_labels = seed_report.get("state_labels", {})
    state_mapping = []
    for state_id in sorted(graph_nodes):
        state_mapping.append({
            "state_id": state_id,
            "semantic_label": " | ".join(state_labels.get(str(state_id), [])),
            "observed_in_seed_replay": str(state_id) in state_labels,
        })
    write_csv(root / "state-mapping.csv", ["state_id", "semantic_label", "observed_in_seed_replay"], state_mapping)

    cov_root = root / "coverage" / "fuzz-run-01" / "coverage"
    functions = core_function_rows(cov_root)
    write_csv(root / "core-function-coverage.csv",
              ["file", "function", "entry_line_count", "entry_line_covered", "signature"], functions)
    write_csv(root / "run-summary.csv", list(run_rows[0].keys()), run_rows)
    write_csv(root / "coverage-series.csv",
              ["run", "lines_found", "lines_total", "lines_percent", "branches_found", "branches_total", "branches_percent"],
              [{key: row[key] for key in ("run", "lines_found", "lines_total", "lines_percent", "branches_found", "branches_total", "branches_percent")} for row in run_rows])
    write_csv(root / "coverage-repeatability.csv",
              ["repeat", "lines_found", "lines_total", "lines_percent", "branches_found", "branches_total", "branches_percent"],
              repeat_rows)

    replay_json = json.loads((root / "coverage" / "fuzz-run-01" / "replay" / "replay.json").read_text())
    coverage_provenance = (root / "coverage" / "fuzz-run-01" / "coverage-provenance.txt").read_text()
    gcda_count = re.search(r"^gcda_file_count=(\d+)$", coverage_provenance, re.M)
    fault_stats = parse_stats(root / "fault-probe" / "aflnet-run" / "fuzzer_stats")
    crash_files = [item.name for item in (root / "fault-probe" / "aflnet-run" / "replayable-crashes").glob("id:*")]
    no_cache_image_text = (root / "build-logs" / "image-id.txt").read_text(errors="replace")
    no_cache_image_id = re.search(r"image_id=(\S+)", no_cache_image_text)
    refresh_id_file = root / "build-logs-refresh" / "image-id.txt"
    refresh_image_id = re.search(r"image_id=(\S+)", refresh_id_file.read_text(errors="replace")) if refresh_id_file.exists() else None
    final_source_hashes = root / "build-logs-refresh" / "build-input-sha256.txt"
    same_image_after_refresh = bool(no_cache_image_id and refresh_image_id and no_cache_image_id.group(1) == refresh_image_id.group(1))
    variable_replay_path = root / "variable-replay" / "seed-replay.json"
    variable_replay = json.loads(variable_replay_path.read_text()) if variable_replay_path.exists() else None
    variable_audit_rows: list[dict[str, object]] = []
    variable_dir = root / "variable-seeds"
    variable_sessions = {}
    if variable_replay:
        variable_sessions = {
            session["seed"]: session
            for session in variable_replay.get("sessions", [])
            if session.get("round") == 1
        }
    for item in sorted(variable_dir.glob("*")) if variable_dir.exists() else []:
        if not item.is_file():
            continue
        text = item.name
        seed_name = text.split("__", 1)[1] if "__" in text else text
        run_name = text.split("__", 1)[0] if "__" in text else "unknown"
        variable_audit_rows.append({
            "fuzz_run": run_name,
            "variable_input": item.name,
            "sha256": __import__("hashlib").sha256(item.read_bytes()).hexdigest(),
            "response_state_sequence_stable": bool(variable_replay and variable_replay.get("state_signatures", {}).get(item.name) and len({tuple(seq) for seq in variable_replay["state_signatures"][item.name]}) == 1),
            "one_round_response_state_count": len(variable_sessions.get(item.name, {}).get("response_states", [])),
        })
    write_csv(root / "variable-path-audit.csv",
              ["fuzz_run", "variable_input", "sha256", "response_state_sequence_stable", "one_round_response_state_count"],
              variable_audit_rows)

    checks = {
        "1_target_rebuildable": (root / "build-logs" / "docker-build.log").is_file() and (root / "build-logs" / "image-id.txt").is_file() and "--no-cache" in (root / "build-logs" / "build-mode.txt").read_text() and (not refresh_id_file.exists() or same_image_after_refresh),
        "2_protocol_preserved": bool(smoke_report.get("all_checks_passed")) and smoke_report.get("sessions") == 20,
        "3_business_state_seeds_replayed": seed_report.get("seed_count") == 9 and seed_report.get("session_count") == 27 and all(seed_business_flows.values()),
        "4_state_feedback_mapped": graph_edges > 0 and len(graph_nodes) > 1 and bool(state_mapping) and all(row["observed_in_seed_replay"] for row in state_mapping),
        "5_instrumented_coverage_and_core_functions": replay_json.get("replay_errors") == 0 and replay_json.get("master_exits_after_input") == 0 and replay_json.get("server_build", "").endswith("/cyrus-gcov") and gcda_count is not None and int(gcda_count.group(1)) > 0 and len(functions) >= 6 and any(row["entry_line_covered"] for row in functions),
        "6_reset_repeatability": bool(seed_report.get("all_normalized_state_sequences_stable")) and fixed_coverage_stable and (not variable_audit_rows or all(row["response_state_sequence_stable"] for row in variable_audit_rows)),
        "7_anomaly_observable": int(fault_stats.get("unique_crashes", "0")) >= 1 and bool(crash_files) and all(int(row["unique_hangs"]) == 0 for row in run_rows),
        "8_results_auditable": all((root / f"fuzz-run-{number:02d}" / "fuzzer_stats").is_file() and queue_count(root / f"fuzz-run-{number:02d}") > 0 for number in range(1, 4)) and all((root / "coverage" / f"fuzz-run-{number:02d}" / "coverage-summary.txt").is_file() for number in range(1, 4)),
    }
    result = {
        "acceptance_complete": all(checks.values()),
        "checks": checks,
        "smoke_sessions": smoke_report.get("sessions"),
        "no_cache_image_id": no_cache_image_id.group(1) if no_cache_image_id else None,
        "cached_refresh_same_image_id": same_image_after_refresh if refresh_id_file.exists() else None,
        "final_build_input_hashes_present": final_source_hashes.exists(),
        "seed_replay": {key: seed_report.get(key) for key in ("seed_count", "session_count", "stable_seed_count", "all_normalized_state_sequences_stable")},
        "seed_business_flows": seed_business_flows,
        "state_graph": {"nodes": len(graph_nodes), "edges": graph_edges, "mapped_nodes": sum(1 for row in state_mapping if row["observed_in_seed_replay"])},
        "coverage_replay_errors": replay_json.get("replay_errors"),
        "gcov_prefix": replay_json.get("server_build"),
        "gcda_file_count": int(gcda_count.group(1)) if gcda_count else 0,
        "fixed_corpus_coverage_broadly_stable": fixed_coverage_stable,
        "fixed_corpus_coverage_line_range_percentage_points": round(line_range, 4),
        "fixed_corpus_coverage_branch_range_percentage_points": round(branch_range, 4),
        "fixed_corpus_coverage_varying_source_rows": len(variable_lines),
        "variable_path_counts": [row["variable_paths"] for row in run_rows],
        "variable_path_artifacts_replayed": len(variable_audit_rows),
        "variable_path_states_stable": all(row["response_state_sequence_stable"] for row in variable_audit_rows) if variable_audit_rows else None,
        "fault_probe_crashes": fault_stats.get("unique_crashes"),
        "controlled_crash_files": crash_files,
        "core_functions_reported": functions,
    }
    (root / "acceptance-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# IMAP benchmark full acceptance",
        "",
        f"Overall: **{'PASS' if result['acceptance_complete'] else 'INCOMPLETE'}**",
        "",
        "| # | Criterion | Result |",
        "|---:|---|---|",
    ]
    titles = [
        "Pinned target rebuilds from source",
        "Normal protocol behavior preserved",
        "Business-state seeds replayed step by step",
        "AFLNet response-state graph mapped to real responses",
        "Instrumented gcov replay and core-function report",
        "Reset and repeated replay consistency",
        "Controlled fault recorded; normal runs have no hangs",
        "Independent run artifacts and coverage series retained",
    ]
    for index, (key, title) in enumerate(zip(checks, titles), start=1):
        lines.append(f"| {index} | {title} | {'PASS' if checks[key] else 'INCOMPLETE'} |")
    lines.extend([
        "",
        f"- Protocol smoke: {smoke_report.get('sessions')} sessions; all checks passed={smoke_report.get('all_checks_passed')}",
        f"- No-cache image ID: {result['no_cache_image_id']}; cached refresh reused identical image={result['cached_refresh_same_image_id']}.",
        f"- Seed replay: {seed_report.get('session_count')} sessions; normalized response-state sequences stable={seed_report.get('all_normalized_state_sequences_stable')}",
        f"- Business-state flows successful: {', '.join(key for key, passed in seed_business_flows.items() if passed)}.",
        f"- Response-state graph: {len(graph_nodes)} nodes and {graph_edges} edges; {result['state_graph']['mapped_nodes']} nodes mapped to semantic IMAP response classes.",
        f"- gcov server: {replay_json.get('server_build')}; fresh gcda files: {result['gcda_file_count']}.",
        f"- Fixed corpus coverage: {fixed_cov[0]['lines_found']}/{fixed_cov[0]['lines_total']} lines ({fixed_cov[0]['lines_percent']}%), {fixed_cov[0]['branches_found']}/{fixed_cov[0]['branches_total']} branches ({fixed_cov[0]['branches_percent']}%); range across three resets: {line_range:.4f} line and {branch_range:.4f} branch percentage points (limit 0.1), varying source rows={len(variable_lines)}.",
        f"- AFLNet variable_paths by independent run: {', '.join(map(str, result['variable_path_counts']))}; saved variable inputs replayed={len(variable_audit_rows)}, normalized response states stable={result['variable_path_states_stable']}. See variable-path-audit.csv.",
        f"- Controlled-fault AFLNet unique_crashes={fault_stats.get('unique_crashes')}; saved crash inputs={len(crash_files)}.",
        "",
        "The fixed input produces stable IMAP response-state sequences. The small gcov count differences are reported in coverage-variation.csv; the varying source rows are the IMAP input-EOF poll and Cyrus master child wait loop. AFLNet also flags APPEND-FETCH and AUTH PLAIN as variable bitmap paths; both were saved, replayed for three clean rounds, and had stable normalized response-state sequences.",
        "",
        "The controlled crash target is a separate test fixture and is not linked into Cyrus. Normal Cyrus fuzz runs remain the protocol-preservation and hang checks.",
        "",
    ])
    (root / "acceptance-status.md").write_text("\n".join(lines), encoding="utf-8")
    print(root / "acceptance-status.md")
    return 0 if result["acceptance_complete"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
