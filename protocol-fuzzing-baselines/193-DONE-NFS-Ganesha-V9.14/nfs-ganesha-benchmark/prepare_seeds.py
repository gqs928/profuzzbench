#!/usr/bin/env python3
"""从真实 MOUNT MNT 回复取文件句柄，再生成固定的 NFSv3 RPC 会话。"""

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

import nfs_rpc
from nfs_rpc import (
    NFS_PROGRAM,
    NFS_PORT,
    NFS_VERSION,
    RpcClient,
    access_args,
    create_args,
    getattr_args,
    get_root_handle,
    lookup_args,
    parse_optional_handle_after_status,
    read_args,
    rpc_call,
    readdir_args,
    remove_args,
    u32,
    write_args,
)


def nfs_request(procedure: int, arguments: bytes, xid: int) -> bytes:
    return rpc_call(NFS_PROGRAM, NFS_VERSION, procedure, arguments, xid)


def materialize_root_handle(log_dir: pathlib.Path) -> tuple[bytes, bytes]:
    binary = pathlib.Path(os.environ["GANESHA_REFERENCE_BIN"])
    config = pathlib.Path(os.environ["GANESHA_REFERENCE_CONFIG"])
    prefix = binary.parent.parent
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ":".join(
        str(path)
        for path in (
            prefix / "lib",
            prefix / "lib64",
            prefix / "lib/ganesha",
            prefix / "lib/x86_64-linux-gnu",
            prefix / "lib/x86_64-linux-gnu/ganesha",
        )
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    ganesha_log = log_dir / "seed-materialization-ganesha.log"
    ganesha_log.unlink(missing_ok=True)
    log_file = (log_dir / "seed-materialization-server.log").open("wb")
    process = subprocess.Popen(
        [
            str(binary),
            "-F",
            "-f",
            str(config),
            "-p",
            "/tmp/ganesha.pid",
            "-L",
            str(ganesha_log),
            "-N",
            "NIV_CRIT",
        ],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    "参考版 Ganesha 启动失败："
                    f"诊断日志见 {ganesha_log}；"
                    + (log_dir / "seed-materialization-server.log").read_text(
                        errors="replace"
                    )[-8000:]
                )
            try:
                with socket.create_connection(("127.0.0.1", nfs_rpc.MOUNT_PORT), timeout=0.2):
                    root_handle = get_root_handle()
                    with RpcClient(NFS_PORT) as client:
                        reply = client.call(
                            NFS_PROGRAM,
                            NFS_VERSION,
                            8,
                            create_args(root_handle, b"fuzzbench-io", guarded=True),
                        )
                        io_handle = parse_optional_handle_after_status(reply)
                    return root_handle, io_handle
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("参考版没有启动 MOUNT v3 TCP 服务")
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        log_file.close()


def main() -> None:
    output = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "seeds")
    manifest_path = pathlib.Path(
        sys.argv[2] if len(sys.argv) > 2 else output.parent / "seeds-manifest.json"
    )
    root_handle, io_handle = materialize_root_handle(output.parent)
    output.mkdir(parents=True, exist_ok=True)
    for old_seed in output.glob("*.bin"):
        old_seed.unlink()
    manifest_path.unlink(missing_ok=True)

    create_name = b"fuzzbench-file"
    duplicate_name = b"fuzzbench-duplicate"
    invalid_handle = bytes.fromhex("ff" * 16)
    seeds = {
        "mount-root.bin": nfs_rpc.rpc_call(
            nfs_rpc.MOUNT_PROGRAM,
            nfs_rpc.MOUNT_VERSION,
            1,
            nfs_rpc.xdr_string(nfs_rpc.NFS_PSEUDO),
            0x4D4E5401,
        ),
        "root-getattr.bin": nfs_request(1, getattr_args(root_handle), 0x4E465301),
        "root-access.bin": nfs_request(4, access_args(root_handle), 0x4E465302),
        "missing-lookup.bin": nfs_request(
            3, lookup_args(root_handle, b"missing-entry"), 0x4E465303
        ),
        "create-lookup-readdir-remove.bin": b"".join(
            (
                nfs_request(8, create_args(root_handle, create_name, guarded=True), 0x4E465310),
                nfs_request(3, lookup_args(root_handle, create_name), 0x4E465311),
                nfs_request(16, readdir_args(root_handle), 0x4E465312),
                nfs_request(12, remove_args(root_handle, create_name), 0x4E465313),
                nfs_request(3, lookup_args(root_handle, create_name), 0x4E465314),
            )
        ),
        "guarded-create-exists-remove.bin": b"".join(
            (
                nfs_request(8, create_args(root_handle, duplicate_name, guarded=True), 0x4E465320),
                nfs_request(8, create_args(root_handle, duplicate_name, guarded=True), 0x4E465321),
                nfs_request(12, remove_args(root_handle, duplicate_name), 0x4E465322),
            )
        ),
        "write-read-create-remove.bin": b"".join(
            (
                nfs_request(
                    8,
                    create_args(root_handle, b"fuzzbench-io", guarded=True),
                    0x4E465330,
                ),
                nfs_request(
                    7,
                    write_args(io_handle, b"nfs-ganesha-benchmark-data"),
                    0x4E465331,
                ),
                nfs_request(
                    6,
                    read_args(io_handle, count=len(b"nfs-ganesha-benchmark-data")),
                    0x4E465332,
                ),
                nfs_request(
                    12,
                    remove_args(root_handle, b"fuzzbench-io"),
                    0x4E465333,
                ),
            )
        ),
        "bad-handle-getattr.bin": nfs_request(
            1, getattr_args(invalid_handle), 0x4E465330
        ),
        "procedure-unavailable.bin": nfs_request(99, b"", 0x4E465340),
        "malformed-xdr-lookup.bin": nfs_request(
            3, getattr_args(root_handle) + u32(8) + b"x", 0x4E465350
        ),
    }
    truncated = nfs_request(1, getattr_args(root_handle), 0x4E465360)
    seeds["truncated-record-tail.bin"] = truncated[:-2]

    manifest = []
    for name, data in sorted(seeds.items()):
        path = output / name
        path.write_bytes(data)
        manifest.append(
            {
                "file": name,
                "bytes": len(data),
                "records": len(nfs_rpc.split_records(data)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest_path.write_text(
        json.dumps(
            {
                "source": "real MOUNT v3 MNT reply from the pinned NFS-Ganesha server",
                "root_filehandle_sha256": hashlib.sha256(root_handle).hexdigest(),
                "root_filehandle_bytes": len(root_handle),
                "pseudo_path": nfs_rpc.NFS_PSEUDO,
                "seeds": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"已从 MNT 回复取得 {len(root_handle)} 字节文件句柄；"
        f"生成 {len(seeds)} 个含状态操作的 RPC 种子到 {output}"
    )


if __name__ == "__main__":
    main()
