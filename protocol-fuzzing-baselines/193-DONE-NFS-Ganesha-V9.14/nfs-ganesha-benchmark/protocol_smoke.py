#!/usr/bin/env python3
"""用普通 NFSv3 客户端验证 MOUNT、文件操作和插桩版服务的一致性。"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time

from nfs_rpc import (
    MOUNT_PORT,
    NFS_PORT,
    RpcClient,
    access_args,
    create_args,
    getattr_args,
    lookup_args,
    lookup_filehandle,
    mount_filehandle,
    nfs_status,
    parse_optional_handle_after_status,
    parse_read_data,
    read_args,
    readdir_args,
    remove_args,
    u32,
    write_args,
)


VARIANT_PREFIXES = {
    "reference": "GANESHA_REFERENCE",
    "afl": "GANESHA_AFL",
}
TEST_DATA = b"nfs-ganesha-fuzzbench-payload-v1"
TEST_NAME = b"acceptance-file"


def server_command(variant: str, diagnostic_log: pathlib.Path) -> tuple[list[str], pathlib.Path, dict[str, str]]:
    prefix = VARIANT_PREFIXES[variant]
    binary = pathlib.Path(os.environ[f"{prefix}_BIN"])
    config = pathlib.Path(os.environ[f"{prefix}_CONFIG"])
    command = [
        str(binary),
        "-F",
        "-f",
        str(config),
        "-p",
        "/tmp/ganesha.pid",
        "-L",
        str(diagnostic_log),
        "-N",
        "NIV_CRIT",
    ]
    install_prefix = binary.parent.parent
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(
        str(path)
        for path in (
            install_prefix / "lib",
            install_prefix / "lib64",
            install_prefix / "lib/ganesha",
            install_prefix / "lib/x86_64-linux-gnu",
            install_prefix / "lib/x86_64-linux-gnu/ganesha",
        )
    )
    return command, config, env


def wait_for_server(variant: str, session: int, output: pathlib.Path):
    log_path = output / f"server-{variant}-{session:02d}.log"
    diagnostic_log = output / f"ganesha-{variant}-{session:02d}.log"
    diagnostic_log.unlink(missing_ok=True)
    command, _, env = server_command(variant, diagnostic_log)
    log_file = log_path.open("wb")
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    deadline = time.monotonic() + 20
    ports = (NFS_PORT, MOUNT_PORT)
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log_file.close()
            detail = log_path.read_text(errors="replace")[-8000:]
            raise RuntimeError(
                f"{variant} Ganesha 启动失败，退出码={process.returncode}；"
                f"诊断日志见 {diagnostic_log}\n{detail}"
            )
        ready = True
        for port in ports:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    pass
            except OSError:
                ready = False
                break
        if ready:
            return process, log_file, log_path, diagnostic_log, command
        time.sleep(0.1)
    stop_server(process, log_file)
    detail = log_path.read_text(errors="replace")[-8000:]
    raise RuntimeError(
        f"{variant} 未监听 TCP/{NFS_PORT} 与 TCP/{MOUNT_PORT}；"
        f"诊断日志见 {diagnostic_log}\n{detail}"
    )


def stop_server(process: subprocess.Popen, log_file) -> None:
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    log_file.close()


def one_session(variant: str, session: int, output: pathlib.Path) -> dict:
    process, log_file, log_path, diagnostic_log, command = wait_for_server(variant, session, output)
    try:
        with RpcClient(MOUNT_PORT) as mount_client:
            mount_reply = mount_client.call(
                100005, 3, 1, __import__("nfs_rpc").xdr_string(__import__("nfs_rpc").NFS_PSEUDO)
            )
            root = mount_filehandle(mount_reply)
            mount_wire = mount_client.responses[:]

        with RpcClient(NFS_PORT) as client:
            steps = []

            def call(name: str, procedure: int, arguments: bytes, expected: int) -> bytes:
                reply = client.call(100003, 3, procedure, arguments)
                actual = nfs_status(reply)
                if actual != expected:
                    raise RuntimeError(
                        f"{name} 的 NFSv3 status 不符：期望 {expected}，收到 {actual}"
                    )
                steps.append(
                    {
                        "operation": name,
                        "procedure": procedure,
                        "expected_status": expected,
                        "actual_status": actual,
                        "reply_sha256": hashlib.sha256(client.responses[-1]).hexdigest(),
                        "reply_bytes": len(client.responses[-1]),
                    }
                )
                return reply

            call("GETATTR 根目录", 1, getattr_args(root), 0)
            call("ACCESS 根目录", 4, access_args(root), 0)
            create_reply = call(
                "CREATE 文件", 8, create_args(root, TEST_NAME, guarded=True), 0
            )
            created = parse_optional_handle_after_status(create_reply)
            write_reply = client.call(100003, 3, 7, write_args(created, TEST_DATA))
            write_status = nfs_status(write_reply)
            if write_status != 0:
                raise RuntimeError(f"WRITE 返回 NFSv3 status={write_status}")
            steps.append(
                {
                    "operation": "WRITE 文件",
                    "procedure": 7,
                    "expected_status": 0,
                    "actual_status": write_status,
                    "reply_sha256": hashlib.sha256(client.responses[-1]).hexdigest(),
                    "reply_bytes": len(client.responses[-1]),
                }
            )
            lookup_reply = call(
                "LOOKUP 已创建文件", 3, lookup_args(root, TEST_NAME), 0
            )
            looked_up = lookup_filehandle(lookup_reply)
            if looked_up != created:
                raise RuntimeError("LOOKUP 与 CREATE 返回的文件句柄不一致")
            read_reply = client.call(100003, 3, 6, read_args(looked_up, count=4096))
            data = parse_read_data(read_reply)
            if data != TEST_DATA:
                raise RuntimeError(f"READ 内容不一致：{data!r}")
            steps.append(
                {
                    "operation": "READ 文件",
                    "procedure": 6,
                    "expected_status": 0,
                    "actual_status": nfs_status(read_reply),
                    "read_bytes": len(data),
                    "read_sha256": hashlib.sha256(data).hexdigest(),
                    "reply_sha256": hashlib.sha256(client.responses[-1]).hexdigest(),
                    "reply_bytes": len(client.responses[-1]),
                }
            )
            call("READDIR 根目录", 16, readdir_args(root), 0)
            call("REMOVE 文件", 12, remove_args(root, TEST_NAME), 0)
            call("LOOKUP 已删除文件", 3, lookup_args(root, TEST_NAME), 2)

            semantic = [
                {
                    "operation": step["operation"],
                    "procedure": step["procedure"],
                    "status": step["actual_status"],
                    "read_sha256": step.get("read_sha256"),
                }
                for step in steps
            ]
            result = {
                "variant": variant,
                "session": session,
                "command": command,
                "root_filehandle_sha256": hashlib.sha256(root).hexdigest(),
                "mount_reply_sha256": hashlib.sha256(b"".join(mount_wire)).hexdigest(),
                "steps": steps,
                "semantic_transcript_sha256": hashlib.sha256(
                    json.dumps(semantic, ensure_ascii=False, sort_keys=True).encode()
                ).hexdigest(),
                "server_log": str(log_path),
                "ganesha_diagnostic_log": str(diagnostic_log),
            }
            return result
    finally:
        stop_server(process, log_file)


def main() -> int:
    output = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/results/protocol-smoke")
    repetitions = int(sys.argv[2] if len(sys.argv) > 2 else "10")
    if repetitions < 10:
        raise SystemExit("验收要求参考版和插桩版各至少重复 10 次")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for variant in ("reference", "afl"):
        for session in range(1, repetitions + 1):
            results.append(one_session(variant, session, output))

    expected = [0, 0, 0, 0, 0, 0, 0, 0, 2]
    for result in results:
        actual = [item["actual_status"] for item in result["steps"]]
        if actual != expected:
            raise RuntimeError(f"{result['variant']} 业务响应序列不完整：{actual}")
    reference = [item for item in results if item["variant"] == "reference"]
    instrumented = [item for item in results if item["variant"] == "afl"]
    for variant_results in (reference, instrumented):
        digests = {item["semantic_transcript_sha256"] for item in variant_results}
        handles = {item["root_filehandle_sha256"] for item in variant_results}
        if len(digests) != 1 or len(handles) != 1:
            raise RuntimeError(
                f"{variant_results[0]['variant']} 同种子会话或根文件句柄跨重启不稳定"
            )
    if reference[0]["semantic_transcript_sha256"] != instrumented[0]["semantic_transcript_sha256"]:
        raise RuntimeError("参考版和 AFL 插桩版的协议业务状态不一致")
    report = {
        "repetitions_per_variant": repetitions,
        "variants": ["reference", "afl"],
        "mount_flow": "MOUNTv3 MNT over TCP obtains the NFSv3 root filehandle",
        "nfs_flow": [
            "GETATTR",
            "ACCESS",
            "CREATE",
            "WRITE",
            "LOOKUP",
            "READ",
            "READDIR",
            "REMOVE",
            "LOOKUP returns NFS3ERR_NOENT",
        ],
        "expected_status_sequence": expected,
        "semantic_transcript_sha256": reference[0]["semantic_transcript_sha256"],
        "root_filehandle_sha256": reference[0]["root_filehandle_sha256"],
        "sessions": results,
    }
    (output / "protocol-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"通过：参考版和 AFL 插桩版各 {repetitions} 次完成 MNT、NFSv3 创建/读写/删除；"
        "根句柄与状态序列可重复"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
