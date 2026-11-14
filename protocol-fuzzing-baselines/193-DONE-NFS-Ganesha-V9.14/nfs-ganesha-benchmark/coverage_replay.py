#!/usr/bin/env python3
"""重置 gcda 后，逐个独立进程回放种子、队列和崩溃样本。"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from seed_replay import replay_one


def replayable_packets(path: pathlib.Path) -> bytes:
    """将 AFLNet 的本机端序长度封装还原成 RPC 线缆串。"""
    raw = path.read_bytes()
    offset = 0
    packets = []
    while offset < len(raw):
        if len(raw) - offset < 4:
            raise ValueError(f"AFLNet 回放文件长度前缀不完整：{path}")
        size = struct.unpack_from("=I", raw, offset)[0]
        offset += 4
        if size > len(raw) - offset:
            raise ValueError(f"AFLNet 回放文件包长度越界：{path}")
        packets.append(raw[offset : offset + size])
        offset += size
    return b"".join(packets)


def parse_gcovr(xml_path: pathlib.Path, csv_path: pathlib.Path):
    import xml.etree.ElementTree as ET

    def coverage_fraction(value: str) -> tuple[int, int]:
        match = re.search(r"\((\d+)\s*/\s*(\d+)\)", value)
        if match is None:
            match = re.search(r"(\d+)\s*/\s*(\d+)", value)
        return (int(match.group(1)), int(match.group(2))) if match else (0, 0)

    root = ET.parse(xml_path).getroot()
    rows = []
    for source in root.findall(".//class"):
        filename = source.attrib.get("filename", "")
        lines = source.findall("./lines/line")
        line_total = sum(
            1 for line in lines if line.attrib.get("type") in (None, "line")
        )
        line_covered = sum(
            1
            for line in lines
            if line.attrib.get("type") in (None, "line")
            and int(line.attrib.get("hits", "0")) > 0
        )
        branch_lines = [line for line in lines if line.attrib.get("branch", "false") == "true"]
        branch_fractions = [
            coverage_fraction(line.attrib.get("condition-coverage", ""))
            for line in branch_lines
        ]
        branch_covered = sum(covered for covered, _ in branch_fractions)
        branch_total = sum(total for _, total in branch_fractions)
        rows.append(
            {
                "source": filename,
                "lines_valid": line_total,
                "lines_covered": line_covered,
                "line_rate": f"{line_covered / line_total:.6f}" if line_total else "0",
                "branches_valid": branch_total,
                "branches_covered": branch_covered,
                "branch_rate": f"{branch_covered / branch_total:.6f}" if branch_total else "0",
            }
        )
    if not rows:
        raise RuntimeError("gcovr 没有输出 NFSv3、MOUNTv3 或 FSAL_MEM 范围内的源码")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def collect_function_coverage(
    build_dir: pathlib.Path, source_dir: pathlib.Path, destination: pathlib.Path
) -> list[dict[str, object]]:
    """从 gcov 的逐函数明细生成函数调用数，而非依赖旧版 gcovr 空的 XML methods。"""
    relevant = ("/Protocols/NFS/", "/FSAL/FSAL_MEM/")
    counters = [
        path
        for path in sorted(build_dir.rglob("*.gcda"))
        if any(token in path.as_posix() for token in relevant)
    ]
    functions: dict[tuple[str, str], dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="gcov-functions-", dir=destination) as temporary:
        scratch = pathlib.Path(temporary)
        for counter in counters:
            result = subprocess.run(
                ["gcov", "-b", "-c", "-f", str(counter)],
                cwd=scratch,
                text=True,
                capture_output=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"gcov 函数明细读取失败：{counter}\n{result.stderr}")
            for report in scratch.glob("*.gcov"):
                content = report.read_text(errors="replace")
                source_match = re.search(r"Source:([^\n]+)", content)
                if source_match is None:
                    report.unlink(missing_ok=True)
                    continue
                source_path = pathlib.Path(source_match.group(1).strip())
                try:
                    relative = source_path.resolve().relative_to(source_dir.resolve()).as_posix()
                except ValueError:
                    report.unlink(missing_ok=True)
                    continue
                nfs3_source = relative.startswith("Protocols/NFS/") and (
                    pathlib.Path(relative).name.startswith(("nfs3_", "mnt_"))
                    or pathlib.Path(relative).name == "nfs_proto_tools.c"
                )
                if not relative.startswith("FSAL/FSAL_MEM/") and not nfs3_source:
                    report.unlink(missing_ok=True)
                    continue
                for match in re.finditer(
                    r"^function (.+) called (\d+) returned [^ ]+ blocks executed [^\n]+$",
                    content,
                    flags=re.MULTILINE,
                ):
                    name, calls = match.group(1), int(match.group(2))
                    key = (relative, name)
                    previous = int(functions.get(key, {}).get("calls", 0))
                    functions[key] = {
                        "source": relative,
                        "function": name,
                        "calls": max(previous, calls),
                        "covered": int(max(previous, calls) > 0),
                    }
                report.unlink(missing_ok=True)
    rows = [functions[key] for key in sorted(functions)]
    if not rows:
        raise RuntimeError("gcov 没有输出 NFSv3、MOUNTv3 或 FSAL_MEM 范围内的函数明细")
    return rows


def main() -> int:
    seeds = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/seeds")
    afl_out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    output = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else "/results/coverage")
    repetitions = int(sys.argv[4] if len(sys.argv) > 4 else "3")
    build_dir = pathlib.Path("/home/ubuntu/experiments/build-gcov")
    source_dir = pathlib.Path("/home/ubuntu/experiments/ganesha-gcov-src/src")
    output.mkdir(parents=True, exist_ok=True)

    corpus = [(path.name, path.read_bytes()) for path in sorted(seeds.glob("*.bin"))]
    if afl_out and afl_out.exists():
        queue = afl_out / "replayable-queue"
        crashes = afl_out / "replayable-crashes"
        if queue.exists():
            for path in sorted(queue.iterdir())[:128]:
                if path.is_file():
                    corpus.append((f"queue-{path.name}.bin", replayable_packets(path)))
        if crashes.exists():
            for path in sorted(crashes.iterdir()):
                if path.is_file() and path.name != "README.txt":
                    corpus.append((f"crash-{path.name}.bin", replayable_packets(path)))
    if not corpus:
        raise SystemExit("覆盖率回放语料为空")

    all_runs = []
    for repetition in range(1, repetitions + 1):
        run_dir = output / f"run-{repetition:02d}"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        input_dir = run_dir / "inputs"
        input_dir.mkdir(parents=True)
        for name, contents in corpus:
            (input_dir / name).write_bytes(contents)

        for counter in build_dir.rglob("*.gcda"):
            counter.unlink()
        runs = []
        for index, seed in enumerate(sorted(input_dir.glob("*.bin")), start=1):
            runs.append(replay_one(seed, "gcov", f"coverage-{repetition:02d}-{index:04d}", run_dir))

        xml_path = run_dir / "gcovr.xml"
        command = [
            "gcovr",
            "--root",
            str(source_dir),
            "--object-directory",
            str(build_dir),
            "--filter",
            ".*/src/Protocols/NFS/(nfs3_[^/]*|mnt_[^/]*|nfs_proto_tools\\.c)$",
            "--filter",
            ".*/src/FSAL/FSAL_MEM/.*",
            "--xml-pretty",
            "--output",
            str(xml_path),
        ]
        (run_dir / "gcovr-command.json").write_text(
            json.dumps(command, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        subprocess.run(command, check=True)
        rows = parse_gcovr(xml_path, run_dir / "coverage.csv")
        function_rows = collect_function_coverage(
            build_dir, source_dir, run_dir
        )
        function_fields = ["source", "function", "calls", "covered"]
        with (run_dir / "protocol-core-functions.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=function_fields)
            writer.writeheader()
            writer.writerows(function_rows)
        summary = {
            "repetition": repetition,
            "samples": len(runs),
            "seed_samples": len(list(seeds.glob("*.bin"))),
            "aflnet_samples": max(0, len(runs) - len(list(seeds.glob("*.bin")))),
            "independent_process_per_sample": True,
            "gcda_reset_before_run": True,
            "coverage_csv": str(run_dir / "coverage.csv"),
            "function_csv": str(run_dir / "protocol-core-functions.csv"),
            "gcovr_xml": str(xml_path),
            "files": rows,
            "functions_valid": len(function_rows),
            "functions_covered": sum(int(row["covered"]) for row in function_rows),
            "function_rate": f"{sum(int(row['covered']) for row in function_rows) / len(function_rows):.6f}",
            "replays": runs,
        }
        (run_dir / "coverage-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        all_runs.append(
            {
                "repetition": repetition,
                "samples": len(runs),
                "coverage_csv": str(run_dir / "coverage.csv"),
                "function_csv": str(run_dir / "protocol-core-functions.csv"),
            }
        )

    report = {
        "variant": "gcov-instrumented NFS-Ganesha V9.14",
        "scope": [
            "NFSv3 handlers (nfs3_*.c)",
            "MOUNTv3 handlers (mnt_*.c)",
            "NFS protocol helpers (nfs_proto_tools.c)",
            "FSAL_MEM",
        ],
        "independent_coverage_repetitions": repetitions,
        "max_aflnet_queue_samples": 128,
        "reset_method": "delete .gcda files before every aggregate replay; start and stop a fresh Ganesha process for every input",
        "runs": all_runs,
    }
    (output / "coverage-replay.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"通过：{repetitions} 次独立覆盖率回放，语料 {len(corpus)} 个样本")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
